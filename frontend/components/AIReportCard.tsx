import Paper from "@mui/material/Paper";
import Chip from "@mui/material/Chip";
import type { ReactNode } from "react";
import type { AIReport, RecommendationReport } from "@/lib/types";

interface AIReportCardProps {
  report: AIReport | RecommendationReport | null;
  type: "company" | "recommendation";
}

interface Section {
  label: string;
  text: string;
  note?: string;
}

function isRecommendation(
  report: AIReport | RecommendationReport,
  type: "company" | "recommendation"
): report is RecommendationReport {
  return type === "recommendation";
}

function renderSalaryText(text: string): ReactNode {
  const signedMatch = text.match(/([+-])\s?([\d,]+원)/);
  if (signedMatch) {
    const [, sign, amount] = signedMatch;
    const direction = sign === "+" ? "증가" : "감소";
    const replacedText = text.replace(signedMatch[0], `${amount} ${direction}`);
    const marker = `${amount} ${direction}`;
    const parts = replacedText.split(marker);

    return (
      <>
        {parts[0]}
        <strong className="font-bold text-[#dc2626]">
        {amount}{" "}
        {direction}
        </strong>
        {parts[1]}
      </>
    );
  }

  const wordMatch = text.match(/([\d,]+원)\s+(증가|감소)/);
  if (!wordMatch) {
    return text;
  }

  const [, amount, direction] = wordMatch;
  const marker = `${amount} ${direction}`;
  const parts = text.split(marker);

  return (
    <>
      {parts[0]}
      <strong className="font-bold text-[#dc2626]">
      {amount}{" "}
      {direction}
      </strong>
      {parts[1]}
    </>
  );
}

export default function AIReportCard({ report, type }: AIReportCardProps) {
  if (!report) return null;

  const sections: Section[] = isRecommendation(report, type)
    ? [
        { label: "리스크", text: report.risk_comment },
        {
          label: "연봉",
          text: report.salary_comment,
          note: "직무·연차 평균 비교 아님, 국민연금 기반 참고값",
        },
      ]
    : [
        { label: "성장성", text: report.growth_comment },
        { label: "안정성", text: report.stability_comment },
        { label: "채용 활동", text: report.hiring_comment },
      ];

  return (
    <Paper variant="outlined" sx={{ p: 2.5 }}>
      <Chip
        label="✨ AI 분석"
        size="small"
        color="primary"
        variant="outlined"
        sx={{ mb: 1.5, fontWeight: 600 }}
      />

      <p className="text-[15px] leading-relaxed text-[#0f172a]">
        {report.summary}
      </p>

      <div className="mt-4 flex flex-col gap-3">
        {sections.map((s) => (
          <Paper key={s.label} variant="outlined" sx={{ p: 1.5 }}>
            <div className="mb-1 text-xs font-semibold text-[#64748b]">
              {s.label}
              {s.note && (
                <span className="ml-1 font-normal text-[#94a3b8]">
                  ({s.note})
                </span>
              )}
            </div>
            <p className="text-sm leading-relaxed text-[#334155]">
              {type === "recommendation" && s.label === "연봉"
                ? renderSalaryText(s.text)
                : s.text}
            </p>
          </Paper>
        ))}
      </div>
    </Paper>
  );
}
