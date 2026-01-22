import csv
import sys
from PyQt6.QtWidgets import QApplication
from dashboard import ParticleDashboard

import serial
import serial.tools.list_ports

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--sim", action="store_true", help="Run with simulated hardware signals")
args = parser.parse_args()

# Entry Point
if __name__ == "__main__":
    if args.sim:
        print("MODE: SIMULATION (unittest.mock)")
        from unittest.mock import patch
        from tests.mock_serial import create_mock_serial

        patcher = patch('serial.Serial', return_value=create_mock_serial())
        patcher.start()
    else:
        print("MODE: REAL HARDWARE")

    # 1. Create the Application
    app = QApplication(sys.argv)

    # 2. Create the Window
    window = ParticleDashboard()
    window.show()

    # 3. Run the Event Loop
    sys.exit(app.exec())
