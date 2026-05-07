import { useState } from "react";

import { useAuth } from "../context/AuthContext";

const defaultRegisterForm = {
  username: "",
  email: "",
  password: "",
  password_confirm: "",
};

const defaultLoginForm = {
  username: "",
  password: "",
};

export function AuthPanel() {
  const { register, signIn, authBusy, authError } = useAuth();
  const [mode, setMode] = useState("login");
  const [loginForm, setLoginForm] = useState(defaultLoginForm);
  const [registerForm, setRegisterForm] = useState(defaultRegisterForm);
  const [message, setMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage("");

    try {
      if (mode === "login") {
        await signIn(loginForm);
        setMessage("Вход выполнен. Лента и рекомендации уже доступны.");
      } else {
        await register(registerForm);
        setMessage("Аккаунт создан, сессия активна.");
        setRegisterForm(defaultRegisterForm);
      }
    } catch (_error) {
      return;
    }
  }

  return (
    <div className="auth-panel">
      <div className="tab-strip">
        <button
          type="button"
          className={mode === "login" ? "tab-button active" : "tab-button"}
          onClick={() => setMode("login")}
        >
          Вход
        </button>
        <button
          type="button"
          className={mode === "register" ? "tab-button active" : "tab-button"}
          onClick={() => setMode("register")}
        >
          Регистрация
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        {mode === "login" ? (
          <>
            <label>
              Username
              <input
                value={loginForm.username}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, username: event.target.value }))
                }
                placeholder="neonfox"
                required
              />
            </label>
            <label>
              Пароль
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="••••••••"
                required
              />
            </label>
          </>
        ) : (
          <>
            <label>
              Username
              <input
                value={registerForm.username}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, username: event.target.value }))
                }
                placeholder="cybernova"
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={registerForm.email}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, email: event.target.value }))
                }
                placeholder="you@example.com"
                required
              />
            </label>
            <label>
              Пароль
              <input
                type="password"
                value={registerForm.password}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Минимум 8 символов"
                required
              />
            </label>
            <label>
              Повтор пароля
              <input
                type="password"
                value={registerForm.password_confirm}
                onChange={(event) =>
                  setRegisterForm((current) => ({
                    ...current,
                    password_confirm: event.target.value,
                  }))
                }
                placeholder="Повтори пароль"
                required
              />
            </label>
          </>
        )}

        <button type="submit" className="primary-button" disabled={authBusy}>
          {authBusy ? "Подключение..." : mode === "login" ? "Войти" : "Создать аккаунт"}
        </button>
      </form>

      {authError ? <p className="form-error">{authError}</p> : null}
      {message ? <p className="form-success">{message}</p> : null}

      <div className="demo-card">
        <span className="eyebrow">Demo</span>
        <p>
          После запуска seed-команды можно войти как `neonfox` с паролем
          `password123`.
        </p>
      </div>
    </div>
  );
}
