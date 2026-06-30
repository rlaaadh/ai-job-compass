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
        industry_name=None,
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
        self.assertTrue(0 <= result.growth <= 40)
        self.assertTrue(0 <= result.stability <= 35)
        self.assertEqual(result.hiring_activity, 0)
        self.assertTrue(0 <= result.size_fit <= 25)
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

    def test_salary_signal_included_as_reference_breakdown(self):
        company = _make_company(employee_count=100, charge=20_000_000)
        result = calculate_health_score(company, _make_stats(1, 100, 1))
        self.assertIn("salary_signal", result.breakdown)
        self.assertFalse(result.breakdown["salary_signal"]["included_in_total"])
        self.assertGreater(result.salary_signal, 0)

    def test_company_size_score_reflects_employee_scale(self):
        medium_company = _make_company(seq=1, name="중소", employee_count=41)
        larger_company = _make_company(seq=2, name="중견", employee_count=531)

        medium_score = calculate_health_score(
            medium_company,
            _make_stats(1, start_count=41, monthly_delta=0, joiners=1, leavers=1),
        )
        larger_score = calculate_health_score(
            larger_company,
            _make_stats(2, start_count=531, monthly_delta=0, joiners=3, leavers=3),
        )

        self.assertGreaterEqual(larger_score.size_fit - medium_score.size_fit, 3)

    def test_company_size_score_uses_company_employee_count(self):
        company = _make_company(seq=1, name="테스트", employee_count=41)
        stats = _make_stats(1, start_count=900, monthly_delta=0, joiners=2, leavers=2)

        result = calculate_health_score(company, stats)

        self.assertEqual(result.size_fit, 8)
        self.assertEqual(result.breakdown["size_fit"]["employee_count"], 41)

    def test_salary_signal_does_not_change_total_score(self):
        base_stats = _make_stats(1, start_count=100, monthly_delta=0, joiners=3, leavers=3)
        low_salary_company = _make_company(seq=1, employee_count=100, charge=9_000_000)
        high_salary_company = _make_company(seq=2, employee_count=100, charge=30_000_000)

        low_salary_score = calculate_health_score(low_salary_company, base_stats)
        high_salary_score = calculate_health_score(high_salary_company, base_stats)

        self.assertNotEqual(low_salary_score.salary_signal, high_salary_score.salary_signal)
        self.assertEqual(low_salary_score.total, high_salary_score.total)


class TestHealthScorePartial(unittest.TestCase):
    def test_no_monthly_stats_returns_partial(self):
        company = _make_company(employee_count=80, charge=15_000_000)
        result = calculate_health_score(company, None)

        self.assertIsInstance(result, HealthScoreResult)
        self.assertTrue(0 <= result.total <= 100)
        self.assertFalse(result.breakdown["has_monthly_stats"])
        self.assertEqual(result.breakdown["months_available"], 0)
        # 부분 점수: 성장성/안정성/기업규모 기준 점수가 들어감
        self.assertGreater(result.growth, 0)
        self.assertGreater(result.stability, 0)
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
        self.assertEqual(rec.salary_change_signal, 9_333_333)
        self.assertIn("salary_change_note", rec.summary)

    def test_role_fit_boost_for_frontend_platform_company(self):
        current_co = _make_company(
            seq=1,
            name="식품회사",
            employee_count=100,
            charge=15_000_000,
        )
        current_co.industry_name = "기타 식품 제조업"
        target_co = _make_company(
            seq=2,
            name="플랫폼회사",
            employee_count=100,
            charge=15_000_000,
        )
        target_co.industry_name = "응용 소프트웨어 개발 및 공급업"

        current = calculate_health_score(current_co, _make_stats(1, 100, 1))
        target = calculate_health_score(target_co, _make_stats(2, 100, 1))
        rec = calculate_recommendation(
            current,
            target,
            current_co,
            target_co,
            role="프론트엔드개발",
        )

        self.assertGreater(rec.role_fit_delta, 0)
        self.assertGreaterEqual(rec.score, 56)

    def test_salary_decrease_penalizes_recommendation(self):
        current_co = _make_company(seq=1, charge=30_000_000, employee_count=100)
        target_co = _make_company(seq=2, charge=15_000_000, employee_count=100)
        current_co.industry_name = "응용 소프트웨어 개발 및 공급업"
        target_co.industry_name = "응용 소프트웨어 개발 및 공급업"

        current = calculate_health_score(current_co, _make_stats(1, 100, 1))
        target = calculate_health_score(target_co, _make_stats(2, 100, 1))
        rec = calculate_recommendation(
            current,
            target,
            current_co,
            target_co,
            role="프론트엔드개발",
        )

        self.assertLess(rec.salary_change_signal, 0)
        self.assertLess(rec.summary["salary_adjustment"], 0)

    def test_large_salary_increase_can_push_recommendation_positive(self):
        current_co = _make_company(seq=1, charge=15_000_000, employee_count=100)
        target_co = _make_company(seq=2, charge=26_250_000, employee_count=100)
        current_co.industry_name = "응용 소프트웨어 개발 및 공급업"
        target_co.industry_name = "응용 소프트웨어 개발 및 공급업"

        current = HealthScoreResult(
            total=58,
            growth=20,
            stability=18,
            hiring_activity=0,
            size_fit=6,
            salary_signal=0,
            risk_penalty=0,
            breakdown={},
            grade="보통",
        )
        target = HealthScoreResult(
            total=54,
            growth=19,
            stability=17,
            hiring_activity=0,
            size_fit=6,
            salary_signal=0,
            risk_penalty=0,
            breakdown={},
            grade="보통",
        )

        rec = calculate_recommendation(
            current,
            target,
            current_co,
            target_co,
            role="프론트엔드개발",
        )

        self.assertGreaterEqual(rec.salary_change_signal, 15_000_000)
        self.assertGreaterEqual(rec.summary["salary_adjustment"], 10)
        self.assertIn(rec.verdict, {"추천", "강력 추천"})

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
