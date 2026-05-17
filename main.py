import sys, os, tkinter as tk
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

# Suppress harmless CTk after() errors on window close
_orig = tk.Tk.report_callback_exception
def _safe(self, exc, val, tb):
    msg = str(val)
    if any(k in msg for k in ("invalid command name","application has been destroyed",
                               "_click_animation","check_dpi_scaling","_tick",
                               "can't invoke")):
        return
    _orig(self, exc, val, tb)
tk.Tk.report_callback_exception = _safe


def main():
    # Initialize database (creates file + tables if not exists)
    from database import init_db
    init_db()

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    while True:
        from ui.login_view import LoginWindow
        login = LoginWindow()
        login.mainloop()
        if not getattr(login, "login_success", False):
            break

        from ui.app import App
        app = App()
        app.mainloop()
        # After logout, loop back to login
        # (break only if window was closed via X button, not logout)
        if not hasattr(app, '_logout_triggered'):
            break


if __name__ == "__main__":
    main()
