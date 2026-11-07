import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppLayout from '../layouts/AppLayout';
import api, { apiErrorMessage } from '../services/api';
import { googleMapsKey, loadGoogleMaps } from '../services/googleMaps';
import { useEffect, useRef } from 'react';

type Report = {
  reference: string;
  category: string;
  status: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
  verified_jurisdiction: { status: string; district?: string | null; taluk?: string | null; gram_panchayat?: string | null };
  ai: { status: string; severity?: string | null; confidence?: number | null; risk_note?: string };
};

const TITLES = {
  gp: 'Gram Panchayat desk',
  taluk: 'Taluk Panchayat desk',
  zilla: 'Zilla Panchayat desk',
};

export default function CivicDesk({ level }: { level: keyof typeof TITLES }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  const queue = useQuery({
    queryKey: ['civic-queue', level],
    queryFn: async () => (await api.get<{ items: Report[]; note?: string }>('/civic/queue')).data,
  });
  const items = queue.data?.items || [];
  const located = items.filter((item) => item.latitude != null && item.longitude != null);
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!googleMapsKey() || !mapRef.current || located.length === 0) return;
    let cancelled = false;
    loadGoogleMaps().then(async () => {
      if (cancelled || !mapRef.current || !window.google?.maps) return;
      const maps = await window.google.maps.importLibrary('maps') as { Map: new (el: HTMLElement, opts: object) => object };
      const markerLib = await window.google.maps.importLibrary('marker') as { Marker: new (opts: object) => void };
      const map = new maps.Map(mapRef.current, { center: { lat: located[0].latitude, lng: located[0].longitude }, zoom: 11 });
      located.forEach((item) => new markerLib.Marker({ map, position: { lat: item.latitude, lng: item.longitude }, title: item.reference }));
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [located.map((item) => item.reference).join('|')]);

  const act = async (reference: string, action: string, extra: Record<string, string> = {}) => {
    setError('');
    try {
      await api.post(`/civic/reports/${reference}/actions`, { action, note, ...extra });
      setNote('');
      await queryClient.invalidateQueries({ queryKey: ['civic-queue'] });
    } catch (err) {
      setError(apiErrorMessage(err, 'The action was not saved.'));
    }
  };

  const download = async (format: 'csv' | 'pdf') => {
    const response = await api.get('/civic/export', { params: { file_format: format }, responseType: 'blob' });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = format === 'csv' ? 'nexus-district-reports.csv' : 'nexus-district-reports.pdf';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Authorized desk</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">{TITLES[level]}</h1>
        <p className="mt-2 text-sm text-slate-400">Only reports inside your verified boundary assignment are listed. Empty means no boundary is assigned or no report matched it.</p>
      </header>
      {queue.data?.note && <p className="text-sm text-amber-100">{queue.data.note}</p>}
      {error && <p className="text-sm text-rose-200">{error}</p>}
      <div className="grid gap-3 sm:grid-cols-3">
        <article className="rounded-2xl border border-slate-800 p-4"><p className="text-xs text-slate-500">Visible reports</p><p className="text-2xl text-white">{items.length}</p></article>
        <article className="rounded-2xl border border-slate-800 p-4"><p className="text-xs text-slate-500">Awaiting verification</p><p className="text-2xl text-white">{items.filter((item) => item.verified_jurisdiction.status !== 'verified').length}</p></article>
        <article className="rounded-2xl border border-slate-800 p-4"><p className="text-xs text-slate-500">High model severity</p><p className="text-2xl text-white">{items.filter((item) => item.ai.severity === 'High').length}</p></article>
      </div>
      {googleMapsKey() && located.length > 0 ? <div ref={mapRef} className="h-72 rounded-2xl" /> : <p className="text-sm text-slate-400">Map markers appear when a Google Maps key is configured and a visible report has coordinates.</p>}
      <textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Action note" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.reference} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
            <p className="font-semibold text-white">{item.reference} · {item.status}</p>
            <p>{item.category}</p>
            <p className="text-slate-400">{item.description}</p>
            <p className="text-xs text-slate-500">Verified GP: {item.verified_jurisdiction.gram_panchayat || 'Pending verification'} · AI {item.ai.status}{item.ai.severity ? ` · ${item.ai.severity}` : ''}</p>
            <p className="text-xs text-slate-500">{item.ai.risk_note}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" onClick={() => act(item.reference, 'confirm_receipt')} className="rounded-lg border border-slate-700 px-2 py-1 text-xs">Confirm NEXUS receipt</button>
              <button type="button" onClick={() => act(item.reference, 'status', { status: 'In Progress' })} className="rounded-lg border border-slate-700 px-2 py-1 text-xs">In progress</button>
              <button type="button" onClick={() => act(item.reference, 'status', { status: 'Escalated' })} className="rounded-lg border border-slate-700 px-2 py-1 text-xs">Escalate</button>
              <button type="button" onClick={() => act(item.reference, 'reject')} className="rounded-lg border border-rose-400/40 px-2 py-1 text-xs">Reject with note</button>
            </div>
          </li>
        ))}
      </ul>
      {level === 'zilla' && (
        <div className="flex gap-2">
          <button type="button" onClick={() => download('csv')} className="rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950">Download CSV</button>
          <button type="button" onClick={() => download('pdf')} className="rounded-xl border border-slate-700 px-3 py-2 text-sm">Download PDF</button>
        </div>
      )}
    </AppLayout>
  );
}
