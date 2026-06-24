"use client";

import { startTransition, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import InputAdornment from "@mui/material/InputAdornment";
import CircularProgress from "@mui/material/CircularProgress";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import Paper from "@mui/material/Paper";
import MenuList from "@mui/material/MenuList";
import MenuItem from "@mui/material/MenuItem";
import CloseIcon from "@mui/icons-material/Close";
import { api } from "@/lib/api";
import type { CompanyBasic, UserProfile } from "@/lib/types";
import CompanyCard from "@/components/CompanyCard";
import HighlightedText from "@/components/HighlightedText";

function normalizeQuery(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function syncCompareListWithProfile(
  profileCompany: CompanyBasic,
  prev: CompanyBasic[],
): CompanyBasic[] {
  const targetOnly = prev.filter((company) => company.seq !== profileCompany.seq);
  return [profileCompany, ...targetOnly].slice(0, 2);
}

export default function HomePage() {
  const router = useRouter();
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const dropdownAbortRef = useRef<AbortController | null>(null);

  const [profile, setProfile] = useState<UserProfile | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [dropdownResults, setDropdownResults] = useState<CompanyBasic[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isDropdownLoading, setIsDropdownLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);

  const [results, setResults] = useState<CompanyBasic[]>([]);
  const [searchRows, setSearchRows] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const [compareList, setCompareList] = useState<CompanyBasic[]>([]);
  const safeSearchQuery = normalizeQuery(searchQuery);

  useEffect(() => {
    const raw = localStorage.getItem("userProfile");
    if (!raw) return;
    try {
      const nextProfile: UserProfile = JSON.parse(raw);
      setProfile(nextProfile);
      setCompareList((prev) => syncCompareListWithProfile(nextProfile.company, prev));
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const q = safeSearchQuery.trim();
    if (!q || q.length < 2 || isComposing) {
      dropdownAbortRef.current?.abort();
      setDropdownResults([]);
      setShowDropdown(false);
      setIsDropdownLoading(false);
      return;
    }
    const timer = setTimeout(async () => {
      dropdownAbortRef.current?.abort();
      const controller = new AbortController();
      dropdownAbortRef.current = controller;
      setIsDropdownLoading(true);
      try {
        const data = await api.searchCompanies(q, 8, {
          fallback: false,
          signal: controller.signal,
        });
        startTransition(() => {
          setDropdownResults(data);
          setShowDropdown(data.length > 0);
        });
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }
        startTransition(() => {
          setDropdownResults([]);
          setShowDropdown(false);
        });
      } finally {
        if (dropdownAbortRef.current === controller) {
          setIsDropdownLoading(false);
        }
      }
    }, 120);
    return () => {
      clearTimeout(timer);
    };
  }, [isComposing, safeSearchQuery]);

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

  useEffect(() => {
    return () => {
      dropdownAbortRef.current?.abort();
    };
  }, []);

  async function handleSearch() {
    const q = safeSearchQuery.trim();
    if (!q || q.length < 2 || isComposing) return;
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
      const data = await api.searchCompanies(safeSearchQuery.trim(), newRows);
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
      if (profile && company.seq === profile.company.seq) {
        return syncCompareListWithProfile(profile.company, prev);
      }

      const exists = prev.find((c) => c.seq === company.seq);
      if (exists) {
        return prev.filter((c) => c.seq !== company.seq);
      }

      if (profile) {
        const [current, target] = syncCompareListWithProfile(profile.company, prev);
        if (target) {
          return [current, company];
        }
        return [current, company];
      }

      if (prev.length >= 2) return prev;
      return [...prev, company];
    });
  }

  function handleDropdownSelect(company: CompanyBasic) {
    setShowDropdown(false);
    setSearchQuery(normalizeQuery(company.name));
    toggleCompare(company);
  }

  function addMyCompany() {
    if (!profile) return;
    setCompareList((prev) => syncCompareListWithProfile(profile.company, prev));
  }

  function goCompare() {
    if (compareList.length !== 2) return;
    const [current, target] = compareList;
    router.push(`/compare?current=${current.seq}&target=${target.seq}`);
  }

  const myCompanyInCompare =
    profile && compareList.some((c) => c.seq === profile.company.seq);

  return (
    <div className="flex flex-col gap-8">
      {/* Hero */}
      <section className="text-center">
        <h1 className="text-2xl font-bold leading-snug text-[#0f172a] sm:text-3xl">
          다른 직장은 어떨까 궁금하다면? 🤔
        </h1>
        <p className="mt-2 text-sm text-[#64748b] sm:text-base">
          국민연금 데이터 기반 이직 추천도
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
                    {" "}·{" "}
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
                <Button variant="contained" size="small" onClick={addMyCompany}>
                  비교에 추가
                </Button>
              )}
              {myCompanyInCompare && (
                <Chip label="비교 중" color="primary" variant="outlined" size="small" />
              )}
              <Button
                variant="outlined"
                size="small"
                component={Link}
                href="/profile"
              >
                수정
              </Button>
            </div>
          </div>
        </section>
      ) : (
        <section className="rounded-xl border border-[#e2e8f0] bg-white p-6 text-center">
          <p className="font-semibold text-[#0f172a]">이직을 고민하고 있나요?</p>
          <p className="mt-1 text-sm text-[#64748b]">
            내 현재 직장을 등록하면 관심 회사와 바로 비교 분석할 수 있어요.
          </p>
          <Button
            variant="contained"
            component={Link}
            href="/profile"
            sx={{ mt: 2 }}
          >
            내 회사 등록하기 →
          </Button>
        </section>
      )}

      {/* 검색 바 + 드롭다운 */}
      <section className="flex flex-col gap-2">
        <div className="relative flex gap-2" ref={searchContainerRef}>
          <div className="relative flex-1">
            <TextField
              fullWidth
              size="small"
              value={safeSearchQuery}
              onChange={(e) => setSearchQuery(normalizeQuery(e.target.value))}
              onCompositionStart={() => setIsComposing(true)}
              onCompositionEnd={(e) => {
                setIsComposing(false);
                setSearchQuery(normalizeQuery(e.target.value));
              }}
              onFocus={() => dropdownResults.length > 0 && setShowDropdown(true)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !isComposing) handleSearch();
                if (e.key === "Escape") setShowDropdown(false);
              }}
              placeholder="비교할 회사명을 검색하세요"
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      {isDropdownLoading ? (
                        <CircularProgress size={16} />
                      ) : safeSearchQuery ? (
                        <IconButton size="small" onClick={clearSearch} edge="end">
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      ) : null}
                    </InputAdornment>
                  ),
                },
              }}
            />

            {/* 자동완성 드롭다운 */}
            {showDropdown && dropdownResults.length > 0 && (
              <Paper
                elevation={3}
                sx={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: "100%",
                  zIndex: 30,
                  mt: 0.5,
                  maxHeight: 288,
                  overflow: "auto",
                }}
              >
                <MenuList dense>
                  {dropdownResults.map((company) => {
                    const inCompare = compareList.some((c) => c.seq === company.seq);
                    const isMyCompany =
                      profile?.company.seq != null &&
                      company.seq === profile.company.seq;
                    const compareFull = compareList.length >= 2 && !inCompare;
                    return (
                      <MenuItem
                        key={company.seq}
                        disabled={compareFull}
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => !compareFull && handleDropdownSelect(company)}
                        sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}
                      >
                        <div className="flex min-w-0 flex-col">
                          <span className="truncate font-medium text-[#0f172a]">
                            <HighlightedText
                              text={company.name}
                              query={safeSearchQuery}
                            />
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
                        <Chip
                          label={
                            isMyCompany
                              ? "내 회사"
                              : inCompare
                              ? "✓ 선택됨"
                              : "+ 비교 추가"
                          }
                          size="small"
                          color={inCompare ? "primary" : "default"}
                          variant={inCompare ? "filled" : "outlined"}
                        />
                      </MenuItem>
                    );
                  })}
                </MenuList>
              </Paper>
            )}
          </div>

          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={isLoading || safeSearchQuery.trim().length < 2}
            sx={{ flexShrink: 0 }}
          >
            {isLoading ? <CircularProgress size={20} color="inherit" /> : "검색"}
          </Button>
        </div>

        {/* 드롭다운 로딩은 InputAdornment로 처리됨 */}
      </section>

      {/* 비교 선택 영역 */}
      {compareList.length > 0 && (
        <section className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-[#64748b]">
                비교 대상 ({compareList.length}/2):
              </span>
              {compareList.map((c, index) => (
                <Chip
                  key={c.seq}
                  label={
                    profile && c.seq === profile.company.seq
                      ? `현재 회사 · ${c.name}`
                      : index === 1
                      ? `관심 회사 · ${c.name}`
                      : c.name
                  }
                  onDelete={
                    profile && c.seq === profile.company.seq
                      ? undefined
                      : () => toggleCompare(c)
                  }
                  variant="outlined"
                  size="small"
                  color={profile && c.seq === profile.company.seq ? "primary" : "default"}
                />
              ))}
            </div>
            <Button
              variant="contained"
              color="success"
              size="small"
              onClick={goCompare}
              disabled={compareList.length !== 2}
            >
              이직 추천도 비교하기
            </Button>
          </div>
          {compareList.length < 2 && (
            <p className="mt-2 text-xs text-[#94a3b8]">
              비교할 회사 2곳을 선택하면 이직 추천도를 분석해드립니다.
            </p>
          )}
        </section>
      )}

      {/* 검색 결과 */}
      {error && <Alert severity="error">{error}</Alert>}

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

          {results.length === searchRows && (
            <div className="flex justify-center pt-2">
              <Button
                variant="outlined"
                onClick={handleLoadMore}
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : undefined}
              >
                {isLoading ? "불러오는 중..." : `더보기 (${results.length}개 표시 중)`}
              </Button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
