-- Example data for the core domain schema and the reconciliation inference
-- engine. Run after the migrations (`supabase db reset` applies both
-- automatically). English comments/identifiers throughout; proper nouns
-- (variety and location names) are kept as-is since they are not words to
-- translate.
--
-- What this seed demonstrates, end to end:
--   1. A lineage of two lots (fundacion -> registrada) across four locations.
--   2. A live, unresolved discrepancy that Tier 0 explains via
--      'unconfirmed_transfer' (the walkthrough in docs/motor-conciliacion-confianza.md).
--   3. A shrinkage discrepancy that trips the z-score test in
--      shrinkage_discrepancies without waiting on any historical data.
--   4. Enough resolved history in diff_resolutions for rule_confidence_stats
--      to return real, non-trivial Wilson intervals instead of an empty table.
--   5. One Tier-3 agent hypothesis, still pending human confirmation.

-- ---------------------------------------------------------------------------
-- Varieties
-- ---------------------------------------------------------------------------
insert into varieties (id, name, breeder, license, usage) values
  ('spunta',    'Spunta',    null,   null,                        'fresh'),
  ('innovator', 'Innovator', 'HZPC', 'disputed breeder royalty',  'industry');

-- ---------------------------------------------------------------------------
-- Locations and plant zones
-- ---------------------------------------------------------------------------
insert into locations (id, name, location_type, locality, province, is_subcontracted, has_scale) values
  ('plant-mdp',     'Planta Mar del Plata',       'plant',        'Mar del Plata', 'Buenos Aires', false, true),
  ('cold-dospanca',  'Frigorífico Dospanca',       'cold_storage', 'Otamendi',      'Buenos Aires', true,  false),
  ('cold-cayetano',  'Frigorífico San Cayetano',   'cold_storage', 'San Cayetano',  'Buenos Aires', true,  false),
  ('field-balcarce', 'Campo Balcarce',             'field',        'Balcarce',      'Buenos Aires', false, false);

insert into plant_zones (id, plant_id, name, zone_role) values
  ('pz-intake',   'plant-mdp', 'Recepción',       'first_intake'),
  ('pz-grading',  'plant-mdp', 'Reclasificación', 'grading_packing'),
  ('pz-dispatch', 'plant-mdp', 'Playa de despacho','dispatch');

-- ---------------------------------------------------------------------------
-- Lots: a foundation lot and its registered-generation child, plus a third
-- lot in a different variety used only for the shrinkage example.
-- ---------------------------------------------------------------------------
insert into lots (id, lot_number, variety_id, subcategory, production_zone, harvest_year,
                   parent_lot_id, seed_grower, registration_number) values
  ('lot-spunta-001', '001', 'spunta', 'fundacion',  'Balcarce', 2025, null,
    'Semillero Balcarce SA', 'INASE-8841'),
  ('lot-spunta-002', '002', 'spunta', 'registrada', 'Balcarce', 2026,
    'lot-spunta-001', 'Semillero Balcarce SA', 'INASE-9012'),
  ('lot-innovator-014', '014', 'innovator', 'certificada_A', 'Otamendi', 2025, null,
    'Semillero Otamendi SRL', 'INASE-7733');

-- ---------------------------------------------------------------------------
-- Movements: build declared stock for both example lots.
-- lot-spunta-002 arrives at cold-dospanca (18,000 kg), then 600 kg leave for
-- cold-cayetano and are never confirmed at destination — this is the
-- movement Tier 0 will find when a count later comes up short by exactly
-- that amount.
-- ---------------------------------------------------------------------------
insert into movements (lot_id, origin_id, destination_id, kg, occurred_at, registered_by,
                        source, confirmed_by, confirmed_at, movement_type) values
  ('lot-spunta-002', 'field-balcarce', 'cold-dospanca', 18000, now() - interval '45 days',
    'juan.operario', 'text', 'juan.operario', now() - interval '45 days', 'harvest_intake');

insert into movements (lot_id, origin_id, destination_id, kg, occurred_at, registered_by,
                        source, transcript, extraction_confidence, movement_type) values
  ('lot-spunta-002', 'cold-dospanca', 'cold-cayetano', 600, now() - interval '3 days',
    'maria.operaria', 'voice', 'trasladé seiscientos kilos del lote cero cero dos a San Cayetano',
    'high', 'cold_transfer');
  -- Note: no confirmed_by / confirmed_at — this is the unconfirmed transfer.

