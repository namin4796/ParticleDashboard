import csv
from datetime import datetime
import sys
import time
import random
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
import pyqtgraph as pg

def read_sensor_data():
    if random.random() < 0.1:
        return None

    return random.gauss(100, 5);

# --- THE CHEF (Background Worker) ---
class SensorWorker(QThread):
    data_signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.is_running = True

    
    def run(self):
        print("Sensor started... press Ctrl+C to stop")
        while self.is_running:
            try:
                #simulate reading a sensor
                simulated_data = read_sensor_data()
                    
                if simulated_data is None:
                    print("[WARNING] Sensor signal lost ... waiting for reconnect.")
                else:
                    print(f"incoming data: {simulated_data:.2f}")
                    #emit the signal
                    self.data_signal.emit(simulated_data)

                #simulate detector dead time
                time.sleep(0.1)

            except KeyboardInterrupt:
                print("\nDashboard stopped by user")
                break
        print("DEBUG: sensor thread stopped.")

    
    #stop the worker
    def stop(self):
        self.is_running = False

# This is our Main Application Class
class ParticleDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Window Setup
        self.setWindowTitle("Particle Flux Monitor - v1.0")
        self.resize(900, 600)

        # --- GLOBAL STYLESHEET ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                }
            QLabel {
                color: #0aac00;
                font-family: "Consolas", "Courier New", monospace;
                }
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #e74c3c;
            }
        """)
    
        # 2. The Central Layout (The "Container")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # 3. Add a placeholder widget (Just to see something)
        self.label = QLabel("SYSTEM READY")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add styles (CSS-like syntax is supported in Qt)
        self.label.setStyleSheet("font-size: 24px; margin-bottom: 10px;")
        self.layout.addWidget(self.label)
       
        # plot widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#1e1e1e')
        self.graph_widget.setTitle("Real-Time Detector Output", color="#bdc3c7", size="12pt")

        styles = {'color': '#bdc3c7', 'font-size': '12px'}
        self.graph_widget.setLabel('left', 'Flux Intensity', units='counts/s', **styles)
        self.graph_widget.setLabel('bottom', 'Time Sample', **styles)
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)

        self.data_buffer =[]
        self.data_line = self.graph_widget.plot([], [], pen=pg.mkPen(color='#00e5ff', width=2))
        self.layout.addWidget(self.graph_widget)


        # Crete a control Button
        self.btn_start = QPushButton("INITIALIZE ACQUISITION")
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.toggle_acquisition)
        self.layout.addWidget(self.btn_start)

        # Initialize the Worker
        self.worker = SensorWorker()

        # Connect the "Bell" to a function in the GUI
        self.worker.data_signal.connect(self.update_display)

        #log file
        self.csv_file = None
        self.csv_write = None

    # Logic functions

    def toggle_acquisition(self):
        #check if button is pressed or released

        if self.btn_start.isChecked():
            self.btn_start.setText("HALT ACQUISITION")
            self.label.setText(">>> ACQUIRING DATA <<<")
            self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")

            #create a unique filename based on current time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"particle_log_{timestamp}.csv"

            self.csv_file = open(filename, mode='w', newline='')
            self.csv_writer = csv.writer(self.csv_file)

            self.csv_writer.writerow(["Timestamp", "Flux_Value"])
            print(f"DEBUG: Recording to {filename}")
            self.worker.is_running = True
            self.worker.start()
        else:
            self.btn_start.setText("INITIALIZE ACQUISITION")
            self.label.setText("SYSTEM READY")
            self.label.setStyleSheet("color: #ecf0f1; font-size: 24px;")
            self.worker.stop()

            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
                print("DEBUG: File closed safely.")

    def update_display(self, val):
        #this function receives the data from signal
        self.data_buffer.append(val)
        if len(self.data_buffer) > 100:
            self.data_buffer.pop(0)

        self.data_line.setData(self.data_buffer)

        if self.csv_writer:
            current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.csv_writer.writerow([current_time, val])

# Entry Point
if __name__ == "__main__":
    # 1. Create the Application
    app = QApplication(sys.argv)

    # 2. Create the Window
    window = ParticleDashboard()
    window.show()

    # 3. Run the Event Loop
    sys.exit(app.exec())
