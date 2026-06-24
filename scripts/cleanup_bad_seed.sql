-- Supabase SQL Editor에서 실행 가능한 정리 SQL 예시
-- 검색 시드 과정에서 원치 않는 레코드(공사명/일용직/현장명 등)를 제거할 때 사용

DELETE FROM company_search_aliases
WHERE seq IN (
  SELECT seq
  FROM companies
  WHERE
    name ILIKE '%일용%'
    OR name ILIKE '%공사%'
    OR name ILIKE '%현장%'
    OR name ILIKE '%유지보수%'
    OR name ILIKE '%개발사업%'
    OR name ILIKE '%본사부지%'
);

DELETE FROM company_monthly_stats
WHERE seq IN (
  SELECT seq
  FROM companies
  WHERE
    name ILIKE '%일용%'
    OR name ILIKE '%공사%'
    OR name ILIKE '%현장%'
    OR name ILIKE '%유지보수%'
    OR name ILIKE '%개발사업%'
    OR name ILIKE '%본사부지%'
);

DELETE FROM companies
WHERE
  name ILIKE '%일용%'
  OR name ILIKE '%공사%'
  OR name ILIKE '%현장%'
  OR name ILIKE '%유지보수%'
  OR name ILIKE '%개발사업%'
  OR name ILIKE '%본사부지%';
