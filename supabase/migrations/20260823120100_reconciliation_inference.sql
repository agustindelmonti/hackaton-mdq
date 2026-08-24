-- Tiered hypothesis + confidence engine for stock reconciliation.
--
-- Full design rationale in docs/motor-conciliacion-confianza.md. Summary of
-- the invariant this schema exists to enforce: confidence is never a
-- hand-written label. It is always computed from a log of real, human-
-- confirmed outcomes (diff_resolutions) using plain arithmetic (Wilson score
-- intervals, z-scores) — never an LLM guess, never a magic number.
--
-- Three tiers, escalating by cost and by confidence:
--   0. Deterministic rules   — exact matches against movements/notes/tare.
--   1. Statistics on tracked outcomes — empirical precision per rule
--      (rule_confidence_stats) and a real significance test for shrinkage
--      (shrinkage_discrepancies).
--   2. Lightweight ranker over tied Tier-0 candidates (future work; this
--      migration only lays the data model, diff_resolutions is its training set).
--   3. Agent — bounded-evidence LLM hypothesis, always amber, never
--      persisted as a trusted outcome until a human confirms it.

-- ---------------------------------------------------------------------------
-- Rule registry — keeps "which rule belongs to which tier" out of
-- application code, so confidence queries never hardcode that mapping.
-- ---------------------------------------------------------------------------
create table hypothesis_rules (
  rule_key    text primary key,
  tier        smallint not null check (tier between 0 and 3),
  description text not null
);

insert into hypothesis_rules (rule_key, tier, description) values
  ('unconfirmed_transfer',        0, 'An in-transit movement of this lot, out of this location, whose kg match the shortfall exactly.'),
  ('digit_entry_error',           0, 'A recent movement whose kg, off by a factor of 10, would close the difference exactly.'),
  ('physical_shrinkage_witnessed',0, 'A team note (temperature excursion, sprouting) that plausibly explains a physical loss.'),
  ('bag_tare',                    0, 'Difference below the taught tare threshold — not a shortfall, expected packaging variance.'),
  ('no_explanation',              0, 'No supporting evidence found in movements, counts, or notes; lowest-confidence default.'),
  ('shrinkage_z_score',           1, 'Statistical test of the counted vs. expected-after-shrinkage kg against the shrinkage curve variance.'),
  ('ranked_candidate_match',      2, 'Learned ranker breaking a tie between two or more Tier-0 candidates that both match.'),
  ('agent_inference',             3, 'LLM-authored hypothesis over a bounded evidence packet, used only when Tiers 0-2 found nothing.');

-- ---------------------------------------------------------------------------
-- The outcome log. One row per closed discrepancy: what was proposed, at
-- what tier, with what evidence, and whether a human later confirmed it was
-- actually correct. This table is the dataset every confidence number in
-- this system is computed from.
-- ---------------------------------------------------------------------------
create table diff_resolutions (
  id                  bigserial primary key,
  count_id            bigint not null references counts(id),
  lot_id              text not null references lots(id),
  location_id         text not null references locations(id),
  difference_kg       numeric not null,
  rule_key            text not null references hypothesis_rules(rule_key),
  tier                smallint not null check (tier between 0 and 3),
  proposed_confidence numeric check (proposed_confidence between 0 and 1),
  proposed_text       text not null,          -- the exact narration shown to the user, for audit
  evidence            jsonb not null default '{}',
  outcome             text not null default 'pending'
                       check (outcome in ('pending', 'confirmed_correct', 'confirmed_incorrect')),
  resolved_by         text,
  resolved_at          timestamptz,
  created_at          timestamptz not null default now()
);

create index on diff_resolutions (rule_key);
create index on diff_resolutions (outcome);
create index on diff_resolutions (lot_id, location_id);

comment on column diff_resolutions.proposed_confidence is
  'The confidence value actually shown to the user at proposal time, kept '
  'for audit even as rule_confidence_stats later computes a different '
  '(measured) value for the next occurrence of this rule.';

comment on column diff_resolutions.outcome is
  'Set by a human closing the discrepancy — via the equivalent of '
  'movimientos.confirmar_en_destino(), a movement correction, a shrinkage '
  'write-off, or a manual recount. Stays ''pending'' until then; nothing in '
  'this table is trusted as ground truth before a human says so.';

-- ---------------------------------------------------------------------------
-- Tier-3 only: the extra context an agent hypothesis needs, kept off the
-- Tier 0-2 rows so those never carry LLM-shaped columns they don't use.
-- ---------------------------------------------------------------------------
create table agent_hypotheses (
  id               bigserial primary key,
  resolution_id    bigint not null references diff_resolutions(id) unique,
  model            text not null,
  evidence_payload jsonb not null,     -- exactly what was handed to the model — the bounded evidence, not the whole DB
  raw_response     text not null,
  promoted_to_rule boolean not null default false,
  created_at       timestamptz not null default now()
);

