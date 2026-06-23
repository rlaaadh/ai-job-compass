// grade / verdict → 색상 매핑 (디자인 스펙 기준)

export function gradeColor(grade: string): string {
  switch (grade) {
    case "매우 좋음":
      return "#10b981"; // 초록
    case "좋음":
      return "#3b82f6"; // 파랑
    case "보통":
      return "#f59e0b"; // 노랑
    case "주의":
      return "#f97316"; // 주황
    case "위험":
      return "#ef4444"; // 빨강
    default:
      return "#64748b"; // 보조
  }
}

export function verdictColor(verdict: string): string {
  switch (verdict) {
    case "강력 추천":
      return "#10b981";
    case "추천":
      return "#3b82f6";
    case "중립":
      return "#64748b";
    case "비추천":
      return "#ef4444";
    default:
      return "#64748b";
  }
}

// 점수(0-100) → grade 문자열 (백엔드가 grade를 안 줄 때 fallback)
export function scoreToGrade(score: number): string {
  if (score >= 80) return "매우 좋음";
  if (score >= 65) return "좋음";
  if (score >= 50) return "보통";
  if (score >= 35) return "주의";
  return "위험";
}
