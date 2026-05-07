import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { SectionCard } from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

function entryToForm(entry) {
  return {
    status: entry?.status || "plan_to_watch",
    rating: entry?.rating ?? "",
    review: entry?.review || "",
    recommended_to_followers: Boolean(entry?.recommended_to_followers),
    watched_at: entry?.watched_at || "",
  };
}

export function MoviePage() {
  const { movieId } = useParams();
  const { isAuthenticated, refreshProfile, token } = useAuth();
  const [movie, setMovie] = useState(null);
  const [form, setForm] = useState(entryToForm(null));
  const [linkForm, setLinkForm] = useState({ source_name: "", url: "" });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadMovie() {
      setLoading(true);
      setError("");

      try {
        const payload = await apiRequest(`/api/movies/${movieId}/`, { token });
        if (!cancelled) {
          setMovie(payload);
          setForm(entryToForm(payload.my_entry));
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(requestError.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadMovie();

    return () => {
      cancelled = true;
    };
  }, [movieId, token]);

  async function reloadMovie() {
    const payload = await apiRequest(`/api/movies/${movieId}/`, { token });
    setMovie(payload);
    setForm(entryToForm(payload.my_entry));
  }

  async function handleSave(event) {
    event.preventDefault();
    if (!isAuthenticated) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    const body = {
      status: form.status,
      rating: form.rating === "" ? null : Number(form.rating),
      review: form.review,
      recommended_to_followers: form.recommended_to_followers,
      watched_at: form.watched_at || null,
    };

    try {
      if (movie.my_entry) {
        await apiRequest(`/api/movies/library/${movieId}/`, {
          method: "PATCH",
          token,
          body,
        });
      } else {
        await apiRequest("/api/movies/library/", {
          method: "POST",
          token,
          body: {
            movie_id: Number(movieId),
            ...body,
          },
        });
      }
      await refreshProfile();
      await reloadMovie();
      setMessage("Библиотека обновлена.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove() {
    if (!isAuthenticated || !movie?.my_entry) {
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      await apiRequest(`/api/movies/library/${movieId}/`, {
        method: "DELETE",
        token,
      });
      await refreshProfile();
      await reloadMovie();
      setMessage("Фильм удалён из твоего списка.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleAddLink(event) {
    event.preventDefault();
    if (!isAuthenticated) {
      return;
    }

    setSaving(true);
    setError("");

    try {
      await apiRequest(`/api/movies/${movieId}/links/`, {
        method: "POST",
        token,
        body: linkForm,
      });
      setLinkForm({ source_name: "", url: "" });
      await reloadMovie();
      setMessage("Ссылка добавлена.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleVote(linkId, value) {
    if (!isAuthenticated) {
      return;
    }

    setSaving(true);
    setError("");

    try {
      await apiRequest(`/api/movies/links/${linkId}/vote/`, {
        method: "POST",
        token,
        body: { value },
      });
      await reloadMovie();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="page-grid">
        <SectionCard eyebrow="Loading" title="Поднимаю карточку фильма...">
          <p>Ожидание данных.</p>
        </SectionCard>
      </div>
    );
  }

  if (!movie) {
    return (
      <div className="page-grid">
        <SectionCard eyebrow="Offline" title="Фильм не найден">
          <p>{error || "Карточка недоступна."}</p>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-grid wide">
      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      <div className="movie-hero">
        <div className="movie-hero-poster">
          {movie.poster_url ? <img src={movie.poster_url} alt={movie.title} /> : <div className="poster-fallback">NO POSTER</div>}
        </div>

        <SectionCard eyebrow={movie.media_type} title={movie.title} className="movie-hero-copy">
          <div className="pill-row">
            {movie.release_year ? <span className="pill">{movie.release_year}</span> : null}
            {movie.tmdb_vote_average ? <span className="pill">TMDb {movie.tmdb_vote_average}</span> : null}
            {movie.community_rating ? <span className="pill neon">Community {movie.community_rating}</span> : null}
            <span className="pill">{movie.watched_by_count} watched</span>
          </div>
          <p>{movie.description || "Описание пока не добавлено."}</p>
          <div className="pill-row">
            {movie.genres.map((genre) => (
              <span key={genre.id} className="pill">
                {genre.name}
              </span>
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="split-grid">
        <SectionCard eyebrow="My library" title="Твой статус">
          {isAuthenticated ? (
            <form className="entry-form" onSubmit={handleSave}>
              <label>
                Статус
                <select
                  value={form.status}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, status: event.target.value }))
                  }
                >
                  <option value="plan_to_watch">Хочу посмотреть</option>
                  <option value="watched">Просмотрено</option>
                </select>
              </label>
              <label>
                Оценка
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={form.rating}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, rating: event.target.value }))
                  }
                  placeholder="1-10"
                />
              </label>
              {/* <label>
                Дата просмотра
                <input
                  type="date"
                  value={form.watched_at}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, watched_at: event.target.value }))
                  }
                />
              </label> */}
              <label>
                Мини-отзыв
                <textarea
                  value={form.review}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, review: event.target.value }))
                  }
                  placeholder="Что зацепило?"
                />
              </label>
              <label className="toggle-row">
                <input
                  type="checkbox"
                  checked={form.recommended_to_followers}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      recommended_to_followers: event.target.checked,
                    }))
                  }
                />
                Рекомендовать подписчикам
              </label>
              <div className="inline-actions">
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? "Сохранение..." : movie.my_entry ? "Обновить запись" : "Добавить в список"}
                </button>
                {movie.my_entry ? (
                  <button type="button" className="ghost-button" onClick={handleRemove} disabled={saving}>
                    Удалить
                  </button>
                ) : null}
              </div>
            </form>
          ) : (
            <p>Войди в систему, чтобы добавить фильм в библиотеку.</p>
          )}
        </SectionCard>

        <SectionCard eyebrow="Where to watch" title="Ссылки сообщества">
          <div className="card-stack">
            {movie.links?.length ? (
              movie.links.map((link) => (
                <div key={link.id} className="link-card">
                  <div>
                    <strong>{link.source_name}</strong>
                    <p>{link.url}</p>
                    <span className="muted-inline">Добавил @{link.added_by}</span>
                  </div>
                  <div className="vote-column">
                    <span className="pill neon">score {link.score}</span>
                    {isAuthenticated ? (
                      <div className="inline-actions">
                        <button type="button" className="ghost-button" onClick={() => handleVote(link.id, 1)}>
                          ▲
                        </button>
                        <button type="button" className="ghost-button" onClick={() => handleVote(link.id, -1)}>
                          ▼
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))
            ) : (
              <p>Пока без ссылок. Можно добавить первую.</p>
            )}
          </div>

          {isAuthenticated ? (
            <form className="entry-form" onSubmit={handleAddLink}>
              <label>
                Источник
                <input
                  value={linkForm.source_name}
                  onChange={(event) =>
                    setLinkForm((current) => ({ ...current, source_name: event.target.value }))
                  }
                  placeholder="Rezka / Kinopoisk / etc"
                  required
                />
              </label>
              <label>
                URL
                <input
                  type="url"
                  value={linkForm.url}
                  onChange={(event) =>
                    setLinkForm((current) => ({ ...current, url: event.target.value }))
                  }
                  placeholder="https://..."
                  required
                />
              </label>
              <button type="submit" className="primary-button" disabled={saving}>
                Добавить ссылку
              </button>
            </form>
          ) : null}
        </SectionCard>
      </div>
    </div>
  );
}
