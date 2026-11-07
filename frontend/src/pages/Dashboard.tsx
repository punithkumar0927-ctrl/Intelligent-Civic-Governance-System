import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, BrainCircuit,
  CheckCircle2, ChevronRight, CircleDot, Clock3, MapPin, Plus, Search,
  ShieldAlert, Sparkles, Target, TriangleAlert,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { analyticsApi, reportApi } from '../services/api';
import { CATEGORY_LABELS, IssueCategory, IssueStatus, SEVERITY_COLORS } from '../types';
import Sidebar from '../components/Sidebar';
import SeverityBadge from '../components/SeverityBadge';
import MapView from '../components/MapView';

const panel = 'rounded-2xl border border-slate-800/90 bg-slate-900/65 shadow-[0_16px_50px_rgba(0,0,0,0.18)]';
const tooltipStyle = {
  backgroundColor: '#0b1321',
  border: '1px solid #253248',
  borderRadius: 12,
  color: '#e2e8f0',
};

const CATEGORY_ORDER: IssueCategory[] = [
  'road_damage', 'garbage', 'water_leak', 'sidewalk', 'drainage', 'pothole',
];

function MetricCard({
  icon: Icon,
  label,
  value,
  caption,
  tone,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  caption: string;
  tone: string;
}) {
  return (
    <article className={`${panel} group min-w-0 p-4 transition duration-200 hover:-translate-y-0.5 hover:border-slate-700 sm:p-5`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-[0.12em] text-slate-400">{label}</p>
          <p className="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-[30px]">{value}</p>
        </div>
        <div className={`rounded-xl border p-2.5 ${tone}`}>
          <Icon size={18} />
        </div>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{caption}</p>
    </article>
  );
}

function severityColor(severity: string) {
  return SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] ?? '#64748b';
}

