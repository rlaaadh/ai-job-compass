"use client";

import Link from "next/link";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
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
    <Card variant="outlined" sx={{ display: "flex", flexDirection: "column", gap: 0 }}>
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-base font-semibold text-[#0f172a]">
            {company.name}
          </h3>
          {company.industry_name && (
            <Chip
              label={company.industry_name}
              size="small"
              color="primary"
              variant="outlined"
              sx={{ flexShrink: 0 }}
            />
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
      </CardContent>

      <CardContent sx={{ pt: 0, display: "flex", gap: 1 }}>
        <Button
          variant="contained"
          size="small"
          component={Link}
          href={`/companies/${company.seq}`}
          fullWidth
        >
          건강도 보기
        </Button>
        {onAddToCompare && (
          <Button
            variant="outlined"
            size="small"
            onClick={() => onAddToCompare(company)}
            disabled={!isInCompare && compareDisabled}
            color={isInCompare ? "success" : "primary"}
            sx={{ whiteSpace: "nowrap", minWidth: 104 }}
          >
            {isInCompare ? "✓ 선택됨" : "비교 추가"}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
