import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Camera, LayoutDashboard, LogIn, Map, MapPinned, FileText,
} from 'lucide-react';
import DemoPlayer from './DemoPlayer';

const STEPS = [
  {
    title: 'Register and Login',
    text: 'Create an account, confirm the verification message when email is not configured, then sign in to open your workspace.',
    icon: LogIn,
  },
  {
    title: 'Open Your Dashboard',
    text: 'The dashboard shows counts and recent reports that are stored for your account. It does not invent detections.',
    icon: LayoutDashboard,
  },
  {
    title: 'Capture or Upload Photos',
    text: 'Open GPS Camera, allow the device camera, and capture a photo or choose a JPG, PNG, or WEBP file. Upload starts only when you press Upload Photo.',
    icon: Camera,
  },
  {
    title: 'Collect GPS Location',
    text: 'If you allow location, the capture stores the browser GPS coordinates and accuracy. If you deny it, the photo is kept and the location is marked unavailable.',
    icon: MapPinned,
  },
  {
    title: 'Explore Geographic Intelligence',
    text: 'Geographic intelligence shows stored reports and your GPS photographs. The Google map appears when a Maps key is configured.',
    icon: Map,
  },
  {
    title: 'Generate and Review Reports',
    text: 'Submit a road report with a title, photo, and location you consent to share, then open it from the reports list and the AI report page.',
    icon: FileText,
  },
];

export default function HowItWorks({ signedIn }: { signedIn: boolean }) {
  const sectionRef = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setVisible(true);
      },
      { threshold: 0.15 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <section
      ref={sectionRef}
      id="how-it-works"
      aria-labelledby="how-it-works-title"
      className={`bg-[#080d17] px-6 py-20 text-slate-100 transition duration-700 ${visible ? 'opacity-100' : 'translate-y-4 opacity-0'}`}
    >
      <div className="mx-auto max-w-screen-xl">
        <p className="text-center text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-300">
          Product demonstration
        </p>
        <h2 id="how-it-works-title" className="mt-3 text-center text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          See NEXUS AI in Action
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-sm leading-relaxed text-slate-400 sm:text-base">
          Discover how NEXUS AI combines artificial intelligence, real-time image capture, GPS intelligence, and geographic insights in one platform.
        </p>

        <div className="mx-auto mt-10 max-w-4xl">
          <DemoPlayer />
        </div>

        <ol className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            return (
              <li key={step.title} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <div>
                  <span className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 text-cyan-200">
                      <Icon size={18} />
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                  </span>
                  <span className="mt-4 block text-base font-semibold text-white">{step.title}</span>
                  <span className="mt-2 block text-sm leading-relaxed text-slate-400">{step.text}</span>
                </div>
              </li>
            );
          })}
        </ol>

        <div className="mt-14 rounded-3xl border border-slate-800 bg-gradient-to-br from-[#10182b] to-[#17122a] px-6 py-10 text-center">
          <h3 className="text-2xl font-semibold text-white">Ready to Experience It Yourself?</h3>
          <p className="mx-auto mt-3 max-w-xl text-sm text-slate-400">
            Explore the platform and experience its capabilities firsthand.
          </p>
          <Link
            to={signedIn ? '/dashboard' : '/register'}
            className="mt-6 inline-flex items-center rounded-xl bg-cyan-300 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 focus:outline-none focus:ring-2 focus:ring-cyan-100"
          >
            Get Started Now
          </Link>
        </div>
      </div>
    </section>
  );
}