export default function Dashboard() {
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [search, setSearch] = useState('');

  const statsQuery = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => analyticsApi.dashboard(),
  });
  const trendsQuery = useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: () => analyticsApi.trends(8),
  });
  const issueQuery = useQuery({
    queryKey: ['recent-issues', statusFilter, categoryFilter, search],
    queryFn: () => reportApi.list(1, 8, {
      ...(statusFilter && { status: statusFilter }),
      ...(categoryFilter && { category: categoryFilter }),
      ...(search.trim() && { q: search.trim() }),
    }),
  });

  const stats = statsQuery.data;
  const severityData = useMemo(
    () => (stats?.by_severity ?? []).map((row) => ({
      name: row.severity,
      value: row.count,
      color: severityColor(row.severity),
    })),
    [stats?.by_severity],
  );
  const categoryData = useMemo(
    () => CATEGORY_ORDER.map((category) => ({
      category: CATEGORY_LABELS[category],
      reports: stats?.by_category.find((row) => row.category === category)?.count ?? 0,
    })),
    [stats?.by_category],
  );

  const metrics = [
    {
      icon: CircleDot,
      label: 'Total reports',
      value: stats?.total_issues ?? '—',
      caption: 'Reports stored in this instance',
      tone: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-300',
    },
    {
      icon: Activity,
      label: 'Active issues',
      value: stats?.active_issues ?? '—',
      caption: 'Submitted, in review, or in progress',
      tone: 'border-blue-400/20 bg-blue-400/10 text-blue-300',
    },
    {
      icon: ShieldAlert,
      label: 'High severity',
      value: stats?.high_severity_issues ?? '—',
      caption: 'High or critical; requires attention',
      tone: 'border-orange-400/20 bg-orange-400/10 text-orange-300',
    },
    {
      icon: CheckCircle2,
      label: 'Verified resolutions',
      value: stats?.verified_resolutions ?? '—',
      caption: 'Counted only after human verification',
      tone: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
    },
    {
      icon: Target,
      label: 'AI detection accuracy',
      value: stats?.ai_detection_accuracy == null
        ? 'Not measured'
        : `${stats.ai_detection_accuracy.toFixed(1)}%`,
      caption: 'Requires a human-labeled evaluation set',
      tone: 'border-violet-400/20 bg-violet-400/10 text-violet-300',
    },
    {
      icon: BrainCircuit,
      label: 'Possible duplicates',
      value: stats?.duplicate_reports ?? '—',
      caption: 'AI match candidates; review before merging',
      tone: 'border-fuchsia-400/20 bg-fuchsia-400/10 text-fuchsia-300',
    },
  ];

  return (
    <div className="nexus-dashboard min-h-full bg-[#080d17] text-slate-100">
      <div className="flex min-h-[calc(100vh-4rem)]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1500px] space-y-6">
            <header className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
              <div>
                <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-300">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-60" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
                  </span>
                  Civic intelligence / overview
                </div>
                <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                  The Living Intelligence Map
                </h1>
                <p className="mt-2 max-w-2xl text-sm text-slate-400">
                  A consolidated view of reported infrastructure issues, model signals, and community follow-through.
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <label className="flex min-w-0 items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-2.5 text-slate-400 sm:min-w-[250px]">
                  <Search size={16} aria-hidden="true" />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search reports..."
                    aria-label="Search reports"
                    className="w-full bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-500"
                  />
                </label>
                <Link
                  to="/report"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
                >
                  <Plus size={17} /> New report
                </Link>
              </div>
            </header>

            <div className="flex flex-col gap-2 rounded-xl border border-cyan-900/50 bg-cyan-950/25 px-4 py-3 text-xs leading-5 text-cyan-100/80 sm:flex-row sm:items-center sm:justify-between">
              <span className="inline-flex items-center gap-2 font-semibold text-cyan-200">
                <Sparkles size={15} />
                {stats?.demo_data ? 'SYNTHETIC DEMO DATA' : 'INSTANCE REPORT DATA'}
              </span>
              <span>
                {stats?.demo_data
                  ? 'All seeded records are illustrative only—not actual reports, repairs, official approvals, or government data.'
                  : 'This dashboard is not an official municipal service or real-time government feed.'}
              </span>
            </div>

            {statsQuery.isError && (
              <div role="alert" className="rounded-xl border border-rose-900/70 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">
                Dashboard data could not be loaded. Check the API connection and sign-in, then refresh.
              </div>
            )}

            <section aria-label="Key performance indicators" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
              {metrics.map((metric) => (
                <MetricCard key={metric.label} {...metric} />
              ))}
            </section>

            <section className="grid gap-5 xl:grid-cols-12">
              <article className={`${panel} min-w-0 p-4 sm:p-5 xl:col-span-8`}>
                <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">Report activity</p>
                    <p className="mt-1 text-xs text-slate-500">Reports created by month</p>
                  </div>
                  <span className="rounded-lg border border-slate-800 px-2.5 py-1 text-[11px] text-slate-400">Last 8 months</span>
                </div>
                <div className="h-[245px]">
                  {trendsQuery.isLoading ? (
                    <div className="h-full animate-pulse rounded-xl bg-slate-800/50" />
                  ) : trendsQuery.isError ? (
                    <div className="flex h-full items-center justify-center text-sm text-slate-500">Trend data unavailable.</div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={trendsQuery.data ?? []} margin={{ top: 8, right: 6, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="reportsGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.28} />
                            <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke="#1e293b" strokeDasharray="3 4" vertical={false} />
                        <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <YAxis allowDecimals={false} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Area type="monotone" dataKey="total" name="Reports" stroke="#22d3ee" strokeWidth={2} fill="url(#reportsGradient)" />
                        <Area type="monotone" dataKey="resolved" name="Verified" stroke="#34d399" strokeWidth={2} fill="transparent" />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </article>

              <article className={`${panel} min-w-0 p-4 sm:p-5 xl:col-span-4`}>
                <div className="mb-1">
                  <p className="text-sm font-semibold text-white">Severity distribution</p>
                  <p className="mt-1 text-xs text-slate-500">Prioritization signals, not a safety certification</p>
                </div>
                <div className="relative h-[225px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={severityData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={84} paddingAngle={4} stroke="none">
                        {severityData.map((item) => <Cell key={item.name} fill={item.color} />)}
                      </Pie>
                      <Tooltip contentStyle={tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-semibold text-white">{stats?.total_issues ?? '—'}</span>
                    <span className="text-[10px] uppercase tracking-[0.15em] text-slate-500">reports</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {severityData.map((item) => (
                    <div key={item.name} className="flex items-center justify-between rounded-lg bg-slate-950/50 px-2.5 py-2 text-xs">
                      <span className="flex items-center gap-2 capitalize text-slate-400">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />{item.name}
                      </span>
                      <span className="font-medium text-slate-200">{item.value}</span>
                    </div>
                  ))}
                </div>
              </article>
            </section>

            <section className="grid gap-5 xl:grid-cols-12">
              <article className={`${panel} min-w-0 p-4 sm:p-5 xl:col-span-5`}>
                <div className="mb-5 flex items-start justify-between">
                  <div>
                    <p className="text-sm font-semibold text-white">Issue categories</p>
                    <p className="mt-1 text-xs text-slate-500">Distribution across the leading categories</p>
                  </div>
                  <TriangleAlert className="text-slate-600" size={18} />
                </div>
                <div className="h-[260px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={categoryData} layout="vertical" margin={{ top: 0, right: 8, left: 16, bottom: 0 }}>
                      <CartesianGrid stroke="#1e293b" strokeDasharray="3 4" horizontal={false} />
                      <XAxis type="number" allowDecimals={false} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="category" width={94} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#152033' }} />
                      <Bar dataKey="reports" name="Reports" fill="#38bdf8" radius={[0, 5, 5, 0]} maxBarSize={16} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </article>

              <article className={`${panel} min-w-0 overflow-hidden p-4 sm:p-5 xl:col-span-7`}>
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-white">Geographic intelligence</p>
                    <p className="mt-1 text-xs text-slate-500">Report locations, color-coded by estimated severity</p>
                  </div>
                  <Link to="/geographic" className="inline-flex items-center gap-1 text-xs font-medium text-cyan-300 hover:text-cyan-200">
                    Open map <ChevronRight size={14} />
                  </Link>
                </div>
                {stats?.geo_points.length ? (
                  <MapView points={stats.geo_points} height="300px" />
                ) : (
                  <div className="flex h-[300px] flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-950/40 text-center">
                    <MapPin className="mb-2 text-slate-600" size={24} />
                    <p className="text-sm text-slate-400">No location-enabled reports yet</p>
                    <p className="mt-1 text-xs text-slate-600">Location sharing is optional.</p>
                  </div>
                )}
              </article>
            </section>

            <section className="grid gap-5 xl:grid-cols-12">
              <article className={`${panel} min-w-0 p-4 sm:p-5 xl:col-span-8`}>
                <div className="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                  <div>
                    <p className="text-sm font-semibold text-white">Recent AI-analyzed reports</p>
                    <p className="mt-1 text-xs text-slate-500">Model outputs are assistive and require appropriate review</p>
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={statusFilter}
                      onChange={(event) => setStatusFilter(event.target.value)}
                      aria-label="Filter reports by status"
                      className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-300 outline-none focus:border-cyan-500"
                    >
                      <option value="">All statuses</option>
                      {Object.entries({
                        pending: 'Pending',
                        under_review: 'Under review',
                        in_progress: 'In progress',
                        resolution_submitted: 'Resolution submitted',
                        verified_resolved: 'Human verified',
                      }).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                    <select
                      value={categoryFilter}
                      onChange={(event) => setCategoryFilter(event.target.value)}
                      aria-label="Filter reports by category"
                      className="max-w-[150px] rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-2 text-xs text-slate-300 outline-none focus:border-cyan-500"
                    >
                      <option value="">All categories</option>
                      {Object.entries(CATEGORY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </div>
                </div>

                {issueQuery.isLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((item) => <div key={item} className="h-[74px] animate-pulse rounded-xl bg-slate-800/50" />)}
                  </div>
                ) : issueQuery.isError ? (
                  <p role="alert" className="rounded-xl border border-rose-900/60 bg-rose-950/25 p-4 text-sm text-rose-200">
                    Reports could not be loaded. Check the API connection and your account permissions.
                  </p>
                ) : issueQuery.data?.items.length ? (
                  <div className="divide-y divide-slate-800/80">
                    {issueQuery.data.items.map((issue) => (
                      <Link
                        key={issue.id}
                        to={`/issue/${issue.id}`}
                        className="flex flex-col gap-3 py-3 transition hover:bg-slate-800/25 sm:flex-row sm:items-center sm:justify-between sm:px-2"
                      >
                        <div className="flex min-w-0 items-start gap-3">
                          <div className="mt-0.5 rounded-lg border border-slate-800 bg-slate-950 p-2 text-cyan-300">
                            <AlertTriangle size={16} />
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium text-slate-200">{issue.title}</p>
                            <p className="mt-1 truncate text-xs text-slate-500">
                              {CATEGORY_LABELS[issue.category]}{issue.city ? ` · ${issue.city}` : ''}
                              {issue.created_at ? ` · ${new Date(issue.created_at).toLocaleDateString()}` : ''}
                            </p>
                          </div>
                        </div>
                        <div className="flex shrink-0 items-center gap-2 pl-11 sm:pl-0">
                          <SeverityBadge severity={issue.severity} confidence={issue.ai_confidence ?? undefined} size="sm" />
                          <span className="rounded-full border border-slate-700 bg-slate-800/70 px-2.5 py-1 text-[10px] font-medium text-slate-300">
                            {issue.status.replace(/_/g, ' ')}
                          </span>
                          <ChevronRight size={15} className="text-slate-600" />
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-700 py-10 text-center">
                    <CircleDot className="mx-auto mb-2 text-slate-600" size={22} />
                    <p className="text-sm text-slate-400">No reports match these filters.</p>
                  </div>
                )}
                <Link to="/reports" className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-cyan-300 hover:text-cyan-200">
                  View report list <ChevronRight size={14} />
                </Link>
              </article>

              <div className="space-y-5 xl:col-span-4">
                <article className={`${panel} p-4 sm:p-5`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-semibold text-white">Model performance</p>
                      <p className="mt-1 text-xs text-slate-500">Evaluation metrics</p>
                    </div>
                    <BrainCircuit className="text-violet-300" size={18} />
                  </div>
                  <div className="mt-5 rounded-xl border border-violet-900/50 bg-violet-950/20 p-3.5">
                    <div className="flex items-center gap-2 text-sm font-medium text-violet-200">
                      <Clock3 size={15} /> Benchmark not configured
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">
                      Precision, recall, and mAP are withheld until evaluated against a labeled holdout set. Detection confidence is not accuracy.
                    </p>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                    {['Precision', 'Recall', 'mAP50', 'mAP50-95'].map((metric) => (
                      <div key={metric} className="flex justify-between rounded-lg bg-slate-950/60 px-3 py-2.5">
                        <span className="text-slate-500">{metric}</span>
                        <span className="text-slate-400">—</span>
                      </div>
                    ))}
                  </div>
                </article>

                <article className={`${panel} p-4 sm:p-5`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-semibold text-white">Resolution tracking</p>
                      <p className="mt-1 text-xs text-slate-500">Human-reviewed outcomes only</p>
                    </div>
                    <CheckCircle2 className="text-emerald-300" size={18} />
                  </div>
                  <div className="mt-5 flex items-end justify-between">
                    <div>
                      <p className="text-3xl font-semibold text-white">{stats?.verified_resolutions ?? '—'}</p>
                      <p className="mt-1 text-xs text-slate-500">verified resolutions</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-emerald-300">
                        {stats?.resolution_rate != null ? `${stats.resolution_rate}%` : '—'}
                      </p>
                      <p className="text-xs text-slate-500">of all reports</p>
                    </div>
                  </div>
                  <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-800">
                    <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400" style={{ width: `${Math.min(stats?.resolution_rate ?? 0, 100)}%` }} />
                  </div>
                  <p className="mt-3 text-xs text-slate-500">
                    {stats?.by_status.find((row) => row.status === 'resolution_submitted')?.count ?? 0} awaiting human verification
                  </p>
                </article>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
