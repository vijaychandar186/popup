"""
PopUp Wellness Monitor — entry point.

Run with:
    python main.py
"""

from src.monitor import EyeStrainMonitor


def main() -> None:
    monitor = EyeStrainMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
