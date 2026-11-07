interface GoogleMapsNamespace {
  maps: {
    importLibrary: (name: string) => Promise<Record<string, new (...args: any[]) => any>>;
    Map?: new (el: HTMLElement, opts: object) => GoogleMap;
    Marker?: new (opts: object) => GoogleMarker;
    InfoWindow?: new (opts?: object) => { setContent: (html: string) => void; open: (opts: object) => void };
    Geocoder?: new () => { geocode: (req: object) => Promise<{ results: Array<{ formatted_address: string; place_id?: string; geometry: { location: { lat: () => number; lng: () => number } } }> }> };
    Polyline?: new (opts: object) => { setMap: (map: GoogleMap | null) => void };
    LatLngBounds?: new () => { extend: (pos: { lat: number; lng: number }) => void };
  };
}
interface GoogleMap {
  setCenter: (pos: { lat: number; lng: number }) => void;
  setZoom: (zoom: number) => void;
  panTo: (pos: { lat: number; lng: number }) => void;
  setMapTypeId: (id: string) => void;
  fitBounds: (bounds: { extend: (pos: { lat: number; lng: number }) => void }) => void;
  addListener: (event: string, handler: (event: { latLng?: { lat: () => number; lng: () => number } }) => void) => void;
}
interface GoogleMarker {
  setMap: (map: GoogleMap | null) => void;
  addListener: (event: string, handler: () => void) => void;
  getPosition: () => { lat: () => number; lng: () => number } | null;
}
declare global {
  interface Window {
    google?: GoogleMapsNamespace;
  }
}

const KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined;

export function googleMapsKey(): string {
  return (KEY || '').trim();
}

let loading: Promise<void> | null = null;

export function loadGoogleMaps(): Promise<void> {
  const key = googleMapsKey();
  if (!key) {
    return Promise.reject(new Error('VITE_GOOGLE_MAPS_API_KEY is not set.'));
  }
  if (window.google?.maps?.importLibrary) return Promise.resolve();
  if (loading) return loading;
  loading = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly&loading=async`;
    script.async = true;
    script.onerror = () => {
      loading = null;
      reject(new Error('Google Maps JavaScript API failed to load. Check the key, billing, and referrer restrictions.'));
    };
    script.onload = () => resolve();
    document.head.appendChild(script);
  });
  return loading;
}

export function decodePolyline(encoded: string): Array<{ lat: number; lng: number }> {
  const points: Array<{ lat: number; lng: number }> = [];
  let index = 0;
  let lat = 0;
  let lng = 0;
  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lat += result & 1 ? ~(result >> 1) : result >> 1;
    shift = 0;
    result = 0;
    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);
    lng += result & 1 ? ~(result >> 1) : result >> 1;
    points.push({ lat: lat / 1e5, lng: lng / 1e5 });
  }
  return points;
}
