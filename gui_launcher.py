import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import sys

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.after(0, self._write_safe, message)

    def _write_safe(self, message):
        try:
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
        except Exception:
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            self.text_widget.insert(tk.END, safe_message)
            self.text_widget.see(tk.END)

    def flush(self):
        pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard/Mouse to XInput")
        self.process = None
        
        #tk.Label(root, text="").pack()
        button_frame = tk.Frame(root)
        button_frame.pack(pady=(10, 5), fill='x')

        self.start_button = tk.Button(button_frame, text="Start", command=self.start_script)
        self.start_button.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop", command=self.stop_script)
        self.stop_button.pack(side=tk.LEFT, fill='x', expand=True, padx=5)

        self.console = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=6, width=50)
        self.console.pack(padx=10, pady=10)

        sys.stdout = ConsoleRedirector(self.console)
        sys.stderr = ConsoleRedirector(self.console)

    def start_script(self):
        if self.process and self.process.poll() is None:
            self.console.delete('1.0', tk.END)
            print("Script is already running.")
            return
            
        self.console.delete('1.0', tk.END)
        
        def run():
            try:
                self.process = subprocess.Popen(
                    [sys.executable, "keyboard_mouse_to_xinput.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    universal_newlines=True
                )
                for line in self.process.stdout:
                    try:
                        print(line, end="")
                    except Exception:
                        print(line.encode('ascii', 'replace').decode('ascii'), end="")
                self.process.wait()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        threading.Thread(target=run, daemon=True).start()

    def stop_script(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            print("Script stopped.")
        else:
            self.console.delete('1.0', tk.END)
            print("Script is not running.")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()