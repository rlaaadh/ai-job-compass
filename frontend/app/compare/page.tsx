"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import Chip from "@mui/material/Chip";
import { api } from "@/lib/api";
import type { CompareResult, HealthScore, UserProfile } from "@/lib/types";
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
      <ScoreBreakdown
        growth={health.growth}
        stability={health.stability}
        size_fit={health.size_fit}
        employee_count={health.employee_count}
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
  const [profileRole, setProfileRole] = useState<string | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("userProfile");
    if (!raw) return;
    try {
      const profile: UserProfile = JSON.parse(raw);
      setProfileRole(profile.role ?? null);
    } catch {
      // ignore malformed data
    }
  }, []);

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
        role: profileRole,
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
  }, [currentSeq, profileRole, targetSeq]);

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
            <Chip
              label={result.verdict}
              sx={{
                backgroundColor: verdictColor(result.verdict),
                color: "white",
                fontWeight: 600,
                fontSize: "1rem",
                height: 36,
                px: 1,
              }}
            />
          </section>

          {/* 좌우 비교 */}
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <CompanyColumn title="현재 회사" health={result.current} />
            <CompanyColumn title="관심 회사" health={result.target} />
          </section>

          <section className="rounded-xl border border-[#dbeafe] bg-[#f8fbff] p-4">
            <p className="text-sm font-semibold text-[#1d4ed8]">
              점수 안내
            </p>
            <p className="mt-2 text-sm leading-6 text-[#475569]">
              총점은 성장성(40) + 안정성(35) + 기업 규모(25)로 계산하고,
              최근 직원 수가 급격히 감소하는 경우에는 리스크를 추가로 감점해요.
            </p>
            <p className="mt-1 text-sm leading-6 text-[#64748b]">
              최근 직원 수 감소나 변동 폭은 성장성과 안정성 판단에 반영되고,
              기업 규모는 현재 국민연금 가입 직원 수만 기준으로 계산해요.
            </p>
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
        <div className="flex justify-center py-12">
          <CircularProgress size={40} />
        </div>
      }
    >
      <CompareContent />
    </Suspense>
  );
}
