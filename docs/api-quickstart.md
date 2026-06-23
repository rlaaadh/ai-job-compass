# NPS API Quickstart

## Environment variable

Fill in `.env`:

```env
NPS_API_KEY=your_key_here
```

## Quick test commands

Search company basic info:

```bash
rtk python3 scripts/test_nps_api.py establishment-basic --name 카카오
```

Get company detail with `seq`:

```bash
rtk python3 scripts/test_nps_api.py establishment-detail --seq 1
```

Get monthly hiring/leaving counts:

```bash
rtk python3 scripts/test_nps_api.py establishment-period --seq 1 --year-month 202501
```

Search withdrawn establishments:

```bash
rtk python3 scripts/test_nps_api.py withdrawn-basic --name 카카오
```

Save raw JSON for later ETL work:

```bash
rtk python3 scripts/test_nps_api.py establishment-basic --name 카카오 --save data/raw/sample-establishment.json
```

## Recommended workflow

1. Run `establishment-basic` with a known company name.
2. Copy the returned `seq`.
3. Run `establishment-detail` and `establishment-period`.
4. Save example responses into `data/raw/` before designing the database schema.
