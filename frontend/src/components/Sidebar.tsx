import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3, BrainCircuit, LayoutDashboard, LogOut, Map,
  Camera, Images, Landmark, PlusCircle, Settings2, Shield, UserRound,
} from 'lucide-react';
import { useAuthStore } from '../hooks/useAuthStore';

const navigation = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/report-public-issue', label: 'Report a Public Issue', icon: Landmark },
  { to: '/my-reports', label: 'My public reports', icon: PlusCircle },
  { to: '/report-issue', label: 'Report an issue', icon: PlusCircle },
  { to: '/gram-panchayat', label: 'Gram Panchayat desk', icon: Shield },
  { to: '/taluk-panchayat', label: 'Taluk desk', icon: Shield },
  { to: '/zilla-panchayat', label: 'Zilla desk', icon: Shield },
  { to: '/gps-camera', label: 'GPS Camera', icon: Camera },
  { to: '/gps-gallery', label: 'GPS Photo Gallery', icon: Images },
  { to: '/reports', label: 'All issues', icon: Map },
  { to: '/geographic-intelligence', label: 'Geographic intelligence', icon: Map },
  { to: '/repair-verification', label: 'Repair verification', icon: Settings2 },
  { to: '/ai-reports', label: 'AI reports', icon: BrainCircuit },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/profile', label: 'My profile', icon: UserRound },
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();

  const signOut = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside className="hidden w-[235px] shrink-0 border-r border-slate-800/80 bg-[#0a101b] lg:flex lg:flex-col">
      <div className="px-5 pb-4 pt-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">Workspace</p>
        <nav aria-label="Main navigation" className="mt-4 space-y-1">
          {navigation.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to ||
              (to === '/reports' && location.pathname.startsWith('/issue/')) ||
              (to === '/report-issue' && location.pathname === '/report') ||
              (to === '/geographic-intelligence' && location.pathname === '/geographic') ||
              (to === '/repair-verification' && location.pathname === '/verification');
            return (
              <Link
                key={to}
                to={to}
                aria-current={active ? 'page' : undefined}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] transition ${
                  active
                    ? 'border border-cyan-400/15 bg-cyan-400/[0.08] font-medium text-cyan-200'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100'
                }`}
              >
                <Icon size={17} className={active ? 'text-cyan-300' : 'text-slate-500 group-hover:text-slate-300'} />
                {label}
                {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-cyan-300 shadow-[0_0_10px_#67e8f9]" />}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto border-t border-slate-800/80 p-4">
        <div className="mb-4 rounded-xl border border-slate-800 bg-slate-900/60 p-3">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">AI pipeline</p>
            <span className="flex items-center gap-1.5 text-[10px] text-emerald-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" /> Available
            </span>
          </div>
          <div className="mt-3 space-y-2 text-xs text-slate-400">
            <div className="flex items-center justify-between"><span>Vision</span><span className="text-slate-500">Assistive</span></div>
            <div className="flex items-center justify-between"><span>Severity</span><span className="text-slate-500">Estimate</span></div>
            <div className="flex items-center justify-between"><span>Duplicates</span><span className="text-slate-500">Review</span></div>
          </div>
        </div>
        {(user?.role === 'admin' || user?.role === 'officer') && (
          <Link to="/admin" className="mb-3 flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-slate-300 hover:bg-slate-800">
            <Shield size={14} /> Admin review
          </Link>
        )}
        <div className="flex items-center gap-2.5 px-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-cyan-400/20 bg-cyan-400/10 text-xs font-semibold text-cyan-200">
            {user?.username?.slice(0, 1).toUpperCase() ?? 'U'}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-slate-200">{user?.full_name || user?.username || 'Workspace user'}</p>
            <p className="text-[10px] capitalize text-slate-500">{user?.role ?? 'citizen'}</p>
          </div>
          <button
            type="button"
            onClick={signOut}
            aria-label="Log out"
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-800 hover:text-rose-300"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}
