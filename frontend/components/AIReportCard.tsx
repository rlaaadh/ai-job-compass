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

export default function AIReportCard({ report, type }: AIReportCardProps) {
  if (!report) return null;

  const sections: Section[] = isRecommendation(report, type)
    ? [
        { label: "리스크", text: report.risk_comment },
        {
          label: "연봉",
          text: report.salary_comment,
          note: "참고값, 실제 급여와 다를 수 있음",
        },
      ]
    : [
        { label: "성장성", text: report.growth_comment },
        { label: "안정성", text: report.stability_comment },
        { label: "채용 활동", text: report.hiring_comment },
      ];

  return (
    <section className="rounded-xl border border-[#e2e8f0] bg-[#f8fafc] p-5">
      <div className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-[#eff6ff] px-3 py-1 text-xs font-semibold text-[#3b82f6]">
        <span aria-hidden>✨</span>
        AI 분석
      </div>

      <p className="text-[15px] leading-relaxed text-[#0f172a]">
        {report.summary}
      </p>

      <div className="mt-4 flex flex-col gap-3">
        {sections.map((s) => (
          <div
            key={s.label}
            className="rounded-lg border border-[#e2e8f0] bg-white p-3"
          >
            <div className="mb-1 text-xs font-semibold text-[#64748b]">
              {s.label}
              {s.note && (
                <span className="ml-1 font-normal text-[#94a3b8]">
                  ({s.note})
                </span>
              )}
            </div>
            <p className="text-sm leading-relaxed text-[#334155]">{s.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
