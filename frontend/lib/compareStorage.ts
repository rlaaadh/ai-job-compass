import type { CompanyBasic } from "./types";

const COMPARE_STORAGE_KEY = "compareCompanies";
export const COMPARE_STORAGE_EVENT = "compare-companies-updated";

function isCompanyBasic(value: unknown): value is CompanyBasic {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.seq === "number" &&
    typeof candidate.name === "string" &&
    ("address" in candidate) &&
    ("industry_name" in candidate) &&
    ("employee_count" in candidate) &&
    ("join_status" in candidate)
  );
}

export function loadCompareCompanies(): CompanyBasic[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(COMPARE_STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(isCompanyBasic).slice(0, 2);
  } catch {
    return [];
  }
}

export function saveCompareCompanies(companies: CompanyBasic[]): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    COMPARE_STORAGE_KEY,
    JSON.stringify(companies.slice(0, 2)),
  );
  window.dispatchEvent(new Event(COMPARE_STORAGE_EVENT));
}
