import { useState, useRef, useEffect } from "react";

interface Props {
  beforeUrl: string;
  afterUrl: string;
  ssimScore?: number;
  edgeReductionPct?: number;
  resolvedProbability?: number;
  label?: string;
}

export default function BeforeAfterViewer({
  beforeUrl,
  afterUrl,
  ssimScore,
  edgeReductionPct,
  resolvedProbability,
  label,
}: Props) {
  const [slider, setSlider] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const updateSlider = (clientX: number) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
    setSlider(pct);
  };

  useEffect(() => {
    const onMove = (e: MouseEvent) => { if (dragging.current) updateSlider(e.clientX); };
    const onTouch = (e: TouchEvent) => { if (dragging.current) updateSlider(e.touches[0].clientX); };
    const onUp = () => { dragging.current = false; };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("touchmove", onTouch);
    window.addEventListener("mouseup", onUp);
    window.addEventListener("touchend", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("touchmove", onTouch);
      window.removeEventListener("mouseup", onUp);
      window.removeEventListener("touchend", onUp);
    };
  }, []);

  const verdict = resolvedProbability !== undefined
    ? resolvedProbability >= 0.75 ? "LIKELY FIXED"
    : resolvedProbability >= 0.55 ? "PARTIALLY FIXED"
    : resolvedProbability >= 0.35 ? "NEEDS REVIEW"
    : "NOT FIXED"
    : null;

  const verdictColor = verdict === "LIKELY FIXED" ? "text-green-700"
    : verdict === "PARTIALLY FIXED" ? "text-amber-700"
    : verdict === "NEEDS REVIEW" ? "text-blue-700"
    : "text-red-700";

  return (
    <div className="space-y-3">
      <div
        ref={containerRef}
        className="relative overflow-hidden rounded-xl border border-gray-200 cursor-col-resize select-none"
        style={{ aspectRatio: "4/3", touchAction: "none" }}
        onMouseDown={(e) => { dragging.current = true; updateSlider(e.clientX); }}
        onTouchStart={(e) => { dragging.current = true; updateSlider(e.touches[0].clientX); }}
      >
        <img src={afterUrl} alt="After repair" className="absolute inset-0 w-full h-full object-cover" draggable={false} />
        <div className="absolute inset-0 overflow-hidden" style={{ width: `${slider}%` }}>
          <img
            src={beforeUrl}
            alt="Before repair"
            className="absolute inset-0 h-full object-cover"
            style={{ width: containerRef.current ? `${containerRef.current.offsetWidth}px` : "100%", maxWidth: "none" }}
            draggable={false}
          />
        </div>
        <div
          className="absolute top-0 bottom-0 w-1 bg-white shadow pointer-events-none"
          style={{ left: `${slider}%` }}
        >
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white shadow flex items-center justify-center text-gray-600 text-xs font-bold">
            ↔
          </div>
        </div>
        <div className="absolute top-2 left-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded">Before</div>
        <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded">After</div>
      </div>

      {label && <p className="text-sm text-gray-600">{label}</p>}

      {(ssimScore !== undefined || edgeReductionPct !== undefined || resolvedProbability !== undefined) && (
        <div className="flex flex-wrap gap-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-3">
          {ssimScore !== undefined && (
            <span>SSIM: <strong>{ssimScore.toFixed(3)}</strong></span>
          )}
          {edgeReductionPct !== undefined && (
            <span>Edge Reduction: <strong>{edgeReductionPct.toFixed(1)}%</strong></span>
          )}
          {resolvedProbability !== undefined && (
            <span>AI Confidence: <strong>{Math.round(resolvedProbability * 100)}%</strong></span>
          )}
          {verdict && (
            <span className={`ml-auto font-bold ${verdictColor}`}>{verdict}</span>
          )}
        </div>
      )}
    </div>
  );
}
