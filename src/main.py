import asyncio
from typing import Any, ClassVar, Dict, List, Mapping, Optional, Sequence

from typing_extensions import Self
from logging import getLogger
from viam.components.sensor import Sensor
from viam.module.module import Module
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import Geometry, ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import SensorReading, ValueTypes, struct_to_dict

import time
import board as pyboard
import adafruit_hcsr04

LOGGER = getLogger("ultrasonic-adafruit")

# Mapping of physical pin numbers (as strings) to BCM → board.Dxx
BOARD_TO_BCM = {
    "3": 2, "5": 3, "7": 4, "8": 14, "10": 15, "11": 17, "12": 18,
    "13": 27, "15": 22, "16": 23, "18": 24, "19": 10, "21": 9,
    "22": 25, "23": 11, "24": 8, "26": 7, "29": 5, "31": 6,
    "32": 12, "33": 13, "35": 19, "36": 16, "37": 26, "38": 20, "40": 21
}

class UltrasonicAdafruit(Sensor, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("joyce", "ultrasonic-adafruit"), "ultrasonic-adafruit"
    )

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        return super().new(config, dependencies)

    def _resolve_pin(self, pin_str: str):
        """Resolve a pin string into a board.Dxx object.

        Supports:
        - Physical pin numbers (e.g., '16')
        - D-formatted strings (e.g., 'D23')
        - GPIO-formatted strings (e.g., 'GPIO23')
        - BCM numbers (e.g., '23')
        """
        attr = None

        # Physical pin number
        if pin_str in BOARD_TO_BCM:
            bcm = BOARD_TO_BCM[pin_str]
            attr = f"D{bcm}"
            LOGGER.info(f"Resolved physical pin {pin_str} → BCM {bcm} → board.{attr}")

        # Dxx format (e.g. D23)
        elif pin_str.startswith("D") and pin_str[1:].isdigit():
            attr = pin_str
            LOGGER.info(f"Using direct board constant: board.{attr}")

        # GPIO format (e.g. GPIO23)
        elif pin_str.startswith("GPIO") and pin_str[4:].isdigit():
            attr = f"D{pin_str[4:]}"
            LOGGER.info(f"Resolved {pin_str} → board.{attr}")

        # Raw BCM (e.g. "23")
        elif pin_str.isdigit():
            attr = f"D{pin_str}"
            LOGGER.info(f"Assuming BCM {pin_str} → board.{attr}")

        else:
            raise ValueError(f"Invalid pin format: {pin_str}. Use physical pin (e.g. '16'), D23, GPIO23, or BCM number.")

        try:
            return getattr(pyboard, attr)
        except AttributeError:
            raise ValueError(f"{attr} is not available on this board module")

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        attrs = struct_to_dict(config.attributes)
        required_attributes = ["echo_interrupt_pin", "trigger_pin"]
        for attr in required_attributes:
            if attr not in attrs or not isinstance(attrs[attr], str):
                raise ValueError(f"{attr} is required and must be a string")
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        attrs = struct_to_dict(config.attributes)

        try:
            trigger_pin_str = str(attrs.get("trigger_pin"))
            echo_pin_str = str(attrs.get("echo_interrupt_pin"))
            timeout_sec = float(attrs.get("timeout_ms", 1000)) / 1000.0

            trigger_pin = self._resolve_pin(trigger_pin_str)
            echo_pin = self._resolve_pin(echo_pin_str)

            self.sonar = adafruit_hcsr04.HCSR04(
                trigger_pin=trigger_pin,
                echo_pin=echo_pin,
                timeout=timeout_sec
            )

            self.trigger_pin = trigger_pin_str
            self.echo_interrupt_pin = echo_pin_str

            LOGGER.info("Adafruit HCSR04 initialized successfully")

        except Exception as e:
            LOGGER.error(f"Failed to initialize HCSR04: {e}")

        return super().reconfigure(config, dependencies)

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, SensorReading]:
        try:
            distance = self.sonar.distance / 100.0  # cm to meters
            return {"distance": distance}
        except Exception as e:
            LOGGER.error(f"Ultrasonic sensor read failed: {e}")
            return {"distance": -1.0}

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        raise NotImplementedError()

    async def get_geometries(
        self, *, extra: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[Geometry]:
        raise NotImplementedError()

    async def close(self):
        pass

    def __del__(self):
        pass

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())