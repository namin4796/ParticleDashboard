import csv
import sys
from PyQt6.QtWidgets import QApplication
from dashboard import ParticleDashboard

import serial
import serial.tools.list_ports

# Entry Point
if __name__ == "__main__":
    # 1. Create the Application
    app = QApplication(sys.argv)

    # 2. Create the Window
    window = ParticleDashboard()
    window.show()

    # 3. Run the Event Loop
    sys.exit(app.exec())
