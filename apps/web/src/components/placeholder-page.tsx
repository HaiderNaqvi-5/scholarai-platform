type DetailCard = {
  title: string;
  body: string;
};

type PlaceholderPageProps = {
  eyebrow: string;
  title: string;
  summary: string;
  metrics: Array<{ label: string; value: string }>;
  primaryActionLabel: string;
  secondaryActionLabel: string;
  detailCards: DetailCard[];
  placeholderList: string[];
};

export function PlaceholderPage({
  eyebrow,
  title,
  summary,
  metrics,
  primaryActionLabel,
  secondaryActionLabel,
  detailCards,
  placeholderList,
}: PlaceholderPageProps) {
  return (
    <main className="page-frame">
      <section className="surface-panel space-y-8">
        <div className="space-y-4">
          <p className="eyebrow">{eyebrow}</p>
          <h1 className="page-title">{title}</h1>
          <p className="lead">{summary}</p>
        </div>

        <div className="metric-row">
          {metrics.map((metric) => (
            <div className="metric-chip" key={metric.label}>
              <strong>{metric.label}</strong>
              <span>{metric.value}</span>
            </div>
          ))}
        </div>

        <div className="action-row" aria-hidden="true">
          <span className="primary-link">{primaryActionLabel}</span>
          <span className="secondary-link">{secondaryActionLabel}</span>
        </div>
      </section>

      <section className="route-grid mt-8">
        <div className="subgrid">
          {detailCards.map((card) => (
            <article className="tone-card" key={card.title}>
              <div className="space-y-3">
                <p className="token-pill">Placeholder</p>
                <h2 className="section-title">{card.title}</h2>
                <p className="body-copy">{card.body}</p>
              </div>
            </article>
          ))}
        </div>

        <aside className="surface-panel">
          <div className="space-y-4">
            <p className="token-pill">Initial scope</p>
            <h2 className="section-title">What this route reserves</h2>
            <ul className="list-block">
              {placeholderList.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </aside>
      </section>
    </main>
  );
}
