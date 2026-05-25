import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";

type User = { id: number; email: string; name: string };
type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuthState(): AuthContextValue {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!api.token) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then(setUser)
      .catch(() => api.setToken(null))
      .finally(() => setLoading(false));
  }, []);

  return useMemo(
    () => ({
      user,
      loading,
      async login(email: string, password: string) {
        const result = await api.post<{ access_token: string; user: User }>("/auth/login", { email, password });
        api.setToken(result.access_token);
        setUser(result.user);
      },
      async register(name: string, email: string, password: string) {
        const result = await api.post<{ access_token: string; user: User }>("/auth/register", { name, email, password });
        api.setToken(result.access_token);
        setUser(result.user);
      },
      logout() {
        api.setToken(null);
        setUser(null);
      },
    }),
    [user, loading],
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthContext.Provider");
  return value;
}
