"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  COMPARE_STORAGE_EVENT,
  loadCompareCompanies,
} from "@/lib/compareStorage";
import type { CompanyBasic } from "@/lib/types";

function buildCompareHref(companies: CompanyBasic[]): string {
  if (companies.length < 2) {
    return "/compare";
  }

  const [current, target] = companies;
  return `/compare?current=${current.seq}&target=${target.seq}`;
}

function isSameCompanyList(a: CompanyBasic[], b: CompanyBasic[]): boolean {
  if (a.length !== b.length) {
    return false;
  }

  return a.every((company, index) => {
    const other = b[index];
    return (
      other != null &&
      company.seq === other.seq &&
      company.name === other.name &&
      company.employee_count === other.employee_count
    );
  });
}

export default function HeaderNav() {
  const [compareCompanies, setCompareCompanies] = useState<CompanyBasic[]>([]);

  useEffect(() => {
    function syncCompareCompanies() {
      const nextCompanies = loadCompareCompanies();
      setCompareCompanies((prev) => (
        isSameCompanyList(prev, nextCompanies) ? prev : nextCompanies
      ));
    }

    syncCompareCompanies();
    window.addEventListener("storage", syncCompareCompanies);
    window.addEventListener(COMPARE_STORAGE_EVENT, syncCompareCompanies);

    return () => {
      window.removeEventListener("storage", syncCompareCompanies);
      window.removeEventListener(COMPARE_STORAGE_EVENT, syncCompareCompanies);
    };
  }, []);

  return (
    <div className="flex items-center gap-1">
      <Link
        href="/"
        className="rounded-md px-3 py-1.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9] hover:text-[#0f172a]"
      >
        홈
      </Link>
      <Link
        href={buildCompareHref(compareCompanies)}
        className="rounded-md px-3 py-1.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9] hover:text-[#0f172a]"
      >
        비교하기
      </Link>
      <Link
        href="/profile"
        className="ml-1 rounded-md bg-[#eff6ff] px-3 py-1.5 text-sm font-medium text-[#3b82f6] transition-colors hover:bg-[#dbeafe]"
      >
        내 정보
      </Link>
    </div>
  );
}
