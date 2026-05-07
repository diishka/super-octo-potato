import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ActivityCard } from "../components/ActivityCard";
import { AuthPanel } from "../components/AuthPanel";
import { MovieTile } from "../components/MovieTile";
import { SectionCard } from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

function statusLabel(status) {
  return status === "watched" ? "Посмотрел" : "В планах";
}

function normalizeFriendPopular(items = []) {
  return items.map((item) => ({
    id: item.movie_id,
    title: item.movie__title,
    posterUrl: item.movie__poster_url,
    meta: `${item.friend_watch_count} друзей`,
    description: item.avg_friend_rating
      ? `Средняя оценка: ${Number(item.avg_friend_rating).toFixed(1)}/10`
      : "Пока без оценки",
    badges: ["Популярно у друзей"],
  }));
}

function entryMeta(entry) {
  const parts = [`@${entry.user.username}`, statusLabel(entry.status)];
  if (entry.rating) {
    parts.push(`${entry.rating}/10`);
  }
  return parts.join(" • ");
}

function entryDescription(entry) {
  return entry.review || entry.movie.description || "Без описания";
}

export function HomePage() {
  const { isAuthenticated, token, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [overview, setOverview] = useState({
    hero_entry: null,
    friend_recommendations: [],
    friend_recent_watched: [],
    friend_watchlist: [],
    feed: [],
  });
  const [recommendations, setRecommendations] = useState({
    friends_popular: [],
    similar_users: [],
    similar_movies: [],
  });
  const [busyActivityId, setBusyActivityId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadHome() {
      if (!isAuthenticated) {
        setOverview({
          hero_entry: null,
          friend_recommendations: [],
          friend_recent_watched: [],
          friend_watchlist: [],
          feed: [],
        });
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [overviewData, recommendationData] = await Promise.all([
          apiRequest("/api/feed/overview/", { token }),
          apiRequest("/api/recommendations/", { token }),
        ]);

        if (!cancelled) {
          setOverview(overviewData);
          setRecommendations(recommendationData);
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

    loadHome();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, token]);

  async function handleLike(activityId) {
    setBusyActivityId(activityId);
    try {
      const updated = await apiRequest(`/api/feed/${activityId}/like/`, {
        method: "POST",
        token,
      });
      setOverview((current) => ({
        ...current,
        feed: current.feed.map((item) => (item.id === activityId ? updated : item)),
      }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyActivityId(null);
    }
  }

  async function handleComment(activityId, text) {
    setBusyActivityId(activityId);
    try {
      const created = await apiRequest(`/api/feed/${activityId}/comments/`, {
        method: "POST",
        token,
        body: { text },
      });
      setOverview((current) => ({
        ...current,
        feed: current.feed.map((item) =>
          item.id === activityId
            ? {
                ...item,
                comment_count: item.comment_count + 1,
                comments: [...(item.comments || []), created],
              }
            : item,
        ),
      }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusyActivityId(null);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="page-grid">
        <section className="hero-banner hero-banner-guest">
          <div className="hero-scrim" />
          <div className="hero-content">
            <div className="hero-meta-line">
              <span>social movie network</span>
              <span>tmdb powered</span>
            </div>
            <h1>Минималистичная лента фильмов и друзей</h1>
            <p>
              Один экран для рекомендаций друзей, их просмотренного, watchlist и
              твоего каталога. Без лишнего шума, с акцентом на контент.
            </p>
          </div>
        </section>

        <div className="split-grid home-guest-grid">
          <SectionCard eyebrow="Вход" title="Подключиться">
            <AuthPanel />
          </SectionCard>

          <SectionCard eyebrow="Что внутри" title="Главный сценарий">
            <ul className="stack-list">
              <li>Ищешь фильм, сериал или аниме через TMDb.</li>
              <li>Импортируешь карточку в свой каталог.</li>
              <li>Видишь, что рекомендуют и смотрят друзья.</li>
              <li>Следишь за их будущими планами на просмотр.</li>
            </ul>
          </SectionCard>
        </div>
      </div>
    );
  }

  const featuredEntry = overview.hero_entry;
  const featuredMovie = featuredEntry?.movie;
  const featuredBackground = featuredMovie?.backdrop_url || featuredMovie?.poster_url || "";
  const friendPopular = normalizeFriendPopular(recommendations.friends_popular);

  return (
    <div className="page-grid">
      {error ? <p className="form-error">{error}</p> : null}

      <section
        className="hero-banner"
        style={
          featuredBackground
            ? {
                backgroundImage: `linear-gradient(90deg, rgba(10, 10, 10, 0.92) 0%, rgba(10, 10, 10, 0.64) 48%, rgba(10, 10, 10, 0.78) 100%), url(${featuredBackground})`,
              }
            : undefined
        }
      >
        <div className="hero-scrim" />
        <div className="hero-content">
          <div className="hero-meta-line">
            <span>{loading ? "загрузка..." : `для @${user.username}`}</span>
            {featuredEntry ? <span>советует @{featuredEntry.user.username}</span> : null}
          </div>

          <h1>{featuredMovie?.title || "Твоя персональная лента"}</h1>

          <p>
            {featuredEntry
              ? entryDescription(featuredEntry)
              : "Добавь друзей и оценки, чтобы здесь появились персональные рекомендации и живая активность круга."}
          </p>

          <div className="hero-pill-row">
            <span className="hero-pill">{user.watched_count} просмотрено</span>
            <span className="hero-pill">{user.wishlist_count} в списке</span>
            {featuredMovie?.release_year ? <span className="hero-pill">{featuredMovie.release_year}</span> : null}
            {featuredEntry?.rating ? <span className="hero-pill">{featuredEntry.rating}/10</span> : null}
          </div>

          <div className="hero-actions">
            {featuredMovie ? (
              <Link to={`/movie/${featuredMovie.id}`} className="primary-button">
                Открыть карточку
              </Link>
            ) : null}
            {featuredEntry ? (
              <Link to={`/profile/${featuredEntry.user.username}`} className="ghost-button">
                Профиль друга
              </Link>
            ) : null}
          </div>
        </div>
      </section>

      <SectionCard
        eyebrow="Советуют друзья"
        title="На что обратить внимание"
        action={<Link className="inline-link" to="/recommendations">Все подборки</Link>}
      >
        <div className="media-rail">
          {(overview.friend_recommendations.length
            ? overview.friend_recommendations
            : friendPopular
          )
            .slice(0, 8)
            .map((item) => {
              if ("movie" in item) {
                return (
                  <MovieTile
                    key={`friend-reco-${item.id}`}
                    title={item.movie.title}
                    posterUrl={item.movie.poster_url}
                    to={`/movie/${item.movie.id}`}
                    meta={entryMeta(item)}
                    description={entryDescription(item)}
                    badges={[
                      item.recommended_to_followers ? "Рекомендует" : "Высокая оценка",
                    ]}
                  />
                );
              }

              return (
                <MovieTile
                  key={`popular-${item.id}`}
                  title={item.title}
                  posterUrl={item.posterUrl}
                  to={`/movie/${item.id}`}
                  meta={item.meta}
                  description={item.description}
                  badges={item.badges}
                />
              );
            })}
        </div>
      </SectionCard>

      <div className="dual-rail-grid">
        <SectionCard eyebrow="Смотрят" title="Недавно посмотрели">
          <div className="media-rail">
            {overview.friend_recent_watched.slice(0, 8).map((entry) => (
              <MovieTile
                key={`watched-${entry.id}`}
                title={entry.movie.title}
                posterUrl={entry.movie.poster_url}
                to={`/movie/${entry.movie.id}`}
                meta={entryMeta(entry)}
                description={entryDescription(entry)}
                badges={entry.rating ? [`${entry.rating}/10`] : ["Просмотрено"]}
              />
            ))}
            {!overview.friend_recent_watched.length ? (
              <p className="empty-copy">Пока пусто. Следи за друзьями, чтобы увидеть их свежие просмотры.</p>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Планируют" title="Что в очереди у друзей">
          <div className="media-rail">
            {overview.friend_watchlist.slice(0, 8).map((entry) => (
              <MovieTile
                key={`queue-${entry.id}`}
                title={entry.movie.title}
                posterUrl={entry.movie.poster_url}
                to={`/movie/${entry.movie.id}`}
                meta={`@${entry.user.username} • хочет посмотреть`}
                description={entry.movie.description || "Фильм уже в очереди у друга."}
                badges={["В планах"]}
              />
            ))}
            {!overview.friend_watchlist.length ? (
              <p className="empty-copy">Пока нет открытых планов на просмотр.</p>
            ) : null}
          </div>
        </SectionCard>
      </div>

      <SectionCard eyebrow="Лента" title="Активность друзей">
        {overview.feed.length ? (
          <div className="card-stack">
            {overview.feed.map((activity) => (
              <ActivityCard
                key={activity.id}
                activity={activity}
                onLike={handleLike}
                onComment={handleComment}
                busy={busyActivityId === activity.id}
              />
            ))}
          </div>
        ) : (
          <p className="empty-copy">
            Лента пока тихая. После `seed_demo` или подписок здесь появятся свежие действия друзей.
          </p>
        )}
      </SectionCard>
    </div>
  );
}
