import { Github, Linkedin, Mail } from 'lucide-react';

const socialLinks = [
  {
    label: 'GitHub',
    href: 'https://github.com/punithkumar0927-ctrl',
    icon: Github,
    external: true,
  },
  {
    label: 'LinkedIn',
    href: 'https://www.linkedin.com/in/punithkumarab/',
    icon: Linkedin,
    external: true,
  },
  {
    label: 'Email',
    href: 'mailto:punithkumar0927@gmail.com',
    icon: Mail,
    external: false,
  },
];

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-800 bg-[#080d17] text-slate-300">
      <div className="mx-auto grid max-w-screen-xl grid-cols-1 gap-8 px-6 py-10 text-sm md:grid-cols-3">
        <div>
          <h3 className="mb-2 font-bold text-white">NEXUS AI</h3>
          <p className="leading-relaxed text-slate-400">
            The Living Intelligence Map. AI-powered civic issue detection,
            severity prediction, and transparent resolution tracking.
          </p>
        </div>
        <div>
          <h4 className="mb-2 font-semibold text-slate-100">Standards Reference</h4>
          <ul className="space-y-1 text-slate-400">
            <li>IRC:73-2018 – Road Maintenance</li>
            <li>CPHEEO Manual 2013 – Drainage</li>
            <li>SWM Rules 2016 – Waste Management</li>
            <li>ABC Rules 2023 – Stray Animals</li>
          </ul>
        </div>
        <div>
          <h4 className="mb-2 font-semibold text-slate-100">Privacy & Data</h4>
          <ul className="space-y-1 text-slate-400">
            <li>EXIF GPS stripped on upload</li>
            <li>Coordinates rounded for display</li>
            <li>No personal data sold or shared</li>
            <li>Open-source under MIT license</li>
          </ul>
        </div>
      </div>

      <section className="border-t border-slate-800/80 bg-gradient-to-br from-[#0b1220] via-[#10182b] to-[#15102a]">
        <div className="mx-auto flex max-w-screen-xl flex-col gap-6 px-6 py-8 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-300/80">
              About the Developer
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-tight text-white sm:text-2xl">
              Punith Kumar AB
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
              Bachelor of Engineering in Artificial Intelligence and Machine Learning Engineering
            </p>
            <p className="mt-1 text-sm text-slate-500">Davanagere, Karnataka, India</p>
          </div>

          <div className="flex items-center gap-3">
            {socialLinks.map(({ label, href, icon: Icon, external }) => (
              <a
                key={label}
                href={href}
                aria-label={label}
                {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-700/80 bg-slate-900/70 text-slate-300 transition duration-200 hover:-translate-y-0.5 hover:border-cyan-400/40 hover:bg-cyan-400/10 hover:text-cyan-200"
              >
                <Icon size={18} />
              </a>
            ))}
          </div>
        </div>
      </section>

      <div className="border-t border-slate-800 px-6 py-4 text-center text-xs text-slate-500">
        <p>© 2026 Punith Kumar AB. All Rights Reserved.</p>
        <p className="mt-1">Designed & Developed by Punith Kumar AB.</p>
      </div>
    </footer>
  );
}