insert into movements (lot_id, origin_id, destination_id, kg, occurred_at, registered_by,
                        source, confirmed_by, confirmed_at, movement_type) values
  ('lot-innovator-014', 'field-balcarce', 'cold-cayetano', 9000, now() - interval '10 days',
    'juan.operario', 'text', 'juan.operario', now() - interval '10 days', 'harvest_intake');

-- ---------------------------------------------------------------------------
-- Shrinkage curve (placeholder values — calibrate with real operational
-- data). stddev_pct at day 0 models normal scale/weighing variance, since no
-- biological shrinkage has occurred yet.
-- ---------------------------------------------------------------------------
insert into shrinkage_curve (days_since_intake, cumulative_pct, stddev_pct) values
  (0,   0.0, 0.5),
  (30,  4.5, 0.8),
  (60,  5.8, 0.9),
  (90,  6.6, 1.0),
  (120, 7.1, 1.1);

-- ---------------------------------------------------------------------------
-- Live examples: the two discrepancies walked through in
-- docs/motor-conciliacion-confianza.md.
-- ---------------------------------------------------------------------------

-- Example A: cold-dospanca counts lot-spunta-002 at 17,400 kg against a
-- declared_kg of 18,000 — the ledger snapshot taken when the count opened,
-- which does not yet reflect the 600 kg transfer above (still unconfirmed
-- at that moment). A 600 kg shortfall that matches it exactly.
insert into counts (lot_id, location_id, declared_kg, counted_kg, counted_at, counted_by)
values ('lot-spunta-002', 'cold-dospanca', 18000, 17400, now() - interval '1 day', 'pedro.encargado')
returning id \gset live_a_

-- Example B: cold-cayetano counts lot-innovator-014 at 8,850 kg against a
-- declared 9,000 kg on day 0 — small in absolute terms, but outside 2
-- standard deviations of expected weighing variance, so
-- shrinkage_discrepancies classifies it as 'excede_merma'.
insert into counts (lot_id, location_id, declared_kg, counted_kg, counted_at, counted_by)
values ('lot-innovator-014', 'cold-cayetano', 9000, 8850, now(), 'pedro.encargado')
returning id \gset live_b_

insert into diff_resolutions (count_id, lot_id, location_id, difference_kg, rule_key, tier,
                               proposed_confidence, proposed_text, evidence, outcome)
values (
  :'live_a_id', 'lot-spunta-002', 'cold-dospanca', -600, 'unconfirmed_transfer', 0,
  0.79,
  'El movimiento del 3 días atrás sacó 600 kg de Frigorífico Dospanca hacia '
  'Frigorífico San Cayetano y nadie lo confirmó en destino. Son exactamente '
  'los kilos que faltan acá.',
  jsonb_build_object('movement_kg', 600, 'movement_source', 'voice'),
  'pending'
);

insert into diff_resolutions (count_id, lot_id, location_id, difference_kg, rule_key, tier,
                               proposed_confidence, proposed_text, evidence, outcome)
values (
  :'live_b_id', 'lot-innovator-014', 'cold-cayetano', -150, 'shrinkage_z_score', 1,
  0.95,
  'Faltan 150 kg y no es tara de bolsón: está a más de 2 desvíos estándar de '
  'la variación normal de pesaje esperada en el día 0. Conviene recontar.',
  jsonb_build_object('z_score', -3.33, 'stddev_pct', 0.5),
  'pending'
);

-- ---------------------------------------------------------------------------
-- Resolved history: fabricated past cases so rule_confidence_stats returns
-- real Wilson intervals instead of an empty table. Each block inserts
-- synthetic counts (needed only to satisfy the foreign key) and the matching
-- resolved diff_resolutions rows.
-- ---------------------------------------------------------------------------

-- unconfirmed_transfer: 11 of 13 historical proposals confirmed correct.
with hist_counts as (
  insert into counts (lot_id, location_id, declared_kg, counted_kg, counted_at, counted_by)
  select
    'lot-spunta-002', 'cold-dospanca',
    18000,
    18000 - (100 + g * 37),
    now() - (g || ' days')::interval,
    'operario_' || (1 + g % 3)
  from generate_series(1, 13) as g
  returning id
),
hist_ids as (
  select id, row_number() over (order by id) as rn from hist_counts
)
insert into diff_resolutions (count_id, lot_id, location_id, difference_kg, rule_key, tier,
                               proposed_confidence, proposed_text, evidence, outcome,
                               resolved_by, resolved_at)
