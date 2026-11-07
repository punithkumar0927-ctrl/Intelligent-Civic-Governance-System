import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    fill?: boolean;
  }>;
}

const PIE_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

interface BarChartProps {
  type: "bar";
  title: string;
  data: ChartData;
  height?: number;
}

interface LineChartProps {
  type: "line";
  title: string;
  data: ChartData;
  height?: number;
}

interface PieChartProps {
  type: "pie";
  title: string;
  data: { name: string; value: number }[];
  height?: number;
}

export type AnalyticsChartProps = BarChartProps | LineChartProps | PieChartProps;

export default function AnalyticsChart(props: AnalyticsChartProps) {
  const { title, height = 280 } = props;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>

      {props.type === "bar" && (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={toRows(props.data)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {props.data.datasets.map((ds, i) => (
              <Bar key={ds.label} dataKey={ds.label} fill={Array.isArray(ds.backgroundColor) ? PIE_COLORS[i % PIE_COLORS.length] : (ds.backgroundColor ?? PIE_COLORS[i % PIE_COLORS.length])} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )}

      {props.type === "line" && (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={toRows(props.data)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {props.data.datasets.map((ds) => (
              <Line key={ds.label} type="monotone" dataKey={ds.label}
                stroke={ds.borderColor ?? "#6366f1"} strokeWidth={2}
                fill={typeof ds.backgroundColor === 'string' ? ds.backgroundColor : (ds.backgroundColor?.[0] ?? '#6366f1')} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}

      {props.type === "pie" && (
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie data={props.data} dataKey="value" nameKey="name"
              cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) =>
                `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`
              } labelLine={false} fontSize={11}>
              {props.data.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function toRows(cd: ChartData) {
  return cd.labels.map((label, i) => {
    const row: Record<string, string | number> = { label };
    cd.datasets.forEach((ds) => { row[ds.label] = ds.data[i] ?? 0; });
    return row;
  });
}
