import LinearProgress from "@mui/material/LinearProgress";

interface ScoreBreakdownProps {
  growth: number;
  stability: number;
  hiring_activity: number;
  size_fit?: number;
  salary_signal?: number;
}

interface Item {
  name: string;
  value: number;
  max: number;
  note?: string;
}

function Bar({ item }: { item: Item }) {
  const pct = item.max > 0 ? Math.max(0, Math.min(100, (item.value / item.max) * 100)) : 0;
  const showLowHiringNote = item.name === "채용 활동성" && item.value <= 5;
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between text-sm">
        <span className="font-medium text-[#0f172a]">
          {item.name}
          {item.note && (
            <span className="ml-1 text-xs font-normal text-[#94a3b8]">
              {item.note}
            </span>
          )}
        </span>
        <span className="tabular-nums text-[#64748b]">
          {Math.round(item.value)}
          <span className="text-[#94a3b8]"> / {item.max}</span>
        </span>
      </div>
      <LinearProgress
        variant="determinate"
        value={pct}
        sx={{
          height: 8,
          borderRadius: 9999,
          backgroundColor: "#e2e8f0",
          "& .MuiLinearProgress-bar": {
            borderRadius: 9999,
            transition: "transform 0.7s ease-out",
          },
        }}
      />
      {showLowHiringNote && (
        <p className="mt-2 text-xs text-[#94a3b8]">
          최근에 채용을 하고 있지 않는 기업이에요
        </p>
      )}
    </div>
  );
}

export default function ScoreBreakdown({
  growth,
  stability,
  hiring_activity,
  size_fit,
  salary_signal,
}: ScoreBreakdownProps) {
  const items: Item[] = [
    { name: "성장성", value: growth, max: 35 },
    { name: "안정성", value: stability, max: 30 },
    { name: "채용 활동성", value: hiring_activity, max: 15 },
  ];

  if (size_fit !== undefined) {
    items.push({
      name: "기업 규모",
      value: size_fit,
      max: 10,
      note: "(직원 수와 규모 변화 흐름 기준)",
    });
  }
  if (salary_signal !== undefined) {
    items.push({
      name: "연봉 추정 신호",
      value: salary_signal,
      max: 10,
      note: "(직무·연차 평균 비교 아님, 국민연금 기반 참고값)",
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {items.map((item) => (
        <Bar key={item.name} item={item} />
      ))}
    </div>
  );
}
