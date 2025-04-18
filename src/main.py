import asyncio
from typing import Any, ClassVar, Final, List, Mapping, Optional, Sequence, Dict, cast

from typing_extensions import Self
from logging import getLogger
from viam.components.board import Board
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

LOGGER = getLogger("ultrasonic-dimled")

class UltrasonicAdafruit(Sensor, EasyResource):
    MODEL: ClassVar[Model] = Model(
        ModelFamily("joyce", "ultrasonic-adafruit"), "ultrasonic-adafruit"
    )

    auto_start = True
    task: Optional[asyncio.Task] = None  # Ensure task is properly typed
    event = asyncio.Event()  # Use asyncio.Event for compatibility with asyncio

    @classmethod
    def start_task(cls) -> None:
        """Start the background task for the sensor."""
        if cls.task is None or cls.task.done():
            cls.task = asyncio.create_task(cls._run_task())
            LOGGER.info("Background task started.")

    @classmethod
    async def _run_task(cls) -> None:
        """Background task to handle sensor operations."""
        try:
            while True:
                cls.event.clear()
                # Simulate sensor reading or perform actual sensor operations
                LOGGER.error("Running sensor task...")
                await asyncio.sleep(1)  # Simulate periodic task
                cls.event.set()
        except asyncio.CancelledError:
            LOGGER.info("Background task cancelled.")
        except Exception as e:
            LOGGER.error(f"Error in background task: {e}")

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        """This method creates a new instance of this Sensor component.
        The default implementation sets the name from the `config` parameter and then calls `reconfigure`.

        Args:
            config (ComponentConfig): The configuration for this resource
            dependencies (Mapping[ResourceName, ResourceBase]): The dependencies (both implicit and explicit)

        Returns:
            Self: The resource
        """
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        """This method allows you to validate the configuration object received from the machine,
        as well as to return any implicit dependencies based on that `config`.

        Args:
            config (ComponentConfig): The configuration for this resource

        Returns:
            Sequence[str]: A list of implicit dependencies
        """
        attrs = struct_to_dict(config.attributes)
        required_dependencies = ["board"]
        required_attributes = ["echo_interrupt_pin", "trigger_pin"]
        implicit_dependencies = []

        for component in required_dependencies:
            if component not in attrs or not isinstance(attrs[component], str):
                raise ValueError(f"{component} is required and must be a string")
            else:
                implicit_dependencies.append(attrs[component])

        for attribute in required_attributes:
            if attribute not in attrs or not isinstance(attrs[attribute], str):
                raise ValueError(f"{attribute} is required and must be a string")

        return implicit_dependencies

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """This method allows you to dynamically update your service when it receives a new `config` object.

        Args:
            config (ComponentConfig): The new configuration
            dependencies (Mapping[ResourceName, ResourceBase]): Any dependencies (both implicit and explicit)
        """
        attrs = struct_to_dict(config.attributes)
        self.auto_start = bool(attrs.get("auto_start", self.auto_start))

        LOGGER.error("Reconfiguring ultrasonic Adafruit module...")

        board_resource = dependencies.get(Board.get_resource_name(str(attrs.get("board"))))
        self.board = cast(Board, board_resource)

        if not self.board:
            raise ValueError(f"Board resource {attrs.get('board')} not found")
        self.trigger_pin = str(attrs.get("trigger_pin"))
        self.echo_interrupt_pin = str(attrs.get("echo_interrupt_pin"))

        if self.auto_start:
            self.start()

        trigger_pin = getattr(pyboard, self.trigger_pin)
        echo_pin = getattr(pyboard, self.echo_interrupt_pin)
        timeout_sec = float(attrs.get("timeout_ms", 1000)) / 1000.0
        self.sonar = adafruit_hcsr04.HCSR04(trigger_pin=trigger_pin, echo_pin=echo_pin, timeout=timeout_sec)
        
        return super().reconfigure(config, dependencies)

    async def get_readings(
        self,
        *,
        extra: Optional[Mapping[str, Any]] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, SensorReading]:
        try:
            distance = self.sonar.distance / 100.0  # Convert cm to meters
            return {"distance": distance}
        except RuntimeError:
            LOGGER.warning("Ultrasonic sensor read failed — retrying")
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

    def start(self):
        if self.task is None or self.task.done():
            self.event.clear()
            self.task = asyncio.create_task(self._background_loop())

    def stop(self):
        self.event.set()
        if self.task is not None:
            self.task.cancel()

    async def _background_loop(self):
        while not self.event.is_set():
            await asyncio.sleep(1)

    async def close(self):
        self.stop()

    def __del__(self):
        self.stop()

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())

