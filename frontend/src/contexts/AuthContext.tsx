import { createContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { jwtDecode } from "jwt-decode";
import type { User, LoginCredentials, RegisterData } from "../types";
import * as authApi from "../services/authApi";
import { queryClient } from "../main";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  loginWithGoogle: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  // Verificar tokens no mount
  useEffect(() => {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      try {
        const decoded = jwtDecode<{ exp: number; sub: string }>(accessToken);
        if (decoded.exp * 1000 > Date.now()) {
          // Token valido — buscar perfil
          authApi.getProfile(accessToken).then(setUser).catch(() => {
            localStorage.removeItem("access_token");
          });
        } else {
          // Token expirado — tentar refresh via cookie HttpOnly
          authApi.refreshTokenApi().then((tokens) => {
            localStorage.setItem("access_token", tokens.access_token);
            if (tokens.user) setUser(tokens.user);
            else authApi.getProfile(tokens.access_token).then(setUser);
          }).catch(() => {
            localStorage.removeItem("access_token");
          });
        }
      } catch {
        localStorage.removeItem("access_token");
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await authApi.loginUser(credentials);
    queryClient.clear();
    localStorage.setItem("access_token", response.access_token);
    if (response.user) setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    const response = await authApi.registerUser(data);
    queryClient.clear();
    localStorage.setItem("access_token", response.access_token);
    if (response.user) setUser(response.user);
  }, []);

  const loginWithGoogle = useCallback(async (code: string) => {
    const response = await authApi.googleAuth(code);
    queryClient.clear();
    localStorage.setItem("access_token", response.access_token);
    if (response.user) setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      try {
        await authApi.logoutUser(accessToken);
      } catch {
        // Ignorar erro — limpar tokens localmente de qualquer forma
      }
    }
    localStorage.removeItem("access_token");
    queryClient.clear();
    setUser(null);
  }, []);

  const updateUser = useCallback((updatedUser: User) => {
    setUser(updatedUser);
  }, []);

  return (
    <AuthContext.Provider value={{
      user, isAuthenticated, isLoading,
      login, register, loginWithGoogle, logout, updateUser,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
