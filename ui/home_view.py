from datetime import datetime, timezone, timedelta
import customtkinter as ctk
from ui.theme import BG, CARD_BG, ACCENT, ACCENT_H, SUCCESS, TEXT_D, TEXT_M, TEXT_L

TZ = timezone(timedelta(hours=-3))
MESES = ["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]


class HomeView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self._after_id = None
        self._build()
        self._tick()
        self.load_data()
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event=None):
        if event and event.widget is not self: return
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except Exception: pass
            self._after_id = None

    # ── Build ──────────────────────────────────────────────────────────────────
    def _build(self):
        now   = datetime.now(TZ)
        saud  = "Bom dia" if now.hour < 12 else "Boa tarde" if now.hour < 18 else "Boa noite"

        # Top header
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        hdr.pack(fill="x", padx=22, pady=(18, 10))
        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=16)

        ctk.CTkLabel(inner, text=f"🏥  {saud}!",
                     font=("Segoe UI", 18, "bold"), text_color=TEXT_D).pack(side="left")

        clock_f = ctk.CTkFrame(inner, fg_color=ACCENT, corner_radius=10)
        clock_f.pack(side="right")
        ctk.CTkLabel(clock_f, text="📍 Maceió, AL",
                     font=("Segoe UI", 10), text_color="white").pack(padx=14, pady=(6, 0))
        self._clock_lbl = ctk.CTkLabel(clock_f, text="--:--:--",
                                        font=("Segoe UI", 22, "bold"), text_color="white")
        self._clock_lbl.pack(padx=18, pady=(0, 8))

        # Stat cards row
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=22, pady=(0, 8))
        cards_frame.pack_propagate(False)

        self._stat_widgets = {}
        cards_frame.columnconfigure((0,1,2,3,4,5), weight=1)
        card_defs = [
            ("dia_n",  "✂  Hoje",                       ACCENT,   "castrações"),
            ("mes_n",  f"📆  {MESES[now.month]}",        "#7D3C98","castrações"),
            ("ano_n",  f"📅  {now.year}",                "#1A5276","castrações"),
            ("dia_r",  "💰  Hoje",                       SUCCESS,  "arrecadado"),
            ("mes_r",  f"💰  {MESES[now.month]}",        "#117A65","arrecadado"),
            ("ano_r",  f"💰  {now.year}",                "#D4AC0D","arrecadado"),
        ]
        for i, (key, label, color, sub) in enumerate(card_defs):
            c = _StatCard(cards_frame, label=label, sub=sub, color=color)
            c.grid(row=0, column=i, sticky="nsew", padx=4, pady=2)
            self._stat_widgets[key] = c

        # Refresh button
        ref_row = ctk.CTkFrame(self, fg_color="transparent")
        ref_row.pack(fill="x", padx=22, pady=(0, 4))
        ctk.CTkButton(ref_row, text="↺  Atualizar", width=130, height=32,
                      font=("Segoe UI", 11), fg_color=ACCENT, hover_color=ACCENT_H,
                      corner_radius=8, command=self.load_data).pack(side="right")

        # Recent castrations table
        rec_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        rec_card.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        ctk.CTkLabel(rec_card, text="📋  Últimas castrações",
                     font=("Segoe UI", 14, "bold"), text_color=TEXT_D,
                     anchor="w").pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkFrame(rec_card, height=1, fg_color="#E5E8EA").pack(fill="x", padx=20)
        self._list_scroll = ctk.CTkScrollableFrame(rec_card, fg_color="transparent",
                                                    scrollbar_button_color="#D5D8DC")
        self._list_scroll.pack(fill="both", expand=True, padx=14, pady=10)
        self._render_list([])

    # ── Clock ──────────────────────────────────────────────────────────────────
    def _tick(self):
        try:
            self._clock_lbl.configure(text=datetime.now(TZ).strftime("%H:%M:%S"))
            self._after_id = self.after(1000, self._tick)
        except Exception:
            self._after_id = None

    # ── Data ───────────────────────────────────────────────────────────────────
    def load_data(self, _=None):
        try:
            from database import stats, listar_castracoes
            s = stats()
            self._stat_widgets["dia_n"].set(str(s["dia"]["count"]))
            self._stat_widgets["mes_n"].set(str(s["mes"]["count"]))
            self._stat_widgets["ano_n"].set(str(s["ano"]["count"]))
            self._stat_widgets["dia_r"].set(f"R$ {s['dia']['total']:.2f}")
            self._stat_widgets["mes_r"].set(f"R$ {s['mes']['total']:.2f}")
            self._stat_widgets["ano_r"].set(f"R$ {s['ano']['total']:.2f}")
            rows = listar_castracoes("mes")[:15]
            self._render_list(rows)
        except Exception as e:
            import traceback; traceback.print_exc()

    def on_resume(self):
        self.load_data()

    def _render_list(self, rows: list):
        for w in self._list_scroll.winfo_children(): w.destroy()
        if not rows:
            ctk.CTkLabel(self._list_scroll, text="Nenhuma castração registrada este mês.",
                         font=("Segoe UI", 12), text_color=TEXT_M).pack(pady=30)
            return

        # Header
        _Row(self._list_scroll, ["Data/Hora", "Animal", "Sexo", "Peso", "Valor"],
             [148, 90, 80, 90, 100], header=True)
        for i, r in enumerate(rows):
            dt = r["criado_em"][:16]
            from ui.castracoes_view import _fmt_data, _fmt_peso
            peso_txt = _fmt_peso(r["peso_kg"]) + " kg" if r["animal"] != "Gato" else "—"
            _Row(self._list_scroll,
                 [_fmt_data(r["criado_em"]), r["animal"], r["sexo"],
                  peso_txt, f"R$ {r['valor']:.2f}"],
                 [148, 90, 80, 90, 100], even=(i % 2 == 0))


class _StatCard(ctk.CTkFrame):
    def __init__(self, parent, label, sub, color):
        super().__init__(parent, fg_color=color, corner_radius=12, height=96)
        self.pack_propagate(False)
        ctk.CTkLabel(self, text=label, font=("Segoe UI", 10),
                     text_color="white", wraplength=150).pack(pady=(12, 2))
        self._val = ctk.CTkLabel(self, text="—",
                                  font=("Segoe UI", 22, "bold"), text_color="white")
        self._val.pack()
        ctk.CTkLabel(self, text=sub, font=("Segoe UI", 9),
                     text_color="#C8DEFF").pack()

    def set(self, v): self._val.configure(text=str(v))


class _Row(ctk.CTkFrame):
    def __init__(self, parent, cols, widths, header=False, even=True):
        from ui.theme import ROW_EVEN, CARD_BG
        bg = "#E8F0FE" if header else (ROW_EVEN if even else CARD_BG)
        super().__init__(parent, fg_color=bg, corner_radius=6, height=40)
        self.pack(fill="x", pady=1); self.pack_propagate(False)
        font  = ("Segoe UI", 12, "bold") if header else ("Segoe UI", 12)
        color = ACCENT if header else "#1B2631"
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8)
        for text, width in zip(cols, widths):
            ctk.CTkLabel(inner, text=text, font=font, text_color=color,
                         width=width, anchor="w").pack(side="left", padx=4)
