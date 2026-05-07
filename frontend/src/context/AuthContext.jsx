import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
} from "react";

import { apiRequest } from "../lib/api";

const AuthContext = createContext(null);
const storageKey = "scene-circle.auth";

function readStoredSession() {
  const raw = localStorage.getItem(storageKey);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(storageKey);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => readStoredSession());
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(
    Boolean(readStoredSession()?.access)
  );
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");

  function persistSession(nextSession) {
    setSession(nextSession);

    if (nextSession) {
      localStorage.setItem(storageKey, JSON.stringify(nextSession));
    } else {
      localStorage.removeItem(storageKey);
    }
  }

  function signOut() {
    persistSession(null);
    setUser(null);
    setAuthError("");
  }

  async function refreshProfile(token = session?.access) {
    if (!token) {
      setUser(null);
      return null;
    }

    const profile = await apiRequest("/api/auth/me/", {
      token,
    });

    startTransition(() => setUser(profile));
    return profile;
  }

  async function signIn(credentials) {
    setAuthBusy(true);
    setAuthError("");

    try {
      const tokens = await apiRequest("/api/auth/token/", {
        method: "POST",
        body: credentials,
      });

      persistSession(tokens);
      await refreshProfile(tokens.access);

      return tokens;
    } catch (error) {
      setAuthError(error.message);
      throw error;
    } finally {
      setAuthBusy(false);
    }
  }

  async function register(payload) {
    setAuthBusy(true);
    setAuthError("");

    try {
      await apiRequest("/api/auth/register/", {
        method: "POST",
        body: payload,
      });

      return await signIn({
        username: payload.username,
        password: payload.password,
      });
    } catch (error) {
      setAuthError(error.message);
      throw error;
    } finally {
      setAuthBusy(false);
    }
  }

  async function saveProfile(payload) {
    const profile = await apiRequest("/api/auth/me/", {
      method: "PATCH",
      body: payload,
      token: session?.access,
    });

    startTransition(() => setUser(profile));
    return profile;
  }

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = session?.access;

      if (!token) {
        setLoadingUser(false);
        setUser(null);
        return;
      }

      setLoadingUser(true);

      try {
        const profile = await apiRequest("/api/auth/me/", {
          token,
        });

        if (!cancelled) {
          startTransition(() => setUser(profile));
        }
      } catch {
        if (!cancelled) signOut();
      } finally {
        if (!cancelled) setLoadingUser(false);
      }
    }

    bootstrap();

    return () => {
      cancelled = true;
    };
  }, [session?.access]);

  return (
    <AuthContext.Provider
      value={{
        authBusy,
        authError,
        isAuthenticated: Boolean(session?.access && user),
        loadingUser,
        refreshProfile,
        register,
        saveProfile,
        session,
        signIn,
        signOut,
        token: session?.access,
        user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}