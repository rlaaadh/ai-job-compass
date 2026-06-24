// API 응답 타입 — FastAPI 백엔드 src/api/schemas.py와 일치

export interface CompanyBasic {
  seq: number
  name: string
  address: string | null
  industry_name: string | null
  employee_count: number | null
  join_status: string | null
}

export interface AIReport {
  summary: string
  growth_comment: string
  stability_comment: string
  hiring_comment: string
}

export interface MonthlyEmployeeStat {
  year_month: string
  employee_count: number
  new_joiners: number
  leavers: number
}

export interface HealthScore {
  seq: number
  name: string
  employee_count: number | null
  health_score: number       // 0-100
  grade: string              // 매우 좋음 / 좋음 / 보통 / 주의 / 위험
  growth: number             // 0-35
  stability: number          // 0-30
  hiring_activity: number    // 0-15
  size_fit: number           // 0-10
  salary_signal: number      // 0-10 (참고값)
  recent_employee_change_pct: number | null
  monthly_employee_stats: MonthlyEmployeeStat[]
  breakdown: Record<string, unknown>
  ai_report: AIReport | null
}

export interface RecommendationReport {
  summary: string
  risk_comment: string
  salary_comment: string
}

export interface CompareResult {
  recommendation_score: number   // 0-100
  verdict: string                // 강력 추천 / 추천 / 중립 / 비추천
  current: HealthScore
  target: HealthScore
  salary_change_signal: number   // 참고값
  ai_report: RecommendationReport | null
}

export interface CompareRequest {
  current_seq: number
  target_seq: number
  role?: string | null
}

export interface UserProfile {
  company: CompanyBasic
  role: string
  yearsOfExp: number | null
  education: string | null
  gender: string | null
}
