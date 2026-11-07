import { FormEvent, useEffect, useRef, useState } from 'react';
import { Crosshair, MapPinned, Trash2 } from 'lucide-react';
import { useGeoPoints } from '../hooks/useReports';
import { decodePolyline, googleMapsKey, loadGoogleMaps } from '../services/googleMaps';
import { placesService, SavedPlace } from '../services/placesService';
import api from '../services/api';

type MapType = 'roadmap' | 'satellite' | 'terrain' | 'hybrid';
type Point = { id: string; name: string; address: string; lat: number; lng: number; category: string; source: string; placeId?: string };
type Pin = { setMap: (map: null) => void; addListener: (event: string, handler: () => void) => void };
type MapHandle = {
  setCenter: (pos: { lat: number; lng: number }) => void;
  setZoom: (zoom: number) => void;
  panTo: (pos: { lat: number; lng: number }) => void;
  setMapTypeId: (id: string) => void;
  addListener: (event: string, handler: (event: { latLng?: { lat: () => number; lng: () => number } }) => void) => void;
};
type PlaceResult = {
  fetchFields: (opts: object) => Promise<void>;
  displayName?: string;
  formattedAddress?: string;
  id?: string;
  location?: { lat: () => number; lng: () => number };
};

const CATEGORIES = ['saved', 'pothole', 'road_damage', 'landmark', 'imported'];
const COLORS: Record<string, string> = {
  pothole: '#f97316',
  road_damage: '#ef4444',
  garbage: '#84cc16',
  water_leak: '#38bdf8',
  saved: '#22d3ee',
  gps: '#c4b5fd',
  imported: '#facc15',
  landmark: '#fb7185',
  report: '#94a3b8',
};

const RECENT_KEY = 'nexus_recent_searches';

function readRecent(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]') as string[];
  } catch {
    return [];
  }
}

