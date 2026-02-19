import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { useAuth } from "./hooks/useAuth";
import ProtectedRoute from "./components/ProtectedRoute";
import UserMenu from "./components/UserMenu";
import MonthlyView from "./pages/MonthlyView";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ProfilePage from "./pages/ProfilePage";
import DailyExpensesView from "./pages/DailyExpensesView";
import { InstallmentsView } from "./pages/InstallmentsView";

function AppHeader() {
  const { isAuthenticated, user } = useAuth();
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-4 px-6 shadow-lg shadow-blue-900/10 flex justify-between items-center">
      <h1 className="text-xl font-extrabold tracking-wide">MEU CONTROLE</h1>
      {isAuthenticated && (
        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-white/70 font-medium hidden sm:block">
              Olá, {user.nome}
            </span>
          )}
          <UserMenu />
        </div>
      )}
    </header>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-background">
        <AppHeader />
        <main>
          <Routes>
            {/* Rotas publicas */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Rotas protegidas */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<MonthlyView />} />
              <Route path="/daily-expenses" element={<DailyExpensesView />} />
              <Route path="/installments" element={<InstallmentsView />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
