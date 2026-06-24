"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import { api } from "@/lib/api";
import type { HealthScore } from "@/lib/types";
import { gradeColor } from "@/lib/colors";
import CircleGauge from "@/components/CircleGauge";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import AIReportCard from "@/components/AIReportCard";
import EmployeeTrendChart from "@/components/EmployeeTrendChart";

function formatChange(changePct: number | null): string {
  if (changePct == null) {
    return "데이터 부족";
  }
  if (changePct > 0) {
    return `최근 ${changePct.toFixed(1)}% 증가`;
  }
  if (changePct < 0) {
    return `최근 ${Math.abs(changePct).toFixed(1)}% 감소`;
  }
  return "최근 변동 없음";
}

export default function CompanyDetailPage({
  params,
}: {
  params: Promise<{ seq: string }>;
}) {
  const { seq } = use(params);
  const seqNum = Number(seq);

  const [health, setHealth] = useState<HealthScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);
    api
      .getHealth(seqNum)
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch((e) => {
        if (active)
          setError(e instanceof Error ? e.message : "정보를 불러오지 못했습니다.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [seqNum]);

  function addToCompare() {
    if (!health) return;
    try {
      sessionStorage.setItem("compare-target-seq", String(health.seq));
      sessionStorage.setItem("compare-target-name", health.name);
    } catch {
      // sessionStorage 사용 불가 시 무시
    }
    setAdded(true);
  }

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/"
        className="inline-flex w-fit items-center gap-1 text-sm text-[#64748b] hover:text-[#0f172a]"
      >
        ← 뒤로가기
      </Link>

      {isLoading && (
        <div className="flex justify-center py-12">
          <CircularProgress size={40} />
        </div>
      )}

      {error && !isLoading && (
        <Alert severity="error">{error}</Alert>
      )}

      {health && !isLoading && (
        <>
          <header>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold text-[#0f172a]">
                {health.name}
              </h1>
            </div>
          </header>

          <section className="flex flex-col items-center gap-8 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-6 sm:flex-row sm:items-start">
            <div className="flex flex-col items-center gap-3">
              <CircleGauge score={health.health_score} grade={health.grade} />
              <Chip
                label={health.grade}
                size="small"
                sx={{
                  backgroundColor: gradeColor(health.grade),
                  color: "white",
                  fontWeight: 600,
                }}
              />
            </div>
            <div className="w-full flex-1">
              <h2 className="mb-4 text-sm font-semibold text-[#64748b]">
                항목별 점수
              </h2>
              <ScoreBreakdown
                growth={health.growth}
                stability={health.stability}
                hiring_activity={health.hiring_activity}
                size_fit={health.size_fit}
                salary_signal={health.salary_signal}
              />
            </div>
          </section>

          <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-[#e2e8f0] bg-white p-5">
              <p className="text-sm font-medium text-[#64748b]">현재 직원 수</p>
              <p className="mt-2 text-3xl font-bold text-[#0f172a]">
                {health.employee_count != null
                  ? `${health.employee_count.toLocaleString()}명`
                  : "-"}
              </p>
              <p className="mt-2 text-xs text-[#94a3b8]">
                국민연금 가입 직원 수 기준
              </p>
            </div>
            <div className="rounded-xl border border-[#e2e8f0] bg-white p-5">
              <p className="text-sm font-medium text-[#64748b]">최근 직원 변화율</p>
              <p className="mt-2 text-3xl font-bold text-[#0f172a]">
                {health.recent_employee_change_pct != null
                  ? `${Math.abs(health.recent_employee_change_pct).toFixed(1)}%`
                  : "-"}
              </p>
              <p className="mt-2 text-xs text-[#94a3b8]">
                {formatChange(health.recent_employee_change_pct)}
              </p>
            </div>
            <div className="rounded-xl border border-[#e2e8f0] bg-white p-5">
              <p className="text-sm font-medium text-[#64748b]">월별 데이터 범위</p>
              <p className="mt-2 text-3xl font-bold text-[#0f172a]">
                {health.monthly_employee_stats.length}개월
              </p>
              <p className="mt-2 text-xs text-[#94a3b8]">
                최근 확보된 국민연금 월별 통계 기준
              </p>
            </div>
          </section>

          <EmployeeTrendChart stats={health.monthly_employee_stats} />

          <AIReportCard report={health.ai_report} type="company" />

          <div className="flex flex-col items-start gap-2">
            <Button
              variant="outlined"
              onClick={addToCompare}
              color={added ? "success" : "primary"}
            >
              {added ? "✓ 비교 대상에 담김" : "이직 비교에 추가하기"}
            </Button>
            {added && (
              <Link
                href="/"
                className="text-sm text-[#64748b] underline hover:text-[#0f172a]"
              >
                홈으로 가서 비교할 다른 회사 선택하기
              </Link>
            )}
          </div>
        </>
      )}
    </div>
  );
}
