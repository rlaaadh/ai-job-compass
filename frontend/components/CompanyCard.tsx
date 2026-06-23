"use client";

import Link from "next/link";
import type { CompanyBasic } from "@/lib/types";

interface CompanyCardProps {
  company: CompanyBasic;
  onAddToCompare?: (company: CompanyBasic) => void;
  isInCompare?: boolean;
  compareDisabled?: boolean;
}

export default function CompanyCard({
  company,
  onAddToCompare,
  isInCompare = false,
  compareDisabled = false,
}: CompanyCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-4 transition-shadow hover:shadow-sm">
      <div>
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-semibold text-[#0f172a]">
            {company.name}
          </h3>
          {company.industry_name && (
            <span className="shrink-0 rounded-full bg-[#eff6ff] px-2.5 py-0.5 text-xs font-medium text-[#3b82f6]">
              {company.industry_name}
            </span>
          )}
        </div>
        {company.address && (
          <p className="mt-1 text-sm text-[#64748b]">{company.address}</p>
        )}
        {company.employee_count != null && (
          <p className="mt-0.5 text-xs text-[#94a3b8]">
            직원 수 약 {company.employee_count.toLocaleString()}명
          </p>
        )}
      </div>

      <div className="flex gap-2">
        <Link
          href={`/companies/${company.seq}`}
          className="flex-1 rounded-lg bg-[#3b82f6] px-3 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-[#2563eb]"
        >
          건강도 보기
        </Link>
        {onAddToCompare && (
          <button
            type="button"
            onClick={() => onAddToCompare(company)}
            disabled={!isInCompare && compareDisabled}
            className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
              isInCompare
                ? "border-[#10b981] bg-[#ecfdf5] text-[#10b981]"
                : compareDisabled
                  ? "cursor-not-allowed border-[#e2e8f0] bg-[#f1f5f9] text-[#cbd5e1]"
                  : "border-[#e2e8f0] bg-white text-[#64748b] hover:border-[#3b82f6] hover:text-[#3b82f6]"
            }`}
          >
            {isInCompare ? "✓ 선택됨" : "비교에 추가"}
          </button>
        )}
      </div>
    </div>
  );
}
