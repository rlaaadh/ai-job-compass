"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CompanyBasic, UserProfile } from "@/lib/types";

const EDUCATION_OPTIONS = [
  { value: "", label: "선택 안 함" },
  { value: "high_school", label: "고졸" },
  { value: "associate", label: "전문대졸" },
  { value: "bachelor", label: "대졸" },
  { value: "master", label: "대학원졸 (석사)" },
  { value: "phd", label: "대학원졸 (박사)" },
];

const GENDER_OPTIONS = [
  { value: "", label: "선택 안 함" },
  { value: "male", label: "남성" },
  { value: "female", label: "여성" },
];

const EXP_OPTIONS = [
  { value: "", label: "선택하세요" },
  { value: "0", label: "1년 미만" },
  ...Array.from({ length: 9 }, (_, i) => ({ value: String(i + 1), label: `${i + 1}년` })),
  { value: "10", label: "10년 이상" },
];

export default function ProfilePage() {
  const router = useRouter();
  const dropdownRef = useRef<HTMLUListElement>(null);

  const [companyQuery, setCompanyQuery] = useState("");
  const [companyResults, setCompanyResults] = useState<CompanyBasic[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<CompanyBasic | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const [role, setRole] = useState("");
  const [yearsOfExp, setYearsOfExp] = useState("");
  const [education, setEducation] = useState("");
  const [gender, setGender] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("userProfile");
    if (!raw) return;
    try {
      const profile: UserProfile = JSON.parse(raw);
      setSelectedCompany(profile.company);
      setCompanyQuery(profile.company.name);
      setRole(profile.role);
      setYearsOfExp(profile.yearsOfExp != null ? String(profile.yearsOfExp) : "");
      setEducation(profile.education ?? "");
      setGender(profile.gender ?? "");
    } catch {
      // ignore malformed data
    }
  }, []);

  useEffect(() => {
    const q = companyQuery.trim();
    if (!q || selectedCompany?.name === q) {
      setCompanyResults([]);
      setShowDropdown(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await api.searchCompanies(q, 5);
        setCompanyResults(results);
        setShowDropdown(results.length > 0);
      } catch {
        setCompanyResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [companyQuery, selectedCompany]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function selectCompany(company: CompanyBasic) {
    setSelectedCompany(company);
    setCompanyQuery(company.name);
    setCompanyResults([]);
    setShowDropdown(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCompany) return;
    const profile: UserProfile = {
      company: selectedCompany,
      role,
      yearsOfExp: yearsOfExp !== "" ? Number(yearsOfExp) : null,
      education: education || null,
      gender: gender || null,
    };
    localStorage.setItem("userProfile", JSON.stringify(profile));
    setSaved(true);
    setTimeout(() => router.push("/"), 800);
  }

  const canSubmit = !!selectedCompany && role.trim() !== "" && yearsOfExp !== "";

  return (
    <div className="mx-auto max-w-lg">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-[#0f172a]">내 정보 등록</h1>
        <p className="mt-1 text-sm text-[#64748b]">
          내 현재 직장 정보를 등록하면 이직 분석을 더 빠르게 시작할 수 있어요.
        </p>
      </div>

      {saved && (
        <div className="mb-4 rounded-lg bg-[#ecfdf5] px-4 py-3 text-sm text-[#059669]">
          저장되었습니다. 홈으로 이동합니다...
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {/* 현재 회사 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[#0f172a]">
            현재 회사 <span className="text-[#ef4444]">*</span>
          </label>
          <div className="relative">
            <input
              type="text"
              value={companyQuery}
              onChange={(e) => {
                setCompanyQuery(e.target.value);
                setSelectedCompany(null);
              }}
              onFocus={() => companyResults.length > 0 && setShowDropdown(true)}
              placeholder="회사명 검색 (예: 카카오, 네이버)"
              className="w-full rounded-lg border border-[#e2e8f0] bg-white px-4 py-2.5 text-[#0f172a] outline-none placeholder:text-[#94a3b8] focus:border-[#3b82f6]"
            />
            {isSearching && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#94a3b8]">
                검색 중...
              </span>
            )}
            {showDropdown && companyResults.length > 0 && (
              <ul
                ref={dropdownRef}
                className="absolute z-10 mt-1 w-full rounded-lg border border-[#e2e8f0] bg-white shadow-md"
              >
                {companyResults.map((c) => (
                  <li key={c.seq}>
                    <button
                      type="button"
                      onClick={() => selectCompany(c)}
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-[#f1f5f9]"
                    >
                      <span className="font-medium text-[#0f172a]">{c.name}</span>
                      {c.industry_name && (
                        <span className="ml-2 text-xs text-[#94a3b8]">{c.industry_name}</span>
                      )}
                      {c.employee_count != null && (
                        <span className="ml-1 text-xs text-[#94a3b8]">· {c.employee_count.toLocaleString()}명</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {selectedCompany && (
            <p className="text-xs text-[#10b981]">✓ {selectedCompany.name} 선택됨</p>
          )}
          {!selectedCompany && companyQuery.trim() !== "" && !isSearching && companyResults.length === 0 && (
            <p className="text-xs text-[#f59e0b]">검색 결과가 없습니다. 다른 이름으로 검색해보세요.</p>
          )}
        </div>

        {/* 직무 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[#0f172a]">
            직무 <span className="text-[#ef4444]">*</span>
          </label>
          <input
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="예: 프론트엔드 개발자, 마케터, 기획자"
            className="rounded-lg border border-[#e2e8f0] bg-white px-4 py-2.5 text-[#0f172a] outline-none placeholder:text-[#94a3b8] focus:border-[#3b82f6]"
          />
        </div>

        {/* 연차 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[#0f172a]">
            연차 <span className="text-[#ef4444]">*</span>
          </label>
          <select
            value={yearsOfExp}
            onChange={(e) => setYearsOfExp(e.target.value)}
            className="rounded-lg border border-[#e2e8f0] bg-white px-4 py-2.5 text-[#0f172a] outline-none focus:border-[#3b82f6]"
          >
            {EXP_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* 학력 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[#0f172a]">
            학력{" "}
            <span className="text-xs font-normal text-[#94a3b8]">(선택)</span>
          </label>
          <select
            value={education}
            onChange={(e) => setEducation(e.target.value)}
            className="rounded-lg border border-[#e2e8f0] bg-white px-4 py-2.5 text-[#0f172a] outline-none focus:border-[#3b82f6]"
          >
            {EDUCATION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* 성별 */}
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[#0f172a]">
            성별{" "}
            <span className="text-xs font-normal text-[#94a3b8]">(선택)</span>
          </label>
          <select
            value={gender}
            onChange={(e) => setGender(e.target.value)}
            className="rounded-lg border border-[#e2e8f0] bg-white px-4 py-2.5 text-[#0f172a] outline-none focus:border-[#3b82f6]"
          >
            {GENDER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-3 pt-1">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="rounded-lg border border-[#e2e8f0] bg-white px-5 py-2.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9]"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={!canSubmit || saved}
            className="flex-1 rounded-lg bg-[#3b82f6] px-6 py-2.5 font-medium text-white transition-colors hover:bg-[#2563eb] disabled:cursor-not-allowed disabled:bg-[#cbd5e1]"
          >
            저장하기
          </button>
        </div>
      </form>
    </div>
  );
}
