import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { MapPin, Brain, User, LogOut, BarChart3, PlusCircle, Home } from 'lucide-react';
import { useAuthStore } from '../hooks/useAuthStore';

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const commandCenter = location.pathname !== '/' && location.pathname !== '/login' && location.pathname !== '/register'
    && !location.pathname.startsWith('/forgot') && !location.pathname.startsWith('/reset') && location.pathname !== '/verify-email';

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isActive = (path: string) =>
    location.pathname === path
      ? commandCenter ? 'text-cyan-300 border-cyan-300' : 'text-nexus-600 border-nexus-600'
      : commandCenter
        ? 'text-slate-400 border-transparent hover:text-white hover:border-slate-600'
        : 'text-gray-500 border-transparent hover:text-gray-900 hover:border-gray-300';

  return (
    <nav className={`sticky top-0 z-50 border-b ${commandCenter ? 'border-slate-800 bg-[#0a101b]' : 'border-gray-200 bg-white'}`}>
      <div className="max-w-screen-xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className={`flex items-center gap-2 rounded-lg px-3 py-1.5 transition-colors ${commandCenter ? 'bg-cyan-400 text-slate-950 group-hover:bg-cyan-300' : 'bg-nexus-600 text-white group-hover:bg-nexus-700'}`}>
              <Brain size={20} />
              <span className="font-bold text-lg tracking-tight">NEXUS AI</span>
            </div>
            <span className={`mt-0.5 hidden text-xs sm:inline ${commandCenter ? 'text-slate-500' : 'text-gray-400'}`}>
              The Living Intelligence Map
            </span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-1">
            {[
              { to: '/dashboard', label: 'Dashboard', icon: <Home size={16} /> },
              { to: '/reports', label: 'Reports',   icon: <MapPin size={16} /> },
              { to: '/report-issue',  label: 'Report',    icon: <PlusCircle size={16} /> },
              { to: '/analytics',label: 'Analytics',icon: <BarChart3 size={16} /> },
            ].map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium transition-colors ${isActive(l.to)}`}
              >
                {l.icon} {l.label}
              </Link>
            ))}
          </div>

          {/* User */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <span className={`hidden items-center gap-2 text-sm sm:flex ${commandCenter ? 'text-slate-300' : 'text-gray-600'}`}>
                  <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${commandCenter ? 'bg-cyan-400/10 text-cyan-200' : 'bg-nexus-100 text-nexus-700'}`}>
                    {user.username[0].toUpperCase()}
                  </div>
                  {user.full_name || user.username}
                  <span className={`rounded px-1.5 py-0.5 text-xs ${commandCenter ? 'bg-slate-800 text-slate-400' : 'bg-gray-100'}`}>{user.role}</span>
                </span>
                <button
                  onClick={handleLogout}
                  className={`p-2 transition-colors ${commandCenter ? 'text-slate-500 hover:text-rose-300' : 'text-gray-400 hover:text-red-500'}`}
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-primary text-sm py-1.5">
                <User size={16} className="inline mr-1" /> Sign In
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="md:hidden flex gap-1 px-4 pb-2 overflow-x-auto">
        {['/', '/gps-camera', '/gps-gallery', '/reports', '/analytics'].map((path) => (
          <Link
            key={path}
            to={path}
            className={`whitespace-nowrap px-3 py-1.5 rounded-lg text-sm font-medium ${
              location.pathname === path
                ? commandCenter ? 'bg-cyan-400 text-slate-950' : 'bg-nexus-600 text-white'
                : commandCenter ? 'bg-slate-800 text-slate-300' : 'bg-gray-100 text-gray-600'
            }`}
          >
            {path === '/' ? 'Home' : path === '/gps-camera' ? 'Camera' : path === '/gps-gallery' ? 'Gallery' : path === '/reports' ? 'Reports' : 'Stats'}
          </Link>
        ))}
      </div>
    </nav>
  );
}
