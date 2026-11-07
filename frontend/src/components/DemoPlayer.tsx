import { useEffect, useRef, useState } from 'react';
import { Maximize, Pause, Play, RotateCcw, Volume2, VolumeX } from 'lucide-react';

type DemoMeta = {
  available: boolean;
  url?: string;
  poster?: string | null;
  captions?: string | null;
};

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}:${(whole % 60).toString().padStart(2, '0')}`;
}

const SLIDES = Array.from({ length: 15 }, (_, index) => `/demo/slides/${String(index + 1).padStart(2, '0')}.png`);
const SLIDE_MS = 5000;

function Slideshow() {
  const shellRef = useRef<HTMLDivElement>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setElapsed((value) => {
        const next = value + 100;
        if (next >= SLIDE_MS) {
          setIndex((current) => (current + 1) % SLIDES.length);
          return 0;
        }
        return next;
      });
    }, 100);
    return () => window.clearInterval(timer);
  }, [playing]);

  const progress = ((index * SLIDE_MS + elapsed) / (SLIDES.length * SLIDE_MS)) * 100;

  return (
    <div ref={shellRef} className="overflow-hidden rounded-2xl border border-slate-700/80 bg-black shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
      <div className="relative aspect-video">
        <img src={SLIDES[index]} alt={`NEXUS AI presentation slide ${index + 1} of ${SLIDES.length}`} className="h-full w-full object-contain" />
        <p className="absolute left-3 top-3 rounded-lg bg-black/60 px-2 py-1 text-xs text-white">Slide {index + 1} / {SLIDES.length}</p>
      </div>
      <div className="flex flex-wrap items-center gap-3 bg-[#0c1322] px-3 py-3 text-slate-200 sm:px-4">
        <button type="button" onClick={() => setPlaying((value) => !value)} aria-label={playing ? 'Pause' : 'Play'} className="rounded-lg p-2 hover:bg-white/10">{playing ? <Pause size={18} /> : <Play size={18} />}</button>
        <label className="flex min-w-[140px] flex-1 items-center gap-2 text-xs">
          <span className="sr-only">Progress</span>
          <input type="range" min={0} max={100} step={0.1} value={progress} onChange={(event) => {
            const total = (Number(event.target.value) / 100) * SLIDES.length * SLIDE_MS;
            setIndex(Math.min(SLIDES.length - 1, Math.floor(total / SLIDE_MS)));
            setElapsed(total % SLIDE_MS);
          }} className="w-full accent-cyan-300" />
          <span className="w-16 shrink-0 tabular-nums text-slate-400">{index + 1} / {SLIDES.length}</span>
        </label>
        <button type="button" aria-label="Replay" onClick={() => { setIndex(0); setElapsed(0); setPlaying(true); }} className="rounded-lg p-2 hover:bg-white/10"><RotateCcw size={18} /></button>
        <button type="button" aria-label="Full screen" onClick={() => {
          const shell = shellRef.current;
          if (!shell) return;
          if (document.fullscreenElement) void document.exitFullscreen();
          else void shell.requestFullscreen();
        }} className="rounded-lg p-2 hover:bg-white/10"><Maximize size={18} /></button>
      </div>
      <p className="bg-[#0c1322] px-4 pb-3 text-xs text-slate-400">Playing the uploaded NEXUS AI presentation. An admin MP4 replaces this when one is stored.</p>
    </div>
  );
}

function Player({ src, poster, captions }: { src: string; poster?: string | null; captions?: string | null }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [current, setCurrent] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const toggle = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) await video.play();
    else video.pause();
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onTime = () => {
      setCurrent(video.currentTime);
      setProgress(video.duration ? (video.currentTime / video.duration) * 100 : 0);
    };
    const onMeta = () => {
      setDuration(video.duration);
      setLoading(false);
    };
    const onWaiting = () => setLoading(true);
    const onCanPlay = () => setLoading(false);
    const onError = () => setError('The demo video could not be loaded.');
    video.addEventListener('play', onPlay);
    video.addEventListener('pause', onPause);
    video.addEventListener('timeupdate', onTime);
    video.addEventListener('loadedmetadata', onMeta);
    video.addEventListener('waiting', onWaiting);
    video.addEventListener('canplay', onCanPlay);
    video.addEventListener('error', onError);
    return () => {
      video.removeEventListener('play', onPlay);
      video.removeEventListener('pause', onPause);
      video.removeEventListener('timeupdate', onTime);
      video.removeEventListener('loadedmetadata', onMeta);
      video.removeEventListener('waiting', onWaiting);
      video.removeEventListener('canplay', onCanPlay);
      video.removeEventListener('error', onError);
    };
  }, [src]);

  return (
    <div ref={shellRef} className="overflow-hidden rounded-2xl border border-slate-700/80 bg-black shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
      <div className="relative aspect-video">
        <video ref={videoRef} className="h-full w-full" src={src} poster={poster || undefined} preload="metadata" playsInline controls={false}>
          {captions && <track kind="subtitles" src={captions} srcLang="en" label="English" default />}
        </video>
        {loading && !error && <p className="absolute left-3 top-3 rounded-lg bg-black/60 px-2 py-1 text-xs text-white">Loading video…</p>}
        {error && <p className="absolute inset-0 flex items-center justify-center bg-black/70 px-6 text-center text-sm text-rose-200" role="alert">{error}</p>}
      </div>
      <div className="flex flex-wrap items-center gap-3 bg-[#0c1322] px-3 py-3 text-slate-200 sm:px-4">
        <button type="button" onClick={toggle} aria-label={playing ? 'Pause' : 'Play'} className="rounded-lg p-2 hover:bg-white/10">{playing ? <Pause size={18} /> : <Play size={18} />}</button>
        <label className="flex min-w-[140px] flex-1 items-center gap-2 text-xs">
          <span className="sr-only">Progress</span>
          <input type="range" min={0} max={100} step={0.1} value={progress} onChange={(event) => {
            const video = videoRef.current;
            if (!video?.duration) return;
            video.currentTime = (Number(event.target.value) / 100) * video.duration;
          }} className="w-full accent-cyan-300" />
          <span className="w-20 shrink-0 tabular-nums text-slate-400">{formatTime(current)} / {formatTime(duration)}</span>
        </label>
        <button type="button" aria-label={muted ? 'Unmute' : 'Mute'} onClick={() => {
          const video = videoRef.current;
          if (!video) return;
          video.muted = !video.muted;
          setMuted(video.muted);
        }} className="rounded-lg p-2 hover:bg-white/10">{muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}</button>
        <label className="flex items-center">
          <span className="sr-only">Volume</span>
          <input type="range" min={0} max={1} step={0.05} value={muted ? 0 : volume} onChange={(event) => {
            const video = videoRef.current;
            const next = Number(event.target.value);
            if (!video) return;
            video.volume = next;
            video.muted = next === 0;
            setVolume(next);
            setMuted(next === 0);
          }} className="w-20 accent-cyan-300" />
        </label>
        <label className="text-xs text-slate-400">
          <span className="sr-only">Playback speed</span>
          <select value={speed} onChange={(event) => {
            const next = Number(event.target.value);
            setSpeed(next);
            if (videoRef.current) videoRef.current.playbackRate = next;
          }} className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1">
            {[0.5, 1, 1.25, 1.5, 2].map((rate) => <option key={rate} value={rate}>{rate}x</option>)}
          </select>
        </label>
        <button type="button" aria-label="Replay" onClick={() => {
          const video = videoRef.current;
          if (!video) return;
          video.currentTime = 0;
          void video.play();
        }} className="rounded-lg p-2 hover:bg-white/10"><RotateCcw size={18} /></button>
        <button type="button" aria-label="Full screen" onClick={() => {
          const shell = shellRef.current;
          if (!shell) return;
          if (document.fullscreenElement) document.exitFullscreen();
          else shell.requestFullscreen();
        }} className="rounded-lg p-2 hover:bg-white/10"><Maximize size={18} /></button>
      </div>
    </div>
  );
}

export default function DemoPlayer() {
  const [meta, setMeta] = useState<DemoMeta | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetch('/api/demo-video')
      .then((response) => response.json())
      .then((data: DemoMeta) => setMeta(data))
      .catch(() => setFailed(true));
  }, []);

  if (meta?.available && meta.url) return <Player src={meta.url} poster={meta.poster} captions={meta.captions} />;
  if (!meta && !failed) return <p className="rounded-2xl border border-slate-800 p-6 text-sm text-slate-400">Loading video…</p>;
  return <Slideshow />;
}
