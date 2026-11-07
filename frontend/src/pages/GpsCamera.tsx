import { useEffect, useRef, useState } from 'react';
import AppLayout from '../layouts/AppLayout';
import { apiErrorMessage } from '../services/api';
import api from '../services/api';
import { googleMapsKey, loadGoogleMaps } from '../services/googleMaps';

type Fix = {
  latitude: number;
  longitude: number;
  accuracy: number;
} | null;

type Shot = {
  blob: Blob;
  url: string;
  takenAt: Date;
  fix: Fix;
  address: string;
  locationNote: string;
};

const MAX_BYTES = 20 * 1024 * 1024;

export default function GpsCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [facing, setFacing] = useState<'environment' | 'user'>('environment');
  const [live, setLive] = useState(false);
  const [torchOn, setTorchOn] = useState(false);
  const [torchAvailable, setTorchAvailable] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [shot, setShot] = useState<Shot | null>(null);
  const [showStill, setShowStill] = useState(false);
  const [watermark, setWatermark] = useState(false);
  const [attachHere, setAttachHere] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const stop = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setLive(false);
    setTorchOn(false);
    setTorchAvailable(false);
  };

  useEffect(() => () => stop(), []);

  const openCamera = async (mode: 'environment' | 'user') => {
    setCameraError('');
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('This browser cannot open a camera. Use Chrome or Edge on localhost or HTTPS.');
      return;
    }
    stop();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: mode } },
      });
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      video.srcObject = stream;
      await video.play();
      setFacing(mode);
      setLive(true);
      const track = stream.getVideoTracks()[0];
      const caps = track.getCapabilities?.() as { torch?: boolean } | undefined;
      setTorchAvailable(Boolean(caps?.torch));
    } catch (err) {
      const name = (err as { name?: string }).name;
      setCameraError(name === 'NotAllowedError'
        ? 'Camera permission was denied. No preview was started.'
        : 'The camera could not be opened.');
    }
  };

  const toggleTorch = async () => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track) return;
    try {
      await track.applyConstraints({ advanced: [{ torch: !torchOn }] } as unknown as MediaTrackConstraints);
      setTorchOn(!torchOn);
    } catch {
      setTorchAvailable(false);
      setCameraError('Torch is not available on this camera.');
    }
  };

  const locate = () => new Promise<Fix>((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
      }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 },
    );
  });

  const reverseAddress = async (fix: Fix) => {
    if (!fix) return { address: '', note: 'Location unavailable. Permission was denied or GPS returned no position.' };
    const key = googleMapsKey();
    if (!key) return { address: '', note: 'Coordinates were saved. No address was looked up because the Google Maps key is not configured.' };
    try {
      await loadGoogleMaps();
      const geocoding = await window.google!.maps.importLibrary('geocoding') as {
        Geocoder: new () => { geocode: (req: object) => Promise<{ results: Array<{ formatted_address: string }> }> };
      };
      const response = await new geocoding.Geocoder().geocode({ location: { lat: fix.latitude, lng: fix.longitude } });
      const address = response.results[0]?.formatted_address || '';
      return { address, note: address ? 'Address returned by Google Geocoding.' : 'Google Geocoding returned no address.' };
    } catch {
      return { address: '', note: 'Coordinates were saved. Google Geocoding did not return an address.' };
    }
  };

  const capture = async () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) {
      setCameraError('Open the camera before capturing.');
      return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92));
    if (!blob) {
      setCameraError('The photograph could not be captured.');
      return;
    }
    const fix = await locate();
    const looked = await reverseAddress(fix);
    if (shot?.url) URL.revokeObjectURL(shot.url);
    setShot({ blob, url: URL.createObjectURL(blob), takenAt: new Date(), fix, address: looked.address, locationNote: looked.note });
    setShowStill(true);
    setNotice('');
    setError('');
  };

  const onFile = async (file: File) => {
    setError('');
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Choose a JPG, PNG, or WEBP image.');
      return;
    }
    if (file.size > MAX_BYTES) {
      setError('That image is larger than 20MB.');
      return;
    }
    let fix: Fix = null;
    let address = '';
    let locationNote = 'Location unavailable. Current GPS was not applied to a photo chosen from the device.';
    if (attachHere) {
      fix = await locate();
      const looked = await reverseAddress(fix);
      address = looked.address;
      locationNote = fix
        ? `Current device location at selection. ${looked.note} This is not a location read from the file.`
        : 'Location permission was denied, so this existing photo has no coordinates.';
    }
    if (shot?.url) URL.revokeObjectURL(shot.url);
    setShot({
      blob: file,
      url: URL.createObjectURL(file),
      takenAt: new Date(file.lastModified),
      fix,
      address,
      locationNote,
    });
    setShowStill(true);
  };

  const retake = () => {
    if (shot?.url) URL.revokeObjectURL(shot.url);
    setShot(null);
    setShowStill(false);
  };

  const buildWatermark = async (source: Blob, lines: string[]) => {
    const bitmap = await createImageBitmap(source);
    const canvas = document.createElement('canvas');
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return source;
    ctx.drawImage(bitmap, 0, 0);
    const size = Math.max(18, Math.round(bitmap.width * 0.028));
    ctx.font = `${size}px sans-serif`;
    const width = Math.min(bitmap.width - size * 2, Math.max(...lines.map((line) => ctx.measureText(line).width)) + size * 2);
    const block = size * 1.4 * lines.length + size;
    const top = bitmap.height - block - size;
    ctx.fillStyle = 'rgba(8, 13, 23, 0.75)';
    ctx.fillRect(size, top, width, block);
    ctx.fillStyle = '#f8fafc';
    lines.forEach((line, index) => ctx.fillText(line, size * 1.5, top + size * 1.3 + index * size * 1.4));
    const marked = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92));
    return marked || source;
  };

  const upload = async () => {
    if (!shot) return;
    setError('');
    setNotice('');
    const lines = [
      'NEXUS AI website watermark',
      'Not a certified camera timestamp',
      shot.address || 'Location unavailable',
      shot.fix ? `${shot.fix.latitude.toFixed(6)}, ${shot.fix.longitude.toFixed(6)}` : 'No coordinates',
      shot.takenAt.toLocaleString(),
      shot.fix ? `Accuracy ${Math.round(shot.fix.accuracy)} m` : 'Accuracy unavailable',
    ];
    const marked = watermark ? await buildWatermark(shot.blob, lines) : null;
    const form = new FormData();
    form.append('image', shot.blob, 'capture.jpg');
    form.append('captured_at', shot.takenAt.toISOString());
    form.append('watermark_enabled', watermark ? 'true' : 'false');
    if (shot.fix) {
      form.append('latitude', String(shot.fix.latitude));
      form.append('longitude', String(shot.fix.longitude));
      form.append('gps_accuracy', String(shot.fix.accuracy));
    }
    if (shot.address) form.append('location_address', shot.address);
    if (marked) form.append('watermark', marked, 'watermark.jpg');
    setProgress(0);
    try {
      await api.post('/gps-photos', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total) setProgress(Math.round((event.loaded / event.total) * 100));
        },
      });
      setNotice('Photograph uploaded.');
      setProgress(100);
    } catch (err) {
      setError(apiErrorMessage(err, 'The photograph was not uploaded.'));
      setProgress(null);
    }
  };

  return (
    <AppLayout>
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">GPS Camera</p>
        <h1 className="mt-1 text-2xl font-semibold text-white">Capture a photograph</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          The camera starts only after you press Open Camera, and nothing is uploaded until you press Upload Photo.
          Location is requested when a photo is captured. If you deny it, the photo can still be kept and the location is marked unavailable.
          A watermark is drawn by this website. It is not a certified camera timestamp or proof of authenticity.
        </p>
      </header>

      {cameraError && <p className="rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-sm text-amber-100" role="alert">{cameraError}</p>}
      {error && <p className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-200" role="alert">{error}</p>}
      {notice && <p className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-3 py-2 text-sm text-emerald-200" role="status">{notice}</p>}

      <div className="overflow-hidden rounded-3xl border border-slate-800 bg-black">
        <div className="relative aspect-[3/4] bg-slate-950 sm:aspect-video">
          <video ref={videoRef} className={`h-full w-full object-cover ${showStill ? 'hidden' : ''}`} playsInline autoPlay muted />
          {shot && showStill && <img src={shot.url} alt="Captured photograph preview" className="h-full w-full object-contain" />}
          {!live && !showStill && (
            <div className="absolute inset-0 flex items-center justify-center px-6 text-center text-sm text-slate-400">
              No camera preview yet. Open the camera to use this device.
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 bg-[#0c1322] p-3">
          <button type="button" onClick={() => openCamera(facing)} className="rounded-xl bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950">Open Camera</button>
          <button type="button" onClick={() => openCamera(facing === 'environment' ? 'user' : 'environment')} className="rounded-xl border border-slate-700 px-3 py-2 text-sm">
            {facing === 'environment' ? 'Front camera' : 'Rear camera'}
          </button>
          <button type="button" onClick={capture} disabled={!live} className="h-14 w-14 rounded-full border-4 border-white bg-rose-500 disabled:opacity-40" aria-label="Capture Photo" />
          <button type="button" onClick={retake} disabled={!shot} className="rounded-xl border border-slate-700 px-3 py-2 text-sm disabled:opacity-40">Retake Photo</button>
          <button type="button" onClick={() => setShowStill((value) => !value)} disabled={!shot} className="rounded-xl border border-slate-700 px-3 py-2 text-sm disabled:opacity-40">
            {showStill ? 'Live preview' : 'Preview Captured Image'}
          </button>
          <button type="button" onClick={toggleTorch} disabled={!torchAvailable} className="rounded-xl border border-slate-700 px-3 py-2 text-sm disabled:opacity-40">
            {torchOn ? 'Torch off' : 'Torch'}
          </button>
        </div>
      </div>

      <label className="block text-sm text-slate-300">
        Upload an existing JPG, PNG, or WEBP
        <input type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" className="mt-2 block w-full text-sm" onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void onFile(file);
        }} />
      </label>
      <label className="flex items-start gap-2 text-sm text-slate-300">
        <input type="checkbox" checked={attachHere} onChange={(event) => setAttachHere(event.target.checked)} className="mt-1" />
        For a photo chosen from this device, attach my current GPS position. This is the position now, not a location stored inside the file.
      </label>
      <label className="flex items-start gap-2 text-sm text-slate-300">
        <input type="checkbox" checked={watermark} onChange={(event) => setWatermark(event.target.checked)} className="mt-1" />
        Save a separate watermarked copy. The original file stays unchanged.
      </label>

      {shot && (
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
          <h2 className="font-semibold text-white">Location for this photograph</h2>
          <dl className="mt-3 grid gap-2 sm:grid-cols-2">
            <div><dt className="text-slate-500">Latitude</dt><dd>{shot.fix ? shot.fix.latitude.toFixed(6) : 'Unavailable'}</dd></div>
            <div><dt className="text-slate-500">Longitude</dt><dd>{shot.fix ? shot.fix.longitude.toFixed(6) : 'Unavailable'}</dd></div>
            <div><dt className="text-slate-500">Accuracy</dt><dd>{shot.fix ? `${Math.round(shot.fix.accuracy)} m` : 'Unavailable'}</dd></div>
            <div><dt className="text-slate-500">Address</dt><dd>{shot.address || 'Unavailable'}</dd></div>
            <div><dt className="text-slate-500">Date</dt><dd>{shot.takenAt.toLocaleDateString()}</dd></div>
            <div><dt className="text-slate-500">Time</dt><dd>{shot.takenAt.toLocaleTimeString()}</dd></div>
          </dl>
          <p className="mt-3 text-xs text-slate-400">{shot.locationNote}</p>
          <button type="button" onClick={upload} className="mt-4 rounded-xl bg-cyan-300 px-4 py-2 font-semibold text-slate-950">Upload Photo</button>
          {progress !== null && (
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} role="progressbar">
              <div className="h-full bg-cyan-300" style={{ width: `${progress}%` }} />
            </div>
          )}
        </section>
      )}
    </AppLayout>
  );
}
