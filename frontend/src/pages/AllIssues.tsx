import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import AppLayout from '../layouts/AppLayout';
import { apiErrorMessage, reportApi } from '../services/api';
import { useAuthStore } from '../hooks/useAuthStore';
import { Issue } from '../types';

type PendingDelete =
  | { kind: 'one'; issue: Issue }
  | { kind: 'many' }
  | { kind: 'all'; step: 1 | 2 };

export default function AllIssues() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<number[]>([]);
  const [pending, setPending] = useState<PendingDelete | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const query = useQuery({
    queryKey: ['issues', 'mine', page],
    queryFn: () => reportApi.list(page, 50, { mine: 'true' }),
  });
  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const selectedOnPage = items.filter((issue) => selected.includes(issue.id));

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ['issues'] });
    await queryClient.invalidateQueries({ queryKey: ['reports'] });
    await queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    await queryClient.invalidateQueries({ queryKey: ['dashboard-trends'] });
    await queryClient.invalidateQueries({ queryKey: ['recent-issues'] });
    await queryClient.invalidateQueries({ queryKey: ['analytics-dashboard'] });
    await queryClient.invalidateQueries({ queryKey: ['geo-points'] });
    await queryClient.invalidateQueries({ queryKey: ['hotspots'] });
  };

  const confirmDelete = async () => {
    if (!pending) return;
    setBusy(true);
    setError('');
    try {
      const result = pending.kind === 'one'
        ? await reportApi.remove(pending.issue.id)
        : pending.kind === 'many'
          ? await reportApi.removeMany(selectedOnPage.map((issue) => issue.id))
          : await reportApi.removeAllMine();
      setSelected([]);
      setPending(null);
      if (pending.kind === 'one' && items.length === 1 && page > 1) setPage(page - 1);
      await refresh();
      setNotice(result.deleted === 1 ? 'Report deleted successfully.' : 'Reports deleted successfully.');
      if (result.file_errors.length) {
        setError(`The report record was deleted. A stored file could not be removed: ${result.file_errors.join(' ')}`);
      }
    } catch (err) {
      setError(apiErrorMessage(err, 'The report could not be deleted.'));
    } finally {
      setBusy(false);
    }
  };

  const toggle = (id: number) => {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  };

  return (
    <AppLayout>
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Reports</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">Your reports</h1>
          <p className="mt-1 text-sm text-slate-400">{total} saved {total === 1 ? 'report' : 'reports'}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={selectedOnPage.length === 0 || busy}
            onClick={() => setPending({ kind: 'many' })}
            className="rounded-xl border border-slate-700 px-3 py-2 text-sm text-slate-200 disabled:opacity-40"
          >
            Delete selected ({selectedOnPage.length})
          </button>
          <button
            type="button"
            disabled={total === 0 || busy}
            onClick={() => setPending({ kind: 'all', step: 1 })}
            className="rounded-xl border border-rose-400/40 px-3 py-2 text-sm text-rose-200 disabled:opacity-40"
          >
            Delete all reports
          </button>
        </div>
      </header>

      {notice && <p className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-200" role="status">{notice}</p>}
      {error && <p className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-200" role="alert">{error}</p>}
      {query.isLoading && <p className="text-sm text-slate-400">Loading reports…</p>}
      {query.isError && <p className="text-sm text-rose-300">Reports could not be loaded.</p>}

      <ul className="space-y-3">
        {items.map((issue) => {
          const own = issue.reporter?.id === user?.id;
          return (
            <li key={issue.id} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex items-start gap-3">
                {own && (
                  <input
                    type="checkbox"
                    checked={selected.includes(issue.id)}
                    onChange={() => toggle(issue.id)}
                    aria-label={`Select ${issue.title}`}
                    className="mt-1"
                  />
                )}
                <div className="min-w-0 flex-1">
                  <Link to={`/issue/${issue.id}`} className="font-medium text-cyan-200 hover:underline">{issue.title}</Link>
                  <p className="mt-1 text-xs text-slate-400">{issue.category} · {issue.status} · {issue.severity}</p>
                </div>
                <Link to={`/ai-reports?issue=${issue.id}`} className="text-xs text-slate-300 hover:text-white">AI report</Link>
                {own && (
                  <button
                    type="button"
                    aria-label={`Delete ${issue.title}`}
                    onClick={() => setPending({ kind: 'one', issue })}
                    className="rounded-lg p-2 text-slate-400 hover:bg-rose-400/10 hover:text-rose-300"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      {query.data && items.length === 0 && <p className="text-sm text-slate-400">No reports yet.</p>}
      {total > 50 && (
        <div className="flex items-center gap-3 text-sm text-slate-300">
          <button type="button" disabled={page === 1} onClick={() => setPage(page - 1)} className="rounded-lg border border-slate-700 px-3 py-1 disabled:opacity-40">Previous</button>
          <span>Page {page}</span>
          <button type="button" disabled={page * 50 >= total} onClick={() => setPage(page + 1)} className="rounded-lg border border-slate-700 px-3 py-1 disabled:opacity-40">Next</button>
        </div>
      )}

      {pending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4" role="presentation">
          <div role="dialog" aria-modal="true" aria-labelledby="delete-title" className="w-full max-w-md rounded-2xl border border-slate-700 bg-[#0d1422] p-5 text-slate-100 shadow-2xl">
            <h2 id="delete-title" className="text-lg font-semibold">
              {pending.kind === 'all' && pending.step === 2 ? 'Delete every report you created?' : 'Are you sure you want to delete this report?'}
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              {pending.kind === 'one' && `“${pending.issue.title}” and its uploaded files will be removed permanently.`}
              {pending.kind === 'many' && `${selectedOnPage.length} selected reports and their uploaded files will be removed permanently.`}
              {pending.kind === 'all' && pending.step === 1 && 'This starts deletion of every report on your account.'}
              {pending.kind === 'all' && pending.step === 2 && 'This cannot be undone. Other people’s reports stay untouched.'}
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setPending(null)} className="rounded-xl px-3 py-2 text-sm text-slate-300">Cancel</button>
              {pending.kind === 'all' && pending.step === 1 ? (
                <button type="button" onClick={() => setPending({ kind: 'all', step: 2 })} className="rounded-xl bg-rose-500 px-3 py-2 text-sm font-semibold text-white">Continue</button>
              ) : (
                <button type="button" disabled={busy} onClick={confirmDelete} className="rounded-xl bg-rose-500 px-3 py-2 text-sm font-semibold text-white disabled:opacity-60">
                  {busy ? 'Deleting…' : 'Delete Permanently'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
