import { Link } from "react-router-dom";

export function MovieTile({
  title,
  posterUrl,
  to,
  meta,
  description,
  badges = [],
  actions,
  className = "",
  variant = "default",
}) {
  return (
    <article className={`movie-tile movie-tile-${variant} ${className}`.trim()}>
      <div className="movie-poster">
        {posterUrl ? <img src={posterUrl} alt={title} /> : <div className="poster-fallback">ARCHIVE</div>}
      </div>

      <div className="movie-copy">
        <div className="movie-header">
          {to ? <Link to={to}>{title}</Link> : <h3>{title}</h3>}
          {meta ? <span className="movie-meta">{meta}</span> : null}
        </div>

        {badges.length ? (
          <div className="pill-row">
            {badges.map((badge) => (
              <span key={badge} className="pill">
                {badge}
              </span>
            ))}
          </div>
        ) : null}

        {description ? <p>{description}</p> : null}
        {actions ? <div className="tile-actions">{actions}</div> : null}
      </div>
    </article>
  );
}
