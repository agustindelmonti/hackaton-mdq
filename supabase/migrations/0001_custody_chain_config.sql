-- Generic custody-chain configuration schema
--
-- Context: the current operation map (backend/core/mapa.py,
-- frontend/src/sections/MapaOperacion.jsx) hardcodes the potato-seed domain
-- (INASE category ladder, brotacion/decay window, bolson weight) as Python
-- constants in data-papasud/dominio.py. That makes the graph engine unusable
-- for any other industry.
--
-- This migration introduces a per-tenant configuration layer so the same
-- custody-chain graph (locations, lots, movements, stock) can serve any
-- industry that tracks a chain of custody with a graded/lineage hierarchy
-- and a non-linear decay curve, by swapping rows instead of code. See
-- supabase/seed.sql for worked examples across several industries.

create extension if not exists pgcrypto;

-- One row per customer/organization using the system. Every config table
-- below is scoped to a tenant so unrelated industries never collide.
create table tenant (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  industry    text,                         -- free-text label, e.g. "seed potato", "pharma cold chain"
  created_at  timestamptz not null default now()
);

comment on table tenant is
  'A customer/organization. Every domain-config table is scoped to a tenant so the schema can serve multiple industries at once.';

-- Kinds of physical (or virtual) locations a lot can sit at: a cold room,
-- a warehouse, a field, a lab, a barrel cellar, a curing room, etc.
-- Replaces the hardcoded UBICACIONES dict in data-papasud/dominio.py.
create table location_type (
  tenant_id   uuid not null references tenant(id) on delete cascade,
  id          text not null,                -- slug, e.g. 'cold_room', 'barrel_cellar'
  label       text not null,                -- UI display label
  icon        text,                         -- icon key resolved client-side
  attributes  jsonb not null default '{}'::jsonb,  -- free-form per-type fields (capacity_kg, target_temp_c, ...)
  primary key (tenant_id, id)
);

comment on table location_type is
  'Tenant-defined kinds of locations in the custody chain (cold room, field, lab, cellar, curing room, ...). Replaces hardcoded location constants.';
comment on column location_type.attributes is
  'Schema-less per-type fields, e.g. {"capacity_kg": 50000, "target_temp_c": 4} for a cold room, or {"target_humidity_pct": 70} for a curing room.';

-- The graded/lineage hierarchy a lot's category belongs to (e.g. INASE seed
-- categories, pharma API grades, wafer bin grades, coffee grading tiers).
-- "sort_order" is what the lineage-validation rule compares: a child lot's
-- category must be on the correct side of its parent lot's category.
--
-- IMPORTANT: the comparison direction is NOT universal. In seed potato /
-- pharma / coffee / textile, a child lot's grade must be >= its parent's
-- grade (you cannot "promote" a lot to a higher category than its lineage
-- supports). In semiconductor die binning it runs the other way: a die can
-- never be binned ABOVE the max grade its parent wafer tested at, i.e.
-- child <= parent. lineage_rule makes this explicit and queryable instead
-- of assuming one direction, as the original mapa.py did with a hardcoded
-- "Preinicial" string match.
create table category (
  tenant_id     uuid not null references tenant(id) on delete cascade,
  id            text not null,              -- slug, e.g. 'certified_a', 'die_bin_a'
  label         text not null,
  sort_order    int not null,               -- position in the ladder; compared per lineage_rule
  lineage_rule  text not null default 'child_gte_parent'
                  check (lineage_rule in ('child_gte_parent', 'child_lte_parent')),
  attributes    jsonb not null default '{}'::jsonb,  -- free-form per-category fields (max_virus_pct, min_sca_score, ...)
  primary key (tenant_id, id)
);

comment on table category is
  'Tenant-defined graded/lineage hierarchy (seed category ladder, API grade, wafer bin, coffee grade, ...). sort_order + lineage_rule drive lineage validation.';
comment on column category.lineage_rule is
  'child_gte_parent: a child lot''s sort_order must be >= its parent''s (seed potato, pharma, coffee, textile). child_lte_parent: a child lot''s sort_order must be <= its parent''s (semiconductor die binning).';
comment on column category.attributes is
  'Schema-less per-category fields, e.g. {"max_virus_pct": 0.5} for a seed category, or {"min_sca_score": 80} for a coffee grade.';

-- The unit a quantity is counted in, and its real-world weight/capacity.
-- Replaces the hardcoded KG_POR_BOLSON constant (which, notably, was wrong
-- in the original code: 1000 instead of the real ~700 kg per bag).
create table unit_of_measure (
  tenant_id     uuid not null references tenant(id) on delete cascade,
  id            text not null,              -- slug, e.g. 'bag_700kg', 'barrel_225l'
  label         text not null,
  weight_kg     numeric,                    -- null when the unit has no fixed weight
  max_capacity  jsonb,                      -- free-form, e.g. {"max_kg": 50} for a labeled field bag
  primary key (tenant_id, id)
);

comment on table unit_of_measure is
  'Tenant-defined counting unit and its real-world weight/capacity (a potato bag, a wine barrel, a semiconductor lot carrier, ...).';

-- Non-linear decay/loss curve by category and days in storage: weight loss
-- from respiration (potato), potency loss from a broken cold chain
-- (pharma), evaporation during aging (wine), THC degradation (cannabis
-- flower), moisture loss during ripening (cheese), etc. Discrepancy
-- validation reads this table instead of assuming a flat percentage.
create table decay_curve (
  tenant_id     uuid not null references tenant(id) on delete cascade,
  category_id   text not null,
  days          int not null check (days >= 0),
  expected_pct  numeric not null check (expected_pct >= 0 and expected_pct <= 100),
  primary key (tenant_id, category_id, days),
  foreign key (tenant_id, category_id) references category(tenant_id, id) on delete cascade
);

comment on table decay_curve is
  'Expected cumulative loss/decay (%) by category and days in storage. Non-linear on purpose: most domains front-load loss in the first days/weeks, mirroring the "55-70% of season loss happens in the first 30 days" rule for seed potato.';
comment on column decay_curve.expected_pct is
  'Cumulative expected loss at this many days, as a percentage of the originally declared quantity/potency. Discrepancy validation compares (declared - expected_pct-at-day-N) against the actual count, not declared vs count directly.';
