"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CompanyBasic, UserProfile } from "@/lib/types";
import CompanyCard from "@/components/CompanyCard";

export default function HomePage() {
  const router = useRouter();
  const searchContainerRef = useRef<HTMLDivElement>(null);

  const [profile, setProfile] = useState<UserProfile | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [dropdownResults, setDropdownResults] = useState<CompanyBasic[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isDropdownLoading, setIsDropdownLoading] = useState(false);

  const [results, setResults] = useState<CompanyBasic[]>([]);
  const [searchRows, setSearchRows] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const [compareList, setCompareList] = useState<CompanyBasic[]>([]);

  // localStorage에서 프로필 로드
  useEffect(() => {
    const raw = localStorage.getItem("userProfile");
    if (!raw) return;
    try {
      setProfile(JSON.parse(raw));
    } catch {
      // ignore
    }
  }, []);

  // 타이핑 시 드롭다운 자동완성 (디바운스 300ms)
  useEffect(() => {
    const q = searchQuery.trim();
    if (!q) {
      setDropdownResults([]);
      setShowDropdown(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsDropdownLoading(true);
      try {
        const data = await api.searchCompanies(q, 8);
        setDropdownResults(data);
        setShowDropdown(data.length > 0);
      } catch {
        setDropdownResults([]);
        setShowDropdown(false);
      } finally {
        setIsDropdownLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleSearch() {
    const q = searchQuery.trim();
    if (!q) return;
    setShowDropdown(false);
    setIsLoading(true);
    setError(null);
    setSearchRows(10);
    try {
      const data = await api.searchCompanies(q, 10);
      setResults(data);
      setSearched(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "검색에 실패했습니다.");
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLoadMore() {
    const newRows = searchRows + 10;
    setSearchRows(newRows);
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.searchCompanies(searchQuery.trim(), newRows);
      setResults(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "더보기에 실패했습니다.");
      setSearchRows(searchRows);
    } finally {
      setIsLoading(false);
    }
  }

  function clearSearch() {
    setSearchQuery("");
    setDropdownResults([]);
    setShowDropdown(false);
    setResults([]);
    setSearched(false);
    setError(null);
  }

  function toggleCompare(company: CompanyBasic) {
    setCompareList((prev) => {
      const exists = prev.find((c) => c.seq === company.seq);
      if (exists) return prev.filter((c) => c.seq !== company.seq);
      if (prev.length >= 2) return prev;
      return [...prev, company];
    });
  }

  function handleDropdownSelect(company: CompanyBasic) {
    setShowDropdown(false);
    setSearchQuery(company.name);
    toggleCompare(company);
  }

  function addMyCompany() {
    if (!profile) return;
    setCompareList((prev) => {
      if (prev.find((c) => c.seq === profile.company.seq)) return prev;
      if (prev.length >= 2) return prev;
      return [...prev, profile.company];
    });
  }

  function goCompare() {
    if (compareList.length !== 2) return;
    const [current, target] = compareList;
    router.push(`/compare?current=${current.seq}&target=${target.seq}`);
  }

  const myCompanyInCompare =
    profile && compareList.some((c) => c.seq === profile.company.seq);
  const anyLoading = isLoading || isDropdownLoading;

  return (
    <div className="flex flex-col gap-8">
      {/* Hero */}
      <section className="text-center">
        <h1 className="text-2xl font-bold leading-snug text-[#0f172a] sm:text-3xl">
          <span aria-hidden>🧭</span> 감이 아닌 데이터로 이직을 결정하다
        </h1>
        <p className="mt-2 text-sm text-[#64748b] sm:text-base">
          국민연금 데이터 기반 기업 건강도 &amp; 이직 추천도
        </p>
      </section>

      {/* 내 정보 배너 */}
      {profile ? (
        <section className="rounded-xl border border-[#bfdbfe] bg-[#eff6ff] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[#3b82f6]">
                내 현재 직장
              </p>
              <p className="mt-0.5 font-semibold text-[#0f172a]">
                {profile.company.name}
              </p>
              <p className="text-sm text-[#64748b]">
                {profile.role}
                {profile.yearsOfExp != null && (
                  <span>
                    {" "}
                    ·{" "}
                    {profile.yearsOfExp === 0
                      ? "1년 미만"
                      : profile.yearsOfExp === 10
                      ? "10년 이상"
                      : `${profile.yearsOfExp}년차`}
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {!myCompanyInCompare && compareList.length < 2 && (
                <button
                  type="button"
                  onClick={addMyCompany}
                  className="rounded-lg bg-[#3b82f6] px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-[#2563eb]"
                >
                  비교에 추가
                </button>
              )}
              {myCompanyInCompare && (
                <span className="rounded-lg bg-[#dbeafe] px-3 py-1.5 text-sm font-medium text-[#3b82f6]">
                  비교 중
                </span>
              )}
              <Link
                href="/profile"
                className="rounded-lg border border-[#bfdbfe] bg-white px-3 py-1.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9]"
              >
                수정
              </Link>
            </div>
          </div>
        </section>
      ) : (
        <section className="rounded-xl border border-[#e2e8f0] bg-white p-6 text-center">
          <p className="font-semibold text-[#0f172a]">이직을 고민하고 있나요?</p>
          <p className="mt-1 text-sm text-[#64748b]">
            내 현재 직장을 등록하면 관심 회사와 바로 비교 분석할 수 있어요.
          </p>
          <Link
            href="/profile"
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-[#3b82f6] px-5 py-2.5 font-medium text-white transition-colors hover:bg-[#2563eb]"
          >
            <span>내 회사 등록하기</span>
            <span aria-hidden>→</span>
          </Link>
        </section>
      )}

      {/* 검색 바 + 드롭다운 */}
      <section className="flex flex-col gap-2">
        <div className="relative flex gap-2" ref={searchContainerRef}>
          {/* 입력 필드 */}
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => dropdownResults.length > 0 && setShowDropdown(true)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSearch();
                if (e.key === "Escape") setShowDropdown(false);
              }}
              placeholder="비교할 회사명을 검색하세요"
              className="w-full rounded-lg border border-[#e2e8f0] bg-white py-2.5 pl-4 pr-9 text-[#0f172a] outline-none placeholder:text-[#94a3b8] focus:border-[#3b82f6]"
            />
            {/* X 버튼 */}
            {searchQuery && (
              <button
                type="button"
                onClick={clearSearch}
                aria-label="검색어 지우기"
                className="absolute right-3 top-1/2 -translate-y-1/2 flex h-5 w-5 items-center justify-center rounded-full text-[#94a3b8] transition-colors hover:bg-[#f1f5f9] hover:text-[#64748b]"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="h-3.5 w-3.5"
                >
                  <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                </svg>
              </button>
            )}

            {/* 자동완성 드롭다운 */}
            {showDropdown && dropdownResults.length > 0 && (
              <ul className="absolute left-0 right-0 top-full z-30 mt-1 max-h-72 overflow-y-auto rounded-lg border border-[#e2e8f0] bg-white shadow-lg">
                {dropdownResults.map((company) => {
                  const inCompare = compareList.some((c) => c.seq === company.seq);
                  const compareFull = compareList.length >= 2 && !inCompare;
                  return (
                    <li key={company.seq}>
                      <button
                        type="button"
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => !compareFull && handleDropdownSelect(company)}
                        disabled={compareFull}
                        className={[
                          "flex w-full cursor-pointer items-center justify-between px-4 py-3 text-left transition-colors",
                          compareFull
                            ? "cursor-not-allowed opacity-40"
                            : "hover:bg-[#f1f5f9]",
                        ].join(" ")}
                      >
                        <div className="flex min-w-0 flex-col">
                          <span className="truncate font-medium text-[#0f172a]">
                            {company.name}
                          </span>
                          <span className="text-xs text-[#94a3b8]">
                            {[
                              company.industry_name,
                              company.employee_count != null
                                ? `${company.employee_count.toLocaleString()}명`
                                : null,
                            ]
                              .filter(Boolean)
                              .join(" · ")}
                          </span>
                        </div>

                        {/* 상태 배지 */}
                        <span className="ml-3 shrink-0">
                          {inCompare ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-[#dbeafe] px-2 py-0.5 text-xs font-medium text-[#3b82f6]">
                              ✓ 선택됨
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-[#f1f5f9] px-2 py-0.5 text-xs text-[#64748b]">
                              + 비교 추가
                            </span>
                          )}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <button
            type="button"
            onClick={handleSearch}
            disabled={isLoading || !searchQuery.trim()}
            className="shrink-0 rounded-lg bg-[#3b82f6] px-6 py-2.5 font-medium text-white transition-colors hover:bg-[#2563eb] disabled:cursor-not-allowed disabled:bg-[#cbd5e1]"
          >
            {isLoading ? "검색 중..." : "검색"}
          </button>
        </div>

        {/* 로딩 바 */}
        {anyLoading && (
          <div className="h-0.5 w-full overflow-hidden rounded-full bg-[#e2e8f0]">
            <div className="loading-bar-thumb h-full w-2/5 rounded-full bg-[#3b82f6]" />
          </div>
        )}
      </section>

      {/* 비교 선택 영역 */}
      {compareList.length > 0 && (
        <section className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-[#64748b]">
                비교 대상 ({compareList.length}/2):
              </span>
              {compareList.map((c) => (
                <span
                  key={c.seq}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-sm text-[#0f172a] ring-1 ring-[#e2e8f0]"
                >
                  {c.name}
                  <button
                    type="button"
                    onClick={() => toggleCompare(c)}
                    className="text-[#94a3b8] hover:text-[#ef4444]"
                    aria-label={`${c.name} 제거`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            <button
              type="button"
              onClick={goCompare}
              disabled={compareList.length !== 2}
              className="rounded-lg bg-[#10b981] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#059669] disabled:cursor-not-allowed disabled:bg-[#cbd5e1]"
            >
              이직 추천도 비교하기
            </button>
          </div>
          {compareList.length < 2 && (
            <p className="mt-2 text-xs text-[#94a3b8]">
              비교할 회사 2곳을 선택하면 이직 추천도를 분석해드립니다.
            </p>
          )}
        </section>
      )}

      {/* 검색 결과 */}
      {error && (
        <p className="rounded-lg bg-[#fef2f2] px-4 py-3 text-sm text-[#ef4444]">
          {error}
        </p>
      )}

      {searched && !error && results.length === 0 && !isLoading && (
        <p className="text-center text-sm text-[#64748b]">검색 결과가 없습니다.</p>
      )}

      {results.length > 0 && (
        <section className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {results.map((company) => (
              <CompanyCard
                key={company.seq}
                company={company}
                onAddToCompare={toggleCompare}
                isInCompare={compareList.some((c) => c.seq === company.seq)}
                compareDisabled={
                  compareList.length >= 2 &&
                  !compareList.some((c) => c.seq === company.seq)
                }
              />
            ))}
          </div>

          {/* 더보기 */}
          {results.length === searchRows && (
            <div className="flex justify-center pt-2">
              <button
                type="button"
                onClick={handleLoadMore}
                disabled={isLoading}
                className="rounded-lg border border-[#e2e8f0] bg-white px-6 py-2.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isLoading ? "불러오는 중..." : `더보기 (${results.length}개 표시 중)`}
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
