import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import api from '../services/api';

type Report = {
  reference: string;
  description: string;
  category: string;
  status: string;
  government_delivery: string;
  official_reference?: string | null;
  verified_jurisdiction: { status: string; gram_panchayat?: string | null; district?: string | null; taluk?: string | null };
  authority?: { name: string; verified: boolean } | null;
  history: Array<{ status: string; source: string; note?: string }>;
};

export default function MyCivicReports() {
  const reports = useQuery({
    queryKey: ['civic-mine'],
    queryFn: async () => (await api.get<{ items: Report[] }>('/civic/reports/mine')).data.items,
  });
  const notes = useQuery({
    queryKey: ['civic-notes'],
    queryFn: async () => (await api.get<{ items: Array<{ id: number; message: string }> }>('/civic/notifications')).data.items,
  });

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Tracking</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Your public reports</h1>
        <p className="mt-2 text-sm text-slate-400">A NEXUS AI reference is not a government complaint number. Government delivery stays “not sent” until an authorized official records a receipt.</p>
      </header>
      <Link to="/report-public-issue" className="text-sm text-cyan-200">Report a Public Issue</Link>
      {(notes.data || []).slice(0, 5).map((item) => <p key={item.id} className="text-sm text-slate-300">{item.message}</p>)}
      {reports.isLoading && <p className="text-sm text-slate-400">Loading reports…</p>}
      <ul className="space-y-3">
        {(reports.data || []).map((report) => (
          <li key={report.reference} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
            <p className="font-semibold text-cyan-100">{report.reference}</p>
            <p className="mt-1 text-white">{report.category}</p>
            <p className="text-slate-400">{report.description}</p>
            <p className="mt-2">Status: {report.status}</p>
            <p>Verified jurisdiction: {report.verified_jurisdiction.status}{report.verified_jurisdiction.gram_panchayat ? ` · ${report.verified_jurisdiction.gram_panchayat}` : ''}</p>
            <p>Authority: {report.authority ? `${report.authority.name} (${report.authority.verified ? 'verified record' : 'unverified record'})` : 'Not routed'}</p>
            <p>Government reference: {report.official_reference || 'None recorded'}</p>
            <p className="text-slate-500">Delivery: {report.government_delivery}</p>
            <ol className="mt-2 space-y-1 text-xs text-slate-400">
              {report.history.map((item, index) => <li key={`${item.status}-${index}`}>{item.source}: {item.status}{item.note ? ` — ${item.note}` : ''}</li>)}
            </ol>
          </li>
        ))}
      </ul>
      {reports.data && reports.data.length === 0 && <p className="text-sm text-slate-400">No public reports yet.</p>}
    </AppLayout>
  );
}
