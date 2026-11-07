import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AppLayout from '../layouts/AppLayout';
import { useAuthStore } from '../hooks/useAuthStore';
import api from '../services/api';

export default function Admin() {
  const role = useAuthStore((state) => state.user?.role);
  const allowed = role === 'admin' || role === 'officer';
  const [statusNote, setStatusNote] = useState('');
  const [error, setError] = useState('');
  const [videoNote, setVideoNote] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [posterFile, setPosterFile] = useState<File | null>(null);
  const [captionFile, setCaptionFile] = useState<File | null>(null);

  const reports = useQuery({
    queryKey: ['admin-reports'],
    queryFn: async () => (await api.get('/admin/reports')).data,
    enabled: allowed,
  });
  const logs = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => (await api.get('/admin/audit-logs')).data,
    enabled: role === 'admin',
  });

  const setStatus = async (id: number, status: string) => {
    setError('');
    try {
      await api.patch(`/admin/reports/${id}/status`, { status, note: statusNote || undefined });
      reports.refetch();
    } catch {
      setError('Status was not updated. Officer or admin access is required.');
    }
  };

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Administration</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Review queue</h1>
      </header>
      {!allowed && <p className="text-sm text-rose-300">This area is limited to officers and administrators.</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}
      {allowed && (
        <>
          <input value={statusNote} onChange={(event) => setStatusNote(event.target.value)} placeholder="Review note" className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
          <ul className="space-y-3">
            {(reports.data ?? []).map((issue: { id: number; title: string; status: string }) => (
              <li key={issue.id} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="font-medium">{issue.title}</p>
                <p className="mt-1 text-xs text-slate-400">Current status: {issue.status}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {['under_review', 'in_progress', 'resolved', 'rejected'].map((status) => (
                    <button key={status} onClick={() => setStatus(issue.id, status)} className="rounded-lg border border-slate-700 px-2 py-1 text-xs">
                      {status}
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
      {role === 'admin' && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <h2 className="font-medium text-white">Homepage demo video</h2>
          <p className="mt-1 text-sm text-slate-400">Upload the recorded MP4. Until then, the homepage plays the presentation slides stored in the project.</p>
          <label className="mt-3 block text-xs text-slate-400">MP4
            <input type="file" accept="video/mp4" className="mt-1 block w-full text-sm" onChange={(event) => setVideoFile(event.target.files?.[0] || null)} />
          </label>
          <label className="mt-3 block text-xs text-slate-400">Poster image
            <input type="file" accept="image/jpeg,image/png,image/webp" className="mt-1 block w-full text-sm" onChange={(event) => setPosterFile(event.target.files?.[0] || null)} />
          </label>
          <label className="mt-3 block text-xs text-slate-400">English captions (WebVTT)
            <input type="file" accept=".vtt,text/vtt" className="mt-1 block w-full text-sm" onChange={(event) => setCaptionFile(event.target.files?.[0] || null)} />
          </label>
          <button type="button" className="mt-3 rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950" onClick={async () => {
            if (!videoFile) {
              setVideoNote('Choose an MP4 first.');
              return;
            }
            const form = new FormData();
            form.append('video', videoFile);
            if (posterFile) form.append('poster', posterFile);
            if (captionFile) form.append('captions', captionFile);
            try {
              await api.post('/demo-video', form, { headers: { 'Content-Type': 'multipart/form-data' } });
              setVideoNote('Demo video uploaded. Reload the homepage to play it.');
            } catch {
              setVideoNote('The video was not uploaded. Admin access and an MP4 file are required.');
            }
          }}>Upload demo video</button>
          {videoNote && <p className="mt-2 text-sm text-slate-300">{videoNote}</p>}
        </section>
      )}
      {role === 'admin' && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
          <h2 className="font-medium text-white">Verified jurisdiction boundary</h2>
          <p className="mt-1 text-slate-400">Paste a GeoJSON polygon from a boundary dataset you trust. The name is stored only as supplied here. No Gram Panchayat list is built in.</p>
          <BoundaryForm />
        </section>
      )}
      {role === 'admin' && (
        <section>
          <h2 className="mb-2 font-medium">Audit log</h2>
          <ul className="space-y-2 text-xs text-slate-400">
            {(logs.data?.items ?? []).map((row: { id: number; action: string; detail?: string; created_at?: string }) => (
              <li key={row.id}>{row.created_at} · {row.action} · {row.detail || ''}</li>
            ))}
          </ul>
        </section>
      )}
    </AppLayout>
  );
}

function BoundaryForm() {
  const [name, setName] = useState('');
  const [level, setLevel] = useState('gram_panchayat');
  const [source, setSource] = useState('');
  const [geometry, setGeometry] = useState('');
  const [message, setMessage] = useState('');
  return (
    <form className="mt-3 space-y-2" onSubmit={async (event) => {
      event.preventDefault();
      try {
        await api.post('/civic/boundaries', { level, name, source, geometry: JSON.parse(geometry), verified: true });
        setMessage('Boundary stored and marked verified.');
      } catch {
        setMessage('The boundary was not stored. Check the GeoJSON polygon, name, and source.');
      }
    }}>
      <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Name from the dataset" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" />
      <input value={source} onChange={(event) => setSource(event.target.value)} placeholder="Dataset source" className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" />
      <select value={level} onChange={(event) => setLevel(event.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2">
        {['state', 'district', 'taluk', 'village', 'gram_panchayat', 'ulb'].map((item) => <option key={item}>{item}</option>)}
      </select>
      <textarea value={geometry} onChange={(event) => setGeometry(event.target.value)} placeholder='{"type":"Polygon","coordinates":[...]}' className="h-28 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" />
      <button className="rounded-xl bg-cyan-300 px-3 py-2 font-semibold text-slate-950">Store boundary</button>
      {message && <p>{message}</p>}
    </form>
  );
}
