interface ScoreBreakdownProps {
  growth: number; // 0-35
  stability: number; // 0-30
  hiring_activity: number; // 0-15
  size_fit?: number; // 참고
  salary_signal?: number; // 참고값
}

interface Item {
  name: string;
  value: number;
  max: number;
  note?: string;
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
      <div className="h-2 w-full overflow-hidden rounded-full bg-[#e2e8f0]">
        <div
          className="h-full rounded-full bg-[#3b82f6] transition-[width] duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
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
    items.push({ name: "규모 적합도", value: size_fit, max: 20 });
  }
  if (salary_signal !== undefined) {
    items.push({
      name: "연봉 시그널",
      value: salary_signal,
      max: 100,
      note: "(참고값, 실제 급여와 다를 수 있음)",
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
