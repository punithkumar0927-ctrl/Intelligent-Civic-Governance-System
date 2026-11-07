import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import api from '../services/api';

export default function AIReports() {
  const [params] = useSearchParams();
  const [issueId, setIssueId] = useState(params.get('issue') || '');
  const [report, setReport] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get(`/ai-reports/${issueId}`);
      setReport(data.report);
      setNote(data.note);
    } catch {
      setError('That report could not be generated. Check the issue id and your access.');
      setReport('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Generative AI</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Evidence-based report</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-400">
          The narrative is built from the stored issue. It does not invent detections, coordinates, or a completed repair.
        </p>
      </header>
      <div className="flex gap-2">
        <input
          value={issueId}
          onChange={(event) => setIssueId(event.target.value)}
          placeholder="Issue id"
          className="w-40 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
        />
        <button onClick={load} disabled={!issueId || loading} className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950">
          {loading ? 'Generating…' : 'Generate'}
        </button>
      </div>
      {error && <p className="text-sm text-rose-300">{error}</p>}
      {note && <p className="text-xs text-slate-500">{note}</p>}
      {report && <article className="whitespace-pre-wrap rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm leading-6 text-slate-200">{report}</article>}
    </AppLayout>
  );
}
