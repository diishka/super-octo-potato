export function SectionCard({ eyebrow, title, action, children, className = "" }) {
  return (
    <section className={`section-card ${className}`.trim()}>
      <div className="section-header">
        <div>
          {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
          <h2>{title}</h2>
        </div>
        {action ? <div className="section-action">{action}</div> : null}
      </div>
      <div className="section-body">{children}</div>
    </section>
  );
}
