import { useEffect, useId, useRef, useState } from "react";
import { AlertTriangle, HelpCircle, RefreshCw, ExternalLink } from "lucide-react";
import { useT } from "../lib/i18n";

// ============================================================================
// ConfidenceIndicator — the "Confidence Indicators" AI-UX pattern
// (score / meter / badge / hedging copy), adapted to this app's design
// system (Tailwind v4 tokens in index.css, useT i18n, tabular-nums money).
//
// The pattern exists to help a person decide whether to trust, verify, or
// escalate — so every guard below maps to one of the anti-patterns it's
// meant to prevent. This component refuses to be pure decoration:
//
//   - No sampleSize            → never prints a percentage (a number with no
//                                 casework behind it is the "97% forever"
//                                 anti-pattern, just with a different digit).
//   - No evidence link          → band is forced to 'unverified' regardless
//                                 of score. A green badge with no path to a
//                                 source is worse than no badge.
//   - tier === 3 (an agent      → always capped at 'unverified'. An LLM
//     hypothesis, not a rule)     hypothesis is never "confirmed" on its own.
//   - No legend prop            → dev-time console.error; falls back to
//                                 generic copy rather than shipping an
//                                 unexplained color silently.
//   - Every band, including     → the hedge caption always renders. A
//     'high', shows its caption   confident tone never hides the sample size
//                                 it's actually resting on.
//
// This is a per-claim component, not a per-sentence one: call it once for
// the specific claim that's costly to get wrong (a hypothesis, a diagnosis,
// a recommendation), not once per line of prose. See
// .claude/skills/confidence-indicators/SKILL.md for the full pattern brief
// and the "when NOT to use" list.
// ============================================================================

const BAND_TOKENS = {
  high: { text: "text-salvia", bg: "bg-salvia/10", ring: "ring-salvia/25", dot: "bg-salvia" },
  medium: { text: "text-oro-tinta", bg: "bg-oro/10", ring: "ring-oro/30", dot: "bg-oro" },
  low: { text: "text-rojo", bg: "bg-rojo/10", ring: "ring-rojo/25", dot: "bg-rojo" },
  unverified: { text: "text-hielo", bg: "bg-hielo-claro", ring: "ring-hielo/25", dot: "bg-hielo" },
};

function resolveBand({ score, sampleSize, tier, hasEvidence, qualitativeBand }) {
  // The two hard guards apply no matter which kind of signal we were given.
  if (tier === 3) return "unverified";
  if (!hasEvidence) return "unverified";

  if (sampleSize != null && sampleSize > 0 && score != null) {
    if (score >= 0.75 && sampleSize >= 5) return "high";
    if (score >= 0.4) return "medium";
    return "low";
  }
  // No measured stat yet — a caller can still assert a rule-strength
  // judgment call (e.g. "this rule is usually right"), but it renders with
  // its own disclosure copy (see autoHedge) so it never reads as a measured
  // number. This is the honest state most rules will be in until enough
  // resolved cases accumulate in diff_resolutions.
  if (qualitativeBand && ["high", "medium", "low"].includes(qualitativeBand)) {
    return qualitativeBand;
  }
  return "unverified";
}

