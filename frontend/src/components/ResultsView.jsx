const STOCK_COLORS = [
  "#1B4332",
  "#2D6A4F",
  "#40916C",
  "#1D3557",
  "#457B9D",
  "#B08968",
  "#9B2226",
  "#6D597A",
];

const SECTOR_META = {
  "Financial Services": { label: "Financial Services", icon: "bank" },
  IT: { label: "Information Technology", icon: "chip" },
  Energy: { label: "Energy", icon: "flame" },
  FMCG: { label: "FMCG", icon: "cart" },
  Pharma: { label: "Pharma", icon: "beaker" },
  Automobile: { label: "Automobile", icon: "car" },
  Infrastructure: { label: "Infrastructure", icon: "bridge" },
  Telecom: { label: "Telecom", icon: "signal" },
  "Consumer Durables": { label: "Consumer Durables", icon: "home" },
  Cement: { label: "Cement", icon: "block" },
  Utilities: { label: "Utilities", icon: "bolt" },
};

function hashColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return STOCK_COLORS[Math.abs(hash) % STOCK_COLORS.length];
}

function initials(name) {
  const parts = name.split(" ").filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

function SectorIcon({ type }) {
  const common = {
    viewBox: "0 0 24 24",
    width: "18",
    height: "18",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "1.8",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };

  if (type === "bank") {
    return (
      <svg {...common}>
        <path d="M3 10 12 4l9 6" />
        <path d="M5 10v8M9 10v8M15 10v8M19 10v8M4 18h16" />
      </svg>
    );
  }
  if (type === "chip") {
    return (
      <svg {...common}>
        <rect x="7" y="7" width="10" height="10" rx="1.5" />
        <path d="M9 4v3M12 4v3M15 4v3M9 17v3M12 17v3M15 17v3M4 9h3M4 12h3M4 15h3M17 9h3M17 12h3M17 15h3" />
      </svg>
    );
  }
  if (type === "cart") {
    return (
      <svg {...common}>
        <path d="M4 6h2l1.5 9h10l2-6H8" />
        <circle cx="10" cy="19" r="1.2" fill="currentColor" stroke="none" />
        <circle cx="16" cy="19" r="1.2" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  if (type === "beaker") {
    return (
      <svg {...common}>
        <path d="M9 3h6M10 3v5.2L6 17.5A2 2 0 0 0 7.8 20h8.4A2 2 0 0 0 18 17.5L14 8.2V3" />
      </svg>
    );
  }
  if (type === "flame") {
    return (
      <svg {...common}>
        <path d="M12 3c2 4-1 5 1 9 3-2 5-5 4-8 4 3 5 8 3 11a7 7 0 1 1-12.5-4C9 8 11 6 12 3z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="7" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true">
      <path
        d="M10 3v10M6.5 9.5 10 13.2l3.5-3.7M4 16.5h12"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true">
      <circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" />
      <path d="M8 7.2v4" stroke="currentColor" strokeLinecap="round" />
      <circle cx="8" cy="5.1" r="0.7" fill="currentColor" />
    </svg>
  );
}

function downloadReport(exposure) {
  const lines = [
    "Stock,Appears in,Total weight %",
    ...exposure.stocks.map(
      (s) =>
        `${s.stock},${s.funds_holding} of ${s.fund_count},${s.avg_weight}`
    ),
    "",
    "Sector,Total weight %",
    ...exposure.sectors.map((s) => `${s.sector},${s.total_weight}`),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "portfolio-overlap.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-mark" aria-hidden="true">
        <span className="logo-circle logo-navy" />
        <span className="logo-circle logo-green" />
      </div>
      <h2>Your real exposure lives here</h2>
      <p>
        Pick at least two funds on the left. We’ll show which stocks you
        actually hold — and how concentrated that really is.
      </p>
    </div>
  );
}

function ErrorState({ message }) {
  return (
    <div className="empty-state" role="alert">
      <h2>Can’t reach the database right now</h2>
      <p>{message}</p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="results-body">
      <div className="skeleton-callout" />
      <div className="skeleton-row" />
      <div className="skeleton-row" />
      <div className="skeleton-row" />
      <div className="skeleton-bar" />
      <div className="skeleton-bar" />
    </div>
  );
}

export default function ResultsView({
  exposure,
  loading,
  error,
  hasSelection,
}) {
  const showEmpty = !loading && !error && !exposure;

  return (
    <main className="card results">
      <div className="results-toolbar">
        {exposure && !loading && (
          <button
            type="button"
            className="download-btn"
            onClick={() => downloadReport(exposure)}
          >
            <DownloadIcon />
            Download report
          </button>
        )}
      </div>

      {loading && <Skeleton />}
      {error && <ErrorState message={error} />}
      {showEmpty && <EmptyState />}

      {exposure && !loading && !error && (
        <div className="results-body">
          {exposure.headline && (
            <section className="callout">
              <div className="callout-icon">
                <SectorIcon type="bank" />
              </div>
              <div>
                <h2 className="callout-title">
                  {exposure.headline.stock} appears in{" "}
                  {exposure.headline.funds_holding} of your{" "}
                  {exposure.headline.fund_count} funds.
                </h2>
                <p className="callout-sub">
                  {hasSelection &&
                  exposure.headline.funds_holding >= 2
                    ? "You have overlapping exposure. Review your top stock overlaps below."
                    : "You're more concentrated than you think. Review your top stock overlaps below."}
                </p>
              </div>
            </section>
          )}

          <section>
            <table className="stock-table">
              <thead>
                <tr>
                  <th>Stock</th>
                  <th>Appears in</th>
                  <th>
                    <span className="th-with-info">
                      Your total weight
                      <span
                        className="info-tip"
                        title="Equal-weighted average: each selected fund is one equal slice of your portfolio. Funds that don't hold the stock contribute 0."
                      >
                        <InfoIcon />
                      </span>
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {exposure.stocks.map((row) => (
                  <tr key={row.stock}>
                    <td>
                      <div className="stock-cell">
                        <span
                          className="stock-avatar"
                          style={{ background: hashColor(row.stock) }}
                        >
                          {initials(row.stock)}
                        </span>
                        {row.stock}
                      </div>
                    </td>
                    <td className="muted">
                      {row.funds_holding} of {row.fund_count}
                    </td>
                    <td className="weight">{row.avg_weight.toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="sector-section">
            <h3 className="sector-heading">Sector concentration</h3>
            <ul className="sector-list">
              {exposure.sectors.map((row) => {
                const meta = SECTOR_META[row.sector] || {
                  label: row.sector,
                  icon: "default",
                };
                const max = exposure.sectors[0]?.total_weight || 1;
                const width = Math.max(8, (row.total_weight / max) * 100);
                return (
                  <li key={row.sector} className="sector-row">
                    <span className="sector-icon">
                      <SectorIcon type={meta.icon} />
                    </span>
                    <span className="sector-name">{meta.label}</span>
                    <span className="sector-track">
                      <span
                        className="sector-fill"
                        style={{ width: `${width}%` }}
                      />
                    </span>
                    <span className="sector-pct">
                      {row.total_weight.toFixed(1)}%
                    </span>
                  </li>
                );
              })}
            </ul>
            <p className="sector-note">
              Showing top sectors by total weight across your selected funds.
            </p>
          </section>
        </div>
      )}
    </main>
  );
}
