from __future__ import annotations

import time
from typing import Callable

from src.cnc_controller.backends.backend import AbstractBackend
from src.cnc_controller.domain.models import (
    AxisLoad,
    BackendError,
    MachinePosition,
    MachineState,
    MachineStatus,
    ProgramState,
)

AXES = ("x", "y", "z")

JOG_SPEED_MM_PER_S = 1000 / 60  # 1000 mm/min


class SimulatedBackend(AbstractBackend):
    """Hardware-free machine; axis positions are integrated lazily from a clock."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._last_time = clock()
        self._machine_state = MachineState.ESTOP
        self._program_state = ProgramState.IDLE
        self._position = {a: 0.0 for a in AXES}       # machine coordinates
        self._jog_direction = {a: 0 for a in AXES}    # -1, 0, +1
        self._work_offset = {a: 0.0 for a in AXES}    # machine coordinate of work zero
        self._spindle_rpm = 0.0
        self._light_on = False
        self._coolant_on = False
        self._hardware_estop_pressed = True           # machine starts with E-stop pressed

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    def _update(self) -> None:
        """Integrate axis positions up to the current clock time."""
        now = self._clock()
        dt = now - self._last_time
        self._last_time = now

        for a in AXES:
            self._position[a] += self._jog_direction[a] * JOG_SPEED_MM_PER_S * dt

    def _check_axis(self, axis: str) -> None:
        if axis not in AXES:
            raise BackendError(f"Unknown axis: {axis!r}")

    def _check_direction(self, direction: int) -> None:
        if direction not in (-1, 1):
            raise BackendError("Direction must be in (-1, 1)")

    def _require_on(self, action: str) -> None:
        if self._machine_state != MachineState.ON:
            raise BackendError(
                f"{action} requires machine state ON, is {self._machine_state.name}"
            )

    def _require_on_and_idle(self, action: str) -> None:
        self._require_on(action)
        if self._program_state != ProgramState.IDLE:
            raise BackendError(
                f"{action} not allowed while program is {self._program_state.name}"
            )

    def _halt_everything(self) -> None:
        """Stop all axes, spindle and coolant and abort any program."""
        for a in AXES:
            self._jog_direction[a] = 0
        self._spindle_rpm = 0.0
        self._coolant_on = False
        self._program_state = ProgramState.IDLE

    # ---------------------------------------------------------------
    # Status
    # ---------------------------------------------------------------

    def get_status(self) -> MachineStatus:
        """Return a consistent snapshot of the simulated machine."""
        self._update()
        p = self._position
        o = self._work_offset

        return MachineStatus(
            machine_state=self._machine_state,
            program_state=self._program_state,
            position_machine=MachinePosition(p["x"], p["y"], p["z"]),
            position_work=MachinePosition(p["x"] - o["x"], p["y"] - o["y"], p["z"] - o["z"]),
            distance_to_go=MachinePosition(0.0, 0.0, 0.0),
            work_offset_name="G54",
            spindle_rpm_actual=self._spindle_rpm,
            spindle_on=self._spindle_rpm > 0.0,
            feed_programmed=0.0,
            feed_actual=0.0,
            axis_load=AxisLoad(0.0, 0.0, 0.0),
            spindle_load=0.0,
            current_line=0,
            light_on=self._light_on,
            coolant_on=self._coolant_on,
        )

    # ---------------------------------------------------------------
    # Machine state
    # ---------------------------------------------------------------

    def set_hardware_estop(self, pressed: bool) -> None:
        """Simulate the operator pressing or releasing the hardware E-stop switch.

        Simulator only, not part of AbstractBackend: on a real machine the
        switch acts on STO and the backend merely reports ESTOP.
        """
        self._update()
        self._hardware_estop_pressed = pressed
        if pressed:
            self._halt_everything()
            self._machine_state = MachineState.ESTOP

    def estop(self) -> None:
        """Trigger an emergency stop via STO: halt all motion and abort the program."""
        self._update()  # account for the distance travelled up to this moment first
        self._halt_everything()
        self._machine_state = MachineState.ESTOP

    def reset_estop(self) -> None:
        """Release STO and enable the machine (ESTOP -> ON).

        Fails while the hardware E-stop is pressed.
        """
        self._update()
        if self._machine_state != MachineState.ESTOP:
            raise BackendError(
                f"reset_estop requires ESTOP, is {self._machine_state.name}"
            )
        if self._hardware_estop_pressed:
            raise BackendError("Hardware E-stop is still pressed")
        self._machine_state = MachineState.ON

    # ---------------------------------------------------------------
    # Jogging
    # ---------------------------------------------------------------

    def jog_start(self, axis: str, direction: int) -> None:
        """Start continuous jogging of one axis (direction -1 or +1)."""
        self._update()
        self._check_axis(axis)
        self._check_direction(direction)
        self._require_on_and_idle("Jog")
        self._jog_direction[axis] = direction

    def jog_stop(self, axis: str) -> None:
        """Stop continuous jogging of one axis."""
        self._update()  # distance up to now must be counted before the direction changes
        self._check_axis(axis)
        self._jog_direction[axis] = 0

    def jog_increment(self, axis: str, direction: int, step: float) -> None:
        """Move one axis by a fixed step in mm (direction -1 or +1)."""
        self._update()
        self._check_axis(axis)
        self._check_direction(direction)
        if step <= 0:
            raise BackendError("Step must be > 0")
        self._require_on_and_idle("Jog")
        self._position[axis] += direction * step

    # ---------------------------------------------------------------
    # Homing and offsets
    # ---------------------------------------------------------------

    def home(self, axis: str | None) -> None:
        """Home one axis, or all axes if axis is None."""
        self._update()
        if axis is not None:
            self._check_axis(axis)
        self._require_on_and_idle("Homing")
        for a in AXES if axis is None else (axis,):
            self._position[a] = 0.0

    def set_work_offset(self, axis: str, value: float) -> None:
        """Set the machine coordinate of the work zero for one axis."""
        self._update()
        self._check_axis(axis)
        self._work_offset[axis] = value

    # ---------------------------------------------------------------
    # MDI
    # ---------------------------------------------------------------

    def run_mdi(self, line: str) -> None:
        """Execute one line of G-code in MDI mode."""
        self._update()
        self._require_on_and_idle("MDI")
        raise NotImplementedError

    # ---------------------------------------------------------------
    # Program (stage 2)
    # ---------------------------------------------------------------

    def load_program(self, path: str) -> None:
        """Load a G-code program from a file."""
        raise NotImplementedError

    def start_program(self) -> None:
        """Start the loaded program."""
        self._update()
        self._require_on_and_idle("Start")
        raise NotImplementedError

    def pause_program(self) -> None:
        """Pause the program (feed halted, spindle keeps running)."""
        raise NotImplementedError

    def resume_program(self) -> None:
        """Resume a paused program."""
        raise NotImplementedError

    def abort_program(self) -> None:
        """Abort the program and return to IDLE."""
        raise NotImplementedError

    # ---------------------------------------------------------------
    # Spindle and peripherals
    # ---------------------------------------------------------------

    def set_spindle(self, rpm: float) -> None:
        """Set spindle speed in rpm; 0 turns the spindle off."""
        self._update()
        self._require_on("Spindle")
        if rpm < 0:
            raise BackendError("rpm must be >= 0")
        self._spindle_rpm = rpm

    def set_light(self, on: bool) -> None:
        """Switch the work light."""
        self._update()
        self._light_on = on

    def set_coolant(self, on: bool) -> None:
        """Switch the coolant."""
        self._update()
        self._require_on("Coolant")
        self._coolant_on = on