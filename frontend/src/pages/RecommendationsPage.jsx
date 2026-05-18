import { useEffect, useState } from "react";

import { MovieTile } from "../components/MovieTile";
import { SectionCard } from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

function normalizeFriends(items = []) {
  return items.map((item) => ({
    id: item.movie_id,
    title: item.movie__title,
    posterUrl: item.movie__poster_url,
    meta: `${item.friend_watch_count} друзей`,
    description: item.avg_friend_rating
      ? `Средняя оценка круга: ${Number(item.avg_friend_rating).toFixed(1)}/10`
      : "Пока без оценок",
  }));
}

function normalizeSimilarUsers(items = []) {
  return items.map((item) => ({
    id: item.movie_id,
    title: item.title,
    posterUrl: item.poster_url,
    meta: `score ${item.score}`,
    description: item.supporters?.length
      ? `Советуют: ${item.supporters.join(", ")}`
      : "Похожий taste cluster",
  }));
}

function normalizeSimilarMovies(items = []) {
  return items.map((item) => ({
    id: item.movie_id,
    title: item.title,
    posterUrl: item.poster_url,
    meta: `${item.shared_genres} общих жанров`,
  }));
}

function buildFeaturedRecommendation(payload) {
  const fromFriends = normalizeFriends(payload.friends_popular)[0];
  const fromUsers = normalizeSimilarUsers(payload.similar_users)[0];
  const fromMovies = normalizeSimilarMovies(payload.similar_movies)[0];

  return fromFriends || fromUsers || fromMovies || null;
}

export function RecommendationsPage() {
  const { isAuthenticated, token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState({
    friends_popular: [],
    similar_users: [],
    similar_movies: [],
  });

  useEffect(() => {
    let cancelled = false;

    async function loadRecommendations() {
      if (!isAuthenticated) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const response = await apiRequest("/api/recommendations/", { token });
        if (!cancelled) {
          setPayload(response);
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

    loadRecommendations();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, token]);

  if (!isAuthenticated) {
    return (
      <div className="page-grid">
        <SectionCard eyebrow="Locked" title="Рекомендации доступны после входа">
          <p>
            Алгоритм опирается на твои оценки, друзей и историю просмотренного,
            поэтому без аккаунта здесь будет тихо.
          </p>
        </SectionCard>
      </div>
    );
  }

  const featuredRecommendation = buildFeaturedRecommendation(payload);

  return (
    <div className="page-grid wide recommendations-shell">
      <section
        className="hero-banner recommendations-hero"
        style={
          featuredRecommendation?.posterUrl
            ? {
                backgroundImage: `linear-gradient(90deg, rgba(9, 9, 9, 0.95) 0%, rgba(9, 9, 9, 0.72) 50%, rgba(9, 9, 9, 0.84) 100%), url(${featuredRecommendation.posterUrl})`,
              }
            : undefined
        }
      >
        <div className="hero-scrim" />
        <div className="hero-grid">
          <div className="hero-content">
            <div className="hero-meta-line">
              <span>recommendation engine</span>
              {loading ? <span>sync...</span> : <span>3 слоя подбора</span>}
            </div>
            <h1>{featuredRecommendation?.title || "Рекомендации для тебя"}</h1>
            <p>
              Три уровня: популярное в твоём круге, похожие пользователи и похожие
              фильмы по жанрам. Социальная лента остаётся сердцем продукта, а этот
              экран превращает её сигналы в подборки.
            </p>
            {featuredRecommendation ? (
              <div className="hero-pill-row">
                <span className="hero-pill">{featuredRecommendation.meta}</span>
              </div>
            ) : null}
          </div>

          <aside className="hero-side-panel hero-side-panel-compact">
            <div className="hero-side-intro">
              <span className="eyebrow">Навигация</span>
              <h3>Как читать этот экран</h3>
            </div>
            <div className="hero-side-list">
              <div className="hero-side-item">
                <strong>1. Круг друзей</strong>
                <span>Смотрим, что чаще всего всплывает у тех, кому ты доверяешь.</span>
              </div>
              <div className="hero-side-item">
                <strong>2. Похожие вкусы</strong>
                <span>Ищем людей с похожими оценками и переносим их сигналы.</span>
              </div>
              <div className="hero-side-item">
                <strong>3. Родственные тайтлы</strong>
                <span>Добираем похожее по жанрам и паттернам просмотров.</span>
              </div>
            </div>
          </aside>
        </div>
      </section>

      {error ? <p className="form-error">{error}</p> : null}

      <div className="page-grid">
        <SectionCard eyebrow="Level 1" title="Популярно среди друзей" className="shelf-card">
          <div className="media-rail">
            {normalizeFriends(payload.friends_popular).map((item) => (
              <MovieTile
                key={item.id}
                variant="rail"
                title={item.title}
                posterUrl={item.posterUrl}
                to={`/movie/${item.id}`}
                meta={item.meta}
                description={item.description}
              />
            ))}
            {!payload.friends_popular.length ? <p>Пока мало данных для friend graph.</p> : null}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Level 2" title="Похожие пользователи" className="shelf-card">
          <div className="media-rail">
            {normalizeSimilarUsers(payload.similar_users).map((item) => (
              <MovieTile
                key={item.id}
                variant="rail"
                title={item.title}
                posterUrl={item.posterUrl}
                to={`/movie/${item.id}`}
                meta={item.meta}
                description={item.description}
              />
            ))}
            {!payload.similar_users.length ? <p>Нужно больше собственных оценок, чтобы вычислить вкус.</p> : null}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Level 3" title="Похожие фильмы" className="shelf-card">
          <div className="media-rail">
            {normalizeSimilarMovies(payload.similar_movies).map((item) => (
              <MovieTile
                key={item.id}
                variant="rail"
                title={item.title}
                posterUrl={item.posterUrl}
                to={`/movie/${item.id}`}
                meta={item.meta}
              />
            ))}
            {!payload.similar_movies.length ? <p>Пока недостаточно просмотренного для жанрового анализа.</p> : null}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
