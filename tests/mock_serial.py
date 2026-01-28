# Usage: Use this mock to run the dashboard without physical h/w connected

from unittest.mock import MagicMock
import math
import time
import random

from unittest.mock import PropertyMock

def create_mock_serial():
    """
    Create a MagicMock to emulate Arduino connected via Serial.
    """
    mock_serial = MagicMock()

    mock_serial.is_open = True

    type(mock_serial).in_waiting = PropertyMock(return_value=1)

    start_time = time.time()

    # Method to acknowledge 'write' to mock h/w
    def virtual_write(data):
        command = data.decode('utf-8')
        if command == 'H':
            print("\n MOCK H/W: LED ON")
        elif command == 'L':
            print("\n MOCK H/W: LED OFF")

        return len(data)

    mock_serial.write.side_effect = virtual_write

    def dynamic_readline():
        """
        Generate sine waves for Light and Potentiometer
        """

        t = time.time() - start_time

        # light = fast sine wave + noise
        light = 500 + 200*math.sin(t*2.0) + random.uniform(-10, 10)

        # potentiometer = slow sine wave
        pot = 500 + 500*math.sin(t*0.5)
        
        # temperatute = random temp fluctuations
        temp = 300 + t*random.uniform(-10, 10)

        # return inputs like arduino
        data_str = f"{light:.2f},{pot:.2f},{temp:.2f}\n"

        time.sleep(0.05)

        return data_str.encode('utf-8')

    mock_serial.readline.side_effect = dynamic_readline
    
    return mock_serial
