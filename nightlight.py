"""
Nightlight mode entry point.

Run with:
    python nightlight.py
"""

from src.nightlight import NightLightController


def main() -> None:
    NightLightController().run()


if __name__ == "__main__":
    main()
