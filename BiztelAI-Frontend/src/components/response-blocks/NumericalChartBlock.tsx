import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  BarChart,
  Bar,
} from "recharts";
import { Activity } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

export interface NumericalChartProps {
  type?: "pressure" | "tolerance" | "custom";
  title?: string;
  unit?: string;
  data?: Array<Record<string, unknown>>;
  threshold?: number;
  thresholdLabel?: string;
}

export const NumericalChartBlock: React.FC<NumericalChartProps> = ({
  type = "pressure",
  title,
  unit = "bar",
  data,
  threshold = 450,
  thresholdLabel = "Safety Limit (450 bar)",
}) => {
  // Preset default data for SOP-305 hydraulic press pressure curve
  const defaultPressureData = [
    { time: "0s", pressure: 0, nominal: 400 },
    { time: "5s", pressure: 120, nominal: 400 },
    { time: "10s", pressure: 280, nominal: 400 },
    { time: "15s", pressure: 395, nominal: 400 },
    { time: "20s", pressure: 410, nominal: 400 },
    { time: "25s", pressure: 420, nominal: 400 },
    { time: "30s", pressure: 415, nominal: 400 },
    { time: "35s", pressure: 400, nominal: 400 },
    { time: "40s", pressure: 0, nominal: 400 },
  ];

  // Preset default data for QC-012 vernier caliper tolerance limits
  const defaultToleranceData = [
    { sample: "#1", deviation: 0.008, lowerLimit: -0.02, upperLimit: 0.02 },
    { sample: "#2", deviation: -0.012, lowerLimit: -0.02, upperLimit: 0.02 },
    { sample: "#3", deviation: 0.015, lowerLimit: -0.02, upperLimit: 0.02 },
    { sample: "#4", deviation: -0.005, lowerLimit: -0.02, upperLimit: 0.02 },
    { sample: "#5", deviation: 0.019, lowerLimit: -0.02, upperLimit: 0.02 },
  ];

  const chartData = data && data.length > 0 ? data : type === "tolerance" ? defaultToleranceData : defaultPressureData;

  return (
    <Card className="my-4 border-border/80 bg-card overflow-hidden">
      <CardHeader className="py-2.5 px-4 bg-muted/40 border-b border-border/60 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-amber-500 shrink-0" />
          <CardTitle className="text-xs uppercase tracking-wider font-mono font-semibold">
            {title || (type === "tolerance" ? "Tolerance Deviation Bands (mm)" : "Operating Pressure Cycle vs Limits (bar)")}
          </CardTitle>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
          TELEMETRY SPEC
        </span>
      </CardHeader>

      <CardContent className="p-4 pt-4">
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {type === "tolerance" ? (
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="sample" tick={{ fill: "#a1a1aa", fontSize: 10, fontFamily: "monospace" }} />
                <YAxis tick={{ fill: "#a1a1aa", fontSize: 10, fontFamily: "monospace" }} domain={[-0.03, 0.03]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    borderColor: "#3f3f46",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontFamily: "monospace",
                    color: "#f4f4f5",
                  }}
                />
                <ReferenceLine y={0.02} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "+0.02mm Upper", fill: "#f59e0b", fontSize: 10 }} />
                <ReferenceLine y={-0.02} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: "-0.02mm Lower", fill: "#f59e0b", fontSize: 10 }} />
                <Bar dataKey="deviation" fill="#f59e0b" radius={[2, 2, 0, 0]} />
              </BarChart>
            ) : (
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="time" tick={{ fill: "#a1a1aa", fontSize: 10, fontFamily: "monospace" }} />
                <YAxis tick={{ fill: "#a1a1aa", fontSize: 10, fontFamily: "monospace" }} domain={[0, 550]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    borderColor: "#3f3f46",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontFamily: "monospace",
                    color: "#f4f4f5",
                  }}
                  formatter={(value: unknown) => [`${value} ${unit}`, "Measured"]}
                />
                <ReferenceLine
                  y={threshold}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  label={{ value: thresholdLabel, fill: "#ef4444", fontSize: 10, position: "top" }}
                />
                <ReferenceLine
                  y={400}
                  stroke="#f59e0b"
                  strokeDasharray="2 2"
                  label={{ value: "Nominal (400 bar)", fill: "#f59e0b", fontSize: 10, position: "insideBottomRight" }}
                />
                <Line
                  type="monotone"
                  dataKey="pressure"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ r: 2, fill: "#f59e0b" }}
                  activeDot={{ r: 4, fill: "#fcd34d" }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>

        <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-2 font-mono pt-2 border-t border-border/40">
          <span>Tolerance: ±{type === "tolerance" ? "0.02 mm" : "15 bar"}</span>
          <span>Standard: Grounded in verified manual</span>
        </div>
      </CardContent>
    </Card>
  );
};

