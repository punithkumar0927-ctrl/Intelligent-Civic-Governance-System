import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { TrendingUp, Users, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../services/api';
import { IssueCategory, CATEGORY_LABELS } from '../types';

const COLORS = ['#0ea5e9', '#22c55e', '#f97316', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b'];

export default function Analytics() {
  const [months, setMonths] = useState(12);

  const { data: stats } = useQuery({
    queryKey: ['analytics-dashboard'],
    queryFn: () => analyticsApi.dashboard(),
  });

  const { data: trends } = useQuery({
    queryKey: ['analytics-trends', months],
    queryFn: () => analyticsApi.trends(months),
  });

  const catData = stats?.by_category.map(c => ({
    name: CATEGORY_LABELS[c.category as IssueCategory]?.slice(0, 15) ?? c.category,
    count: c.count,
  })) ?? [];

  const sevData = stats?.by_severity.map(s => ({
    name: s.severity.toUpperCase(),
    value: s.count,
    color: { low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#ef4444' }[s.severity] ?? '#6b7280',
  })) ?? [];

  return (
    <div className="max-w-screen-xl mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp size={24} className="text-nexus-600" /> Analytics & Insights
        </h1>
        <p className="text-sm text-gray-500 mt-1">Data-driven view of urban infrastructure health</p>
      </div>

      {/* Summary tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total', value: stats?.total_issues, icon: <AlertTriangle size={20} className="text-orange-500" />, bg: 'bg-orange-50' },
          { label: 'Resolved', value: stats?.resolved_issues, icon: <CheckCircle2 size={20} className="text-green-500" />, bg: 'bg-green-50' },
          { label: 'Resolution Rate', value: stats ? `${stats.resolution_rate}%` : null, icon: <TrendingUp size={20} className="text-blue-500" />, bg: 'bg-blue-50' },
          { label: 'Avg Days', value: stats ? `${stats.avg_resolution_days}d` : null, icon: <Users size={20} className="text-purple-500" />, bg: 'bg-purple-50' },
        ].map((t) => (
          <div key={t.label} className="card p-4 flex items-center gap-3">
            <div className={`p-2 rounded-lg ${t.bg}`}>{t.icon}</div>
            <div>
              <div className="text-2xl font-bold">{t.value ?? '—'}</div>
              <div className="text-sm text-gray-500">{t.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">

        {/* Monthly trend */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">Monthly Reports</h2>
            <select
              value={months} onChange={e => setMonths(Number(e.target.value))}
              className="input-field text-sm w-auto py-1"
            >
              {[3, 6, 12, 24].map(m => <option key={m} value={m}>Last {m}m</option>)}
            </select>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={trends ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total" name="Reported" stroke="#0ea5e9" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="resolved" name="Resolved" stroke="#22c55e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category bar chart */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Issues by Category</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={catData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">

        {/* Severity pie */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Severity Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={sevData}
                cx="50%" cy="50%"
                innerRadius={60} outerRadius={90}
                paddingAngle={4}
                dataKey="value"
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
              >
                {sevData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Resolution by status */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Status Breakdown</h2>
          <div className="space-y-3">
            {stats?.by_status.map((s) => {
              const pct = Math.round((s.count / Math.max(stats.total_issues, 1)) * 100);
              const colors: Record<string, string> = {
                pending: '#9ca3af', under_review: '#60a5fa', in_progress: '#fbbf24',
                resolved: '#34d399', rejected: '#f87171', duplicate: '#a78bfa',
              };
              return (
                <div key={s.status}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize">{s.status.replace('_', ' ')}</span>
                    <span>{s.count} ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: colors[s.status] ?? '#6b7280' }}
                    />
                  </div>
                </div>
              );
            }) ?? []}
          </div>
        </div>
      </div>
    </div>
  );
}
