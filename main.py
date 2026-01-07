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
        self.resize(800, 600)

        # 2. The Central Layout (The "Container")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # 3. Add a placeholder widget (Just to see something)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-color: yellow; color: red; font-size: 60px; font-weight:bold;")
        # Add styles (CSS-like syntax is supported in Qt)
        self.label.setText("System ready to acquire data")
        self.layout.addWidget(self.label)
       
        # plot widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w')
        self.graph_widget.setTitle("Real-Time Detector Output", color="k", size="15pt")
        self.graph_widget.setLabel('left', 'Flux Intensity', units='counts/s')
        self.graph_widget.setLabel('bottom', 'Time Sample')
        self.graph_widget.showGrid(x=True, y=True)

        self.data_buffer =[]
        self.data_line = self.graph_widget.plot([], [], pen=pg.mkPen(color='b', width=2))
        self.layout.addWidget(self.graph_widget)


        # Crete a control Button
        self.btn_start = QPushButton("start acquisition")
        self.btn_start.setStyleSheet("font-size: 18px; padding: 10px")
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.toggle_acquisition)
        self.layout.addWidget(self.btn_start)

        # Initialize the Worker
        self.worker = SensorWorker()

        # Connect the "Bell" to a function in the GUI
        self.worker.data_signal.connect(self.update_display)
        print("DEBUG: signal connected successfully")

    # Logic functions

    def toggle_acquisition(self):
        #check if button is pressed or released

        if self.btn_start.isChecked():
            self.btn_start.setText("Stop Acquisition")
            self.label.setText("System acquiring data")
            self.worker.is_running = True
            self.worker.start()
        else:
            self.btn_start.setText("Start Acquisition")
            self.label.setText("System ready to acquire data")
            self.worker.stop()

    def update_display(self, val):
        #this function receives the data from signal
        self.data_buffer.append(val)
        if len(self.data_buffer) > 100:
            self.data_buffer.pop(0)

        self.data_line.setData(self.data_buffer)

# Entry Point
if __name__ == "__main__":
    # 1. Create the Application
    app = QApplication(sys.argv)

    # 2. Create the Window
    window = ParticleDashboard()
    window.show()

    # 3. Run the Event Loop
    sys.exit(app.exec())