export default function GoogleMapDashboard() {
  const key = googleMapsKey();
  const mapRef = useRef<HTMLDivElement>(null);
  const searchHost = useRef<HTMLDivElement>(null);
  const mapObj = useRef<MapHandle | null>(null);
  const markers = useRef<Array<{ id: string; marker: { setMap: (map: null) => void } }>>([]);
  const routeLine = useRef<{ setMap: (map: null) => void } | null>(null);
  const markerLib = useRef<{
    Marker: (new (opts: object) => Pin) | null;
    info: { setContent: (html: string) => void; open: (opts: object) => void } | null;
  }>({ Marker: null, info: null });
  const [mapReady, setMapReady] = useState(false);
  const [placesReady, setPlacesReady] = useState(false);
  const [mapError, setMapError] = useState('');
  const [mapType, setMapType] = useState<MapType>('roadmap');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<Point | null>(null);
  const [custom, setCustom] = useState<Point[]>([]);
  const [saved, setSaved] = useState<SavedPlace[]>([]);
  const [photoPoints, setPhotoPoints] = useState<Point[]>([]);
  const [imported, setImported] = useState<Point[]>([]);
  const [gps, setGps] = useState<Point | null>(null);
  const [gpsMessage, setGpsMessage] = useState('');
  const [category, setCategory] = useState('');
  const [showReports, setShowReports] = useState(true);
  const [cluster, setCluster] = useState(true);
  const [originId, setOriginId] = useState('');
  const [destinationId, setDestinationId] = useState('');
  const [travelMode, setTravelMode] = useState('DRIVE');
  const [routeNote, setRouteNote] = useState('');
  const [recent, setRecent] = useState<string[]>(readRecent);
  const [status, setStatus] = useState('');
  const reports = useGeoPoints(showReports ? { category: category || undefined } : undefined);

  useEffect(() => {
    placesService.list().then(setSaved).catch(() => setSaved([]));
    api.get<{ items: Array<{ id: number; latitude: number | null; longitude: number | null; location_address: string | null }> }>('/gps-photos')
      .then((response) => {
        setPhotoPoints(response.data.items.flatMap((photo) => (
          photo.latitude == null || photo.longitude == null ? [] : [{
            id: `photo-${photo.id}`,
            name: 'GPS photo',
            address: photo.location_address || 'Address unavailable',
            lat: photo.latitude,
            lng: photo.longitude,
            category: 'gps',
            source: 'your GPS photo',
          }]
        )));
      })
      .catch(() => setPhotoPoints([]));
  }, []);

  useEffect(() => {
    if (!key || !mapRef.current) return;
    let cancelled = false;
    loadGoogleMaps()
      .then(async () => {
        const maps = window.google?.maps;
        if (!maps || cancelled || !mapRef.current) return;
        const lib = await maps.importLibrary('maps') as {
          Map: new (el: HTMLElement, opts: object) => MapHandle;
          InfoWindow?: new () => { setContent: (html: string) => void; open: (opts: object) => void };
        };
        const importedMarkers = await maps.importLibrary('marker') as { Marker?: new (opts: object) => Pin };
        markerLib.current.Marker = importedMarkers.Marker ?? null;
        if (lib.InfoWindow) markerLib.current.info = new lib.InfoWindow();
        const MapCtor = lib.Map;
        const map = new MapCtor(mapRef.current, {
          center: { lat: 12.9716, lng: 77.5946 },
          zoom: 12,
          mapTypeId: 'roadmap',
          fullscreenControl: true,
          streetViewControl: false,
          mapTypeControl: false,
        });
        mapObj.current = map;
        map.addListener('click', (event) => {
          const latLng = event.latLng;
          if (!latLng) return;
          void focusPoint({
            id: `click-${Date.now()}`,
            name: 'Selected map point',
            address: 'Address lookup uses the Google Geocoding API.',
            lat: latLng.lat(),
            lng: latLng.lng(),
            category: 'saved',
            source: 'map click',
          }, false);
        });
        await attachAutocomplete();
        if (!cancelled) {
          if (!markerLib.current.Marker) setMapError('Google Maps loaded, but the marker library is unavailable.');
          setMapReady(true);
        }
      })
      .catch((error: Error) => {
        if (!cancelled) setMapError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [key]);

  useEffect(() => {
    if (!mapReady) return;
    drawMarkers();
  }, [mapReady, custom, saved, imported, gps, photoPoints, reports.data, showReports, cluster, category]);

  const allPoints = (): Point[] => {
    const reportPoints: Point[] = showReports
      ? (reports.data ?? []).map((point) => ({
          id: `report-${point.id}`,
          name: point.category.replace(/_/g, ' '),
          address: 'Stored NEXUS report. This is not a Google place record.',
          lat: point.lat,
          lng: point.lon,
          category: point.category,
          source: 'nexus report',
        }))
      : [];
    const savedPoints: Point[] = saved.map((place) => ({
      id: `saved-${place.id}`,
      name: place.name,
      address: place.address || '',
      lat: place.latitude,
      lng: place.longitude,
      category: place.category,
      source: 'saved by you',
      placeId: place.google_place_id || undefined,
    }));
    return [...reportPoints, ...savedPoints, ...photoPoints, ...imported, ...custom, ...(gps ? [gps] : [])];
  };

  function pinIcon(color: string) {
    const maps = window.google?.maps as unknown as {
      Size: new (w: number, h: number) => object;
      Point: new (x: number, y: number) => object;
    };
    return {
      url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28"><circle cx="14" cy="14" r="8" fill="${color}" stroke="white" stroke-width="2"/></svg>`)}`,
      scaledSize: new maps.Size(28, 28),
      anchor: new maps.Point(14, 14),
    };
  }

  function clearMarkers() {
    markers.current.forEach((item) => item.marker.setMap(null));
    markers.current = [];
  }

  function addMarker(point: Point) {
    const map = mapObj.current;
    const Marker = markerLib.current.Marker;
    if (!Marker || !map) return;
    const marker = new Marker({
      map,
      position: { lat: point.lat, lng: point.lng },
      title: point.name,
      icon: pinIcon(COLORS[point.category] || COLORS.saved),
    });
    marker.addListener('click', () => {
      setSelected(point);
      markerLib.current.info?.setContent(
        `<div style="color:#0f172a;font:13px sans-serif;max-width:220px"><strong>${escapeHtml(point.name)}</strong><br>${escapeHtml(point.address || 'No address returned')}<br>${point.lat.toFixed(6)}, ${point.lng.toFixed(6)}<br>${escapeHtml(point.source)}</div>`,
      );
      markerLib.current.info?.open({ map, anchor: marker });
    });
    markers.current.push({ id: point.id, marker });
  }

  function drawMarkers() {
    if (!mapObj.current || !window.google?.maps) return;
    clearMarkers();
    const points = allPoints();
    const grouped = cluster && points.length > 25 ? clusterPoints(points) : points;
    grouped.forEach(addMarker);
  }

  async function attachAutocomplete() {
    const host = searchHost.current;
    const maps = window.google?.maps;
    if (!host || !maps) return;
    try {
      const places = await maps.importLibrary('places') as unknown as {
        PlaceAutocompleteElement: new () => HTMLElement;
      };
      const box = new places.PlaceAutocompleteElement();
      box.className = 'w-full';
      host.replaceChildren(box);
      setPlacesReady(true);
      const onPick = async (event: Event & { placePrediction?: { toPlace: () => Promise<PlaceResult> } }) => {
        const prediction = event.placePrediction;
        if (!prediction) return;
        const place = await prediction.toPlace();
        await place.fetchFields({ fields: ['displayName', 'formattedAddress', 'location', 'id'] });
        const location = place.location;
        if (!location) return;
        const name = place.displayName || 'Selected place';
        remember(name);
        await focusPoint({
          id: place.id || `place-${Date.now()}`,
          name,
          address: place.formattedAddress || '',
          lat: location.lat(),
          lng: location.lng(),
          category: 'landmark',
          source: 'Google Places',
          placeId: place.id,
        }, true);
      };
      const listener = box as unknown as { addEventListener: (name: string, handler: (event: Event & { placePrediction?: { toPlace: () => Promise<PlaceResult> } }) => void) => void };
      listener.addEventListener('gmp-select', onPick);
      listener.addEventListener('gmp-placeselect', onPick);
    } catch {
      setStatus('Places Autocomplete did not load. Address search still uses the Geocoding API.');
    }
  }

  async function focusPoint(point: Point, pan: boolean) {
    setSelected(point);
    if (pan && mapObj.current) {
      mapObj.current.panTo({ lat: point.lat, lng: point.lng });
      mapObj.current.setZoom(15);
    }
    if ((point.source === 'Google Places' || point.source === 'Google Geocoding') && point.address) return;
    const maps = window.google?.maps;
    if (!maps) return;
    try {
      const geocoding = await maps.importLibrary('geocoding') as {
        Geocoder: new () => { geocode: (req: object) => Promise<{ results: Array<{ formatted_address: string; place_id?: string }> }> };
      };
      const geocoder = new geocoding.Geocoder();
      const response = await geocoder.geocode({ location: { lat: point.lat, lng: point.lng } });
      const formatted = response.results[0]?.formatted_address;
      if (formatted) setSelected({ ...point, address: formatted, placeId: response.results[0]?.place_id });
    } catch {
      setStatus('Google Geocoding did not return an address for this point.');
    }
  }

  function remember(text: string) {
    const next = [text, ...readRecent().filter((item) => item !== text)].slice(0, 6);
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    setRecent(next);
  }

  async function searchAddress(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    if (!mapReady || !window.google?.maps) {
      setMapError('The Google map is not loaded, so this search cannot be shown.');
      return;
    }
    const geocoding = await window.google.maps.importLibrary('geocoding') as unknown as {
      Geocoder: new () => { geocode: (req: object) => Promise<{ results: Array<{ formatted_address: string; place_id?: string; geometry: { location: { lat: () => number; lng: () => number } } }> }> };
    };
    const geocoder = new geocoding.Geocoder();
    const response = await geocoder.geocode({ address: query });
    const result = response.results[0];
    if (!result) {
      setStatus('Google Geocoding returned no match.');
      return;
    }
    remember(query.trim());
    await focusPoint({
      id: result.place_id || `geo-${Date.now()}`,
      name: query.trim(),
      address: result.formatted_address,
      lat: result.geometry.location.lat(),
      lng: result.geometry.location.lng(),
      category: 'landmark',
      source: 'Google Geocoding',
      placeId: result.place_id,
    }, true);
  }

  function findMe() {
    if (!navigator.geolocation) {
      setGpsMessage('This browser does not provide GPS.');
      return;
    }
    setGpsMessage('Requesting location permission…');
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const point: Point = {
          id: 'gps',
          name: 'Your location',
          address: '',
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          category: 'gps',
          source: 'browser GPS',
        };
        setGps(point);
        setGpsMessage('');
        void focusPoint(point, true);
      },
      (error) => {
        setGps(null);
        setGpsMessage(error.code === error.PERMISSION_DENIED
          ? 'Location permission was denied. No position was assumed.'
          : 'GPS is unavailable. No position was assumed.');
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function saveSelected() {
    if (!selected) return;
    const created = await placesService.create({
      name: selected.name,
      address: selected.address,
      latitude: selected.lat,
      longitude: selected.lng,
      category: selected.category || 'saved',
      google_place_id: selected.placeId,
      source: selected.source,
    });
    setSaved((current) => [created, ...current]);
    setStatus('Saved to your account.');
  }

  async function removeSaved(id: number) {
    await placesService.remove(id);
    setSaved((current) => current.filter((place) => place.id !== id));
  }

  function importFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const points = file.name.endsWith('.json') || text.trim().startsWith('{')
        ? parseGeoJson(text)
        : parseCsv(text);
      setImported(points);
      setStatus(points.length ? `Imported ${points.length} points from the file.` : 'The file had no point locations.');
    };
    reader.readAsText(file);
  }

  async function calculateRoute() {
    const points = allPoints();
    const origin = points.find((point) => point.id === originId);
    const destination = points.find((point) => point.id === destinationId);
    if (!origin || !destination) {
      setRouteNote('Choose a start and destination from the markers on the map.');
      return;
    }
    try {
      const result = await placesService.route(
        { latitude: origin.lat, longitude: origin.lng },
        { latitude: destination.lat, longitude: destination.lng },
        travelMode,
      );
      routeLine.current?.setMap(null);
      if (result.encoded_polyline && window.google?.maps && mapObj.current) {
        const path = decodePolyline(result.encoded_polyline);
        const maps = window.google.maps as unknown as { Polyline: new (opts: object) => { setMap: (map: null) => void } };
        routeLine.current = new maps.Polyline({
          map: mapObj.current,
          path,
          strokeColor: '#67e8f9',
          strokeWeight: 4,
        });
      }
      const km = result.distance_meters != null ? `${(result.distance_meters / 1000).toFixed(2)} km` : 'distance not returned';
      setRouteNote(result.note || `Google Routes: ${km}, duration ${result.duration || 'not returned'}.`);
    } catch (error) {
      const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setRouteNote(detail || 'The route request failed. No distance was estimated.');
    }
  }

  const selectable = allPoints();

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-800 bg-[#080d17] text-slate-100">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <MapPinned size={16} className="text-cyan-300" /> Google Maps
        </div>
        <form onSubmit={searchAddress} className="flex min-w-[220px] flex-1 gap-2">
          <div ref={searchHost} className={`min-w-0 flex-1 ${placesReady ? '' : 'hidden'}`} />
          {!placesReady && (
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search a place or address with Google"
              className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
            />
          )}
          {!placesReady && <button className="rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950">Search</button>}
        </form>
        <button type="button" onClick={findMe} className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-sm">
          <Crosshair size={15} /> Find My Location
        </button>
      </div>

      {!key && (
        <div className="m-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
          Google Maps is not loaded. Set <code>VITE_GOOGLE_MAPS_API_KEY</code> in <code>frontend/.env</code>, enable Maps JavaScript, Places, and Geocoding on that key, and restrict it by HTTP referrer. No map image is being substituted.
        </div>
      )}
      {mapError && <p className="mx-4 mt-3 text-sm text-rose-300">{mapError}</p>}
      {gpsMessage && <p className="mx-4 mt-3 text-sm text-slate-300">{gpsMessage}</p>}

      <div className="grid lg:grid-cols-[240px_minmax(0,1fr)_280px]">
        <aside className="space-y-4 border-slate-800 p-4 lg:border-r">
          <label className="block text-xs text-slate-400">
            Report category
            <select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-sm">
              <option value="">All stored reports</option>
              {['pothole', 'road_damage', 'garbage', 'water_leak', 'drainage', 'sidewalk'].map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={showReports} onChange={(event) => setShowReports(event.target.checked)} /> Show stored reports</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={cluster} onChange={(event) => setCluster(event.target.checked)} /> Cluster many markers</label>
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Saved places</p>
            <ul className="mt-2 space-y-2 text-sm">
              {saved.length === 0 && <li className="text-slate-500">None saved yet.</li>}
              {saved.map((place) => (
                <li key={place.id} className="flex items-start justify-between gap-2">
                  <button type="button" className="text-left text-cyan-200" onClick={() => focusPoint({
                    id: `saved-${place.id}`, name: place.name, address: place.address || '', lat: place.latitude, lng: place.longitude, category: place.category, source: 'saved by you',
                  }, true)}>{place.name}</button>
                  <button type="button" aria-label={`Remove ${place.name}`} onClick={() => removeSaved(place.id)}><Trash2 size={14} /></button>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Recent searches on this device</p>
            <ul className="mt-2 space-y-1 text-sm text-slate-400">{recent.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
          <label className="block text-xs text-slate-400">
            Import CSV or GeoJSON
            <input type="file" accept=".csv,.json,.geojson" className="mt-1 block w-full text-xs" onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) importFile(file);
            }} />
          </label>
        </aside>

        <div className="min-h-[420px] bg-slate-950">
          <div className="flex gap-2 p-3">
            {(['roadmap', 'satellite', 'terrain', 'hybrid'] as MapType[]).map((type) => (
              <button
                key={type}
                type="button"
                disabled={!mapReady}
                onClick={() => {
                  setMapType(type);
                  mapObj.current?.setMapTypeId(type);
                }}
                className={`rounded-lg px-2 py-1 text-xs capitalize ${mapType === type ? 'bg-cyan-300 text-slate-950' : 'border border-slate-700'}`}
              >
                {type}
              </button>
            ))}
          </div>
          {key ? (
            <div ref={mapRef} className="h-[480px] w-full" role="application" aria-label="Google Map" />
          ) : (
            <div className="flex h-[480px] items-center justify-center px-6 text-center text-sm text-amber-100">
              This area stays blank until the Google Maps JavaScript API loads. Roadmap, satellite, terrain, hybrid, and full screen are part of that map, and they stay disabled while the key is missing.
            </div>
          )}
        </div>

        <aside className="space-y-3 border-slate-800 p-4 lg:border-l">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Selected location</p>
          {selected ? (
            <>
              <h3 className="text-lg font-semibold">{selected.name}</h3>
              <p className="text-sm text-slate-300">{selected.address || 'No formatted address returned.'}</p>
              <p className="text-xs text-slate-400">{selected.lat.toFixed(6)}, {selected.lng.toFixed(6)}</p>
              <p className="text-xs text-slate-500">Source: {selected.source}</p>
              <label className="block text-xs text-slate-400">
                Marker category
                <select value={selected.category} onChange={(event) => setSelected({ ...selected, category: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-sm">
                  {CATEGORIES.map((item) => <option key={item}>{item}</option>)}
                </select>
              </label>
              <button type="button" onClick={() => setCustom((current) => [...current, { ...selected, id: `custom-${Date.now()}` }])} className="w-full rounded-xl border border-slate-700 py-2 text-sm">Add marker</button>
              <button type="button" onClick={saveSelected} className="w-full rounded-xl bg-cyan-300 py-2 text-sm font-semibold text-slate-950">Save for my account</button>
            </>
          ) : <p className="text-sm text-slate-400">Search, click the map, or use Find My Location.</p>}
          {custom.length > 0 && (
            <button type="button" onClick={() => setCustom([])} className="text-xs text-rose-300">Remove added markers</button>
          )}
          <div className="border-t border-slate-800 pt-3">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Route</p>
            <select value={originId} onChange={(event) => setOriginId(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-xs">
              <option value="">Start</option>
              {selectable.map((point) => <option key={point.id} value={point.id}>{point.name}</option>)}
            </select>
            <select value={destinationId} onChange={(event) => setDestinationId(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-xs">
              <option value="">Destination</option>
              {selectable.map((point) => <option key={point.id} value={point.id}>{point.name}</option>)}
            </select>
            <select value={travelMode} onChange={(event) => setTravelMode(event.target.value)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-2 text-xs">
              {['DRIVE', 'WALK', 'BICYCLE', 'TRANSIT', 'TWO_WHEELER'].map((mode) => <option key={mode}>{mode}</option>)}
            </select>
            <button type="button" onClick={calculateRoute} className="mt-2 w-full rounded-xl border border-slate-700 py-2 text-sm">Calculate route</button>
            {routeNote && <p className="mt-2 text-xs text-slate-300">{routeNote}</p>}
          </div>
        </aside>
      </div>

      <div className="grid gap-3 border-t border-slate-800 px-4 py-4 text-xs text-slate-400 sm:grid-cols-3">
        <p>Stored NEXUS reports on this filter: {showReports ? (reports.data?.length ?? 0) : 0}. These counts come from the application database.</p>
        <p>Saved places: {saved.length}. Imported file points: {imported.length}. Added markers: {custom.length}.</p>
        <p>{status || 'Google place details appear only after Places or Geocoding returns them. Clusters only group markers already on the map.'}</p>
      </div>
    </section>
  );
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char] || char));
}

function clusterPoints(points: Point[]): Point[] {
  const groups = new Map<string, Point[]>();
  points.forEach((point) => {
    const key = `${point.lat.toFixed(2)}:${point.lng.toFixed(2)}`;
    groups.set(key, [...(groups.get(key) || []), point]);
  });
  return [...groups.values()].map((group) => {
    if (group.length === 1) return group[0];
    const lat = group.reduce((sum, point) => sum + point.lat, 0) / group.length;
    const lng = group.reduce((sum, point) => sum + point.lng, 0) / group.length;
    return {
      id: `cluster-${lat}-${lng}`,
      name: `${group.length} markers`,
      address: 'Cluster of markers currently on the map. This is not a Google statistic.',
      lat,
      lng,
      category: 'saved',
      source: 'marker cluster',
    };
  });
}

function parseCsv(text: string): Point[] {
  const lines = text.split(/\r?\n/).filter(Boolean);
  const header = lines[0]?.toLowerCase().split(',').map((item) => item.trim()) || [];
  const latIndex = header.indexOf('latitude');
  const lngIndex = header.findIndex((item) => item === 'longitude' || item === 'lng');
  if (latIndex < 0 || lngIndex < 0) return [];
  return lines.slice(1).map((line, index) => {
    const cells = line.split(',');
    return {
      id: `import-${index}`,
      name: cells[header.indexOf('name')] || `Imported ${index + 1}`,
      address: cells[header.indexOf('address')] || 'Imported from CSV',
      lat: Number(cells[latIndex]),
      lng: Number(cells[lngIndex]),
      category: cells[header.indexOf('category')] || 'imported',
      source: 'imported file',
    };
  }).filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lng));
}

function parseGeoJson(text: string): Point[] {
  const data = JSON.parse(text) as { features?: Array<{ properties?: Record<string, string>; geometry?: { type?: string; coordinates?: number[] } }> };
  return (data.features || []).flatMap((feature, index) => {
    if (feature.geometry?.type !== 'Point' || !feature.geometry.coordinates) return [];
    const [lng, lat] = feature.geometry.coordinates;
    return [{
      id: `import-${index}`,
      name: feature.properties?.name || `Imported ${index + 1}`,
      address: feature.properties?.address || 'Imported from GeoJSON',
      lat: Number(lat),
      lng: Number(lng),
      category: feature.properties?.category || 'imported',
      source: 'imported file',
    }];
  }).filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.lng));
}
