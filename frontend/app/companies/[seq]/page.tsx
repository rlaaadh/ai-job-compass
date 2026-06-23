"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { HealthScore } from "@/lib/types";
import { gradeColor } from "@/lib/colors";
import CircleGauge from "@/components/CircleGauge";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import AIReportCard from "@/components/AIReportCard";

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
        <p className="text-center text-sm text-[#64748b]">불러오는 중...</p>
      )}

      {error && !isLoading && (
        <p className="rounded-lg bg-[#fef2f2] px-4 py-3 text-sm text-[#ef4444]">
          {error}
        </p>
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
              <span
                className="rounded-full px-3 py-1 text-sm font-semibold text-white"
                style={{ backgroundColor: gradeColor(health.grade) }}
              >
                {health.grade}
              </span>
            </div>
            <div className="w-full flex-1">
              <h2 className="mb-4 text-sm font-semibold text-[#64748b]">
                항목별 점수
              </h2>
              <ScoreBreakdown
                growth={health.growth}
                stability={health.stability}
                hiring_activity={health.hiring_activity}
              />
            </div>
          </section>

          <AIReportCard report={health.ai_report} type="company" />

          <div className="flex flex-col items-start gap-2">
            <button
              type="button"
              onClick={addToCompare}
              className="rounded-lg border border-[#3b82f6] bg-white px-4 py-2 text-sm font-medium text-[#3b82f6] transition-colors hover:bg-[#eff6ff]"
            >
              {added ? "✓ 비교 대상에 담김" : "이직 비교에 추가하기"}
            </button>
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
