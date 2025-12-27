from pybricks.hubs import TechnicHub
from pybricks.pupdevices import Motor
try:
    # Newer Pybricks versions
    from pybricks.iodevices import XboxController
except ImportError:
    # Older Pybricks versions (kept for compatibility)
    from pybricks.pupdevices import XboxController
from pybricks.parameters import Port, Direction, Button, Color
from pybricks.tools import wait

hub = TechnicHub()
hub.light.on(Color.RED)  # Red: Waiting

# Set up motors
drive_motor1 = Motor(Port.B, Direction.COUNTERCLOCKWISE)  # Driving XL 1 - reversed
drive_motor2 = Motor(Port.D, Direction.CLOCKWISE)         # Driving XL 2

# Maximize speed/acceleration for both
drive_motor1.control.limits(speed=2000, acceleration=20000)
drive_motor2.control.limits(speed=2000, acceleration=20000)

# Cruise + light state
cruise_mode = False
cruise_speed = 1000  # Adjust this: 2000 = full forward, -1000 = reverse, etc.
cruise_speed_step = 100
cruise_speed_min = -2000
cruise_speed_max = 2000
previous_lb_pressed = False
previous_b_pressed = False
previous_rb_pressed = False
previous_up_pressed = False
previous_down_pressed = False

# Button B color cycle (press = next color, wraps around)
b_color_cycle = [Color.BLUE, Color.CYAN, Color.ORANGE, Color.RED, Color.GREEN]
b_color_index = -1  # -1 means "no override" (use mode colors)

def set_base_light():
    """Set hub light to the current 'base' color (B override if set, else mode)."""
    if b_color_index >= 0:
        hub.light.on(b_color_cycle[b_color_index])
    else:
        hub.light.on(Color.YELLOW if cruise_mode else Color.GREEN)

def stop_motors():
    """Stop both drive motors in a way that works across Pybricks versions."""
    # Some Pybricks versions support stop(Stop.BRAKE); others only stop().
    try:
        from pybricks.parameters import Stop  # local import for compatibility
        drive_motor1.stop(Stop.BRAKE)
        drive_motor2.stop(Stop.BRAKE)
        return
    except Exception:
        pass

    try:
        drive_motor1.stop()
        drive_motor2.stop()
        return
    except Exception:
        pass

    # Last resort: command 0 speed.
    drive_motor1.run(0)
    drive_motor2.run(0)

# Retry loop for connection
controller = None
while controller is None:
    try:
        controller = XboxController()
        set_base_light()  # Connected: show base light (mode or B override)
    except (OSError, RuntimeError) as e:
        hub.light.blink(Color.ORANGE, [100, 100])  # Orange: Retrying
        wait(5000)  # Wait 5s before retry

# Main loop
while True:
    # Read inputs once per loop (more reliable than polling pressed() repeatedly)
    left_horizontal, left_vertical = controller.joystick_left()
    right_horizontal, right_vertical = controller.joystick_right()
    pressed = controller.buttons.pressed()

    # Detect LB button press (rising edge) to toggle cruise mode
    lb_pressed = Button.LB in pressed
    if lb_pressed and not previous_lb_pressed:
        cruise_mode = not cruise_mode
        if not cruise_mode:
            # Explicitly stop when toggling cruise off
            stop_motors()
        set_base_light()
    previous_lb_pressed = lb_pressed

    # Button B: rumble + advance color cycle once per press (rising edge)
    b_pressed = Button.B in pressed
    if b_pressed and not previous_b_pressed:
        controller.rumble(power=80, duration=250)
        b_color_index = (b_color_index + 1) % len(b_color_cycle)
        set_base_light()
    previous_b_pressed = b_pressed

    # D-pad UP/DOWN: adjust cruise speed (persists after release)
    up_pressed = Button.UP in pressed
    if up_pressed and not previous_up_pressed:
        cruise_speed = min(cruise_speed + cruise_speed_step, cruise_speed_max)
    previous_up_pressed = up_pressed

    down_pressed = Button.DOWN in pressed
    if down_pressed and not previous_down_pressed:
        cruise_speed = max(cruise_speed - cruise_speed_step, cruise_speed_min)
    previous_down_pressed = down_pressed

    # Determine motor speeds
    if cruise_mode:
        motor1_speed = cruise_speed
        motor2_speed = cruise_speed

        # No rumble in cruise mode
    else:
        motor1_speed = left_vertical * 20
        motor2_speed = right_vertical * 20

        # Rumble if joysticks pushed in opposite directions (skid-steer warning)
        if (left_vertical > 20 and right_vertical < -20) or (left_vertical < -20 and right_vertical > 20):
            controller.rumble(power=50, duration=100)

    # Run motors
    drive_motor1.run(motor1_speed)
    drive_motor2.run(motor2_speed)

    # Button A: Flash blue, then return to current mode color
    if Button.A in pressed:
        hub.light.on(Color.BLUE)
        wait(200)
        set_base_light()

    # Button Y: Your original color sequence (unchanged)
    if Button.Y in pressed:
        hub.light.on(Color.CYAN)
        wait(200)
        hub.light.on(Color.RED)
        wait(200)
        hub.light.on(Color.ORANGE)
        wait(200)
        hub.light.on(Color.RED)
        wait(200)
        set_base_light()

    # Button RB: Set red while held (unchanged)
    rb_pressed = Button.RB in pressed
    if rb_pressed:
        hub.light.on(Color.RED)
    elif previous_rb_pressed:
        # Restore base color on release
        set_base_light()
    previous_rb_pressed = rb_pressed

    # Small delay to prevent overload
    wait(50)
