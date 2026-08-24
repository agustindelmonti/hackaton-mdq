-- Core domain schema for seed-potato custody tracking.
--
-- English port of the schema drafted in docs/papa-semilla-modelo-de-datos.md.
-- The hackathon prototype (backend/core/store.py) runs on a JSON file store
-- with Spanish field names; this is the schema for the real Postgres/Supabase
-- backend going forward. See docs/motor-conciliacion-confianza.md for the
-- name-equivalence table between the two.
--
-- Design invariant carried over from the prototype: stock is never an
-- editable cell. It is always a SUM over an append-only movements ledger
-- (the `stock` view at the bottom of this file). That is what removes the
-- "two people edited the spreadsheet at once" failure mode the whole project
-- exists to fix.

-- ---------------------------------------------------------------------------
-- Varieties, as an entity — not a string in a spreadsheet cell.
-- ---------------------------------------------------------------------------
create table varieties (
  id      text primary key,          -- 'innovator', 'spunta', 'atlantic'
  name    text not null,
  breeder text,                      -- 'HZPC'
  license text,                      -- breeder's-rights regime / holder
  usage   text check (usage in ('industry', 'fresh'))
);

comment on table varieties is
  'A seed potato variety, with its breeder and licensing terms — modeled as '
  'a first-class entity because those rights are legally contestable, not '
  'incidental metadata.';

-- ---------------------------------------------------------------------------
-- Locations: the endpoints of a multi-year, multi-province custody chain.
-- ---------------------------------------------------------------------------
create table locations (
  id               text primary key,
  name             text not null,
  location_type    text not null check (
                     location_type in ('plant', 'cold_storage', 'field', 'laboratory', 'client')),
  locality         text,
  province         text,
  district         text,
  is_subcontracted boolean not null default false,   -- cold storages are usually third-party
  has_scale        boolean not null default false,   -- only the plant, in practice
  geom             jsonb
);

-- Processing stations inside the plant. Not warehouses on their own — stock
-- lives at the plant location; these are stages within it (intake scale,
-- grading/repackaging, dispatch yard).
create table plant_zones (
  id        text primary key,
  plant_id  text not null references locations(id),
  name      text not null,
  zone_role text not null check (
              zone_role in ('first_intake', 'grading_packing', 'dispatch'))
);

-- ---------------------------------------------------------------------------
-- Lots. The important column is parent_lot_id: lineage IS the model.
-- ---------------------------------------------------------------------------
create table lots (
  id                   text primary key,
  lot_number           text not null,
  variety_id           text not null references varieties(id),
  subcategory          text not null check (subcategory in (
                          'preinicial_0', 'preinicial_I', 'preinicial_II',
                          'inicial_I', 'inicial_II', 'inicial_III', 'fundacion',
                          'registrada', 'certificada_A', 'certificada_B')),
  production_zone      text not null,
  harvest_year         int not null,
  parent_lot_id        text references lots(id),
  seed_grower          text,
  registration_number  text,
  chemically_treated   boolean not null default false,
  presumed_destination text,                 -- 'export:VN' | 'domestic' | 'DEE'
  created_at           timestamptz not null default now(),
  unique (seed_grower, variety_id, subcategory, production_zone, harvest_year, lot_number)
);

comment on column lots.parent_lot_id is
  'INASE lineage rule: a lot may only descend from a subcategory that is the '
  'same as, or earlier/more foundational ("superior") than, its own. '
  'Enforcement lives in application code today (see conciliacion docs); a '
  'DB-level check constraint is future work, not part of this migration.';

create index on lots (parent_lot_id);
create index on lots (variety_id);

-- ---------------------------------------------------------------------------
-- Movements: the append-only ledger. Stock is a SUM over this, never a cell.
-- ---------------------------------------------------------------------------
create table movements (
  id                     bigserial primary key,
  lot_id                 text not null references lots(id),
  origin_id              text references locations(id),        -- null = intake/harvest
  destination_id         text references locations(id),        -- null = outbound/dispatch
  kg                     numeric not null check (kg > 0),
  kg_estimated           boolean not null default false,        -- legitimate amber state, not an error
  occurred_at            timestamptz not null default now(),
  registered_by          text not null,
  source                 text not null check (source in ('voice', 'text', 'count', 'import')),
  transcript             text,                                  -- original audio transcript, for audit
  extraction_confidence  text check (extraction_confidence in ('high', 'doubtful')),
  confirmed_by           text,                                  -- nothing is trusted unconfirmed
  confirmed_at           timestamptz,
  note                   text,
  movement_type          text,                                  -- 'hopper_intake' | 'to_cold_storage' | ...
  vehicle_type           text,                                  -- 'hopper' | 'bagged_truck'
  plant_zone             text,                                  -- 'first_intake' | 'dispatch' (a stage, not a location)
  load_order_id          text,
  scale_weight_kg        numeric,
  check (origin_id is not null or destination_id is not null)
);