select
  id, 'lot-spunta-002', 'cold-dospanca', -(100 + rn * 37), 'unconfirmed_transfer', 0,
  0.7, 'Historical seed case for rule_confidence_stats demonstration.',
  jsonb_build_object('seed', true, 'case', rn),
  case when rn <= 11 then 'confirmed_correct' else 'confirmed_incorrect' end,
  'operario_' || (1 + rn % 3), now() - (rn || ' days')::interval
from hist_ids;

-- digit_entry_error: 6 of 7 historical proposals confirmed correct.
with hist_counts as (
  insert into counts (lot_id, location_id, declared_kg, counted_kg, counted_at, counted_by)
  select
    'lot-innovator-014', 'cold-cayetano',
    9000,
    9000 - (20 + g * 11),
    now() - (g || ' days')::interval,
    'operario_' || (1 + g % 2)
  from generate_series(1, 7) as g
  returning id
),
hist_ids as (
  select id, row_number() over (order by id) as rn from hist_counts
)
insert into diff_resolutions (count_id, lot_id, location_id, difference_kg, rule_key, tier,
                               proposed_confidence, proposed_text, evidence, outcome,
                               resolved_by, resolved_at)
select
  id, 'lot-innovator-014', 'cold-cayetano', -(20 + rn * 11), 'digit_entry_error', 0,
  0.6, 'Historical seed case for rule_confidence_stats demonstration.',
  jsonb_build_object('seed', true, 'case', rn),
  case when rn <= 6 then 'confirmed_correct' else 'confirmed_incorrect' end,
  'operario_' || (1 + rn % 2), now() - (rn || ' days')::interval
from hist_ids;

-- shrinkage_z_score: 5 of 6 historical proposals confirmed correct.
with hist_counts as (
  insert into counts (lot_id, location_id, declared_kg, counted_kg, counted_at, counted_by)
  select
    'lot-spunta-001', 'cold-dospanca',
    12000,
    12000 - (80 + g * 15),
    now() - (g || ' days')::interval,
    'operario_' || (1 + g % 3)
  from generate_series(1, 6) as g
  returning id
),
hist_ids as (
  select id, row_number() over (order by id) as rn from hist_counts
)
insert into diff_resolutions (count_id, lot_id, location_id, difference_kg, rule_key, tier,
                               proposed_confidence, proposed_text, evidence, outcome,
                               resolved_by, resolved_at)
select
  id, 'lot-spunta-001', 'cold-dospanca', -(80 + rn * 15), 'shrinkage_z_score', 1,
  0.85, 'Historical seed case for rule_confidence_stats demonstration.',
  jsonb_build_object('seed', true, 'case', rn, 'z_score', -2.1 - rn * 0.1),
  case when rn <= 5 then 'confirmed_correct' else 'confirmed_incorrect' end,
  'operario_' || (1 + rn % 3), now() - (rn || ' days')::interval
from hist_ids;

-- ---------------------------------------------------------------------------
-- Tier 3: one agent hypothesis, still pending human confirmation. Shows the
-- shape of the extra columns agent_hypotheses carries and that a pending
-- agent proposal never contributes to rule_confidence_stats until resolved.
-- ---------------------------------------------------------------------------
insert into counts (lot_id, location_id, declared_kg, counted_kg, counted_at, counted_by)
values ('lot-spunta-001', 'cold-dospanca', 12000, 11400, now() - interval '2 days', 'pedro.encargado')
returning id \gset agent_

insert into diff_resolutions (count_id, lot_id, location_id, difference_kg, rule_key, tier,
                               proposed_confidence, proposed_text, evidence, outcome)
values (
  :'agent_id', 'lot-spunta-001', 'cold-dospanca', -600, 'agent_inference', 3,
  0.4,
  'No encuentro movimiento, cero de más ni nota que lo expliquen. Por el '
  'patrón de conteos de esta cámara en la última semana, podría ser un '
  'traslado a Reclasificación que se registró con el código de otro lote.',
  jsonb_build_object('tier', 3, 'source', 'agent'),
  'pending'
)
returning id \gset agent_res_

insert into agent_hypotheses (resolution_id, model, evidence_payload, raw_response, promoted_to_rule)
values (
  :'agent_res_id',
  'claude-sonnet-5',
  jsonb_build_object(
    'notes_last_14_days', jsonb_build_array('sin novedad de merma en Dospanca'),
    'other_lots_same_variety_this_week', jsonb_build_array('lot-spunta-002')
  ),
  'No encuentro movimiento, cero de más ni nota que lo expliquen. Por el patrón '
  'de conteos de esta cámara en la última semana, podría ser un traslado a '
  'Reclasificación que se registró con el código de otro lote.',
  false
);
