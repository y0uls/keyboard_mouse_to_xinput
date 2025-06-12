import sys
import traceback
import json
import time
import threading
import psutil
import win32gui
import win32api
import win32process
import win32con
import ctypes
from pynput import keyboard, mouse
import vgamepad as vg

# Chargement de la configuration
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

EXE_NAME = config["executable_name"]
SENSITIVITY = config["sensitivity"]
DEADZONE = config["deadzone"]
user_key_mapping = config["key_mapping"]

# Mappage des touches
key_map = {
    "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "GUIDE": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    "LEFT_SHOULDER": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RIGHT_SHOULDER": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "LEFT_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "RIGHT_THUMB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "dpad_up": "dpad_up",
    "dpad_down": "dpad_down",
    "dpad_left": "dpad_left",
    "dpad_right": "dpad_right",
    "left_thumb_up": "left_thumb_up",
    "left_thumb_down": "left_thumb_down",
    "left_thumb_left": "left_thumb_left",
    "left_thumb_right": "left_thumb_right"
}

key_to_button = {}
for k, v in user_key_mapping.items():
    try:
        key_obj = getattr(keyboard.Key, k) if hasattr(keyboard.Key, k) else keyboard.KeyCode.from_char(k)
        key_to_button[key_obj] = key_map[v]
    except Exception as e:
        print(f"Error in key mapping '{k}': {e}")

def log_exception(exc_type, exc_value, exc_traceback):
    with open("error_log.txt", "w", encoding="utf-8") as f:
        f.write("An error occurred while running the program:\n\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

sys.excepthook = log_exception

xenia_center = (0, 0)
running = True
pressed_keys = set()
gamepad = vg.VX360Gamepad()
original_cursor = None

def disable_console_input_echo():
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-10)
    mode = ctypes.c_uint()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    mode.value &= ~0x0004
    kernel32.SetConsoleMode(handle, mode)

def set_invisible_cursor():
    global original_cursor
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", ctypes.c_bool),
            ("xHotspot", ctypes.c_ulong),
            ("yHotspot", ctypes.c_ulong),
            ("hbmMask", ctypes.c_void_p),
            ("hbmColor", ctypes.c_void_p),
        ]

    hbm_mask = gdi32.CreateBitmap(1, 1, 1, 1, None)
    hbm_color = gdi32.CreateBitmap(1, 1, 1, 1, None)

    icon_info = ICONINFO()
    icon_info.fIcon = False
    icon_info.xHotspot = 0
    icon_info.yHotspot = 0
    icon_info.hbmMask = hbm_mask
    icon_info.hbmColor = hbm_color

    hcursor = user32.CreateIconIndirect(ctypes.byref(icon_info))
    original_cursor = user32.CopyIcon(user32.LoadCursorW(0, 32512))
    user32.SetSystemCursor(hcursor, 32512)

def restore_cursor():
    if original_cursor:
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)

def release_mouse():
    screen_rect = (0, 0, win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))
    win32api.ClipCursor(screen_rect)
    restore_cursor()

def find_window_by_exe(exe_name=EXE_NAME):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and proc.info['name'].lower() == exe_name.lower():
            pid = proc.info['pid']
            def callback(hwnd, hwnds):
                if win32gui.IsWindowVisible(hwnd):
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        hwnds.append(hwnd)
                return True
            hwnds = []
            win32gui.EnumWindows(callback, hwnds)
            if hwnds:
                return hwnds[0]
    return None

def force_foreground_window(hwnd):
    try:
        foreground_hwnd = win32gui.GetForegroundWindow()
        if hwnd == foreground_hwnd:
            return
        current_thread_id = win32api.GetCurrentThreadId()
        foreground_thread_id = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
        target_thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
        win32process.AttachThreadInput(foreground_thread_id, current_thread_id, True)
        win32process.AttachThreadInput(target_thread_id, current_thread_id, True)
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetActiveWindow(hwnd)
        win32process.AttachThreadInput(foreground_thread_id, current_thread_id, False)
        win32process.AttachThreadInput(target_thread_id, current_thread_id, False)
        time.sleep(0.1)
    except Exception as e:
        print(f"Error brought to the forefront: {e}")

