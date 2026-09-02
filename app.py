"""
NeuroFence desktop entry point.

Usage:
    python app.py
"""

import logging
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("NeuroFence")
    app.setOrganizationName("NeuroFence Security")

    # Use a cleaner default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
