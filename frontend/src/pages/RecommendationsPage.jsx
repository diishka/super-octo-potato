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

  return (
    <div className="page-grid wide">
      <SectionCard eyebrow="Engine" title="Рекомендации" action={loading ? <span className="muted-inline">sync...</span> : null}>
        <p className="muted-copy">
          Три уровня: популярное в твоём круге, похожие пользователи и похожие
          фильмы по жанрам.
        </p>
        {error ? <p className="form-error">{error}</p> : null}
      </SectionCard>

      <div className="page-grid triple">
        <SectionCard eyebrow="Level 1" title="Популярно среди друзей">
          <div className="card-stack">
            {normalizeFriends(payload.friends_popular).map((item) => (
              <MovieTile
                key={item.id}
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

        <SectionCard eyebrow="Level 2" title="Похожие пользователи">
          <div className="card-stack">
            {normalizeSimilarUsers(payload.similar_users).map((item) => (
              <MovieTile
                key={item.id}
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

        <SectionCard eyebrow="Level 3" title="Похожие фильмы">
          <div className="card-stack">
            {normalizeSimilarMovies(payload.similar_movies).map((item) => (
              <MovieTile
                key={item.id}
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
