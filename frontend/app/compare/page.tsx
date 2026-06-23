"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { CompareResult, HealthScore } from "@/lib/types";
import { gradeColor, verdictColor } from "@/lib/colors";
import CircleGauge from "@/components/CircleGauge";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import AIReportCard from "@/components/AIReportCard";

function CompanyColumn({
  title,
  health,
}: {
  title: string;
  health: HealthScore;
}) {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-[#94a3b8]">
          {title}
        </p>
        <h3 className="text-lg font-bold text-[#0f172a]">{health.name}</h3>
      </div>
      <div className="flex flex-col items-center gap-2">
        <CircleGauge
          score={health.health_score}
          grade={health.grade}
          size={140}
        />
        <span
          className="rounded-full px-3 py-1 text-sm font-semibold text-white"
          style={{ backgroundColor: gradeColor(health.grade) }}
        >
          {health.grade}
        </span>
      </div>
      <ScoreBreakdown
        growth={health.growth}
        stability={health.stability}
        hiring_activity={health.hiring_activity}
      />
    </div>
  );
}

function CompareContent() {
  const searchParams = useSearchParams();
  const currentSeq = searchParams.get("current");
  const targetSeq = searchParams.get("target");

  const [result, setResult] = useState<CompareResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!currentSeq || !targetSeq) {
      setError("비교할 두 회사를 선택해주세요. (현재 회사 / 관심 회사)");
      setIsLoading(false);
      return;
    }
    let active = true;
    setIsLoading(true);
    setError(null);
    api
      .compare({
        current_seq: Number(currentSeq),
        target_seq: Number(targetSeq),
      })
      .then((data) => {
        if (active) setResult(data);
      })
      .catch((e) => {
        if (active)
          setError(e instanceof Error ? e.message : "비교에 실패했습니다.");
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });
    return () => {
      active = false;
    };
  }, [currentSeq, targetSeq]);

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/"
        className="inline-flex w-fit items-center gap-1 text-sm text-[#64748b] hover:text-[#0f172a]"
      >
        ← 뒤로가기
      </Link>

      {isLoading && (
        <p className="text-center text-sm text-[#64748b]">비교 중...</p>
      )}

      {error && !isLoading && (
        <p className="rounded-lg bg-[#fef2f2] px-4 py-3 text-sm text-[#ef4444]">
          {error}
        </p>
      )}

      {result && !isLoading && (
        <>
          {/* 이직 추천도 */}
          <section className="flex flex-col items-center gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-8">
            <p className="text-sm font-medium text-[#64748b]">이직 추천도</p>
            <p
              className="text-6xl font-bold leading-none"
              style={{ color: verdictColor(result.verdict) }}
            >
              {Math.round(result.recommendation_score)}
            </p>
            <span
              className="rounded-full px-4 py-1.5 text-base font-semibold text-white"
              style={{ backgroundColor: verdictColor(result.verdict) }}
            >
              {result.verdict}
            </span>
            <p className="text-xs text-[#94a3b8]">
              연봉 변화 시그널: {result.salary_change_signal > 0 ? "+" : ""}
              {result.salary_change_signal} (참고값, 실제 급여와 다를 수 있음)
            </p>
          </section>

          {/* 좌우 비교 */}
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <CompanyColumn title="현재 회사" health={result.current} />
            <CompanyColumn title="관심 회사" health={result.target} />
          </section>

          {/* AI 리포트 */}
          <AIReportCard report={result.ai_report} type="recommendation" />
        </>
      )}
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <p className="text-center text-sm text-[#64748b]">불러오는 중...</p>
      }
    >
      <CompareContent />
    </Suspense>
  );
}
