"""
Collect U.S. Treasury daily yield curve data and save to data/treasury_yield_curve.csv.

  python collect_treasury.py              # Latest (current + previous month)
  python collect_treasury.py --backfill   # Historical from config start year
  python collect_treasury.py --backfill --start-year 2015
"""

from weather_modeling.cli.collect_treasury import main

if __name__ == "__main__":
    main()
