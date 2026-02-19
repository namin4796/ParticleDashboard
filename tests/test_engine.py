import pytest
from pysensorflow.core import SensorEngine

# -- fixtures --
@pytest.fixture
def engine():
    """
    Provides fresh instance of SensorEngine for each test.
    """
    return SensorEngine("config/setup.json")

# -- tests --
def test_parse_valid_csv(engine):
    """
    Test that a valid CSV string maps correctly to sensor IDs.
    """
    raw_serial_line = "512,256,128"
    result = engine.parse(raw_serial_line)

    # assertions
    assert result is not None
    assert result['ldr_sensor'] == 512.0
    assert result['threshold_pot'] == 256.0
    assert result['temp_sensor'] == 128.0

def test_parse_invalid_string(engine):
    """
    Test how the parser handles a string with no commas.
    """
    raw_serial_line = "Garbage_data"
    result = engine.parse(raw_serial_line)

    assert result is None

def test_parse_empty_string(engine):
    """
    Test if the parser handles empty string correctly
    """
    raw_serial_line = ""
    result = engine.parse(raw_serial_line)

    assert result is None

def test_parse_partial_data(engine):
    """
    Test how parser handles missing sensor data point.
    e.g. disconnected sensor
    """
    raw_serial_line = "512,256"
    result = engine.parse(raw_serial_line)

    # parse what is available and set 0.0 to the missing value
    assert result['ldr_sensor'] == 512.0
    assert result['threshold_pot'] == 256.0
    assert result['temp_sensor'] == 0.0
