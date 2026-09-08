import { BrowserRouter, Route, Routes, Link, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import JobDetail from "./pages/JobDetail";
import Admin from "./pages/Admin";
import { currentUsername, hasRole, logout } from "./lib/auth";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <header className="border-b border-rulescope-border bg-rulescope-surface px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl font-bold text-rulescope-orange">Rule</span>
            <span className="text-2xl font-bold text-rulescope-green">Scope</span>
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            {hasRole("admin") && (
              <Link to="/admin" className="text-rulescope-muted hover:text-rulescope-white">
                Admin
              </Link>
            )}
            <span className="text-rulescope-muted">{currentUsername()}</span>
            <button className="btn-secondary text-xs" onClick={() => logout()}>
              Log out
            </button>
          </nav>
        </header>

        <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs/:jobId" element={<JobDetail />} />
            <Route path="/admin" element={hasRole("admin") ? <Admin /> : <Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
