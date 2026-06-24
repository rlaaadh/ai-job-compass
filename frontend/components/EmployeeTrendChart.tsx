"use client";

import type { MonthlyEmployeeStat } from "@/lib/types";

interface EmployeeTrendChartProps {
  stats: MonthlyEmployeeStat[];
}

function formatMonthLabel(value: string): string {
  const normalized = value.replace(/[^0-9]/g, "");
  if (normalized.length >= 6) {
    return `${normalized.slice(2, 4)}.${normalized.slice(4, 6)}`;
  }
  return value;
}

export default function EmployeeTrendChart({
  stats,
}: EmployeeTrendChartProps) {
  if (stats.length === 0) {
    return null;
  }

  const maxCount = Math.max(...stats.map((stat) => stat.employee_count), 1);
  const minCount = Math.min(...stats.map((stat) => stat.employee_count), maxCount);
  const countRange = Math.max(maxCount - minCount, 1);
  const chartHeight = 220;
  const lineHeight = 120;

  const points = stats.map((stat, index) => {
    const x = stats.length === 1 ? 50 : (index / (stats.length - 1)) * 100;
    const normalizedY = (stat.employee_count - minCount) / countRange;
    const y = lineHeight - normalizedY * lineHeight;
    return `${x},${y}`;
  });

  return (
    <div className="rounded-xl border border-[#e2e8f0] bg-white p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-semibold text-[#0f172a]">
            최근 직원 수 변화 추이
          </h3>
          <p className="text-sm text-[#64748b]">
            국민연금 가입 직원 수 기준 최근 {stats.length}개월 흐름
          </p>
        </div>
        <div className="text-right text-xs text-[#94a3b8]">
          <div>최대 {maxCount.toLocaleString()}명</div>
          <div>최소 {minCount.toLocaleString()}명</div>
        </div>
      </div>

      <div className="relative">
        <div className="absolute inset-x-0 top-[12px] h-[120px] border-b border-dashed border-[#dbeafe]" />
        <div className="absolute inset-x-0 top-[72px] h-[1px] bg-[#eff6ff]" />
        <div className="absolute inset-x-0 top-[132px] h-[1px] bg-[#eff6ff]" />

        <div
          className="grid h-[220px] items-end gap-2"
          style={{ gridTemplateColumns: `repeat(${stats.length}, minmax(0, 1fr))` }}
        >
          {stats.map((stat) => {
            const barHeight = Math.max(20, (stat.employee_count / maxCount) * chartHeight);
            return (
              <div key={stat.year_month} className="flex min-w-0 flex-col items-center gap-2">
                <div className="text-[11px] font-medium text-[#64748b]">
                  {stat.employee_count.toLocaleString()}
                </div>
                <div className="relative flex h-[220px] w-full items-end justify-center">
                  <div
                    className="w-full max-w-[36px] rounded-t-xl bg-[#bfdbfe]"
                    style={{ height: `${barHeight}px` }}
                  />
                </div>
                <div className="text-[11px] text-[#94a3b8]">
                  {formatMonthLabel(stat.year_month)}
                </div>
              </div>
            );
          })}
        </div>

        <svg
          viewBox="0 0 100 120"
          preserveAspectRatio="none"
          className="pointer-events-none absolute left-0 right-0 top-[40px] h-[120px] w-full overflow-visible"
        >
          <polyline
            fill="none"
            stroke="#1d4ed8"
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
            points={points.join(" ")}
          />
          {stats.map((stat, index) => {
            const x = stats.length === 1 ? 50 : (index / (stats.length - 1)) * 100;
            const normalizedY = (stat.employee_count - minCount) / countRange;
            const y = lineHeight - normalizedY * lineHeight;
            return (
              <circle
                key={stat.year_month}
                cx={x}
                cy={y}
                r="2.4"
                fill="#1d4ed8"
                stroke="#ffffff"
                strokeWidth="1.2"
              />
            );
          })}
        </svg>
      </div>
    </div>
  );
}
