import sys
import json
import csv
import os
import random
from datetime import datetime
from collections import deque
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QSlider, QCheckBox, QMessageBox)
import pyqtgraph as pg
import pyqtgraph.exporters
from worker import SensorWorker

class ParticleDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Window Setup
        self.setWindowTitle("PySensorFlow Dynamic Dashboard")
        self.resize(1000, 700)

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

        # 1a Load config
        self.load_config("config/setup.json")
    
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
       
        #threshold slider
        self.slider_label = QLabel("Trigger Threshold: 500")
        self.layout.addWidget(self.slider_label)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 1023)
        self.threshold_slider.setValue(500)

        self.threshold_slider.valueChanged.connect(self.update_slider_label)
        self.layout.addWidget(self.threshold_slider)

        # this lets the user choose between Manual Mode and Hardware Mode
        self.chk_hw_sync = QCheckBox("Sync Threshold with Hardware Knob")
        self.chk_hw_sync.setStyleSheet("color: #f1c40f; font-weight: bold;")
        self.chk_hw_sync.setChecked(False) # default is manual mode
        self.layout.addWidget(self.chk_hw_sync)

        self.led_is_on = False
        # dynamic plot widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#1e1e1e')
        self.graph_widget.setTitle("Real-Time Sensor Data", color="#bdc3c7", size="12pt")
        styles = {'color': '#bdc3c7', 'font-size': '12px'}
        self.graph_widget.setLabel('left', 'Raw Signal', units='0-1023', **styles)
        self.graph_widget.setLabel('bottom', 'Time Sample', **styles)
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.addLegend()
        self.layout.addWidget(self.graph_widget)

        # initialize plots dynamically
        #storing plot items in dictionary
        self.buffers = {}
        self.curves = {}


        #define a palette of colors for various sensors
        colors = ['#00e5ff', '#ff5252', '#f1c40f', '#9b59b6', '#2ecc71']

        for i, sensor in enumerate(self.sensor_config):
            s_id = sensor['id']
            s_name = sensor['name']

            #create a bufferfor each 'i'th sensor
            self.buffers[s_id] = deque(maxlen=100)

            #create a curve for this sensor
            color = colors[i % len(colors)]
            curve = self.graph_widget.plot(pen=pg.mkPen(color=color, width=2), name=s_name)
            self.curves[s_id] = curve


        # Create a control Button
        self.btn_start = QPushButton("INITIALIZE ACQUISITION")
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self.toggle_acquisition)
        self.layout.addWidget(self.btn_start)

        #Mode switch Raw <-> voltage
        self.chk_volts = QCheckBox("Show as Volts (0-5V)")
        self.chk_volts.setStyleSheet("color: #ecf0f1; font-size: 14px;")
        self.layout.addWidget(self.chk_volts)

        #smoothing switch
        self.chk_smooth = QCheckBox("Enable Signal Smoothing")
        self.chk_smooth.setStyleSheet("color: #ecf0f1; font-size: 14px;")
        self.layout.addWidget(self.chk_smooth)

        self.smoothing_buffer = deque(maxlen=10)
        self.smoothing_buffer_temp = deque(maxlen=10)

        # save a screenshot button
        self.btn_screenshot = QPushButton("SAVE SNAP")
        self.btn_screenshot.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold")
        self.btn_screenshot.clicked.connect(self.save_screenshot)
        self.layout.addWidget(self.btn_screenshot)

        # save recorded data to csv file
        self.chk_record = QCheckBox("Record to CSV")
        self.chk_record.setStyleSheet("color #aaaaaa;")
        self.layout.addWidget(self.chk_record)

        self.dlg = QMessageBox(self)
        self.dlg.setText("Do you want to save the data?")
        self.dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        self.dlg.setIcon(QMessageBox.Icon.Question)

        #log file

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file = None
        self.csv_write = None
        self.filename = ""

        if not os.path.exists("data"):
            os.makedirs("data")

    def load_config(self, path):
        try:
            with open(path, 'r') as f:
               config = json.load(f)
               self.sensor_config = config.get('sensors', [])
        except Exception as e:
            print(f"Error loading config: {e}")
            self.sensor_config = []