def confine_mouse_to_xenia():
    global xenia_center
    hwnd = None
    print("🔍 Searching for the Xenia window...")
    while hwnd is None:
        hwnd = find_window_by_exe()
        time.sleep(0.5)
    force_foreground_window(hwnd)
    rect = win32gui.GetWindowRect(hwnd)
    print(f"🪟 Xenia window detected: {rect}")
    win32api.ClipCursor(rect)
    xenia_center = ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
    win32api.SetCursorPos(xenia_center)
    set_invisible_cursor()

def monitor_xenia_window():
    while running:
        hwnd = find_window_by_exe()
        if hwnd:
            force_foreground_window(hwnd)
        time.sleep(2)

def update_left_thumb():
    x = y = 0
    if 'left_thumb_left' in pressed_keys:
        x -= 32768
    if 'left_thumb_right' in pressed_keys:
        x += 32767
    if 'left_thumb_up' in pressed_keys:
        y += 32767
    if 'left_thumb_down' in pressed_keys:
        y -= 32768
    gamepad.left_joystick(x_value=x, y_value=y)
    gamepad.update()

def on_press(key):
    global running
    if key == keyboard.Key.f4:
        print("F4 pressed. Exiting script.")
        running = False
        return False

    action = key_to_button.get(key)
    if not action and isinstance(key, keyboard.KeyCode) and key.char:
        action = key_to_button.get(keyboard.KeyCode.from_char(key.char.lower()))

    if action:
        if isinstance(action, vg.XUSB_BUTTON):
            gamepad.press_button(action)
            gamepad.update()
        elif isinstance(action, str):
            pressed_keys.add(action)
            if action.startswith('left_thumb'):
                update_left_thumb()
            elif action.startswith('dpad'):
                if action == 'dpad_up':
                    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                elif action == 'dpad_down':
                    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                elif action == 'dpad_left':
                    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                elif action == 'dpad_right':
                    gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                gamepad.update()

def on_release(key):
    action = key_to_button.get(key)
    if not action and isinstance(key, keyboard.KeyCode) and key.char:
        action = key_to_button.get(keyboard.KeyCode.from_char(key.char.lower()))

    if action:
        if isinstance(action, vg.XUSB_BUTTON):
            gamepad.release_button(action)
            gamepad.update()
        elif isinstance(action, str):
            pressed_keys.discard(action)
            if action.startswith('left_thumb'):
                update_left_thumb()
            elif action.startswith('dpad'):
                if action == 'dpad_up':
                    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                elif action == 'dpad_down':
                    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                elif action == 'dpad_left':
                    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                elif action == 'dpad_right':
                    gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                gamepad.update()

def mouse_to_right_stick():
    global xenia_center
    prev_stick_x = prev_stick_y = 0
    while running:
        time.sleep(0.01)
        curr_pos = win32api.GetCursorPos()
        if curr_pos == xenia_center:
            continue
        dx = curr_pos[0] - xenia_center[0]
        dy = curr_pos[1] - xenia_center[1]
        stick_x = max(min(int(dx * SENSITIVITY), 32767), -32768)
        stick_y = max(min(int(-dy * SENSITIVITY), 32767), -32768)
        stick_x = int((stick_x + prev_stick_x) // 2)
        stick_y = int((stick_y + prev_stick_y) // 2)
        prev_stick_x, prev_stick_y = stick_x, stick_y
        if abs(stick_x) < DEADZONE:
            stick_x = 0
        if abs(stick_y) < DEADZONE:
            stick_y = 0
        gamepad.right_joystick(x_value=stick_x, y_value=stick_y)
        gamepad.update()
        win32api.SetCursorPos(xenia_center)

def mouse_button_listener():
    def on_click(x, y, button, pressed):
        if button == mouse.Button.left:
            gamepad.right_trigger(value=255 if pressed else 0)
        elif button == mouse.Button.right:
            gamepad.left_trigger(value=255 if pressed else 0)
        gamepad.update()
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

disable_console_input_echo()
confine_mouse_to_xenia()
threading.Thread(target=mouse_to_right_stick, daemon=True).start()
threading.Thread(target=mouse_button_listener, daemon=True).start()
threading.Thread(target=monitor_xenia_window, daemon=True).start()

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        print("🎮 Script active. Press F4 to exit.")
        listener.join()
finally:
    release_mouse()
    print("🧹 Cleaning complete.")
