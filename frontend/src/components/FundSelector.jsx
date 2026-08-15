const CATEGORY_ORDER = ["Large Cap", "Flexi Cap", "Mid Cap"];

function CheckIcon() {
  return (
    <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
      <path
        d="M3.5 8.2 6.4 11.1 12.5 4.8"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
      <path
        d="M4 10h11M11 5l5 5-5 5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function FundSelector({
  funds,
  selected,
  onToggle,
  onSubmit,
  loading,
  submitting,
  error,
}) {
  const grouped = CATEGORY_ORDER.map((category) => ({
    category,
    items: funds.filter((f) => f.category === category),
  })).filter((g) => g.items.length > 0);

  const canSubmit = selected.length >= 2 && !submitting;

  return (
    <aside className="card selector">
      <div className="brand">
        <span className="logo" aria-hidden="true">
          <span className="logo-circle logo-navy" />
          <span className="logo-circle logo-green" />
        </span>
        <span className="brand-name">portfolio overlap.</span>
      </div>

      <h1 className="selector-title">Which funds do you hold?</h1>
      <p className="selector-sub">
        Select the mutual funds you currently invest in.
      </p>

      {error && (
        <div className="inline-error" role="alert">
          {error}
        </div>
      )}

      <div className="selector-scroll">
        {loading && (
          <div className="chip-skeleton-wrap">
            {[0, 1, 2].map((i) => (
              <div key={i} className="skeleton-block" />
            ))}
          </div>
        )}

        {!loading &&
          grouped.map((group) => (
            <section key={group.category} className="fund-group">
              <h2 className="group-label">{group.category}</h2>
              <div className="chip-row">
                {group.items.map((fund) => {
                  const active = selected.includes(fund.name);
                  return (
                    <button
                      key={fund.name}
                      type="button"
                      className={`chip${active ? " chip-active" : ""}`}
                      onClick={() => onToggle(fund.name)}
                      aria-pressed={active}
                    >
                      {active && (
                        <span className="chip-check">
                          <CheckIcon />
                        </span>
                      )}
                      {fund.name}
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
      </div>

      <div className="selector-footer">
        {selected.length < 2 && !loading && !error && (
          <p className="hint">Pick at least 2 funds to see overlap</p>
        )}
        <button
          type="button"
          className="cta"
          onClick={onSubmit}
          disabled={!canSubmit}
        >
          See my real exposure
          <ArrowIcon />
        </button>
      </div>
    </aside>
  );
}
