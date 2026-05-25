import { FileUp, LogOut } from "lucide-react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { AuthContext, useAuth, useAuthState } from "./hooks/useAuth";
import LoginPage from "./components/LoginPage";
import RegisterPage from "./components/RegisterPage";
import ConsultationPage from "./pages/ConsultationPage";
import UploadPage from "./pages/UploadPage";

function Shell() {
  const auth = useAuth();
  if (auth.loading) return <main className="p-6">Loading...</main>;
  if (!auth.user) {
    return (
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<LoginPage />} />
      </Routes>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <NavLink to="/upload" className="flex items-center gap-2 font-semibold">
            <FileUp size={20} aria-hidden="true" /> Notability Agent
          </NavLink>
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden sm:inline">{auth.user.name}</span>
            <button className="focus-ring rounded border border-stone-300 px-3 py-2" onClick={auth.logout} title="Log out">
              <LogOut size={16} aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>
      <Routes>
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/consultation/:id" element={<ConsultationPage />} />
        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </div>
  );
}

export default function App() {
  const auth = useAuthState();
  return (
    <AuthContext.Provider value={auth}>
      <Shell />
    </AuthContext.Provider>
  );
}
