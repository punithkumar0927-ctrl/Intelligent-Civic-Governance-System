import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../hooks/useAuthStore";
import HowItWorks from "../components/HowItWorks";

const FEATURES = [
  {
    icon: "🔍",
    title: "AI-Powered Detection",
    desc: "Upload a photo and our YOLOv8 model identifies road damage, potholes, garbage, and blocked drains automatically.",
    to: "/report",
  },
  {
    icon: "📊",
    title: "Severity Intelligence",
    desc: "XGBoost severity prediction combines visual features with road context to classify issues from LOW to CRITICAL.",
    to: "/analytics",
  },
  {
    icon: "🗺️",
    title: "Living Map",
    desc: "Real-time geographic view of all reported issues, hotspot clusters, and ward-level resolution rates.",
    to: "/geographic",
  },
  {
    icon: "✅",
    title: "Repair Verification",
    desc: "Before/after image comparison with SSIM and edge analysis — AI predicts if a repair is genuine.",
    to: "/verification",
  },
];

export default function Home() {
  const { token, user } = useAuthStore();
  const isAuthenticated = !!token;
  const [totalReports, setTotalReports] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/analytics/public")
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => setTotalReports(data?.total_reports ?? null))
      .catch(() => setTotalReports(null));
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero */}
      <section className="bg-gradient-to-br from-indigo-900 via-indigo-700 to-blue-600 text-white py-20 px-6">
        <div className="max-w-screen-xl mx-auto">
          <p className="uppercase tracking-widest text-indigo-200 text-sm font-bold mb-3">
            Open-Source Civic AI Platform
          </p>
          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-6">
            The Living<br />Intelligence Map
          </h1>
          <p className="text-xl text-indigo-100 max-w-2xl mb-10 leading-relaxed">
            NEXUS AI understands real-world urban infrastructure problems using
            images, text, and GPS — identifies issues, estimates severity,
            predicts consequences, recommends evidence-based solutions, and tracks resolution.
          </p>
          <div className="flex flex-wrap gap-4">
            {isAuthenticated ? (
              <Link to="/report" className="bg-white text-indigo-800 font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-indigo-50 transition">
                Report an Issue
              </Link>
            ) : (
              <Link to="/register" className="bg-white text-indigo-800 font-bold px-8 py-4 rounded-xl shadow-lg hover:bg-indigo-50 transition">
                Get Started Free
              </Link>
            )}
            <Link to="/login" className="border-2 border-white/40 text-white font-semibold px-8 py-4 rounded-xl hover:bg-white/10 transition">
              Sign In
            </Link>
          </div>
          {user && (
            <p className="mt-6 text-indigo-200 text-sm">
              Signed in as <strong>{user.full_name || user.username}</strong> · {user.role}
            </p>
          )}
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-indigo-800 text-white py-6 px-6">
        <div className="max-w-screen-xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div>
            <p className="text-3xl font-extrabold">{totalReports === null ? "—" : totalReports}</p>
            <p className="text-indigo-200 text-sm">Stored reports</p>
          </div>
          <div>
            <p className="text-3xl font-extrabold">RDD2022</p>
            <p className="text-indigo-200 text-sm">Detection dataset, when supplied</p>
          </div>
          <div>
            <p className="text-3xl font-extrabold">4</p>
            <p className="text-indigo-200 text-sm">Road classes in the detector spec</p>
          </div>
          <div>
            <p className="text-3xl font-extrabold">{isAuthenticated ? "Signed in" : "Public"}</p>
            <p className="text-indigo-200 text-sm">Session</p>
          </div>
        </div>
      </section>

      <HowItWorks signedIn={isAuthenticated} />

      {/* Features */}
      <section className="max-w-screen-xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-4">What NEXUS AI Does</h2>
        <p className="text-gray-500 text-center max-w-xl mx-auto mb-12">
          Four integrated AI capabilities that work together for transparent civic issue management.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {FEATURES.map((f) => (
            <Link
              key={f.title}
              to={isAuthenticated ? f.to : "/login"}
              className="group bg-white border border-gray-200 rounded-2xl p-8 hover:border-indigo-300 hover:shadow-lg transition"
            >
              <span className="text-4xl mb-4 block">{f.icon}</span>
              <h3 className="text-xl font-bold text-gray-900 group-hover:text-indigo-700 mb-3">
                {f.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">{f.desc}</p>
              <span className="inline-block mt-4 text-indigo-600 font-semibold text-sm group-hover:underline">
                Learn more →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Standards */}
      <section className="bg-gray-50 py-16 px-6">
        <div className="max-w-screen-xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Built on Real Standards, Not Hallucinated Facts
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            {[
              ["IRC:73-2018", "Bituminous road maintenance — pothole repair thresholds and methods"],
              ["CPHEEO Manual 2013", "Sewerage and storm-water drainage engineering guidelines"],
              ["SWM Rules 2016", "Solid Waste Management Rules — collection and segregation duties"],
              ["ABC Rules 2023", "Animal Birth Control — stray dog population management"],
              ["CEA Standards", "Central Electricity Authority — street lighting luminance requirements"],
              ["OpenStreetMap", "Free geographic data — road names, landmarks, ward boundaries"],
            ].map(([std, desc]) => (
              <div key={std} className="bg-white border border-gray-200 rounded-xl p-4">
                <p className="font-bold text-indigo-700">{std}</p>
                <p className="text-gray-600 mt-1">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-screen-xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Ready to make your city visible?</h2>
        <p className="text-gray-500 mb-8 max-w-lg mx-auto">
          NEXUS AI is fully open-source. Deploy it for your municipality,
          residents welfare association, or civic group with no vendor lock-in.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <Link to={isAuthenticated ? "/report" : "/register"}
            className="bg-indigo-700 text-white font-bold px-8 py-4 rounded-xl hover:bg-indigo-600 transition">
            {isAuthenticated ? "Report an Issue" : "Create Account"}
          </Link>
          <a href="https://github.com" target="_blank" rel="noreferrer"
            className="border border-gray-300 text-gray-700 font-semibold px-8 py-4 rounded-xl hover:bg-gray-50 transition">
            View on GitHub
          </a>
        </div>
      </section>
    </div>
  );
}
