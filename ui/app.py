import os
from datetime import datetime
import tkinter as tk
import customtkinter as ctk
from ui.theme import SIDEBAR_BG, SIDEBAR_HOVER, SIDEBAR_SEL, BG, TEXT_L, TEXT_D

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_sidebar_logo(target_w=160):
    path = os.path.join(_ROOT, "Logo.png")
    if not os.path.exists(path): return None
    try:
        from PIL import Image
        from customtkinter import CTkImage
        sr, sg, sb = int(SIDEBAR_BG[1:3], 16), int(SIDEBAR_BG[3:5], 16), int(SIDEBAR_BG[5:7], 16)
        img = Image.open(path).convert("RGB")
        bg  = Image.new("RGB", img.size, (sr, sg, sb))
        mask = img.convert("L").point(lambda v: 255 if v < 28 else 0, "L")
        result = img.copy(); result.paste(bg, mask=mask)
        ratio  = target_w / result.width
        return CTkImage(light_image=result, size=(target_w, int(result.height * ratio)))
    except Exception:
        return None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cão & Gato — Castrações")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        self.after(10, lambda: self.state("zoomed"))
        try:
            ico = os.path.join(_ROOT, "Logo.ico")
            if os.path.exists(ico): self.iconbitmap(ico)
        except Exception:
            pass
        self._views: dict  = {}
        self._current: str = ""
        self._build_sidebar()
        self._build_content()
        self.show_view("home")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        brand = ctk.CTkFrame(self.sidebar, fg_color=SIDEBAR_BG)
        brand.pack(pady=(18, 4), padx=10, fill="x")
        logo_img = _load_sidebar_logo(160)
        if logo_img:
            lbl = ctk.CTkLabel(brand, image=logo_img, text="")
            lbl.image = logo_img; lbl.pack()
        else:
            ctk.CTkLabel(brand, text="🐾", font=("Segoe UI", 36)).pack()
            ctk.CTkLabel(brand, text="Cão & Gato",
                         font=("Segoe UI", 17, "bold"), text_color="white").pack()

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#3568B5").pack(fill="x", padx=18, pady=8)

        # Nav buttons
        nav_items = [
            ("🏠  Início",         "home"),
            ("✂  Castrações",     "castracoes"),
            ("💰  Financeiro",     "financeiro"),
        ]
        self._nav_btns: dict = {}
        for label, key in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                font=("Segoe UI", 13), height=46, corner_radius=10,
                fg_color="transparent", text_color=TEXT_L,
                hover_color=SIDEBAR_HOVER,
                command=lambda k=key: self.show_view(k))
            btn.pack(fill="x", padx=12, pady=2)
            self._nav_btns[key] = btn

        # Logout
        ctk.CTkButton(self.sidebar, text="⬅  Sair", anchor="w",
                      font=("Segoe UI", 12), height=40, corner_radius=10,
                      fg_color="#C0392B", hover_color="#A93226", text_color="white",
                      command=self._logout).pack(fill="x", padx=12, pady=(12, 4))

        # Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", pady=12)
        ctk.CTkLabel(footer, text="Cão & Gato © 2026",
                     font=("Segoe UI", 11, "bold"), text_color="white").pack()
        ctk.CTkLabel(footer, text="Desenvolvido por",
                     font=("Segoe UI", 10), text_color="#C8DEFF").pack()
        ctk.CTkLabel(footer, text="Jonathan Nunes",
                     font=("Segoe UI", 11, "bold"), text_color="white").pack()

    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def show_view(self, key: str):
        if self._current:
            self._views[self._current].pack_forget()
            self._nav_btns[self._current].configure(
                fg_color="transparent", text_color=TEXT_L)

        if key not in self._views:
            from ui.home_view        import HomeView
            from ui.castracoes_view  import CastracoesView
            from ui.financeiro_view  import FinanceiroView
            view_map = {"home": HomeView, "castracoes": CastracoesView,
                        "financeiro": FinanceiroView}
            self._views[key] = view_map[key](self.content)

        self._views[key].pack(fill="both", expand=True)
        self._nav_btns[key].configure(fg_color=SIDEBAR_SEL, text_color="white")
        self._current = key
        if hasattr(self._views[key], "load_data"):
            self._views[key].load_data()

    def _logout(self):
        self.destroy()
