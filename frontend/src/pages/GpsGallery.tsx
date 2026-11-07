import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppLayout from '../layouts/AppLayout';
import api, { apiErrorMessage } from '../services/api';
import { googleMapsKey, loadGoogleMaps } from '../services/googleMaps';
import { useRef } from 'react';

type Photo = {
  id: number;
  original_filename: string;
  latitude: number | null;
  longitude: number | null;
  gps_accuracy: number | null;
  location_address: string | null;
  captured_at: string;
  uploaded_at: string | null;
  watermark_enabled: boolean;
  upload_status: string;
};

function AuthImage({ id, alt }: { id: number; alt: string }) {
  const [url, setUrl] = useState('');
  useEffect(() => {
    let active = true;
    let objectUrl = '';
    api.get(`/gps-photos/${id}/file`, { responseType: 'blob' })
      .then((response) => {
        objectUrl = URL.createObjectURL(response.data);
        if (active) setUrl(objectUrl);
      })
      .catch(() => {
        if (active) setUrl('');
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [id]);
  if (!url) return <div className="aspect-square animate-pulse bg-slate-800" />;
  return <img src={url} alt={alt} className="aspect-square w-full object-cover" />;
}

function PhotoMap({ photos, onSelect }: { photos: Photo[]; onSelect: (photo: Photo) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const located = photos.filter((photo) => photo.latitude != null && photo.longitude != null);
  const key = googleMapsKey();
  useEffect(() => {
    if (!key || !ref.current || located.length === 0) return;
    let cancelled = false;
    loadGoogleMaps().then(async () => {
      if (cancelled || !ref.current || !window.google?.maps) return;
      const maps = await window.google.maps.importLibrary('maps') as {
        Map: new (el: HTMLElement, opts: object) => { fitBounds: (bounds: object) => void };
        LatLngBounds: new () => { extend: (pos: object) => void };
        InfoWindow: new () => { setContent: (html: string) => void; open: (opts: object) => void };
      };
      const markerLib = await window.google.maps.importLibrary('marker') as {
        Marker: new (opts: object) => { addListener: (event: string, handler: () => void) => void };
      };
      const bounds = new maps.LatLngBounds();
      const map = new maps.Map(ref.current, { center: { lat: located[0].latitude, lng: located[0].longitude }, zoom: 12, mapTypeControl: true, fullscreenControl: true });
      const info = new maps.InfoWindow();
      located.forEach((photo) => {
        const position = { lat: photo.latitude as number, lng: photo.longitude as number };
        bounds.extend(position);
        const marker = new markerLib.Marker({ map, position, title: photo.location_address || 'GPS photo' });
        marker.addListener('click', () => {
          onSelect(photo);
          info.setContent(`<div style="color:#0f172a;max-width:220px"><strong>GPS photo</strong><br>${photo.location_address || 'Address unavailable'}<br>${position.lat.toFixed(5)}, ${position.lng.toFixed(5)}</div>`);
          info.open({ map, anchor: marker });
        });
      });
      if (located.length > 1) map.fitBounds(bounds);
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [key, located.map((photo) => photo.id).join(','), onSelect]);

  if (!key) {
    return <p className="rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">Google Maps is not loaded, so photo markers are not drawn. Coordinates still appear on each photograph. Set VITE_GOOGLE_MAPS_API_KEY to show them on the map.</p>;
  }
  if (located.length === 0) {
    return <p className="rounded-2xl border border-slate-800 p-4 text-sm text-slate-400">None of the uploaded photographs in this filter have GPS coordinates.</p>;
  }
  return <div ref={ref} className="h-80 w-full rounded-2xl" role="application" aria-label="Map of uploaded GPS photographs" />;
}

export default function GpsGallery() {
  const queryClient = useQueryClient();
  const [date, setDate] = useState('');
  const [location, setLocation] = useState('');
  const [gpsFilter, setGpsFilter] = useState('');
  const [selected, setSelected] = useState<Photo | null>(null);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const photos = useQuery({
    queryKey: ['gps-photos', date, location, gpsFilter],
    queryFn: async () => {
      const response = await api.get<{ items: Photo[] }>('/gps-photos', {
        params: {
          ...(date ? { on: date } : {}),
          ...(location ? { location } : {}),
          ...(gpsFilter === 'yes' ? { has_location: true } : {}),
          ...(gpsFilter === 'no' ? { has_location: false } : {}),
        },
      });
      return response.data.items;
    },
  });

  const download = async (photo: Photo) => {
    const response = await api.get(`/gps-photos/${photo.id}/file`, { responseType: 'blob' });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = photo.original_filename || `nexus-photo-${photo.id}.jpg`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const remove = async (photo: Photo) => {
    if (!window.confirm('Delete this photograph permanently?')) return;
    setError('');
    try {
      await api.delete(`/gps-photos/${photo.id}`);
      if (selected?.id === photo.id) setSelected(null);
      setNotice('Photograph deleted.');
      await queryClient.invalidateQueries({ queryKey: ['gps-photos'] });
    } catch (err) {
      setError(apiErrorMessage(err, 'The photograph could not be deleted.'));
    }
  };

  const items = photos.data ?? [];

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">GPS Photo Gallery</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Your photographs</h1>
        <p className="mt-2 text-sm text-slate-400">Only photographs uploaded to your account are shown. Upload status here means the file was stored.</p>
      </header>
      {notice && <p className="text-sm text-emerald-200" role="status">{notice}</p>}
      {error && <p className="text-sm text-rose-200" role="alert">{error}</p>}
      <div className="grid gap-3 sm:grid-cols-3">
        <label className="text-xs text-slate-400">Date
          <input type="date" value={date} onChange={(event) => setDate(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-sm" />
        </label>
        <label className="text-xs text-slate-400">Location
          <input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Address text" className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-sm" />
        </label>
        <label className="text-xs text-slate-400">GPS
          <select value={gpsFilter} onChange={(event) => setGpsFilter(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-sm">
            <option value="">All uploaded</option>
            <option value="yes">With coordinates</option>
            <option value="no">Location unavailable</option>
          </select>
        </label>
      </div>
      <PhotoMap photos={items} onSelect={setSelected} />
      {photos.isLoading && <p className="text-sm text-slate-400">Loading photographs…</p>}
      {photos.isError && <p className="text-sm text-rose-300">Photographs could not be loaded.</p>}
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((photo) => {
          const taken = new Date(photo.captured_at);
          return (
            <li key={photo.id} className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
              <AuthImage id={photo.id} alt={photo.location_address || photo.original_filename} />
              <div className="space-y-1 p-3 text-sm">
                <p className="font-medium text-white">{photo.location_address || 'Location unavailable'}</p>
                <p className="text-xs text-slate-400">{photo.latitude != null && photo.longitude != null ? `${photo.latitude.toFixed(5)}, ${photo.longitude.toFixed(5)}` : 'No coordinates'}</p>
                <p className="text-xs text-slate-400">{taken.toLocaleDateString()} {taken.toLocaleTimeString()}</p>
                <p className="text-xs text-emerald-300">Upload status: {photo.upload_status}</p>
                <div className="flex flex-wrap gap-2 pt-2">
                  <button type="button" onClick={() => setSelected(photo)} className="rounded-lg border border-slate-700 px-2 py-1 text-xs">View Details</button>
                  <button type="button" onClick={() => download(photo)} className="rounded-lg border border-slate-700 px-2 py-1 text-xs">Download</button>
                  <button type="button" onClick={() => remove(photo)} className="rounded-lg border border-rose-400/40 px-2 py-1 text-xs text-rose-200">Delete</button>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
      {photos.data && items.length === 0 && <p className="text-sm text-slate-400">No photographs match this filter.</p>}
      {selected && (
        <section className="rounded-2xl border border-slate-800 bg-[#0d1422] p-4 text-sm">
          <h2 className="text-lg font-semibold text-white">Photograph details</h2>
          <p className="mt-2">{selected.location_address || 'Address unavailable'}</p>
          <p className="text-slate-400">{selected.latitude != null ? `${selected.latitude}, ${selected.longitude}` : 'Coordinates unavailable'}{selected.gps_accuracy != null ? ` · accuracy ${Math.round(selected.gps_accuracy)} m` : ''}</p>
          <p className="text-slate-400">Captured {new Date(selected.captured_at).toLocaleString()}</p>
          <p className="text-slate-500">{selected.watermark_enabled ? 'A separate website watermark was stored. It is not a certified camera timestamp.' : 'No watermark was stored.'}</p>
          <button type="button" onClick={() => setSelected(null)} className="mt-3 text-xs text-cyan-200">Close</button>
        </section>
      )}
    </AppLayout>
  );
}
