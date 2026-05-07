import { NavLink, Route, Routes } from "react-router-dom";

import { useAuth } from "./context/AuthContext";
import { HomePage } from "./pages/HomePage";
import { MoviePage } from "./pages/MoviePage";
import { ProfilePage } from "./pages/ProfilePage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { SearchPage } from "./pages/SearchPage";

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 11.5 12 5l8 6.5V20a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z" />
    </svg>
  );
}

function GridIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 4h7v7H4zm9 0h7v7h-7zM4 13h7v7H4zm9 0h7v7h-7z" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m12 2 2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4z" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4m0 2c-4.4 0-8 2.2-8 5v1h16v-1c0-2.8-3.6-5-8-5" />
    </svg>
  );
}

const navItems = [
  { to: "/", label: "Лента", icon: HomeIcon },
  { to: "/search", label: "Каталог", icon: GridIcon },
  { to: "/recommendations", label: "Подборки", icon: SparkIcon },
  { to: "/profile", label: "Профиль", icon: UserIcon },
];

function TopBar() {
  const { isAuthenticated, user, signOut } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar-brand">
        <span className="topbar-kicker">SceneCircle</span>
        <strong>movie social</strong>
      </div>

      <div className="topbar-actions">
        <span className="status-pill">
          {isAuthenticated && user ? `@${user.username}` : "Гость"}
        </span>
        {isAuthenticated ? (
          <button type="button" className="ghost-button compact" onClick={signOut}>
            Выйти
          </button>
        ) : null}
      </div>
    </header>
  );
}

function BottomDock() {
  return (
    <nav className="bottom-dock" aria-label="Основная навигация">
      {navItems.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => (isActive ? "dock-link active" : "dock-link")}
        >
          <Icon />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <TopBar />

      <main className="page-shell">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/movie/:movieId" element={<MoviePage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/profile/:username" element={<ProfilePage />} />
        </Routes>
      </main>

      <BottomDock />
    </div>
  );
}
