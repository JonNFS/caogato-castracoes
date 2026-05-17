"""
ui/financeiro_view.py — Relatório Financeiro
Mostra receita do dia, semana e mês + gráfico comparativo mês atual vs mês anterior.
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone, timedelta, date
import customtkinter as ctk
from ui.theme import (
    BG, CARD_BG, ACCENT, ACCENT_H, SUCCESS, SUCCESS_H,
    TEXT_D, TEXT_M, TEXT_L, ROW_EVEN, ROW_ODD, HDR_BG,
)

TZ    = timezone(timedelta(hours=-3))
MESES = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]


class FinanceiroView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self._after_id  = None
        self._chart_canvas = None
        self._build()
        self.load_data()
        self.bind("<Destroy>", self._on_destroy)
        self.bind("<Configure>", lambda e: self._draw_chart())

    def _on_destroy(self, event=None):
        if event and event.widget is not self: return
        if self._after_id:
            try: self.after_cancel(self._after_id)
            except Exception: pass

    # ── Build ──────────────────────────────────────────────────────────────────
    def _build(self):
        now = datetime.now(TZ)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        hdr.pack(fill="x", padx=22, pady=(18, 10))
        ih = ctk.CTkFrame(hdr, fg_color="transparent")
        ih.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(ih, text="💰  Relatório Financeiro",
                     font=("Segoe UI", 17, "bold"), text_color=TEXT_D).pack(side="left")
        ctk.CTkButton(ih, text="↺  Atualizar", width=120, height=34,
                      font=("Segoe UI", 11), fg_color=ACCENT, hover_color=ACCENT_H,
                      corner_radius=8, command=self.load_data).pack(side="right")

        # ── Receita cards (3 in a row, always visible) ──
        cards_outer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        cards_outer.pack(fill="x", padx=22, pady=(0, 10))
        ctk.CTkLabel(cards_outer, text="💵  Receita",
                     font=("Segoe UI", 12, "bold"), text_color=TEXT_M,
                     anchor="w").pack(fill="x", padx=18, pady=(12, 8))

        cards_row = ctk.CTkFrame(cards_outer, fg_color="transparent")
        cards_row.pack(fill="x", padx=12, pady=(0, 14))
        cards_row.columnconfigure((0, 1, 2), weight=1)

        self._r_dia  = _MoneyCard(cards_row, "📅  Hoje",                "#1A5276")
        self._r_mes  = _MoneyCard(cards_row, f"📆  {MESES[now.month]}",  "#7D3C98")
        self._r_ano  = _MoneyCard(cards_row, f"📅  {now.year}",           SUCCESS)

        self._r_dia.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")
        self._r_mes.grid(row=0, column=1, padx=6, pady=4, sticky="nsew")
        self._r_ano.grid(row=0, column=2, padx=6, pady=4, sticky="nsew")

        # ── Castrações cards ──
        cast_outer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        cast_outer.pack(fill="x", padx=22, pady=(0, 10))
        ctk.CTkLabel(cast_outer, text="✂  Castrações Realizadas",
                     font=("Segoe UI", 12, "bold"), text_color=TEXT_M,
                     anchor="w").pack(fill="x", padx=18, pady=(12, 8))

        cast_row = ctk.CTkFrame(cast_outer, fg_color="transparent")
        cast_row.pack(fill="x", padx=12, pady=(0, 14))
        cast_row.columnconfigure((0, 1, 2), weight=1)

        self._n_dia = _CountCard(cast_row, "📅  Hoje",                 ACCENT)
        self._n_mes = _CountCard(cast_row, f"📆  {MESES[now.month]}",  "#C0392B")
        self._n_ano = _CountCard(cast_row, f"📅  {now.year}",           "#D4AC0D")

        self._n_dia.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")
        self._n_mes.grid(row=0, column=1, padx=6, pady=4, sticky="nsew")
        self._n_ano.grid(row=0, column=2, padx=6, pady=4, sticky="nsew")

        # ── Chart ──
        chart_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        chart_card.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        ctk.CTkLabel(chart_card, text="📊  Comparativo: Mês Atual vs Mês Anterior",
                     font=("Segoe UI", 13, "bold"), text_color=TEXT_D,
                     anchor="w").pack(fill="x", padx=18, pady=(14, 0))
        ctk.CTkFrame(chart_card, height=1, fg_color="#E5E8EA").pack(fill="x", padx=18, pady=(6, 0))

        # legend is drawn inside the canvas now

        self._chart_frame = ctk.CTkFrame(chart_card, fg_color="#F8FAFD", corner_radius=8)
        self._chart_frame.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self._chart_frame.bind("<Configure>", lambda e: self._draw_chart())

    # ── Data ───────────────────────────────────────────────────────────────────
    def load_data(self, _=None):
        try:
            from database import stats, financeiro_por_semana
            s = stats()
            self._r_dia.set(f"R$ {s['dia']['total']:.2f}")
            self._r_mes.set(f"R$ {s['mes']['total']:.2f}")
            self._r_ano.set(f"R$ {s['ano']['total']:.2f}")
            self._n_dia.set(str(s['dia']['count']))
            self._n_mes.set(str(s['mes']['count']))
            self._n_ano.set(str(s['ano']['count']))
            self._chart_data = financeiro_por_semana()
            self._draw_chart()
        except Exception as e:
            pass

    def on_resume(self): self.load_data()

    # ── Chart (pure tkinter Canvas bar chart) ────────────────────────────────
    def _draw_chart(self):
        try:
            data = getattr(self, "_chart_data", None)
            if data is None: return
            frame = self._chart_frame
            frame.update_idletasks()
            W = frame.winfo_width()
            H = frame.winfo_height()
            if W < 100 or H < 80: return

            if self._chart_canvas:
                try: self._chart_canvas.destroy()
                except Exception: pass

            cv = tk.Canvas(frame, width=W, height=H, bg="#F8FAFD",
                           highlightthickness=0, bd=0)
            cv.pack(fill="both", expand=True)
            self._chart_canvas = cv

            weeks_prev = data.get("mes_anterior", [0]*4)
            weeks_curr = data.get("mes_atual",    [0]*4)
            nome_prev  = data.get("mes_anterior_nome", "Mês anterior")
            nome_curr  = data.get("mes_atual_nome",    "Mês atual")
            # Week date ranges for labels
            week_labels = ["Dias 1–7", "Dias 8–14", "Dias 15–21", "Dias 22–31"]

            all_vals = weeks_prev + weeks_curr
            max_val  = max(all_vals) if any(v > 0 for v in all_vals) else 200
            # Round max up to a nice number
            import math
            max_val = max(max_val * 1.15, 100)
            step = 10 ** math.floor(math.log10(max_val)) // 2 or 1
            max_val = math.ceil(max_val / step) * step

            pad_l, pad_r = 72, 24
            pad_t, pad_b = 32, 72
            chart_w = W - pad_l - pad_r
            chart_h = H - pad_t - pad_b

            # Background stripe for current month
            cv.create_rectangle(pad_l, pad_t, W - pad_r, pad_t + chart_h,
                                 fill="#F0F5FF", outline="")

            # Y axis gridlines
            n_lines = 5
            for i in range(n_lines + 1):
                y   = pad_t + chart_h - (i / n_lines) * chart_h
                val = (max_val * i) / n_lines
                cv.create_line(pad_l, y, W - pad_r, y,
                               fill="#D5DCE8" if i > 0 else "#9EB0C8", dash=(5, 4))
                cv.create_text(pad_l - 6, y, text=f"R${val:.0f}",
                               anchor="e", font=("Segoe UI", 9, "bold"), fill="#64748B")

            n_groups = 4
            group_w  = chart_w / n_groups
            bar_w    = group_w * 0.26
            gap      = group_w * 0.05

            COLOR_PREV = "#4A7EC7"   # softer blue
            COLOR_CURR = "#5FAD2A"   # green

            for i in range(n_groups):
                vp  = weeks_prev[i] if i < len(weeks_prev) else 0
                vc  = weeks_curr[i] if i < len(weeks_curr) else 0
                gx  = pad_l + i * group_w + group_w * 0.10

                bx  = pad_t + chart_h   # baseline y

                # ── Prev month bar ──
                hp  = (vp / max_val) * chart_h if max_val > 0 else 0
                x1, x2 = gx, gx + bar_w
                y1      = bx - hp
                # Rounded top via arc trick
                cv.create_rectangle(x1, y1 + 4, x2, bx, fill=COLOR_PREV, outline="")
                if hp > 4:
                    cv.create_oval(x1, y1, x2, y1 + 8, fill=COLOR_PREV, outline="")
                if vp > 0:
                    label_y = y1 - 5
                    cv.create_text((x1+x2)/2, label_y,
                                   text=f"R${vp:.0f}",
                                   font=("Segoe UI", 8, "bold"),
                                   fill=COLOR_PREV, anchor="s")

                # ── Curr month bar ──
                hc  = (vc / max_val) * chart_h if max_val > 0 else 0
                x1c = gx + bar_w + gap
                x2c = x1c + bar_w
                y1c = bx - hc
                cv.create_rectangle(x1c, y1c + 4, x2c, bx, fill=COLOR_CURR, outline="")
                if hc > 4:
                    cv.create_oval(x1c, y1c, x2c, y1c + 8, fill=COLOR_CURR, outline="")
                if vc > 0:
                    cv.create_text((x1c+x2c)/2, y1c - 5,
                                   text=f"R${vc:.0f}",
                                   font=("Segoe UI", 8, "bold"),
                                   fill=COLOR_CURR, anchor="s")

                # ── X labels: week range + separator ──
                cx = gx + bar_w + gap / 2
                lbl = week_labels[i]
                cv.create_text(cx, bx + 14, text=lbl,
                               font=("Segoe UI", 9, "bold"), fill="#334155")
                # Vertical separator between groups
                if i < n_groups - 1:
                    sx = gx + group_w - group_w * 0.10
                    cv.create_line(sx, pad_t + 10, sx, bx,
                                   fill="#E2E8F0", dash=(3, 4))

            # ── Baseline ──
            cv.create_line(pad_l, pad_t + chart_h, W - pad_r, pad_t + chart_h,
                           fill="#9EB0C8", width=2)

            # ── Legend at bottom ──
            leg_y = H - 18
            cx = W // 2
            for dx, color, label in [(-90, COLOR_PREV, nome_prev),
                                      (+20, COLOR_CURR, nome_curr)]:
                lx = cx + dx
                cv.create_rectangle(lx, leg_y - 9, lx + 14, leg_y + 3,
                                    fill=color, outline="")
                cv.create_text(lx + 18, leg_y - 3, text=label,
                               anchor="w", font=("Segoe UI", 10, "bold"), fill="#334155")

        except Exception:
            import traceback; traceback.print_exc()


# ── Sub-widgets ────────────────────────────────────────────────────────────────

class _MoneyCard(ctk.CTkFrame):
    def __init__(self, parent, label, color):
        super().__init__(parent, fg_color=color, corner_radius=12, height=86)
        self.pack_propagate(False)
        ctk.CTkLabel(self, text=label, font=("Segoe UI", 10),
                     text_color="white", wraplength=160).pack(pady=(10, 2))
        self._val = ctk.CTkLabel(self, text="R$ —",
                                  font=("Segoe UI", 18, "bold"), text_color="white")
        self._val.pack()

    def set(self, v): self._val.configure(text=v)


class _CountCard(ctk.CTkFrame):
    def __init__(self, parent, label, color):
        super().__init__(parent, fg_color=color, corner_radius=12, height=72)
        self.pack_propagate(False)
        ctk.CTkLabel(self, text=label, font=("Segoe UI", 10),
                     text_color="white", wraplength=160).pack(pady=(8, 2))
        self._val = ctk.CTkLabel(self, text="—",
                                  font=("Segoe UI", 20, "bold"), text_color="white")
        self._val.pack()

    def set(self, v): self._val.configure(text=v)


def _legend_dot(parent, color, label):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(side="left", padx=8)
    ctk.CTkFrame(f, fg_color=color, width=12, height=12,
                 corner_radius=3).pack(side="left", padx=(0, 4))
    ctk.CTkLabel(f, text=label, font=("Segoe UI", 10),
                 text_color=TEXT_M).pack(side="left")