comment on table agent_hypotheses is
  'A promoted_to_rule = true row is a signal, not an automatic action: it '
  'marks a pattern the agent resolved often enough that it is a candidate '
  'for becoming a Tier-0 rule. Promotion itself is still a code change.';

-- ---------------------------------------------------------------------------
-- Empirical confidence per rule, computed live — a 95% Wilson score
-- interval, not the raw proportion. With n=2 and 2 correct, this returns a
-- wide interval instead of a false 100%.
-- ---------------------------------------------------------------------------
create view rule_confidence_stats as
with resolved as (
  select
    rule_key,
    count(*) filter (where outcome in ('confirmed_correct', 'confirmed_incorrect')) as n,
    count(*) filter (where outcome = 'confirmed_correct')                           as n_correct
  from diff_resolutions
  group by rule_key
),
wilson as (
  select
    rule_key,
    n,
    n_correct,
    case when n = 0 then null else n_correct::numeric / n end as point_estimate,
    case when n = 0 then null else
      (
        (n_correct::numeric / n) + (1.96 * 1.96) / (2 * n)
        - 1.96 * sqrt((
            (n_correct::numeric / n) * (1 - n_correct::numeric / n)
            + (1.96 * 1.96) / (4 * n)
          ) / n)
      ) / (1 + (1.96 * 1.96) / n)
    end as wilson_lower_95,
    case when n = 0 then null else
      (
        (n_correct::numeric / n) + (1.96 * 1.96) / (2 * n)
        + 1.96 * sqrt((
            (n_correct::numeric / n) * (1 - n_correct::numeric / n)
            + (1.96 * 1.96) / (4 * n)
          ) / n)
      ) / (1 + (1.96 * 1.96) / n)
    end as wilson_upper_95
  from resolved
)
select
  hr.rule_key,
  hr.tier,
  hr.description,
  coalesce(w.n, 0)         as n,
  coalesce(w.n_correct, 0) as n_correct,
  w.point_estimate,
  w.wilson_lower_95,
  w.wilson_upper_95
from hypothesis_rules hr
left join wilson w using (rule_key);

comment on view rule_confidence_stats is
  'The real confidence of each rule, measured from diff_resolutions. Rules '
  'with n = 0 have never been resolved yet and carry null bounds — the '
  'application should fall back to a conservative default confidence, never '
  'to a fabricated number, when n is small or zero.';

-- ---------------------------------------------------------------------------
-- Shrinkage significance test: a real z-score against the curve's variance,
-- replacing a fixed percentage threshold with a statistical one.
-- ---------------------------------------------------------------------------
create view shrinkage_discrepancies as
select
  c.id as count_id,
  c.lot_id,
  c.location_id,
  c.declared_kg,
  c.counted_kg,
  sc.days_since_intake,
  sc.cumulative_pct,
  sc.stddev_pct,
  c.declared_kg * (1 - sc.cumulative_pct / 100) as expected_kg,
  c.counted_kg - c.declared_kg * (1 - sc.cumulative_pct / 100) as delta_kg,
  case when sc.stddev_pct > 0 and c.declared_kg > 0 then
    (c.counted_kg - c.declared_kg * (1 - sc.cumulative_pct / 100))
      / (c.declared_kg * sc.stddev_pct / 100)
  else null end as z_score,
  case
    when sc.stddev_pct > 0 and c.declared_kg > 0 and abs(
      (c.counted_kg - c.declared_kg * (1 - sc.cumulative_pct / 100))
        / (c.declared_kg * sc.stddev_pct / 100)
    ) >= 2 then 'excede_merma'
    else 'dentro_de_merma'
  end as classification
from counts c
join shrinkage_curve sc on sc.days_since_intake = 0;
-- NOTE: joining on days_since_intake = 0 is a placeholder, same caveat as
-- the original discrepancia view in papa-semilla-modelo-de-datos.md — the
-- application layer is responsible for resolving the correct days-in-storage
-- bucket per lot/location before querying this view, or this join should be
-- replaced with a lateral join against the nearest bucket. Uses
-- counts.declared_kg (the point-in-time snapshot), deliberately not a live
-- join against the `stock` view — see the comment on that column.

comment on view shrinkage_discrepancies is
  'z_score >= 2 in absolute value is the statistical threshold for '
  '"excede_merma" (~95% confidence the difference is not normal shrinkage '
  'variance) — a measured significance test, not an arbitrary percentage. '
  'Only excede_merma rows should reach an LLM for hypothesis narration, and '
  'only over this already-computed list, never over the raw base.';
