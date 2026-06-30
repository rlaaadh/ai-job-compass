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

const COMPARE_RESULT_CACHE_KEY = "compareResultCache";
const compareRequestInflight = new Map<string, Promise<CompareResult>>();

type CompareResultCacheEntry = {
  cacheKey: string;
  result: CompareResult;
};

function buildCompareCacheKey(
  currentSeq: string | null,
  targetSeq: string | null,
  role: string | null,
): string | null {
  if (!currentSeq || !targetSeq) {
    return null;
  }

  return JSON.stringify({
    currentSeq,
    targetSeq,
    role: role ?? null,
  });
}

function loadCachedCompareResult(cacheKey: string): CompareResult | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(COMPARE_RESULT_CACHE_KEY);
    if (!raw) {
      return null;
    }

    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return null;
    }

    const entry = parsed as Partial<CompareResultCacheEntry>;
    if (entry.cacheKey !== cacheKey || !entry.result) {
      return null;
    }

    return entry.result;
  } catch {
    return null;
  }
}

function saveCachedCompareResult(cacheKey: string, result: CompareResult): void {
  if (typeof window === "undefined") {
    return;
  }

  const payload: CompareResultCacheEntry = {
    cacheKey,
    result,
  };
  window.sessionStorage.setItem(COMPARE_RESULT_CACHE_KEY, JSON.stringify(payload));
}

function loadStoredProfileRole(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem("userProfile");
    if (!raw) {
      return null;
    }

    const profile = JSON.parse(raw) as UserProfile;
    return profile.role ?? null;
  } catch {
    return null;
  }
}

function hasStoredProfileCompany(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  try {
    const raw = window.localStorage.getItem("userProfile");
    if (!raw) {
      return false;
    }

    const profile = JSON.parse(raw) as Partial<UserProfile>;
    return Boolean(profile.company?.seq);
  } catch {
    return false;
  }
}

function fetchCompareResult(
  cacheKey: string,
  currentSeq: string,
  targetSeq: string,
  role: string | null,
): Promise<CompareResult> {
  const inflight = compareRequestInflight.get(cacheKey);
  if (inflight) {
    return inflight;
  }

  const request = api
    .compare({
      current_seq: Number(currentSeq),
      target_seq: Number(targetSeq),
      role,
    })
    .then((data) => {
      saveCachedCompareResult(cacheKey, data);
      return data;
    })
    .finally(() => {
      compareRequestInflight.delete(cacheKey);
    });

  compareRequestInflight.set(cacheKey, request);
  return request;
}

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
  const [profileRole] = useState<string | null>(() => loadStoredProfileRole());
  const [hasProfileCompany] = useState<boolean>(() => hasStoredProfileCompany());

  useEffect(() => {
    if (!currentSeq || !targetSeq) {
      setError(
        hasProfileCompany
          ? "비교해볼 다른 회사를 선택해주세요."
          : "비교할 두 회사를 선택해주세요. (현재 회사 / 관심 회사)",
      );
      setIsLoading(false);
      return;
    }

    const cacheKey = buildCompareCacheKey(currentSeq, targetSeq, profileRole);
    if (!cacheKey) {
      setError("비교 요청을 준비하지 못했습니다. 다시 시도해주세요.");
      setIsLoading(false);
      return;
    }

    if (cacheKey) {
      const cachedResult = loadCachedCompareResult(cacheKey);
      if (cachedResult) {
        setResult(cachedResult);
        setError(null);
        setIsLoading(false);
        return;
      }
    }

    let active = true;
    setIsLoading(true);
    setError(null);
    fetchCompareResult(cacheKey, currentSeq, targetSeq, profileRole)
      .then((data) => {
        if (active) {
          setResult(data);
        }
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
  }, [currentSeq, hasProfileCompany, profileRole, targetSeq]);

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
