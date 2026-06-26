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
  const lineHeight = 150;

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
            최근 6개월 직원 수 변화 추이
          </h3>
          <p className="text-sm text-[#64748b]">
            국민연금 가입 직원 수 기준 최근 {stats.length}개월 꺾은선 그래프
          </p>
        </div>
        <div className="text-right text-xs text-[#94a3b8]">
          <div>최대 {maxCount.toLocaleString()}명</div>
          <div>최소 {minCount.toLocaleString()}명</div>
        </div>
      </div>

      <div className="relative rounded-xl bg-[#f8fbff] p-4">
        <div className="absolute inset-x-4 top-[28px] h-[1px] bg-[#dbeafe]" />
        <div className="absolute inset-x-4 top-[88px] h-[1px] bg-[#eaf2ff]" />
        <div className="absolute inset-x-4 top-[148px] h-[1px] bg-[#eaf2ff]" />
        <svg
          viewBox="0 0 100 150"
          preserveAspectRatio="none"
          className="h-[180px] w-full overflow-visible"
        >
          <polyline
            fill="none"
            stroke="#1d4ed8"
            strokeWidth="3"
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

        <div
          className="mt-3 grid gap-2"
          style={{ gridTemplateColumns: `repeat(${stats.length}, minmax(0, 1fr))` }}
        >
          {stats.map((stat) => (
            <div key={stat.year_month} className="min-w-0 text-center">
              <div className="text-[11px] font-medium text-[#475569]">
                {stat.employee_count.toLocaleString()}명
              </div>
              <div className="mt-1 text-[11px] text-[#94a3b8]">
                {formatMonthLabel(stat.year_month)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
