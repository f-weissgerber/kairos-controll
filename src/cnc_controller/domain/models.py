from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

class BackendError(Exception):
    """Backend Error"""

class MachineState(Enum):
    ESTOP = auto()  # STO active: triggered by the controller or the hardware E-stop switch
    ON = auto()     # STO released and machine enabled

class ProgramState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()

@dataclass
class MachinePosition:
    x: float
    y: float
    z: float

@dataclass
class AxisLoad:
    x: float
    y: float
    z: float

@dataclass
class MachineStatus:

    # Machine state
    machine_state: MachineState
    program_state: ProgramState

    # Positions
    position_machine: MachinePosition
    position_work: MachinePosition
    distance_to_go: MachinePosition

    # Offset
    work_offset_name: str

    # Spindle
    spindle_rpm_actual: float
    spindle_on: bool

    # Feeds
    feed_programmed: float
    feed_actual: float

    # Loads
    axis_load: AxisLoad
    spindle_load: float

    # Program
    current_line: int

    # Peripherals
    light_on: bool
    coolant_on: bool