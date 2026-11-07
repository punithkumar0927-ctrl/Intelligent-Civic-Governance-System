import { useState } from "react";
import { useGeoPoints, useHotspots } from "../hooks/useReports";
import AnalyticsChart from "../components/AnalyticsChart";
import GoogleMapDashboard from "../components/GoogleMapDashboard";
import { useQuery } from "@tanstack/react-query";
import { mapService } from "../services/mapService";

const SEVERITY_OPTIONS = ["", "low", "medium", "high", "critical"];
const CATEGORY_OPTIONS = ["", "road_damage", "pothole", "garbage", "streetlight", "water_leak", "drainage", "sidewalk", "traffic_sign", "park", "building", "power_line", "other"];

export default function GeographicIntelligence() {
  const [city, setCity] = useState("");
  const [severity, setSeverity] = useState("");
  const [category, setCategory] = useState("");
  const [epsKm, setEpsKm] = useState(0.5);

  const { data: points = [], isLoading: loadingPoints } = useGeoPoints({
    city: city || undefined,
    severity: severity || undefined,
    category: category || undefined,
  });

  const { data: hotspots = [], isLoading: loadingHotspots } = useHotspots({ eps_km: epsKm });

  const { data: wards = [] } = useQuery({
    queryKey: ["wards", city],
    queryFn: () => mapService.getWards(city || undefined),
  });

  const sevCounts = countBy(points.map((p) => p.severity));
  const catCounts = countBy(points.map((p) => p.category));

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Geographic Intelligence</h1>
        <p className="text-gray-500 mt-1">
          Search real places on Google Maps. Report statistics below come only from stored NEXUS reports.
        </p>
      </div>

      <GoogleMapDashboard />

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5 flex flex-wrap gap-4">
        <FilterInput label="City" value={city} onChange={setCity} placeholder="Bengaluru" />
        <FilterSelect label="Severity" value={severity} onChange={setSeverity} options={SEVERITY_OPTIONS} />
        <FilterSelect label="Category" value={category} onChange={setCategory} options={CATEGORY_OPTIONS} />
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-1">Cluster Radius (km)</label>
          <input type="range" min={0.2} max={1.5} step={0.1} value={epsKm}
            onChange={(e) => setEpsKm(Number(e.target.value))}
            className="w-28 accent-indigo-600" />
          <span className="ml-2 text-xs text-gray-500">{epsKm.toFixed(1)} km</span>
        </div>
        <div className="ml-auto self-end text-sm text-gray-600">
          {points.length} issues · {hotspots.length} hotspots
        </div>
      </div>

      {/* Hotspot Table */}
      <section className="bg-white border border-gray-200 rounded-2xl p-5">
        <h2 className="font-semibold text-gray-800 mb-4">Detected Hotspots</h2>
        {loadingHotspots ? (
          <p className="text-gray-400 text-sm">Computing clusters...</p>
        ) : hotspots.length === 0 ? (
          <p className="text-gray-400 text-sm">No hotspots found. Adjust cluster radius or add more reports.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <Th>Ward</Th><Th>Issues</Th><Th>Avg Severity</Th>
                  <Th>Top Category</Th><Th>Centroid</Th><Th>Risk</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {hotspots.map((h, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <Td>{h.ward}</Td>
                    <Td className="font-bold">{h.count}</Td>
                    <Td>{h.avg_severity.toFixed(2)}</Td>
                    <Td className="capitalize">{h.top_category}</Td>
                    <Td className="text-xs text-gray-500">{h.lat.toFixed(4)}, {h.lon.toFixed(4)}</Td>
                    <Td>
                      <RiskBar score={h.avg_severity * Math.min(h.count / 10, 1)} />
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Charts row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.keys(sevCounts).length > 0 && (
          <AnalyticsChart
            type="pie"
            title="Issues by Severity"
            data={Object.entries(sevCounts).map(([name, value]) => ({ name, value }))}
          />
        )}
        {Object.keys(catCounts).length > 0 && (
          <AnalyticsChart
            type="pie"
            title="Issues by Category"
            data={Object.entries(catCounts).map(([name, value]) => ({ name, value }))}
          />
        )}
      </div>

      {/* Ward Performance */}
      <section className="bg-white border border-gray-200 rounded-2xl p-5">
        <h2 className="font-semibold text-gray-800 mb-4">Ward Resolution Performance</h2>
        {wards.length === 0 ? (
          <p className="text-gray-400 text-sm">No ward data yet.</p>
        ) : (
          <AnalyticsChart
            type="bar"
            title="Total vs Resolved Issues by Ward"
            data={{
              labels: wards.slice(0, 15).map((w) => w.ward),
              datasets: [
                { label: "Total", data: wards.slice(0, 15).map((w) => w.total_issues), backgroundColor: "#3b82f6" },
                { label: "Resolved", data: wards.slice(0, 15).map((w) => w.resolved), backgroundColor: "#22c55e" },
                { label: "Critical", data: wards.slice(0, 15).map((w) => w.critical_count), backgroundColor: "#ef4444" },
              ],
            }}
          />
        )}
      </section>
    </div>
  );
}

function countBy(arr: string[]): Record<string, number> {
  const c: Record<string, number> = {};
  arr.forEach((v) => { if (v) c[v] = (c[v] || 0) + 1; });
  return c;
}

function FilterInput({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 mb-1">{label}</label>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-36" />
    </div>
  );
}

function FilterSelect({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void; options: string[];
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 mb-1">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm w-36 capitalize">
        <option value="">All</option>
        {options.filter(Boolean).map((o) => (
          <option key={o} value={o} className="capitalize">{o}</option>
        ))}
      </select>
    </div>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">{children}</th>;
}
function Td({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return <td className={`px-3 py-2 ${className}`}>{children}</td>;
}

function RiskBar({ score }: { score: number }) {
  const pct = Math.min(score, 1) * 100;
  const color = pct >= 75 ? "bg-purple-500" : pct >= 55 ? "bg-red-500" : pct >= 35 ? "bg-amber-400" : "bg-green-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-7">{Math.round(pct)}%</span>
    </div>
  );
}