export default function ConfidenceIndicator({
  state = "success",              // 'idle' | 'loading' | 'error' | 'success'
  variant = "badge",               // 'badge' | 'meter'
  size = "md",                     // 'sm' | 'md'
  score = null,                    // 0..1, calibrated point estimate
  sampleSize = null,               // n resolved cases behind `score`
  bounds = null,                   // [lower, upper], same 0..1 scale
  tier = null,                     // 0 rule · 1 stats · 2 ranker · 3 agent
  evidenceHref = null,
  onViewEvidence = null,
  qualitativeBand = null,          // 'high' | 'medium' | 'low' — a judgment call, not a measured stat
  legend = null,                   // { high, medium, low, unverified } — required
  hedgeText = null,                // override the auto-generated caption
  label = null,                    // override the auto-generated main label
  onRetry = null,
  className = "",
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef(null);
  const panelRef = useRef(null);
  const legendId = useId();
  const capId = useId();

  if (import.meta.env.DEV && state === "success" && !legend) {
    // eslint-disable-next-line no-console
    console.error(
      "ConfidenceIndicator: no `legend` prop — shipping a colored score with "
      + "no explanation of what high/medium/low mean in this product. "
      + "Pass legend={{ high, medium, low, unverified }}."
    );
  }

  const hasEvidence = Boolean(evidenceHref || onViewEvidence);
  const band = resolveBand({ score, sampleSize, tier, hasEvidence, qualitativeBand });
  const tokens = BAND_TOKENS[band];

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    const onClickOutside = (e) => {
      if (panelRef.current?.contains(e.target) || triggerRef.current?.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onClickOutside);
    panelRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onClickOutside);
    };
  }, [open]);

  if (state === "idle") return null;

  if (state === "loading") {
    return (
      <span
        role="status"
        aria-live="polite"
        className={`inline-flex items-center gap-1.5 rounded-full bg-crema px-2.5 py-1 text-[0.72rem] text-tinta-suave ring-1 ring-linea ${className}`}
      >
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-tinta-suave" />
        {t("conf.state_loading")}
      </span>
    );
  }

  if (state === "error") {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full bg-crema px-2.5 py-1 text-[0.72rem] text-tinta-suave ring-1 ring-linea ${className}`}>
        <AlertTriangle size={12} className="shrink-0" />
        {t("conf.state_error")}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-tinta underline decoration-dotted underline-offset-2 hover:bg-tinta/5"
          >
            <RefreshCw size={11} /> {t("conf.retry")}
          </button>
        )}
      </span>
    );
  }

  const pct = score != null ? Math.round(score * 100) : null;
  const boundsTxt = bounds
    ? `${Math.round(bounds[0] * 100)}–${Math.round(bounds[1] * 100)}%`
    : null;

  const mainLabel = label || (
    pct != null && band !== "unverified"
      ? t("conf.score_label", { pct })
      : t(`conf.band_${band}`)
  );

  const caption = hedgeText || autoHedge(t, { band, sampleSize, tier, qualitativeBand });
  const legendCopy = legend || {
    high: t("conf.legend_default_high"),
    medium: t("conf.legend_default_medium"),
    low: t("conf.legend_default_low"),
    unverified: t("conf.legend_default_unverified"),
  };

  const sizeCls = size === "sm" ? "px-2 py-0.5 text-[0.68rem]" : "px-2.5 py-1 text-[0.78rem]";

  return (
    <span className={`relative inline-flex flex-col gap-1 ${className}`}>
      <span className="inline-flex items-center gap-1.5">
        <button
          type="button"
          ref={triggerRef}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls={legendId}
          aria-describedby={caption ? capId : undefined}
          onClick={() => setOpen((v) => !v)}
          className={`inline-flex items-center gap-1.5 rounded-full font-semibold ring-1 transition ${tokens.bg} ${tokens.text} ${tokens.ring} ${sizeCls} hover:brightness-95`}
        >
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${tokens.dot}`} />
          {variant === "meter" && pct != null && band !== "unverified" ? (
            <MeterBar pct={pct} label={mainLabel} />
          ) : (
            <span className="tabular-nums normal-case">{mainLabel}</span>
          )}
          <HelpCircle size={12} className="shrink-0 opacity-60" aria-hidden="true" />
        </button>

        {hasEvidence && band !== "unverified" && (
          <EvidenceLink href={evidenceHref} onClick={onViewEvidence}>
            {t("conf.view_evidence")} <ExternalLink size={10} />
          </EvidenceLink>
        )}
      </span>

      {caption && (
        <span id={capId} className="text-[0.7rem] leading-snug text-tinta-suave">
          {caption}
          {boundsTxt && ` (${t("conf.interval_label")}: ${boundsTxt})`}
        </span>
      )}

      {open && (
        <div
          id={legendId}
          ref={panelRef}
          role="dialog"
          aria-label={t("conf.legend_title")}
          tabIndex={-1}
          className="absolute left-0 top-full z-20 mt-1.5 w-72 rounded-[0.9rem] border border-linea bg-superficie p-3 text-[0.78rem] leading-snug shadow-lg outline-none"
        >
          <p className="mb-2 text-[0.68rem] font-semibold uppercase tracking-wide text-tinta-suave">
            {t("conf.legend_title")}
          </p>
          <dl className="space-y-1.5">
            {(["high", "medium", "low", "unverified"]).map((b) => (
              <div key={b} className="flex items-start gap-2">
                <span className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${BAND_TOKENS[b].dot} ${b === band ? "" : "opacity-40"}`} />
                <div>
                  <dt className={`font-semibold ${b === band ? BAND_TOKENS[b].text : "text-tinta"}`}>
                    {t(`conf.band_${b}`)}
                  </dt>
                  <dd className="text-tinta-suave">{legendCopy[b]}</dd>
                </div>
              </div>
            ))}
          </dl>
        </div>
      )}
    </span>
  );
}

function EvidenceLink({ href, onClick, children }) {
  const cls = "inline-flex items-center gap-1 text-[0.72rem] text-hielo underline underline-offset-2 hover:text-hielo/80";
  // A real onClick handler (open a panel, jump to a source) takes priority
  // over href — but if only a URL was given, render a real <a> so it works
  // without JS, is right-clickable, and reads correctly to a screen reader.
  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={cls}>
        {children}
      </button>
    );
  }
  return (
    <a href={href} target="_blank" rel="noreferrer" className={cls}>
      {children}
    </a>
  );
}

function MeterBar({ pct, label }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <meter
        min={0}
        max={100}
        low={40}
        high={75}
        optimum={100}
        value={pct}
        aria-label={label}
        className="h-1.5 w-14 align-middle"
      />
      <span className="tabular-nums">{pct}%</span>
    </span>
  );
}

function autoHedge(t, { band, sampleSize, tier, qualitativeBand }) {
  if (tier === 3) return t("conf.hedge_agent");
  if (sampleSize != null && sampleSize > 0) return t("conf.hedge_sample", { n: sampleSize });
  if (band !== "unverified" && qualitativeBand) return t("conf.hedge_qualitative");
  return t("conf.hedge_no_data");
}
