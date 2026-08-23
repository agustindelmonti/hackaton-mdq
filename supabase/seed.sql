-- Worked examples for the generic custody-chain configuration schema
-- (see supabase/migrations/0001_custody_chain_config.sql).
--
-- This file is intentionally NOT applied to remote/production databases by
-- the Supabase CLI (only `supabase db reset` runs it locally). Its purpose
-- here is documentation: each block below is a self-contained example of
-- how a different industry maps onto location_type / category /
-- unit_of_measure / decay_curve, so a new tenant can be modeled by copying
-- the closest block instead of reading the whole schema from scratch.
--
-- Tenant ids are hardcoded, readable UUIDs (not gen_random_uuid()) so the
-- FK references below stay legible as documentation.
--
-- None of the numbers below are real regulatory or lab data — they are
-- illustrative orders of magnitude to show the *shape* of each curve/ladder,
-- the same way the original seed-potato figures in this repo were.

-- ============================================================================
-- 1. Seed potato (this repo's original, hardcoded use case) — data-papasud/dominio.py
-- ============================================================================
insert into tenant (id, name, industry) values
  ('11111111-1111-1111-1111-111111111111', 'Papasud', 'seed potato');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('11111111-1111-1111-1111-111111111111', 'cold_room', 'Cold room', 'snowflake', '{"target_temp_c": 4, "target_temp_tolerance_c": 1}'),
  ('11111111-1111-1111-1111-111111111111', 'warehouse', 'Warehouse', 'warehouse', '{}'),
  ('11111111-1111-1111-1111-111111111111', 'field', 'Field', 'sprout', '{"area_ha": null}'),
  ('11111111-1111-1111-1111-111111111111', 'lab', 'Lab', 'flask', '{}');

-- INASE seed-category ladder. NOTE: the exact article-level ordering of the
-- last steps ("Certificada A" vs "Certificada B") is disputed between
-- sources in this project's own research (see docs/ — Res. INASE 245/98 vs
-- 171/2000) and was never confirmed with Papasud. Treat sort_order here as
-- illustrative of the *shape* of the ladder, not a citable ordering.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('11111111-1111-1111-1111-111111111111', 'pre_basic_0', 'Preinicial 0', 0, 'child_gte_parent', '{"max_virus_pct": 0}'),
  ('11111111-1111-1111-1111-111111111111', 'pre_basic_1', 'Preinicial I', 1, 'child_gte_parent', '{"max_virus_pct": 0}'),
  ('11111111-1111-1111-1111-111111111111', 'pre_basic_2', 'Preinicial II', 2, 'child_gte_parent', '{"max_virus_pct": 0.1}'),
  ('11111111-1111-1111-1111-111111111111', 'basic_1', 'Inicial I', 3, 'child_gte_parent', '{"max_virus_pct": 0.5}'),
  ('11111111-1111-1111-1111-111111111111', 'basic_2', 'Inicial II', 4, 'child_gte_parent', '{"max_virus_pct": 1}'),
  ('11111111-1111-1111-1111-111111111111', 'basic_3', 'Inicial III', 5, 'child_gte_parent', '{"max_virus_pct": 1.5}'),
  ('11111111-1111-1111-1111-111111111111', 'foundation', 'Fundacion', 6, 'child_gte_parent', '{"max_virus_pct": 2}'),
  ('11111111-1111-1111-1111-111111111111', 'registered', 'Registrada', 7, 'child_gte_parent', '{"max_virus_pct": 3}'),
  ('11111111-1111-1111-1111-111111111111', 'certified_a', 'Certificada A', 8, 'child_gte_parent', '{"max_virus_pct": 4}'),
  ('11111111-1111-1111-1111-111111111111', 'certified_b', 'Certificada B', 9, 'child_gte_parent', '{"max_virus_pct": 5}');

-- A bag is ~700 kg in practice (potato density caps it well below the
-- nominal 1000/1250 kg some sources assume — see CLAUDE.md). Labeled bags
-- are capped much lower by regulation.
insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('11111111-1111-1111-1111-111111111111', 'bag_700kg', 'Bulk bag (~700 kg)', 700, '{}'),
  ('11111111-1111-1111-1111-111111111111', 'field_labeled_bag', 'Labeled field bag', null, '{"max_kg": 50}'),
  ('11111111-1111-1111-1111-111111111111', 'prebasic_labeled_bag', 'Labeled pre-basic bag', null, '{"max_kg": 20}');

-- Weight loss from respiration/dehydration in cold storage: non-linear,
-- front-loaded (55-70% of season loss happens in the first 30 days).
insert into decay_curve (tenant_id, category_id, days, expected_pct) values
  ('11111111-1111-1111-1111-111111111111', 'certified_a', 7, 3),
  ('11111111-1111-1111-1111-111111111111', 'certified_a', 30, 11),
  ('11111111-1111-1111-1111-111111111111', 'certified_a', 90, 15),
  ('11111111-1111-1111-1111-111111111111', 'certified_a', 180, 18);

