"use client";

import { startTransition, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import { api } from "@/lib/api";
import type { CompanyBasic, UserProfile } from "@/lib/types";
import HighlightedText from "@/components/HighlightedText";

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
  const searchAbortRef = useRef<AbortController | null>(null);

  const [companyQuery, setCompanyQuery] = useState("");
  const [companyResults, setCompanyResults] = useState<CompanyBasic[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<CompanyBasic | null>(null);
  const [isSearching, setIsSearching] = useState(false);

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
    if (!q || q.length < 2 || selectedCompany?.name === q) {
      searchAbortRef.current?.abort();
      setCompanyResults([]);
      setIsSearching(false);
      return;
    }
    const timer = setTimeout(async () => {
      searchAbortRef.current?.abort();
      const controller = new AbortController();
      searchAbortRef.current = controller;
      setIsSearching(true);
      try {
        const results = await api.searchCompanies(q, 5, {
          fallback: false,
          signal: controller.signal,
        });
        startTransition(() => {
          setCompanyResults(results);
        });
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }
        startTransition(() => {
          setCompanyResults([]);
        });
      } finally {
        if (searchAbortRef.current === controller) {
          setIsSearching(false);
        }
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [companyQuery, selectedCompany]);

  useEffect(() => {
    return () => {
      searchAbortRef.current?.abort();
    };
  }, []);

  function selectCompany(company: CompanyBasic) {
    setSelectedCompany(company);
    setCompanyQuery(company.name);
    setCompanyResults([]);
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
        <Alert severity="success" sx={{ mb: 3 }}>
          저장되었습니다. 홈으로 이동합니다...
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        {/* 현재 회사 */}
        <div className="flex flex-col gap-1">
          <Autocomplete
            options={companyResults}
            forcePopupIcon={false}
            getOptionLabel={(option) => option.name}
            isOptionEqualToValue={(option, value) => option.seq === value.seq}
            value={selectedCompany}
            inputValue={companyQuery}
            onInputChange={(_, value, reason) => {
              if (reason === "input") {
                setCompanyQuery(value);
                setSelectedCompany(null);
              }
            }}
            onChange={(_, value) => {
              if (value) selectCompany(value);
            }}
            filterOptions={(x) => x}
            loading={isSearching}
            loadingText="검색 중..."
            noOptionsText={
              companyQuery && !isSearching ? "검색 결과가 없습니다" : "회사명을 입력하세요"
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="현재 회사"
                required
                placeholder="회사명 검색 (예: 카카오, 네이버)"
                size="small"
                sx={{
                  "& .MuiInputBase-input": {
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  },
                }}
              />
            )}
            renderOption={(props, option) => {
              const { key, ...rest } =
                props as React.HTMLAttributes<HTMLLIElement> & { key: React.Key };
              return (
                <li key={key} {...rest} className={`${rest.className ?? ""} flex items-center gap-2`}>
                  <span className="min-w-0 flex-1 truncate font-medium text-[#0f172a]">
                    <HighlightedText text={option.name} query={companyQuery} />
                  </span>
                  {option.industry_name && (
                    <span className="max-w-[34%] flex-shrink truncate text-xs text-[#94a3b8]">
                      {option.industry_name}
                    </span>
                  )}
                  {option.employee_count != null && (
                    <span className="flex-shrink-0 text-xs text-[#94a3b8]">
                      · {option.employee_count.toLocaleString()}명
                    </span>
                  )}
                </li>
              );
            }}
          />
          {selectedCompany && (
            <p className="text-xs text-[#10b981]">✓ {selectedCompany.name} 선택됨</p>
          )}
          {!selectedCompany && companyQuery.trim() !== "" && !isSearching && companyResults.length === 0 && (
            <p className="text-xs text-[#f59e0b]">
              검색 결과가 없습니다. 다른 이름으로 검색해보세요.
            </p>
          )}
        </div>

        {/* 직무 */}
        <TextField
          label="직무"
          required
          size="small"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="예: 프론트엔드 개발자, 마케터, 기획자"
        />

        {/* 연차 */}
        <TextField
          select
          label="연차"
          required
          size="small"
          value={yearsOfExp}
          onChange={(e) => setYearsOfExp(e.target.value)}
        >
          {EXP_OPTIONS.map((opt) => (
            <MenuItem key={opt.value} value={opt.value} disabled={opt.value === ""}>
              {opt.label}
            </MenuItem>
          ))}
        </TextField>

        {/* 학력 */}
        <TextField
          select
          label="학력 (선택)"
          size="small"
          value={education}
          onChange={(e) => setEducation(e.target.value)}
        >
          {EDUCATION_OPTIONS.map((opt) => (
            <MenuItem key={opt.value} value={opt.value}>
              {opt.label}
            </MenuItem>
          ))}
        </TextField>

        {/* 성별 */}
        <TextField
          select
          label="성별 (선택)"
          size="small"
          value={gender}
          onChange={(e) => setGender(e.target.value)}
        >
          {GENDER_OPTIONS.map((opt) => (
            <MenuItem key={opt.value} value={opt.value}>
              {opt.label}
            </MenuItem>
          ))}
        </TextField>

        <div className="flex gap-3 pt-1">
          <Button
            variant="outlined"
            type="button"
            onClick={() => router.push("/")}
          >
            취소
          </Button>
          <Button
            variant="contained"
            type="submit"
            disabled={!canSubmit || saved}
            fullWidth
          >
            저장하기
          </Button>
        </div>
      </form>
    </div>
  );
}
