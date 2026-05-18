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

const INITIAL_CATALOG_LIMIT = 12;
const INITIAL_TMDB_LIMIT = 12;
const mediaFilterOptions = [
  { id: "all", label: "Все" },
  { id: "movie", label: "Фильмы" },
  { id: "series", label: "Сериалы" },
  { id: "anime", label: "Аниме" },
];

function visibleResults(items, expanded, limit) {
  return expanded ? items : items.slice(0, limit);
}

function pickFeaturedMovie(items) {
  return [...items].sort((left, right) => {
    const leftScore = Number(left.community_rating || left.tmdb_vote_average || 0) + Number(left.watched_by_count || 0) * 0.15;
    const rightScore = Number(right.community_rating || right.tmdb_vote_average || 0) + Number(right.watched_by_count || 0) * 0.15;
    return rightScore - leftScore;
  })[0] || null;
}

function mediaTypeLabel(mediaType) {
  if (mediaType === "series") return "сериал";
  if (mediaType === "anime") return "аниме";
  return "фильм";
}

export function SearchPage() {
  const { isAuthenticated, token } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [catalogItems, setCatalogItems] = useState([]);
  const [tmdbResults, setTmdbResults] = useState([]);
  const [showcase, setShowcase] = useState({
    featured: null,
    weekly_top: {
      movie: [],
      series: [],
      anime: [],
    },
    genres: [],
    stale: false,
  });
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [loadingTmdb, setLoadingTmdb] = useState(false);
  const [loadingShowcase, setLoadingShowcase] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const [tmdbError, setTmdbError] = useState("");
  const [showcaseError, setShowcaseError] = useState("");
  const [busyTmdbId, setBusyTmdbId] = useState(null);
  const [showAllCatalog, setShowAllCatalog] = useState(false);
  const [showAllTmdb, setShowAllTmdb] = useState(false);
  const [mediaFilter, setMediaFilter] = useState("all");
  const deferredCatalogItems = useDeferredValue(catalogItems);
  const deferredTmdbResults = useDeferredValue(tmdbResults);
  const filteredCatalogItems = deferredCatalogItems.filter((movie) =>
    mediaFilter === "all" ? true : movie.media_type === mediaFilter,
  );
  const filteredTmdbResults = deferredTmdbResults.filter((item) =>
    mediaFilter === "all" ? true : item.media_type === mediaFilter,
  );
  const visibleCatalogItems = visibleResults(
    filteredCatalogItems,
    showAllCatalog,
    INITIAL_CATALOG_LIMIT,
  );
  const visibleTmdbItems = visibleResults(
    filteredTmdbResults,
    showAllTmdb,
    INITIAL_TMDB_LIMIT,
  );
  const featuredCatalogMovie =
    pickFeaturedMovie(filteredCatalogItems)
    || pickFeaturedMovie(filteredTmdbResults)
    || pickFeaturedMovie(deferredCatalogItems)
    || filteredTmdbResults[0]
    || deferredTmdbResults[0]
    || null;
  const heroMovie = activeQuery ? featuredCatalogMovie : showcase.featured;
  const hasActiveSearch = Boolean(activeQuery);
  const weeklyTopSections = [
    { key: "movie", title: "Фильмы недели", items: showcase.weekly_top.movie },
    { key: "series", title: "Сериалы недели", items: showcase.weekly_top.series },
    { key: "anime", title: "Аниме недели", items: showcase.weekly_top.anime },
  ];
  const filteredWeeklyTopSections = weeklyTopSections.filter((section) =>
    mediaFilter === "all" ? true : section.key === mediaFilter,
  );
  const filteredGenreRows = showcase.genres.filter((row) =>
    mediaFilter === "all" ? true : row.media_type === mediaFilter,
  );
  const showcaseWeeklyCount = filteredWeeklyTopSections.reduce(
    (total, section) => total + section.items.length,
    0,
  );
  const showcaseGenreCount = filteredGenreRows.reduce(
    (total, row) => total + row.items.length,
    0,
  );
  const showcaseHeroMovie =
    filteredWeeklyTopSections.flatMap((section) => section.items)[0]
    || showcase.featured;
  const resolvedHeroMovie = hasActiveSearch ? heroMovie : showcaseHeroMovie;

  async function fetchCatalog(searchValue = "") {
    const suffix = searchValue.trim() ? `?q=${encodeURIComponent(searchValue.trim())}` : "";
    return apiRequest(`/api/movies/${suffix}`);
  }

  async function loadShowcase() {
    setLoadingShowcase(true);
    setShowcaseError("");

    try {
      const payload = await apiRequest("/api/movies/showcase/");
      startTransition(() => setShowcase(payload));
    } catch (requestError) {
      setShowcaseError(requestError.message);
    } finally {
      setLoadingShowcase(false);
    }
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
    loadShowcase();
  }, []);

  async function handleSearch(event) {
    event.preventDefault();
    const trimmedQuery = query.trim();
    setShowAllCatalog(false);
    setShowAllTmdb(false);

    if (!trimmedQuery) {
      setActiveQuery("");
      startTransition(() => setCatalogItems([]));
      setTmdbResults([]);
      setTmdbError("");
      return;
    }

    setActiveQuery(trimmedQuery);

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
      if (activeQuery) {
        await loadCatalog(query);
      } else {
        await loadShowcase();
      }
      navigate(`/movie/${movie.id}`);
    } catch (requestError) {
      setTmdbError(requestError.message);
    } finally {
      setBusyTmdbId(null);
    }
  }

  function resetBrowse() {
    setQuery("");
    setActiveQuery("");
    startTransition(() => setCatalogItems([]));
    setShowAllCatalog(false);
    setShowAllTmdb(false);
    setTmdbResults([]);
    setTmdbError("");
  }

  function showcaseActions(item) {
    if (item.local_id) {
      return (
        <button
          type="button"
          className="ghost-button compact"
          onClick={() => navigate(`/movie/${item.local_id}`)}
        >
          Открыть
        </button>
      );
    }

    if (!isAuthenticated) {
      return <span className="muted-inline">Войди, чтобы импортировать</span>;
    }

    return (
      <button
        type="button"
        className="primary-button compact"
        disabled={busyTmdbId === item.tmdb_id}
        onClick={() => handleImport(item)}
      >
        {busyTmdbId === item.tmdb_id ? "Импорт..." : "Импортировать"}
      </button>
    );
  }

  return (
    <div className="page-grid wide catalog-shell">
      <section
        className="hero-banner catalog-hero"
        style={
          resolvedHeroMovie?.backdrop_url || resolvedHeroMovie?.poster_url
            ? {
                backgroundImage: `linear-gradient(90deg, rgba(9, 9, 9, 0.94) 0%, rgba(9, 9, 9, 0.72) 46%, rgba(9, 9, 9, 0.8) 100%), url(${resolvedHeroMovie.backdrop_url || resolvedHeroMovie.poster_url})`,
              }
            : undefined
        }
      >
        <div className="hero-scrim" />
        <div className="hero-grid">
          <div className="hero-content">
            <div className="hero-meta-line">
              <span>{hasActiveSearch ? "результаты поиска" : "витрина недели"}</span>
              <span>{hasActiveSearch ? `${filteredCatalogItems.length} локально` : "cached from postgres"}</span>
            </div>
            <h1>{resolvedHeroMovie?.title || "Найти фильм или аниме"}</h1>
            <p>
              {hasActiveSearch
                ? "Локальная база и TMDb-результаты собраны в одном спокойном экране без перегруза."
                : "Сначала смотри, что сейчас в топе недели, потом переходи к жанровым полкам и импортируй нужное к себе."}
            </p>
            <form className="search-box hero-search-box" onSubmit={handleSearch}>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Поиск по каталогу и TMDb..."
              />
              <button type="submit" className="primary-button">
                {loadingCatalog || loadingTmdb ? "Поиск..." : "Найти"}
              </button>
              {hasActiveSearch ? (
                <button type="button" className="ghost-button" onClick={resetBrowse}>
                  Сбросить
                </button>
              ) : null}
            </form>
            <div className="filter-strip">
              {mediaFilterOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={mediaFilter === option.id ? "ghost-button compact active" : "ghost-button compact"}
                  onClick={() => {
                    setMediaFilter(option.id);
                    setShowAllCatalog(false);
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <aside className="hero-side-panel hero-side-panel-compact">
            <div className="hero-side-intro">
              <span className="eyebrow">Быстрый обзор</span>
              <h3>{hasActiveSearch ? "Что найдено" : "Что посмотреть сейчас"}</h3>
            </div>
            <div className="mini-stat-grid">
              <div className="mini-stat-card">
                <strong>{hasActiveSearch ? filteredCatalogItems.length : showcaseWeeklyCount}</strong>
                <span>{hasActiveSearch ? "в каталоге" : "в top недели"}</span>
              </div>
              <div className="mini-stat-card">
                <strong>{hasActiveSearch ? filteredTmdbResults.length : showcaseGenreCount}</strong>
                <span>{hasActiveSearch ? "из TMDb" : "в жанровых полках"}</span>
              </div>
              <div className="mini-stat-card">
                <strong>{hasActiveSearch ? visibleCatalogItems.length : showcase.stale ? "устарел" : "свежий"}</strong>
                <span>{hasActiveSearch ? "на экране" : "кэш"}</span>
              </div>
            </div>
            <div className="hero-side-list">
              {hasActiveSearch ? (
                <>
                  <div className="hero-side-item">
                    <strong>Локальный каталог первый</strong>
                    <span>Сначала смотри, что уже есть в базе, потом добирай недостающее из TMDb.</span>
                  </div>
                  <div className="hero-side-item">
                    <strong>Фильтр по типу</strong>
                    <span>Можно быстро отделить фильмы, сериалы и аниме.</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="hero-side-item">
                    <strong>Топ недели</strong>
                    <span>Собираем горячие тайтлы отдельно для фильмов, сериалов и аниме.</span>
                  </div>
                  <div className="hero-side-item">
                    <strong>Жанровые полки</strong>
                    <span>Ниже не сухой каталог, а живая витрина по жанрам с быстрым импортом.</span>
                  </div>
                </>
              )}
            </div>
          </aside>
        </div>
      </section>

      {catalogError ? <p className="form-error">{catalogError}</p> : null}

      {hasActiveSearch ? (
        <>
          <SectionCard
            eyebrow="Каталог"
            title={`В каталоге: ${filteredCatalogItems.length}`}
            className="shelf-card"
            action={
              filteredCatalogItems.length > INITIAL_CATALOG_LIMIT ? (
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
            {filteredCatalogItems.length ? (
              <>
                <p className="results-caption">
                  Показано {visibleCatalogItems.length} из {filteredCatalogItems.length}
                </p>
                <div className="results-grid">
                  {visibleCatalogItems.map((movie) => {
                    const item = normalizeLocalMovie(movie);
                    return (
                      <MovieTile
                        key={item.id}
                        variant="rail"
                        className="movie-tile-catalog"
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
            className="shelf-card"
            action={
              filteredTmdbResults.length > INITIAL_TMDB_LIMIT ? (
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
              Этот блок нужен для добавления новых фильмов в твою базу.
            </p>

            {tmdbError ? <p className="form-error">{tmdbError}</p> : null}

            {filteredTmdbResults.length ? (
              <>
                <p className="results-caption">
                  Показано {visibleTmdbItems.length} из {filteredTmdbResults.length}
                </p>
                <div className="results-grid results-grid-compact">
                  {visibleTmdbItems.map((result) => (
                    <MovieTile
                      key={`${result.media_type}-${result.tmdb_id}`}
                      variant="compact"
                      className="movie-tile-compact"
                      title={result.title}
                      posterUrl={result.poster_url}
                      meta={
                        [mediaTypeLabel(result.media_type), result.release_year].filter(Boolean).join(" • ") ||
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
        </>
      ) : (
        <>
          {showcaseError ? <p className="form-error">{showcaseError}</p> : null}

          {filteredWeeklyTopSections.map((section) => (
            <SectionCard
              key={section.key}
              eyebrow="Топ недели"
              title={section.title}
              className="shelf-card"
              action={loadingShowcase ? <span className="muted-inline">обновляю...</span> : null}
            >
              <div className="media-rail">
                {section.items.map((item) => (
                  <MovieTile
                    key={`${section.key}-${item.tmdb_id}`}
                    variant="rail"
                    className="movie-tile-catalog"
                    title={item.title}
                    posterUrl={item.poster_url}
                    to={item.local_id ? `/movie/${item.local_id}` : undefined}
                    meta={[mediaTypeLabel(item.media_type), item.release_year].filter(Boolean).join(" • ")}
                    description={item.description}
                    badges={item.tmdb_vote_average ? [`TMDb ${item.tmdb_vote_average}`] : []}
                    actions={showcaseActions(item)}
                  />
                ))}
                {!section.items.length ? (
                  <p className="empty-copy">Пока не удалось собрать эту полку.</p>
                ) : null}
              </div>
            </SectionCard>
          ))}

          {filteredGenreRows.map((genreRow) => (
            <SectionCard
              key={genreRow.slug}
              eyebrow="По жанрам"
              title={genreRow.title}
              className="shelf-card"
            >
              <div className="media-rail">
                {genreRow.items.map((item) => (
                  <MovieTile
                    key={`${genreRow.slug}-${item.tmdb_id}`}
                    variant="rail"
                    className="movie-tile-catalog"
                    title={item.title}
                    posterUrl={item.poster_url}
                    to={item.local_id ? `/movie/${item.local_id}` : undefined}
                    meta={[mediaTypeLabel(item.media_type), item.release_year].filter(Boolean).join(" • ")}
                    description={item.description}
                    badges={item.tmdb_vote_average ? [`TMDb ${item.tmdb_vote_average}`] : []}
                    actions={showcaseActions(item)}
                  />
                ))}
              </div>
            </SectionCard>
          ))}
        </>
      )}
    </div>
  );
}
