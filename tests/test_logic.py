import unittest
from collections import deque

class TestSignalProcessing(unittest.TestCase):
    def test_moving_average(self):
        # Create a buffer with known numbers: 10, 20, 30
        buffer = deque([10, 20, 30], maxlen=10)
        average = sum(buffer) / len(buffer)
        self.assertEqual(average, 20)

    def test_voltage_conversion(self):
        # Test that 1023 becomes 5.0V
        raw_val = 1023
        volts = raw_val * (5.0 / 1023.0)
        self.assertAlmostEqual(volts, 5.0)
