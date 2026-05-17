import os
import customtkinter as ctk
from ui.theme import SIDEBAR_BG, ACCENT, ACCENT_H, CARD_BG, TEXT_D, TEXT_M

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIN_W, WIN_H = 420, 520


def _load_logo(size=110):
    """Load logo — white bg, displayed at natural aspect ratio."""
    path = os.path.join(_ROOT, "Logo.png")
    if not os.path.exists(path):
        return None
    try:
        from PIL import Image
        from customtkinter import CTkImage
        img  = Image.open(path).convert("RGB")
        # Replace dark bg with white
        bg   = Image.new("RGB", img.size, (255, 255, 255))
        mask = img.convert("L").point(lambda v: 255 if v < 28 else 0, "L")
        img.paste(bg, mask=mask)
        # Resize keeping aspect ratio — width drives
        w, h  = img.size
        ratio = size / w
        new_h = int(h * ratio)
        img   = img.resize((size, new_h), Image.LANCZOS)
        return CTkImage(light_image=img, size=(size, new_h))
    except Exception:
        return None


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.login_success = False
        self.title("Cão & Gato")
        self.resizable(False, False)
        self.configure(fg_color=SIDEBAR_BG)
        try:
            ico = os.path.join(_ROOT, "Logo.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{WIN_W}x{WIN_H}+{(sw-WIN_W)//2}+{max(0,(sh-WIN_H)//2-20)}")
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=18)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=36, pady=16)

        logo = _load_logo(110)
        if logo:
            lbl = ctk.CTkLabel(inner, image=logo, text=""); lbl.image = logo; lbl.pack()
        else:
            ctk.CTkLabel(inner, text="🐾", font=("Segoe UI", 34)).pack()

        ctk.CTkLabel(inner, text="Cão & Gato", font=("Segoe UI", 16, "bold"),
                     text_color=TEXT_D).pack(pady=(4, 0))
        ctk.CTkLabel(inner, text="Clínica Veterinária", font=("Segoe UI", 10),
                     text_color=TEXT_M).pack()

        ctk.CTkFrame(inner, height=1, fg_color="#E0E4EA").pack(fill="x", pady=10)

        ctk.CTkLabel(inner, text="Login", font=("Segoe UI", 10, "bold"),
                     text_color=TEXT_D, anchor="w").pack(fill="x")
        self._login_var = ctk.StringVar(value="admin")
        ctk.CTkEntry(inner, textvariable=self._login_var, height=38,
                     border_color="#D5D8DC").pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(inner, text="Senha", font=("Segoe UI", 10, "bold"),
                     text_color=TEXT_D, anchor="w").pack(fill="x")
        self._senha_var = ctk.StringVar(value="admin")
        self._senha_e   = ctk.CTkEntry(inner, textvariable=self._senha_var,
                                        height=38, border_color="#D5D8DC", show="•")
        self._senha_e.pack(fill="x", pady=(2, 8))

        self._err = ctk.CTkLabel(inner, text="", font=("Segoe UI", 11),
                                  text_color="#C0392B")
        self._err.pack(fill="x")

        self._btn = ctk.CTkButton(inner, text="Entrar", height=46,
                                   font=("Segoe UI", 13, "bold"),
                                   fg_color=ACCENT, hover_color=ACCENT_H,
                                   corner_radius=10, command=self._do_login)
        self._btn.pack(fill="x", pady=(6, 0))
        self.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        from database import verificar_login
        login = self._login_var.get().strip()
        senha = self._senha_var.get()
        if not login or not senha:
            self._err.configure(text="Preencha login e senha.")
            return
        self._btn.configure(state="disabled", text="Verificando…")
        self.update()
        if verificar_login(login, senha):
            self.login_success = True
            self.destroy()
        else:
            self._err.configure(text="Login ou senha incorretos.")
            self._btn.configure(state="normal", text="Entrar")
