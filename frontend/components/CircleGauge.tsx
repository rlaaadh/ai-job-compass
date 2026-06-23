import { gradeColor, scoreToGrade } from "@/lib/colors";

interface CircleGaugeProps {
  score: number; // 0-100
  size?: number;
  strokeWidth?: number;
  grade?: string;
  label?: string;
}

export default function CircleGauge({
  score,
  size = 160,
  strokeWidth = 12,
  grade,
  label,
}: CircleGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score));
  const resolvedGrade = grade ?? scoreToGrade(clamped);
  const color = gradeColor(resolvedGrade);

  const radius = size / 2 - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);
  const center = size / 2;

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        {/* 배경 원 */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
        />
        {/* 점수 원 */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: "stroke-dashoffset 0.8s ease, stroke 0.3s ease",
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span
          className="font-bold leading-none"
          style={{ fontSize: size * 0.28, color }}
        >
          {Math.round(clamped)}
        </span>
        <span
          className="mt-1 text-[#64748b]"
          style={{ fontSize: size * 0.09 }}
        >
          {label ?? "점"}
        </span>
      </div>
    </div>
  );
}
