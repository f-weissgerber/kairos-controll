"""
AI generated test for the backend
"""

from src.cnc_controller.domain.models import BackendError, MachineState, ProgramState
from src.cnc_controller.backends.simulated_backend import SimulatedBackend


class FakeClock:
    """Clock whose time only moves when advance() is called."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def expect_error(label: str, fn, *args) -> None:
    try:
        fn(*args)
    except BackendError as e:
        print(f"OK    {label}: BackendError ({e})")
    else:
        print(f"FAIL  {label}: no BackendError")
        raise SystemExit(1)


def expect(label: str, value: float, expected: float) -> None:
    if abs(value - expected) < 1e-6:
        print(f"OK    {label}: {value:.3f}")
    else:
        print(f"FAIL  {label}: {value:.3f}, expected {expected:.3f}")
        raise SystemExit(1)


clock = FakeClock()
b = SimulatedBackend(clock=clock)

# --- Start sequence ---
s = b.get_status()
print(s)
assert (s.machine_state, s.program_state) == (MachineState.ESTOP, ProgramState.IDLE)
print("OK    start state: ESTOP / IDLE")
expect_error("jog in ESTOP", b.jog_start, "x", 1)
expect_error("reset_estop with hardware E-stop pressed", b.reset_estop)
b.set_hardware_estop(False)
b.reset_estop()
assert b.get_status().machine_state == MachineState.ON
print("OK    reset_estop -> ON")
expect_error("reset_estop when already ON", b.reset_estop)

# --- Jogging ---
b.jog_start("x", 1)
clock.advance(60.0)
expect("x after 60 s jog", b.get_status().position_machine.x, 1000.0)
b.jog_stop("x")
clock.advance(60.0)
expect("x after stop + 60 s", b.get_status().position_machine.x, 1000.0)
expect_error("unknown axis 'X'", b.jog_start, "X", 1)
expect_error("bad direction", b.jog_start, "x", 0)
b.jog_increment("y", 1, 5.0)
clock.advance(60.0)
expect("y after 5 mm step + 60 s", b.get_status().position_machine.y, 5.0)
expect_error("step <= 0", b.jog_increment, "y", 1, 0.0)

# --- Offset ---
b.set_work_offset("x", 400.0)
st = b.get_status()
expect("work x", st.position_work.x, 600.0)
expect("machine x unchanged", st.position_machine.x, 1000.0)

# --- Homing ---
b.home("x")
expect("x after home x", b.get_status().position_machine.x, 0.0)
b.home(None)
expect("y after home all", b.get_status().position_machine.y, 0.0)
expect_error("home unknown axis", b.home, "w")

# --- Spindle / peripherals ---
b.set_spindle(500)
st = b.get_status()
assert st.spindle_on and st.spindle_rpm_actual == 500
print("OK    spindle 500 rpm on")
b.set_spindle(0)
assert not b.get_status().spindle_on
print("OK    spindle off")
expect_error("negative rpm", b.set_spindle, -1)
b.set_light(True)
b.set_coolant(True)
st = b.get_status()
assert st.light_on and st.coolant_on
print("OK    light and coolant on")

# --- E-Stop during jog ---
b.set_spindle(800)
b.jog_start("z", 1)
clock.advance(6.0)
b.estop()
z_at_estop = b.get_status().position_machine.z
expect("z at estop (6 s of jog)", z_at_estop, 100.0)
clock.advance(6.0)
expect("z 6 s after estop", b.get_status().position_machine.z, z_at_estop)
st = b.get_status()
assert st.machine_state == MachineState.ESTOP
assert st.program_state == ProgramState.IDLE
assert not st.spindle_on and not st.coolant_on
print("OK    estop: ESTOP / IDLE, spindle and coolant off")
expect_error("jog after estop", b.jog_start, "z", 1)
expect_error("spindle in ESTOP", b.set_spindle, 100)

# --- Hardware E-stop pressed by the operator while jogging ---
b.reset_estop()
b.jog_start("x", 1)
clock.advance(3.0)
b.set_hardware_estop(True)
x_hw = b.get_status().position_machine.x
clock.advance(3.0)
expect("x stands after hardware estop", b.get_status().position_machine.x, x_hw)
assert b.get_status().machine_state == MachineState.ESTOP
print("OK    hardware estop -> ESTOP")
expect_error("reset while switch pressed", b.reset_estop)
b.set_hardware_estop(False)
assert b.get_status().machine_state == MachineState.ESTOP
print("OK    releasing the switch alone does not leave ESTOP")

# --- Back to ON ---
b.reset_estop()
assert b.get_status().machine_state == MachineState.ON
print("OK    reset_estop after switch released -> ON")

# --- Not implemented yet ---
for fn, args in ((b.run_mdi, ("G0 X0",)), (b.start_program, ())):
    try:
        fn(*args)
    except NotImplementedError:
        print(f"OK    {fn.__name__}: NotImplementedError (stage 2)")

print("\nAll checks passed.")