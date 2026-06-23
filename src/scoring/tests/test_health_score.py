from __future__ import annotations

import unittest

from src.db.models import Company, CompanyMonthlyStats
from src.scoring.health_score import calculate_health_score
from src.scoring.recommendation import (
    calculate_recommendation,
    recommend_from_raw,
)
from src.scoring.schemas import HealthScoreResult, RecommendationResult


def _make_company(seq=1, name="테스트회사", employee_count=100, charge=20_000_000):
    return Company(
        seq=seq,
        name=name,
        employee_count=employee_count,
        monthly_charge_amt=charge,
    )


def _make_stats(seq, start_count, monthly_delta, months=12, joiners=5, leavers=2):
    """start_count부터 매월 monthly_delta만큼 변하는 월별 통계 생성."""
    stats = []
    count = start_count
    for i in range(months):
        ym = f"2025{i + 1:02d}" if i < 9 else f"2025{i + 1:02d}"
        # year_month는 정렬 가능한 문자열이면 충분
        ym = f"2025-{i + 1:02d}"
        stats.append(
            CompanyMonthlyStats(
                seq=seq,
                year_month=ym,
                employee_count=count,
                new_joiners=joiners,
                leavers=leavers,
            )
        )
        count += monthly_delta
    return stats


class TestHealthScoreNormal(unittest.TestCase):
    def test_growing_company_returns_full_result(self):
        company = _make_company(employee_count=140)
        stats = _make_stats(1, start_count=100, monthly_delta=5, joiners=8, leavers=2)
        result = calculate_health_score(company, stats)

        self.assertIsInstance(result, HealthScoreResult)
        self.assertTrue(0 <= result.total <= 100)
        self.assertTrue(0 <= result.growth <= 35)
        self.assertTrue(0 <= result.stability <= 30)
        self.assertTrue(0 <= result.hiring_activity <= 15)
        self.assertTrue(0 <= result.size_fit <= 10)
        self.assertTrue(0 <= result.salary_signal <= 10)
        self.assertLessEqual(result.risk_penalty, 0)
        self.assertIn("growth", result.breakdown)
        self.assertEqual(result.breakdown["months_available"], 12)
        self.assertIn(
            result.grade, {"매우 좋음", "좋음", "보통", "주의", "위험"}
        )

    def test_growing_company_scores_higher_than_shrinking(self):
        company = _make_company()
        growing = calculate_health_score(
            company, _make_stats(1, 100, 6, joiners=10, leavers=1)
        )
        shrinking = calculate_health_score(
            company, _make_stats(2, 160, -6, joiners=1, leavers=10)
        )
        self.assertGreater(growing.total, shrinking.total)

    def test_salary_signal_flagged_as_reference(self):
        company = _make_company(employee_count=100, charge=20_000_000)
        result = calculate_health_score(company, _make_stats(1, 100, 1))
        self.assertTrue(
            result.breakdown["salary_signal"].get("is_reference_only")
        )


class TestHealthScorePartial(unittest.TestCase):
    def test_no_monthly_stats_returns_partial(self):
        company = _make_company(employee_count=80, charge=15_000_000)
        result = calculate_health_score(company, None)

        self.assertIsInstance(result, HealthScoreResult)
        self.assertTrue(0 <= result.total <= 100)
        self.assertFalse(result.breakdown["has_monthly_stats"])
        self.assertEqual(result.breakdown["months_available"], 0)
        # 부분 점수: 성장성/안정성 중립 점수가 들어감
        self.assertGreater(result.growth, 0)
        self.assertGreater(result.stability, 0)
        # 채용 활성도는 데이터 없으면 0
        self.assertEqual(result.hiring_activity, 0)

    def test_empty_list_treated_as_no_stats(self):
        company = _make_company()
        result = calculate_health_score(company, [])
        self.assertFalse(result.breakdown["has_monthly_stats"])


class TestHealthScoreNoneSafety(unittest.TestCase):
    def test_company_with_none_fields(self):
        company = Company(
            seq=99,
            name="결측회사",
            employee_count=None,
            monthly_charge_amt=None,
        )
        result = calculate_health_score(company, None)
        self.assertIsInstance(result, HealthScoreResult)
        self.assertTrue(0 <= result.total <= 100)

    def test_stats_with_none_values(self):
        company = _make_company()
        stats = [
            CompanyMonthlyStats(
                seq=1, year_month="2025-01",
                employee_count=None, new_joiners=None, leavers=None,
            ),
            CompanyMonthlyStats(
                seq=1, year_month="2025-02",
                employee_count=50, new_joiners=None, leavers=None,
            ),
            CompanyMonthlyStats(
                seq=1, year_month="2025-03",
                employee_count=None, new_joiners=3, leavers=None,
            ),
        ]
        result = calculate_health_score(company, stats)
        self.assertIsInstance(result, HealthScoreResult)
        self.assertTrue(0 <= result.total <= 100)

    def test_none_in_stats_iterable_is_skipped(self):
        company = _make_company()
        stats = _make_stats(1, 100, 2) + [None]  # None 항목 포함
        result = calculate_health_score(company, stats)
        self.assertIsInstance(result, HealthScoreResult)


class TestRiskPenalty(unittest.TestCase):
    def test_sharp_decline_penalized(self):
        company = _make_company()
        # 100 -> 50 급격한 감소 (>20%) + 연속 감소
        stats = _make_stats(1, 100, -15, months=4)
        result = calculate_health_score(company, stats)
        self.assertLess(result.risk_penalty, 0)


class TestRecommendation(unittest.TestCase):
    def _build(self, current_total_high: bool):
        company = _make_company()
        good = calculate_health_score(
            company, _make_stats(1, 100, 6, joiners=10, leavers=1)
        )
        bad = calculate_health_score(
            company, _make_stats(2, 160, -6, joiners=1, leavers=12)
        )
        return good, bad

    def test_strong_recommend_when_target_much_better(self):
        good, bad = self._build(False)
        rec = calculate_recommendation(current=bad, target=good)
        self.assertIsInstance(rec, RecommendationResult)
        self.assertTrue(0 <= rec.score <= 100)
        self.assertIn(rec.verdict, {"강력 추천", "추천"})
        self.assertGreater(rec.summary["total_diff"], 0)

    def test_not_recommend_when_target_worse(self):
        good, bad = self._build(False)
        rec = calculate_recommendation(current=good, target=bad)
        self.assertIn(rec.verdict, {"비추천", "중립"})

    def test_salary_change_signal_reference(self):
        cur_co = _make_company(seq=1, charge=15_000_000)
        tgt_co = _make_company(seq=2, charge=22_000_000)
        cur = calculate_health_score(cur_co, _make_stats(1, 100, 2))
        tgt = calculate_health_score(tgt_co, _make_stats(2, 120, 3))
        rec = calculate_recommendation(cur, tgt, cur_co, tgt_co)
        self.assertEqual(rec.salary_change_signal, 7_000_000)
        self.assertIn("salary_change_note", rec.summary)

    def test_recommend_from_raw_end_to_end(self):
        cur_co = _make_company(seq=1, charge=15_000_000)
        tgt_co = _make_company(seq=2, charge=20_000_000)
        rec = recommend_from_raw(
            cur_co, _make_stats(1, 160, -5, joiners=1, leavers=10),
            tgt_co, _make_stats(2, 100, 6, joiners=10, leavers=1),
        )
        self.assertIsInstance(rec, RecommendationResult)
        self.assertTrue(0 <= rec.score <= 100)


if __name__ == "__main__":
    unittest.main()
