import serial
import serial.tools.list_ports
import time
from PyQt6.QtCore import QThread, pyqtSignal

class SensorWorker(QThread):
    data_signal = pyqtSignal(float)

    def __init__(self, port_name):
        super().__init__()
        self.is_running = True
        self.port_name = port_name
        self.serial_conn = None

    def send_command(self, command_char):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command_char.encode('utf-8'))
                print(f"DEBUG: Sent command {command_char}")
            except Exception as e:
                print(f"Error sending command: {e}")

    def run(self):
        print("Sensor started... press Ctrl+C to stop\n")
        print("Attemting to connect to {self.port_name}")
        try:
            self.serial_conn = serial.Serial(self.port_name, 9600, timeout=1)
            time.sleep(2)

            self.serial_conn.reset_input_buffer()
        
            while self.is_running:
                if self.serial_conn.in_waiting > 0:
                    #simulate reading a sensor

                    line = self.serial_conn.readline().decode('utf-8').strip() 

                    try:
                        value = float(line)
                        self.data_signal.emit(value)
                    except ValueError:
                        pass

        except serial.SerialException as e:
            print(f"Error: Could not open serial port: {e}")

        finally:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            print("DEBUG: Serial connection closed")

    #stop the worker
    def stop(self):
        self.is_running = False


                                                  
