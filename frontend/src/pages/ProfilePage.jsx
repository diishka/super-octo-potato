import { useEffect, useDeferredValue, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { MovieTile } from "../components/MovieTile";
import { SectionCard } from "../components/SectionCard";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";

function formatLibraryMeta(entry, fallbackLabel) {
  const parts = [];

  if (entry.rating) {
    parts.push(`${entry.rating}/10`);
  }

  if (entry.movie.release_year) {
    parts.push(String(entry.movie.release_year));
  }

  return parts.join(" • ") || fallbackLabel;
}

function profileInitial(profile) {
  return profile?.username?.[0]?.toUpperCase() || "?";
}

export function ProfilePage() {
  const { username } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, saveProfile, token, user } = useAuth();
  const targetUsername = username || user?.username || "";
  const isOwnProfile = Boolean(user?.username && targetUsername === user.username);

  const [profile, setProfile] = useState(null);
  const [watched, setWatched] = useState([]);
  const [wishlist, setWishlist] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [following, setFollowing] = useState([]);
  const [peopleQuery, setPeopleQuery] = useState("");
  const [peopleResults, setPeopleResults] = useState([]);
  const [profileForm, setProfileForm] = useState({ bio: "", avatar_url: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const deferredPeopleQuery = useDeferredValue(peopleQuery);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      if (!targetUsername) {
        return;
      }

      setLoading(true);
      setError("");

      try {
        const [profilePayload, watchedPayload, wishlistPayload, followersPayload, followingPayload] =
          await Promise.all([
            apiRequest(`/api/social/profiles/${targetUsername}/`, { token }),
            apiRequest(`/api/movies/users/${targetUsername}/library/?status=watched`, { token }),
            apiRequest(`/api/movies/users/${targetUsername}/library/?status=plan_to_watch`, {
              token,
            }),
            apiRequest(`/api/social/profiles/${targetUsername}/followers/`, { token }),
            apiRequest(`/api/social/profiles/${targetUsername}/following/`, { token }),
          ]);

        if (!cancelled) {
          setProfile(profilePayload);
          setWatched(watchedPayload);
          setWishlist(wishlistPayload);
          setFollowers(followersPayload);
          setFollowing(followingPayload);
          if (isOwnProfile) {
            setProfileForm({
              bio: user?.bio || profilePayload.bio || "",
              avatar_url: user?.avatar_url || profilePayload.avatar_url || "",
            });
          }
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

    loadProfile();

    return () => {
      cancelled = true;
    };
  }, [targetUsername, token, isOwnProfile, user?.avatar_url, user?.bio]);

  useEffect(() => {
    let cancelled = false;

    async function searchPeople() {
      if (!deferredPeopleQuery.trim()) {
        setPeopleResults([]);
        return;
      }

      try {
        const payload = await apiRequest(
          `/api/social/users/?q=${encodeURIComponent(deferredPeopleQuery.trim())}`,
          { token },
        );
        if (!cancelled) {
          setPeopleResults(payload);
        }
      } catch (_error) {
        if (!cancelled) {
          setPeopleResults([]);
        }
      }
    }

    searchPeople();

    return () => {
      cancelled = true;
    };
  }, [deferredPeopleQuery, token]);

  async function handleFollowToggle() {
    if (!isAuthenticated || !profile || isOwnProfile) {
      return;
    }

    setError("");
    setMessage("");

    try {
      await apiRequest(`/api/social/profiles/${profile.username}/follow/`, {
        method: "POST",
        token,
      });
      const refreshedProfile = await apiRequest(`/api/social/profiles/${profile.username}/`, { token });
      const refreshedFollowers = await apiRequest(`/api/social/profiles/${profile.username}/followers/`, { token });
      setProfile(refreshedProfile);
      setFollowers(refreshedFollowers);
      setMessage(refreshedProfile.is_following ? "Теперь вы подписаны." : "Подписка снята.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handleProfileSave(event) {
    event.preventDefault();
    if (!isOwnProfile) {
      return;
    }

    setError("");
    setMessage("");

    try {
      const updated = await saveProfile(profileForm);
      setProfile((current) => ({
        ...current,
        bio: updated.bio,
        avatar_url: updated.avatar_url,
      }));
      setMessage("Профиль обновлён.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  if (!targetUsername && !isAuthenticated) {
    return (
      <div className="page-grid">
        <SectionCard eyebrow="Profile" title="Сначала войди в систему">
          <p>После авторизации здесь откроется твой профиль и social explorer.</p>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-grid wide">
      {error ? <p className="form-error">{error}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      {profile ? (
        <section className="profile-hero-card">
          <div className="profile-avatar-shell">
            {profile.avatar_url ? (
              <img src={profile.avatar_url} alt={profile.username} className="profile-avatar-image" />
            ) : (
              <div className="profile-avatar-fallback">{profileInitial(profile)}</div>
            )}
          </div>

          <div className="profile-hero-copy">
            <div className="hero-meta-line">
              <span>{isOwnProfile ? "твоя зона" : "профиль пользователя"}</span>
              <span>@{profile.username}</span>
            </div>
            <h1>{isOwnProfile ? "Твой профиль" : `Профиль @${profile.username}`}</h1>
            <p>{profile.bio || "Пока без биографии, но профиль уже собирает историю просмотров и социальный след."}</p>

            <div className="hero-pill-row">
              <span className="hero-pill">{profile.watched_count} просмотрено</span>
              <span className="hero-pill">{profile.wishlist_count} в очереди</span>
              <span className="hero-pill">{profile.follower_count} подписчиков</span>
              <span className="hero-pill">{profile.following_count} подписок</span>
            </div>

            {!isOwnProfile && isAuthenticated ? (
              <div className="hero-actions">
                <button type="button" className="primary-button" onClick={handleFollowToggle}>
                  {profile.is_following ? "Отписаться" : "Подписаться"}
                </button>
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      <div className="split-grid">
        <SectionCard
          eyebrow={loading ? "Syncing" : "Profile"}
          title={profile ? `@${profile.username}` : "Профиль"}
          action={
            !isOwnProfile && isAuthenticated && profile ? (
              <button type="button" className="primary-button compact" onClick={handleFollowToggle}>
                {profile.is_following ? "Отписаться" : "Подписаться"}
              </button>
            ) : null
          }
        >
          {profile ? (
            <>
              <div className="metric-grid">
                <div className="metric-card">
                  <strong>{profile.watched_count}</strong>
                  <span>watched</span>
                </div>
                <div className="metric-card">
                  <strong>{profile.wishlist_count}</strong>
                  <span>queue</span>
                </div>
                <div className="metric-card">
                  <strong>{profile.follower_count}</strong>
                  <span>followers</span>
                </div>
                <div className="metric-card">
                  <strong>{profile.following_count}</strong>
                  <span>following</span>
                </div>
              </div>
              <p className="muted-copy">{profile.bio || "Пока без биографии."}</p>
            </>
          ) : (
            <p>Загрузка профиля...</p>
          )}
        </SectionCard>

        <SectionCard eyebrow="Explore" title="Поиск людей">
          <input
            value={peopleQuery}
            onChange={(event) => setPeopleQuery(event.target.value)}
            placeholder="Ищи по username..."
          />
          <div className="people-grid">
            {peopleResults.map((person) => (
              <button
                key={person.id}
                type="button"
                className="person-chip"
                onClick={() => navigate(`/profile/${person.username}`)}
              >
                @{person.username}
              </button>
            ))}
          </div>
        </SectionCard>
      </div>

      {isOwnProfile ? (
        <SectionCard eyebrow="Edit" title="Редактировать профиль">
          <form className="entry-form" onSubmit={handleProfileSave}>
            <label>
              Bio
              <textarea
                value={profileForm.bio}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, bio: event.target.value }))
                }
              />
            </label>
            <label>
              Avatar URL
              <input
                type="url"
                value={profileForm.avatar_url}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, avatar_url: event.target.value }))
                }
                placeholder="https://..."
              />
            </label>
            <button type="submit" className="primary-button">
              Сохранить
            </button>
          </form>
        </SectionCard>
      ) : null}

      <div className="page-grid triple">
        <SectionCard eyebrow="Watched" title="Просмотрено">
          <div className="library-grid">
            {watched.map((entry) => (
              <MovieTile
                key={entry.id}
                className="movie-tile-profile"
                title={entry.movie.title}
                posterUrl={entry.movie.poster_url}
                to={`/movie/${entry.movie.id}`}
                meta={formatLibraryMeta(entry, "без оценки")}
                description={entry.review || entry.movie.description}
                badges={entry.rating ? [`${entry.rating}/10`] : ["Просмотрено"]}
              />
            ))}
            {!watched.length ? <p>Пока пусто.</p> : null}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Queue" title="Хочу посмотреть">
          <div className="library-grid">
            {wishlist.map((entry) => (
              <MovieTile
                key={entry.id}
                className="movie-tile-profile"
                title={entry.movie.title}
                posterUrl={entry.movie.poster_url}
                to={`/movie/${entry.movie.id}`}
                meta={formatLibraryMeta(entry, "скоро в очереди")}
                description={entry.movie.description}
                badges={["В списке"]}
              />
            ))}
            {!wishlist.length ? <p>Пока пусто.</p> : null}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Network" title="Социальный граф">
          <p className="muted-copy">Подписчики</p>
          <div className="people-grid">
            {followers.map((person) => (
              <button
                key={`follower-${person.id}`}
                type="button"
                className="person-chip"
                onClick={() => navigate(`/profile/${person.username}`)}
              >
                @{person.username}
              </button>
            ))}
          </div>
          <p className="muted-copy">Подписки</p>
          <div className="people-grid">
            {following.map((person) => (
              <button
                key={`following-${person.id}`}
                type="button"
                className="person-chip"
                onClick={() => navigate(`/profile/${person.username}`)}
              >
                @{person.username}
              </button>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
