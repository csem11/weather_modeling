"""
Long-running loop: every N hours, check if today's gas price data exists and fetch if not.

Used by: python main.py run [--interval HOURS] [--data-dir PATH]
"""

from weather_modeling.cli.run_loop import parse_run_args, run_indefinitely

if __name__ == "__main__":
    data_dir, interval = parse_run_args()
    run_indefinitely(data_dir=data_dir, interval_hours=interval)
