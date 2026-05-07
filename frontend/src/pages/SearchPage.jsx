import { startTransition, useEffect, useDeferredValue, useState } from "react";
import { useNavigate } from "react-router-dom";

import { MovieTile } from "../components/MovieTile";
import { SectionCard } from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

function normalizeLocalMovie(movie) {
  return {
    id: movie.id,
    title: movie.title,
    posterUrl: movie.poster_url,
    meta:
      [movie.media_type, movie.release_year, movie.community_rating ? `${movie.community_rating}/10` : null]
        .filter(Boolean)
        .join(" • ") || "в каталоге",
    description: movie.description,
    badges: movie.genres?.slice(0, 2).map((genre) => genre.name) || [],
  };
}

const INITIAL_CATALOG_LIMIT = 8;
const INITIAL_TMDB_LIMIT = 10;

function visibleResults(items, expanded, limit) {
  return expanded ? items : items.slice(0, limit);
}

export function SearchPage() {
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [catalogItems, setCatalogItems] = useState([]);
  const [tmdbResults, setTmdbResults] = useState([]);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [loadingTmdb, setLoadingTmdb] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const [tmdbError, setTmdbError] = useState("");
  const [busyTmdbId, setBusyTmdbId] = useState(null);
  const [showAllCatalog, setShowAllCatalog] = useState(false);
  const [showAllTmdb, setShowAllTmdb] = useState(false);
  const deferredCatalogItems = useDeferredValue(catalogItems);
  const deferredTmdbResults = useDeferredValue(tmdbResults);
  const visibleCatalogItems = visibleResults(
    deferredCatalogItems,
    showAllCatalog,
    INITIAL_CATALOG_LIMIT,
  );
  const visibleTmdbItems = visibleResults(
    deferredTmdbResults,
    showAllTmdb,
    INITIAL_TMDB_LIMIT,
  );

  async function fetchCatalog(searchValue = "") {
    const suffix = searchValue.trim() ? `?q=${encodeURIComponent(searchValue.trim())}` : "";
    return apiRequest(`/api/movies/${suffix}`);
  }

  async function loadCatalog(searchValue = "") {
    setLoadingCatalog(true);
    setCatalogError("");

    try {
      const payload = await fetchCatalog(searchValue);
      startTransition(() => setCatalogItems(payload));
      return payload;
    } catch (requestError) {
      setCatalogError(requestError.message);
      return [];
    } finally {
      setLoadingCatalog(false);
    }
  }

  useEffect(() => {
    loadCatalog();
  }, []);

  async function handleSearch(event) {
    event.preventDefault();
    const trimmedQuery = query.trim();
    setShowAllCatalog(false);
    setShowAllTmdb(false);

    if (!trimmedQuery) {
      setTmdbResults([]);
      setTmdbError("");
      await loadCatalog("");
      return;
    }

    setLoadingCatalog(true);
    setLoadingTmdb(true);
    setCatalogError("");
    setTmdbError("");

    let catalogPayload = [];
    let tmdbPayload = [];

    try {
      catalogPayload = await fetchCatalog(trimmedQuery);
    } catch (requestError) {
      setCatalogError(requestError.message);
    } finally {
      setLoadingCatalog(false);
    }

    try {
      tmdbPayload = await apiRequest(
        `/api/movies/tmdb/search/?q=${encodeURIComponent(trimmedQuery)}`,
      );
    } catch (requestError) {
      setTmdbError(
        requestError.message.includes("TMDb API key")
          ? requestError.message
          : `TMDb сейчас недоступен: ${requestError.message}`,
      );
    } finally {
      setLoadingTmdb(false);
    }

    startTransition(() => {
      setCatalogItems(catalogPayload);
      setTmdbResults(tmdbPayload);
    });
  }

  async function handleImport(result) {
    setBusyTmdbId(result.tmdb_id);
    setTmdbError("");

    try {
      const movie = await apiRequest(
        `/api/movies/tmdb/import/${result.tmdb_id}/?media_type=${result.media_type}`,
        {
          method: "POST",
          token,
        },
      );
      await loadCatalog(query);
      navigate(`/movie/${movie.id}`);
    } catch (requestError) {
      setTmdbError(requestError.message);
    } finally {
      setBusyTmdbId(null);
    }
  }

  return (
    <div className="page-grid wide">
      <SectionCard eyebrow="Каталог" title="Найти фильм">
        <form className="search-box" onSubmit={handleSearch}>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по каталогу и TMDb..."
          />
          <button type="submit" className="primary-button">
            {loadingCatalog || loadingTmdb ? "Поиск..." : "Найти"}
          </button>
        </form>

        <p className="muted-copy">
          Сначала показывается локальная база. Внешний поиск по `TMDb` нужен только
          для импорта новых карточек и больше не ломает каталог, если внешний API
          временно недоступен.
        </p>

        {catalogError ? <p className="form-error">{catalogError}</p> : null}
      </SectionCard>

      <SectionCard
        eyebrow="Локально"
        title={`В каталоге: ${deferredCatalogItems.length}`}
        action={
          deferredCatalogItems.length > INITIAL_CATALOG_LIMIT ? (
            <button
              type="button"
              className="ghost-button compact"
              onClick={() => setShowAllCatalog((current) => !current)}
            >
              {showAllCatalog ? "Свернуть" : "Показать все"}
            </button>
          ) : null
        }
      >
        {deferredCatalogItems.length ? (
          <>
            <p className="results-caption">
              Показано {visibleCatalogItems.length} из {deferredCatalogItems.length}
            </p>
            <div className="results-grid">
              {visibleCatalogItems.map((movie) => {
                const item = normalizeLocalMovie(movie);
                return (
                  <MovieTile
                    key={item.id}
                    className="movie-tile-compact"
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
          </>
        ) : (
          <p className="empty-copy">
            В локальной базе пока нет фильмов по этому фильтру. Можно импортировать их ниже.
          </p>
        )}
      </SectionCard>

      <SectionCard
        eyebrow="TMDb"
        title={`Найдено во внешнем поиске: ${deferredTmdbResults.length}`}
        action={
          deferredTmdbResults.length > INITIAL_TMDB_LIMIT ? (
            <button
              type="button"
              className="ghost-button compact"
              onClick={() => setShowAllTmdb((current) => !current)}
            >
              {showAllTmdb ? "Свернуть" : "Показать все"}
            </button>
          ) : null
        }
      >
        <p className="muted-copy">
          Этот блок нужен для добавления новых фильмов в твою базу. Если запрос пустой,
          он специально не шумит.
        </p>

        {tmdbError ? <p className="form-error">{tmdbError}</p> : null}

        {deferredTmdbResults.length ? (
          <>
            <p className="results-caption">
              Показано {visibleTmdbItems.length} из {deferredTmdbResults.length}
            </p>
            <div className="results-grid results-grid-compact">
              {visibleTmdbItems.map((result) => (
                <MovieTile
                  key={`${result.media_type}-${result.tmdb_id}`}
                  className="movie-tile-compact"
                  title={result.title}
                  posterUrl={result.poster_url}
                  meta={
                    [result.media_type, result.release_year].filter(Boolean).join(" • ") ||
                    "type unknown"
                  }
                  description={result.description}
                  badges={result.tmdb_vote_average ? [`TMDb ${result.tmdb_vote_average}`] : []}
                  actions={
                    isAuthenticated ? (
                      <button
                        type="button"
                        className="primary-button compact"
                        disabled={busyTmdbId === result.tmdb_id}
                        onClick={() => handleImport(result)}
                      >
                        {busyTmdbId === result.tmdb_id ? "Импорт..." : "Импортировать"}
                      </button>
                    ) : (
                      <span className="muted-inline">Войди, чтобы импортировать</span>
                    )
                  }
                />
              ))}
            </div>
          </>
        ) : (
          <p className="empty-copy">
            Здесь появятся новые фильмы из `TMDb`, когда ты введёшь запрос.
          </p>
        )}
      </SectionCard>
    </div>
  );
}
