# 🎮 keyboard_mouse_to_xinput

**keyboard_mouse_to_xinput** is a Python script that simulates an Xbox 360 controller (via XInput) using keyboard and mouse input. It's particularly useful for playing games on emulators like **Xenia** (Xbox 360 emulator) without a physical controller.

---

## 🧩 Features

- 🎮 Full simulation of an Xbox 360 controller via the library `vgamepad`.
- ⌨️ Customizable keyboard mapping to controller buttons.
- 🖱️ Converting mouse movements to right analog stick.
- 🖱️ Left/right click mapped to controller triggers.
- 🪟 Auto-detect emulator window (default `xenia_canary.exe`).
- 🖥️ Cursor confinement in the game window and cursor hiding.
- 🛑 Stopping the script via the key `F4`.

---

## ⚙️ Configuration

The `config.json` file allows you to customize the following settings:

- `executable_name` : name of the emulator process to be detected.
- `sensitivity` : mouse sensitivity for the right stick.
- `deadzone` : dead zone to prevent involuntary movements.
- `key_mapping` : dictionary associating keyboard keys with controller buttons.

---

## 🚀 Installation

1. Install the Windows driver [ViGEmBus_1.22.0_x64_x86_arm64.exe](https://github.com/ton-utilisateur/ton-projet/releases/download/v1.0/monprogramme).
2. Install the necessary dependencies with pip:

```bash
pip install pynput pywin32 psutil vgamepad
```

---

## 🕹️ Use

1. Launch the Xenia emulator (or other program defined in `config.json`).
2. Run the script:

```bash
python keyboard_mouse_to_xinput.py
```

3. Press `F4` to exit cleanly.

---

## 📦 Dependencies

- `pynput` – to listen to keyboard and mouse.
- `pywin32` – to interact with Windows windows.
- `psutil` – to detect processes.
- `vgamepad` – to simulate an Xbox controller via XInput.

---

## ⚠️ Limitations

- Works only on Windows.
- Requires sufficient privileges to interact with system windows.
- Only supports one virtual gamepad.

---

## 📄 Licence

This project is open source. You can freely adapt, improve, and redistribute it.
