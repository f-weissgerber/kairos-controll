from __future__ import annotations

from abc import ABC, abstractmethod

from src.cnc_controller.domain.models import MachineStatus


class AbstractBackend(ABC):
    """Contract between the machine controller and any machine backend."""

    # -------------------------------------------------------------
    # Status
    # -------------------------------------------------------------

    @abstractmethod
    def get_status(self) -> MachineStatus:
        """Return a consistent snapshot of the whole machine."""

    # -------------------------------------------------------------
    # Machine state
    # -------------------------------------------------------------

    @abstractmethod
    def estop(self) -> None:
        """Trigger an emergency stop via STO: halt all motion and abort the program."""

    @abstractmethod
    def reset_estop(self) -> None:
        """
        Release STO and enable the machine (ESTOP -> ON).

        Fails while the hardware E-stop is pressed.
        """

    # -------------------------------------------------------------
    # Jogging
    # -------------------------------------------------------------

    @abstractmethod
    def jog_start(self, axis: str, direction: int) -> None:
        """Start continuous jogging of one axis (direction -1 or +1)."""

    @abstractmethod
    def jog_stop(self, axis: str) -> None:
        """Stop continuous jogging of one axis."""

    @abstractmethod
    def jog_increment(self, axis: str, direction: int, step: float) -> None:
        """Move one axis by a fixed step in mm (direction -1 or +1)."""

    # -------------------------------------------------------------
    # MDI
    # -------------------------------------------------------------

    @abstractmethod
    def run_mdi(self, line: str) -> None:
        """Execute one line of G-code in MDI mode."""

    # -------------------------------------------------------------
    # Homing and offsets
    # -------------------------------------------------------------

    @abstractmethod
    def home(self, axis: str | None) -> None:
        """Home one axis, or all axes if axis is None."""

    @abstractmethod
    def set_work_offset(self, axis: str, value: float) -> None:
        """Set the machine coordinate of the work zero for one axis."""

    # -------------------------------------------------------------
    # Program
    # -------------------------------------------------------------

    @abstractmethod
    def load_program(self, path: str) -> None:
        """Load a G-code program from a file."""

    @abstractmethod
    def start_program(self) -> None:
        """Start the loaded program."""

    @abstractmethod
    def pause_program(self) -> None:
        """Pause the program (feed halted, spindle keeps running)."""

    @abstractmethod
    def resume_program(self) -> None:
        """Resume a paused program."""

    @abstractmethod
    def abort_program(self) -> None:
        """Abort the program and return to IDLE."""

    # -------------------------------------------------------------
    # Spindle and peripherals
    # -------------------------------------------------------------

    @abstractmethod
    def set_spindle(self, rpm: float) -> None:
        """Set spindle speed in rpm. 0 turns the spindle off."""

    @abstractmethod
    def set_light(self, on: bool) -> None:
        """Switch the work light."""

    @abstractmethod
    def set_coolant(self, on: bool) -> None:
        """Switch the coolant."""