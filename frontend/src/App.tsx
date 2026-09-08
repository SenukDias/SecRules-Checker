import { BrowserRouter, Route, Routes, Link, Navigate, useLocation } from "react-router-dom";
import { LayoutDashboard, LogOut, ShieldCheck, Users } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import JobDetail from "./pages/JobDetail";
import Admin from "./pages/Admin";
import { currentUsername, hasRole, logout } from "./lib/auth";

function IconRail() {
  const location = useLocation();
  const isAdmin = hasRole("admin");

  const navItem = (to: string, label: string, Icon: typeof LayoutDashboard) => {
    const active = location.pathname === to;
    return (
      <Link
        to={to}
        title={label}
        className={`flex items-center justify-center w-11 h-11 rounded-xl transition-colors ${
          active ? "bg-rulescope-orange text-white" : "text-rulescope-muted hover:bg-rulescope-surfaceAlt hover:text-rulescope-white"
        }`}
      >
        <Icon size={20} />
      </Link>
    );
  };

  return (
    <aside className="w-16 shrink-0 flex flex-col items-center py-5 gap-3 bg-rulescope-surface border-r border-rulescope-border">
      <Link to="/" className="w-9 h-9 rounded-lg bg-gradient-to-br from-rulescope-orange to-rulescope-green flex items-center justify-center font-bold text-sm mb-4">
        RS
      </Link>
      {navItem("/", "Dashboard", LayoutDashboard)}
      {isAdmin && navItem("/admin", "Admin", Users)}
      <div className="flex-1" />
      <div title={currentUsername()} className="w-9 h-9 rounded-full bg-rulescope-surfaceAlt flex items-center justify-center text-xs font-semibold">
        {currentUsername().slice(0, 2).toUpperCase()}
      </div>
      <button title="Log out" onClick={() => logout()} className="w-9 h-9 rounded-lg flex items-center justify-center text-rulescope-muted hover:text-red-400 hover:bg-rulescope-surfaceAlt">
        <LogOut size={18} />
      </button>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="h-14 shrink-0 border-b border-rulescope-border bg-rulescope-surface px-6 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <ShieldCheck size={18} className="text-rulescope-green" />
        <span className="text-lg font-bold text-rulescope-orange">Rule</span>
        <span className="text-lg font-bold text-rulescope-green">Scope</span>
      </div>
      <span className="text-xs text-rulescope-muted">Firewall &amp; Network Rule Auditor</span>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex">
        <IconRail />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar />
          <main className="flex-1 px-6 py-8 max-w-7xl mx-auto w-full">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/jobs/:jobId" element={<JobDetail />} />
              <Route path="/admin" element={hasRole("admin") ? <Admin /> : <Navigate to="/" />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
