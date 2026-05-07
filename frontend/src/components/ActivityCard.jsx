import { useState } from "react";
import { Link } from "react-router-dom";

const activityLabels = {
  watched: "посмотрел(а)",
  rated: "оценил(а)",
  recommended: "рекомендует",
};

export function ActivityCard({ activity, onLike, onComment, busy }) {
  const [comment, setComment] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (!comment.trim()) {
      return;
    }
    await onComment(activity.id, comment.trim());
    setComment("");
  }

  return (
    <article className="activity-card">
      <div className="activity-poster">
        {activity.movie?.poster_url ? (
          <img src={activity.movie.poster_url} alt={activity.movie.title} />
        ) : (
          <div className="poster-fallback">NO SIGNAL</div>
        )}
      </div>

      <div className="activity-main">
        <div className="activity-heading">
          <div>
            <span className="activity-user">@{activity.user.username}</span>
            <p className="activity-text">
              {activityLabels[activity.activity_type] || "сделал(а) update"}{" "}
              <Link to={`/movie/${activity.movie.id}`}>{activity.movie.title}</Link>
            </p>
          </div>
          <span className="activity-meta">{new Date(activity.created_at).toLocaleString()}</span>
        </div>

        {activity.metadata?.rating ? (
          <div className="pill-row">
            <span className="pill neon">{activity.metadata.rating}/10</span>
          </div>
        ) : null}

        <div className="activity-actions">
          <button
            type="button"
            className={activity.liked_by_me ? "ghost-button active" : "ghost-button"}
            onClick={() => onLike(activity.id)}
            disabled={busy}
          >
            ♥ {activity.like_count}
          </button>
          <span className="muted-inline">{activity.comment_count} комментариев</span>
        </div>

        <div className="comment-stack">
          {activity.comments?.map((item) => (
            <div key={item.id} className="comment-bubble">
              <strong>@{item.user.username}</strong>
              <p>{item.text}</p>
            </div>
          ))}
        </div>

        <form className="inline-form" onSubmit={handleSubmit}>
          <input
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Добавь комментарий в ленту..."
          />
          <button type="submit" className="primary-button compact" disabled={busy}>
            Отправить
          </button>
        </form>
      </div>
    </article>
  );
}