-- ============================================================================
-- 2. Pharma cold chain (biologics / mRNA vaccines)
-- ============================================================================
insert into tenant (id, name, industry) values
  ('22222222-2222-2222-2222-222222222222', 'Example Pharma Co', 'pharma cold chain');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('22222222-2222-2222-2222-222222222222', 'cold_room', 'Cold room (2-8C)', 'snowflake', '{"target_temp_c": 5, "target_temp_tolerance_c": 3}'),
  ('22222222-2222-2222-2222-222222222222', 'distribution_center', 'Distribution center', 'warehouse', '{}'),
  ('22222222-2222-2222-2222-222222222222', 'pharmacy', 'Pharmacy / point of care', 'building', '{}'),
  ('22222222-2222-2222-2222-222222222222', 'lab', 'QA lab', 'flask', '{}');

-- API (active pharmaceutical ingredient) grade ladder: a finished dose can
-- only descend from an API lot graded sterile-injectable or higher.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('22222222-2222-2222-2222-222222222222', 'api_industrial', 'API - industrial grade', 0, 'child_gte_parent', '{}'),
  ('22222222-2222-2222-2222-222222222222', 'api_pharma_grade', 'API - pharma grade', 1, 'child_gte_parent', '{}'),
  ('22222222-2222-2222-2222-222222222222', 'api_sterile_injectable', 'API - sterile injectable grade', 2, 'child_gte_parent', '{}'),
  ('22222222-2222-2222-2222-222222222222', 'finished_dose_mrna', 'Finished dose - mRNA vaccine', 3, 'child_gte_parent', '{}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('22222222-2222-2222-2222-222222222222', 'vial_box_100', 'Box of 100 vials', null, '{}'),
  ('22222222-2222-2222-2222-222222222222', 'cold_chain_pallet', 'Cold-chain pallet', null, '{"max_boxes": 200}');

-- "Decay" here is potency loss from a broken/degraded cold chain, not
-- weight loss — same non-linear, front-loaded shape as the potato curve.
insert into decay_curve (tenant_id, category_id, days, expected_pct) values
  ('22222222-2222-2222-2222-222222222222', 'finished_dose_mrna', 1, 2),
  ('22222222-2222-2222-2222-222222222222', 'finished_dose_mrna', 7, 15),
  ('22222222-2222-2222-2222-222222222222', 'finished_dose_mrna', 30, 40);

-- ============================================================================
-- 3. Winery (barrel aging + appellation classification)
-- ============================================================================
insert into tenant (id, name, industry) values
  ('33333333-3333-3333-3333-333333333333', 'Example Winery', 'wine production');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('33333333-3333-3333-3333-333333333333', 'vineyard', 'Vineyard block', 'grape', '{}'),
  ('33333333-3333-3333-3333-333333333333', 'barrel_cellar', 'Barrel cellar', 'barrel', '{"target_temp_c": 15}'),
  ('33333333-3333-3333-3333-333333333333', 'bottling_line', 'Bottling line', 'factory', '{}'),
  ('33333333-3333-3333-3333-333333333333', 'warehouse', 'Finished-goods warehouse', 'warehouse', '{}');

-- Classification tier: a blend can only be declared at a tier its base
-- lots are certified for — you cannot "promote" table wine into a grand cru.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('33333333-3333-3333-3333-333333333333', 'table_wine', 'Table wine', 0, 'child_gte_parent', '{}'),
  ('33333333-3333-3333-3333-333333333333', 'appellation_controlled', 'Appellation controlled', 1, 'child_gte_parent', '{}'),
  ('33333333-3333-3333-3333-333333333333', 'grand_cru', 'Grand cru', 2, 'child_gte_parent', '{}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('33333333-3333-3333-3333-333333333333', 'barrel_225l', 'Oak barrel (225 L)', null, '{"volume_l": 225}'),
  ('33333333-3333-3333-3333-333333333333', 'case_12_bottles', 'Case of 12 bottles', null, '{}');

-- Evaporation during barrel aging ("angel's share"). Grand cru lots
-- typically age longest, so cumulative evaporation is highest for them.
insert into decay_curve (tenant_id, category_id, days, expected_pct) values
  ('33333333-3333-3333-3333-333333333333', 'grand_cru', 30, 1.5),
  ('33333333-3333-3333-3333-333333333333', 'grand_cru', 180, 5),
  ('33333333-3333-3333-3333-333333333333', 'grand_cru', 365, 8);

-- ============================================================================
-- 4. Dairy (cheese aging)
-- ============================================================================
insert into tenant (id, name, industry) values
  ('44444444-4444-4444-4444-444444444444', 'Example Dairy Co', 'dairy / cheese aging');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('44444444-4444-4444-4444-444444444444', 'aging_cave', 'Aging cave', 'mountain', '{"target_humidity_pct": 85}'),
  ('44444444-4444-4444-4444-444444444444', 'cold_room', 'Cold room', 'snowflake', '{}'),
  ('44444444-4444-4444-4444-444444444444', 'dairy_farm', 'Dairy farm', 'sprout', '{}'),
  ('44444444-4444-4444-4444-444444444444', 'packing_plant', 'Packing plant', 'factory', '{}');

-- A hard-paste wheel must trace back to milk lots that met hard-paste spec.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('44444444-4444-4444-4444-444444444444', 'soft_paste', 'Soft paste', 0, 'child_gte_parent', '{}'),
  ('44444444-4444-4444-4444-444444444444', 'semi_hard_paste', 'Semi-hard paste', 1, 'child_gte_parent', '{}'),
  ('44444444-4444-4444-4444-444444444444', 'hard_paste', 'Hard paste', 2, 'child_gte_parent', '{}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('44444444-4444-4444-4444-444444444444', 'wheel_avg_9kg', 'Cheese wheel (avg ~9 kg)', 9, '{}'),
  ('44444444-4444-4444-4444-444444444444', 'block_20kg', 'Block (20 kg)', 20, '{}');

-- Weight loss from dehydration during ripening — structurally identical to
-- the potato curve, just a different physical process and category.
insert into decay_curve (tenant_id, category_id, days, expected_pct) values
  ('44444444-4444-4444-4444-444444444444', 'soft_paste', 15, 4),
  ('44444444-4444-4444-4444-444444444444', 'soft_paste', 45, 9),
  ('44444444-4444-4444-4444-444444444444', 'hard_paste', 180, 12);

-- ============================================================================
-- 5. Medicinal cannabis (flower curing)
-- ============================================================================
insert into tenant (id, name, industry) values
  ('55555555-5555-5555-5555-555555555555', 'Example Cannabis Co', 'medicinal cannabis');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('55555555-5555-5555-5555-555555555555', 'grow_room', 'Grow room', 'sprout', '{}'),
  ('55555555-5555-5555-5555-555555555555', 'curing_room', 'Curing room', 'jar', '{"target_humidity_pct": 62}'),
  ('55555555-5555-5555-5555-555555555555', 'cold_room', 'Cold room', 'snowflake', '{}'),
  ('55555555-5555-5555-5555-555555555555', 'dispensary', 'Dispensary', 'building', '{}');

-- A batch labeled "indoor" must trace back to mother/clone lots grown indoor.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('55555555-5555-5555-5555-555555555555', 'outdoor', 'Outdoor', 0, 'child_gte_parent', '{}'),
  ('55555555-5555-5555-5555-555555555555', 'greenhouse', 'Greenhouse', 1, 'child_gte_parent', '{}'),
  ('55555555-5555-5555-5555-555555555555', 'indoor', 'Indoor', 2, 'child_gte_parent', '{}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('55555555-5555-5555-5555-555555555555', 'jar_1oz', 'Jar (1 oz / ~28 g)', 0.028, '{}'),
  ('55555555-5555-5555-5555-555555555555', 'case_1kg', 'Case (1 kg)', 1, '{}');

-- THC/terpene degradation during curing and storage, not weight loss.
insert into decay_curve (tenant_id, category_id, days, expected_pct) values
  ('55555555-5555-5555-5555-555555555555', 'indoor', 7, 3),
  ('55555555-5555-5555-5555-555555555555', 'indoor', 30, 8),
  ('55555555-5555-5555-5555-555555555555', 'indoor', 90, 15);

-- ============================================================================
-- 6. Semiconductor (wafer -> die bin grading)
--
-- Deliberately has NO decay_curve rows: not every tenant needs every table
-- populated. Silicon dies don't decay in storage the way organic products
-- do — this tenant only exercises location_type / category / unit_of_measure,
-- and its lineage_rule runs in the OPPOSITE direction from every other
-- example here.
-- ============================================================================
insert into tenant (id, name, industry) values
  ('66666666-6666-6666-6666-666666666666', 'Example Semiconductor Co', 'semiconductor manufacturing');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('66666666-6666-6666-6666-666666666666', 'fab', 'Fabrication plant', 'factory', '{}'),
  ('66666666-6666-6666-6666-666666666666', 'test_floor', 'Test floor', 'flask', '{}'),
  ('66666666-6666-6666-6666-666666666666', 'bin_warehouse', 'Binned-die warehouse', 'warehouse', '{}'),
  ('66666666-6666-6666-6666-666666666666', 'distribution_center', 'Distribution center', 'warehouse', '{}');

-- Binning grade: a die can never be binned ABOVE the max grade its parent
-- wafer lot tested at, so lineage_rule is child_lte_parent here — the
-- mirror image of the seed-potato/pharma/coffee/dairy/cannabis examples.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('66666666-6666-6666-6666-666666666666', 'die_bin_c', 'Bin C (low speed)', 0, 'child_lte_parent', '{}'),
  ('66666666-6666-6666-6666-666666666666', 'die_bin_b', 'Bin B (mid speed)', 1, 'child_lte_parent', '{}'),
  ('66666666-6666-6666-6666-666666666666', 'die_bin_a', 'Bin A (high speed)', 2, 'child_lte_parent', '{"min_speed_mhz": 3800}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('66666666-6666-6666-6666-666666666666', 'wafer_lot_25', 'Wafer lot (25 wafers)', null, '{}'),
  ('66666666-6666-6666-6666-666666666666', 'tray_of_484', 'Die tray (484 units)', null, '{}');

-- ============================================================================
-- 7. Coffee (grading / specialty classification)
-- ============================================================================
insert into tenant (id, name, industry) values
  ('77777777-7777-7777-7777-777777777777', 'Example Coffee Co', 'coffee production');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('77777777-7777-7777-7777-777777777777', 'wet_mill', 'Wet mill', 'droplet', '{}'),
  ('77777777-7777-7777-7777-777777777777', 'dry_mill', 'Dry mill', 'sun', '{}'),
  ('77777777-7777-7777-7777-777777777777', 'warehouse', 'Warehouse', 'warehouse', '{}'),
  ('77777777-7777-7777-7777-777777777777', 'roastery', 'Roastery', 'factory', '{}');

-- A green-coffee lot can never be labeled specialty without traceable
-- lineage to a cherry lot that scored at or above the specialty threshold.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('77777777-7777-7777-7777-777777777777', 'commercial', 'Commercial', 0, 'child_gte_parent', '{}'),
  ('77777777-7777-7777-7777-777777777777', 'premium', 'Premium', 1, 'child_gte_parent', '{}'),
  ('77777777-7777-7777-7777-777777777777', 'specialty_80', 'Specialty (SCA >= 80)', 2, 'child_gte_parent', '{"min_sca_score": 80}'),
  ('77777777-7777-7777-7777-777777777777', 'specialty_85', 'Specialty micro-lot (SCA >= 85)', 3, 'child_gte_parent', '{"min_sca_score": 85}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('77777777-7777-7777-7777-777777777777', 'bag_60kg', 'Green coffee bag (60 kg)', 60, '{}'),
  ('77777777-7777-7777-7777-777777777777', 'micro_lot_box_1kg', 'Micro-lot box (1 kg)', 1, '{}');

-- Green-bean moisture loss / staling during storage.
insert into decay_curve (tenant_id, category_id, days, expected_pct) values
  ('77777777-7777-7777-7777-777777777777', 'specialty_80', 30, 1),
  ('77777777-7777-7777-7777-777777777777', 'specialty_80', 180, 3),
  ('77777777-7777-7777-7777-777777777777', 'specialty_80', 365, 5);

-- ============================================================================
-- 8. Textile (cotton fiber grading)
--
-- Also deliberately has NO decay_curve rows: raw fiber doesn't meaningfully
-- decay in storage the way perishables do.
-- ============================================================================
insert into tenant (id, name, industry) values
  ('88888888-8888-8888-8888-888888888888', 'Example Textile Co', 'textile / cotton');

insert into location_type (tenant_id, id, label, icon, attributes) values
  ('88888888-8888-8888-8888-888888888888', 'gin', 'Cotton gin', 'factory', '{}'),
  ('88888888-8888-8888-8888-888888888888', 'spinning_mill', 'Spinning mill', 'factory', '{}'),
  ('88888888-8888-8888-8888-888888888888', 'warehouse', 'Warehouse', 'warehouse', '{}'),
  ('88888888-8888-8888-8888-888888888888', 'weaving_mill', 'Weaving mill', 'factory', '{}');

-- A "Pima"-labeled yarn lot must trace back to long-staple fiber bales.
insert into category (tenant_id, id, label, sort_order, lineage_rule, attributes) values
  ('88888888-8888-8888-8888-888888888888', 'short_staple', 'Short staple', 0, 'child_gte_parent', '{}'),
  ('88888888-8888-8888-8888-888888888888', 'medium_staple', 'Medium staple', 1, 'child_gte_parent', '{}'),
  ('88888888-8888-8888-8888-888888888888', 'long_staple_pima', 'Long staple (Pima/Egyptian)', 2, 'child_gte_parent', '{}');

insert into unit_of_measure (tenant_id, id, label, weight_kg, max_capacity) values
  ('88888888-8888-8888-8888-888888888888', 'bale_220kg', 'Cotton bale (~220 kg)', 220, '{}');
