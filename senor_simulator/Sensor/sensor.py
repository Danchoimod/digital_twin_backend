from enum import Enum

class QualityFlag(str, Enum):
    """Quality flag representing the reliability and state of sensor reading."""
    VALID = "VALID"
    WARNING = "WARNING"
    UNCERTAIN = "UNCERTAIN"
    ERROR = "ERROR"
    CALIBRATING = "CALIBRATING"

class StationID(str, Enum):
    """IoT Monitoring Station Identifiers across water bodies."""
    CT_CANAL_001 = "CT_CANAL_001"
    CT_RIVER_002 = "CT_RIVER_002"
    CT_LAKE_003 = "CT_LAKE_003"
    CT_COAST_004 = "CT_COAST_004"
    CT_INDUSTRIAL_005 = "CT_INDUSTRIAL_005"

class SensorID(str, Enum):
    """Sensor device hardware model/serial numbers."""
    SENSOR_PH_042 = "SENSOR_PH_042"
    SENSOR_DO_088 = "SENSOR_DO_088"
    SENSOR_TURB_104 = "SENSOR_TURB_104"
    SENSOR_MULTI_205 = "SENSOR_MULTI_205"
    SENSOR_LEVEL_309 = "SENSOR_LEVEL_309"

class SensorType(str, Enum):
    """Types of sensors determining which metrics are generated."""
    PH = "PH"
    DISSOLVED_OXYGEN = "DISSOLVED_OXYGEN"
    TURBIDITY = "TURBIDITY"
    MULTI_PARAMETER = "MULTI_PARAMETER"
    WATER_LEVEL = "WATER_LEVEL"

SENSOR_TYPE_MAP = {
    SensorID.SENSOR_PH_042: SensorType.PH,
    SensorID.SENSOR_DO_088: SensorType.DISSOLVED_OXYGEN,
    SensorID.SENSOR_TURB_104: SensorType.TURBIDITY,
    SensorID.SENSOR_MULTI_205: SensorType.MULTI_PARAMETER,
    SensorID.SENSOR_LEVEL_309: SensorType.WATER_LEVEL,
}

SENSOR_METRICS_MAP = {
    SensorType.PH: ["pH", "temperature_c"],
    SensorType.DISSOLVED_OXYGEN: ["dissolved_oxygen_mg_l", "temperature_c"],
    SensorType.TURBIDITY: ["turbidity_ntu"],
    SensorType.WATER_LEVEL: ["water_level_m"],
    SensorType.MULTI_PARAMETER: [
        "pH", "dissolved_oxygen_mg_l", "temperature_c",
        "turbidity_ntu", "electrical_conductivity_us_cm", "tds_mg_l", "orp_mv"
    ]
}

class DeviceID(str, Enum):
    """Hardware Microcontroller Node IDs transmitting the raw payload."""
    ESP32_NODE_042 = "esp32-node-042"
    ESP32_NODE_088 = "esp32-node-088"
    STM32_NODE_104 = "stm32-node-104"
    RPi_GATEWAY_205 = "rpi-gateway-205"