# Logic functions
    
    def toggle_acquisition(self):

        #if self.chk_record.isChecked():

        #check if button is pressed or released 
        if self.btn_start.isChecked():

            if self.chk_record.isChecked():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.filename = f"data/particle_log_{timestamp}.csv"
                try:
                    self.csv_file = open(self.filename, mode='w', newline='')
                    self.csv_write = csv.writer(self.csv_file)
                    self.csv_write.writerow(["Timestamp", "Flux_Value"])
                    print(f"Started recording to: {self.filename}")
                except Exception as e:
                    print(f"Error creating file: {e}")
            else:
                self.csv_file = None
                self.csv_write = None
                
            arduino_port = "/dev/cu.usbmodem14301"
            self.worker = SensorWorker(arduino_port, config_path="config/setup.json")
            self.worker.data_signal.connect(self.update_display)
            
            self.btn_start.setText("HALT ACQUISITION")
            self.label.setText(">>> ACQUIRING DATA <<<")
            self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")

            self.worker.start()

        else:
            self.btn_start.setText("INITIALIZE ACQUISITION")
            self.label.setText("SYSTEM READY")
            self.label.setStyleSheet("color: #ecf0f1; font-size: 24px;")
         #   self.worker.stop()

            if hasattr(self, 'worker'):
                self.worker.stop()
                self.worker.wait()

            if self.csv_file:
                self.csv_file.close()

                self.button = self.dlg.exec()

                if self.button == QMessageBox.StandardButton.Yes:
                    print(f"Recording to {self.filename}")
                elif self.button == QMessageBox.StandardButton.No:
                    print(f"File {self.filename} is deleted")
                    path = os.path.join(os.getcwd(), self.filename)
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                            print(f"File {self.filename} deleted")
                        except Exception as e:
                            print(f"Error deleting file: {e}")
                    else:
                        print(f"file {filename} doesn't exist")

            self.csv_file = None
            self.csv_write = None


    def update_display(self, data_dict):
        """
        Handles data from PySensorFlow Engine
        Iterates through whatever data comes in and updates the matching plot.
        """

        # dynamic plotting loop
        for s_id, value in data_dict.items():
            if s_id in self.curves:
                #add to specific buffer
                self.buffers[s_id].append(value)
                #update specific curves
                self.curves[s_id].setData(self.buffers[s_id])

        #get data
        ldr_val = data_dict.get('ldr_sensor', 0.0)
        pot_val = data_dict.get('threshold', 500.0)
        temp_val = data_dict.get('temp_sensor', 300.0)

        #threshold control: manual or synced to hardware
        if self.chk_hw_sync.isChecked():
            #hardware mode: knob overrides GUI
            current_threshold = int(pot_val)
            #update the visual slider to match the knob
            self.threshold_slider.blockSignals(True) # prevent feedback loop
            self.threshold_slider.setValue(current_threshold)
            self.threshold_slider.blockSignals(False)
            self.slider_label.setText(f"Trigger Threshold (HW): {current_threshold}")
        else:
            #manual mode: GUI slider controls threshold
            current_threshold = self.threshold_slider.value()

        #apply smoothing
        if self.chk_smooth.isChecked():
            self.smoothing_buffer.append(ldr_val)
            self.smoothing_buffer_temp.append(temp_val)
            val_to_plot = sum(self.smoothing_buffer) / len(self.smoothing_buffer)
        else:
            val_to_plot = ldr_val
            self.smoothing_buffer.clear()

        # convert raw adc to voltage
        if self.chk_volts.isChecked():
            display_val = val_to_plot * (5.0 / 1023.0)
            self.graph_widget.setLabel('left', 'Voltage', units='V')
            self.graph_widget.setYRange(0, 5)
        else:
            display_val = val_to_plot
            self.graph_widget.setLabel('left', 'Raw ADC', units='0-1023')
            self.graph_widget.setYRange(0., 1024.)
    
        if self.csv_write and self.csv_file and not self.csv_file.closed:
            current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.csv_write.writerow([current_time, display_val])

        #control logic
        #compare vs software slider or hardware potentiometer
        #visualize hardware potentiometer on slider

        if hasattr(self, 'worker') and self.worker.isRunning():

            if val_to_plot < current_threshold and not self.led_is_on:
                self.worker.send_command('H')
                self.led_is_on = True
                self.label.setText(f">>> ALERT: {val_to_plot:.0f}  < {current_threshold}")
                self.label.setStyleSheet("color: #e74c3c; font-size: 24px; font-weight: bold;")

            elif val_to_plot >= current_threshold and self.led_is_on:
                self.worker.send_command('L')
                self.led_is_on = False
                self.label.setText(">>> MONITORING <<<")
                self.label.setStyleSheet("color: #00e5ff; font-size: 24px; font-weight: bold;")


    def update_slider_label(self, value):
        #only update in manual mode
        if not self.chk_hw_sync.isChecked():
            self.slider_label.setText(f"Trigger Threshold: {value}")

    def save_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screenshot_{timestamp}.png"
        exporter = pg.exporters.ImageExporter(self.graph_widget.plotItem)

        exporter.parameters()['width'] = 1000
        exporter.export(filename)

        self.label.setText(f"SAVED: {filename}")