create index on movements (lot_id);
create index on movements (destination_id) where confirmed_by is null;

comment on column movements.kg_estimated is
  'Primary-product regulations allow an indeterminate quantity pending '
  'weighing. This is a legitimate amber state, never a red error.';

-- ---------------------------------------------------------------------------
-- Load orders and plant reception (the field → plant handoff).
-- ---------------------------------------------------------------------------
create table load_orders (
  id                    text primary key,
  lot_id                text not null references lots(id),
  field_location_id     text not null references locations(id),
  estimated_kg          numeric not null,
  pending_weighing      boolean not null default true,
  vehicle_type          text not null,
  truck                 text,
  driver                text,
  channel               text not null default 'paper',
  missing_waybill       boolean not null default false,
  harvest_temperature_c numeric,
  notes                 text
);

create table plant_receptions (
  id               text primary key,
  load_order_id    text references load_orders(id),
  movement_id      bigint references movements(id),
  zone_id          text not null references plant_zones(id),   -- always 'first_intake'
  scale_weight_kg  numeric not null,
  estimated_kg     numeric,
  driver           text,
  truck            text,
  vehicle_type     text default 'hopper'
);

-- ---------------------------------------------------------------------------
-- Physical counts, kept separate from movements so a discrepancy is computable.
-- ---------------------------------------------------------------------------
create table counts (
  id            bigserial primary key,
  lot_id        text not null references lots(id),
  location_id   text not null references locations(id),
  declared_kg   numeric not null,
  counted_kg    numeric not null,
  counted_at    timestamptz not null default now(),
  counted_by    text not null
);

create index on counts (lot_id, location_id);

comment on column counts.declared_kg is
  'A snapshot of what the ledger claimed for this lot/location at the '
  'moment the count was taken — captured by the application from the '
  '`stock` view right before counting, not recomputed live by this table. '
  'This is deliberate: if it were a live join against `stock`, a later '
  'correcting movement would silently rewrite the discrepancy this count '
  'exposed, which breaks the audit trail in diff_resolutions. An '
  'unconfirmed movement is exactly the kind of gap that can make this '
  'value stale versus a fully-reconciled ledger — which is precisely what '
  'the ''unconfirmed_transfer'' hypothesis (Tier 0) exists to explain.';

-- ---------------------------------------------------------------------------
-- Shrinkage curve: non-linear weight loss by days in storage.
-- stddev_pct feeds the statistical significance test in the next migration
-- (see shrinkage_discrepancies in 20260823120100_reconciliation_inference.sql).
-- ---------------------------------------------------------------------------
create table shrinkage_curve (
  days_since_intake int primary key,        -- 0, 30, 60, 90, 120, ...
  cumulative_pct    numeric not null,       -- 0, 4.5, 5.8, 6.6, 7.1, ...
  stddev_pct        numeric not null default 0
);

comment on table shrinkage_curve is
  'Potatoes lose weight in cold storage through respiration and dehydration '
  '— legitimate shrinkage, not an error. 55-70% of a season''s total loss '
  'happens in the first 30 days, so this is a curve, never a flat monthly '
  'percentage. Calibrate with real operational data; these are placeholders.';

-- ---------------------------------------------------------------------------
-- Stock: a derived view, never an editable cell.
-- ---------------------------------------------------------------------------
create view stock as
select
  m.lot_id,
  loc.id   as location_id,
  loc.name as location_name,
  sum(case when m.destination_id = loc.id then m.kg
           when m.origin_id      = loc.id then -m.kg
           else 0 end) as declared_kg
from movements m
join locations loc on loc.id in (m.origin_id, m.destination_id)
group by m.lot_id, loc.id, loc.name
having sum(case when m.destination_id = loc.id then m.kg
                when m.origin_id      = loc.id then -m.kg
                else 0 end) <> 0;

comment on view stock is
  'Derived from the movements ledger, always. This is what eliminates the '
  '"two people edited the spreadsheet at once" version-conflict failure '
  'mode. Live totals only — for a stable, point-in-time expected quantity '
  'to compare a physical count against, use counts.declared_kg, not a '
  'fresh read of this view (see the comment on that column).';
