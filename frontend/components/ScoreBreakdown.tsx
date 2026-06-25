import LinearProgress from "@mui/material/LinearProgress";

interface ScoreBreakdownProps {
  growth: number;
  stability: number;
  size_fit?: number;
  employee_count?: number | null;
  salary_signal?: number;
}

interface Item {
  name: string;
  value: number;
  max: number;
  note?: string;
  helperText?: string;
}

function getCompanySizeMessage(employeeCount: number | null | undefined): string | undefined {
  if (employeeCount == null || employeeCount < 0) {
    return undefined;
  }

  const formattedCount = employeeCount.toLocaleString();

  if (employeeCount < 5) {
    return `최근 총 직원수는 ${formattedCount}명으로, 5인 미만 사업장이에요`;
  }
  if (employeeCount >= 1_000) {
    return `최근 총 직원수는 ${formattedCount}명으로, 대기업 수준이에요`;
  }
  if (employeeCount >= 300) {
    return `최근 총 직원수는 ${formattedCount}명으로, 중견 기업 수준이에요`;
  }
  return `최근 총 직원수는 ${formattedCount}명으로, 중소 기업 수준이에요`;
}

function Bar({ item }: { item: Item }) {
  const pct = item.max > 0 ? Math.max(0, Math.min(100, (item.value / item.max) * 100)) : 0;
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
      {item.helperText && (
        <p className="mt-2 text-xs text-[#94a3b8]">
          {item.helperText}
        </p>
      )}
    </div>
  );
}

export default function ScoreBreakdown({
  growth,
  stability,
  size_fit,
  employee_count,
  salary_signal,
}: ScoreBreakdownProps) {
  const items: Item[] = [
    { name: "성장성", value: growth, max: 40 },
    { name: "안정성", value: stability, max: 35 },
  ];

  if (size_fit !== undefined) {
    items.push({
      name: "기업 규모",
      value: size_fit,
      max: 25,
      note: "(직원 수 기준)",
      helperText: getCompanySizeMessage(employee_count),
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
