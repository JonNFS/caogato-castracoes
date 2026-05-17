"""
ui/castracoes_view.py — Lista e formulário de castrações.
Features:
  - Filtro por período (hoje/semana/mês/todos)
  - Peso exibido com 3 casas decimais (ex: 10.500)
  - Data no formato brasileiro DD/MM/AAAA HH:MM
  - Forma de pagamento: Pix / Cartão / Espécie
  - Botão direito: copiar registro individual
  - Botão "Copiar Lista": copia todos em formato tabular bonito
"""
import re
from tkinter import messagebox
import customtkinter as ctk
from tkinter import ttk
from ui.theme import (
    BG, CARD_BG, ACCENT, ACCENT_H, SUCCESS, SUCCESS_H,
    DANGER, DANGER_H, TEXT_D, TEXT_M, TEXT_L,
    ROW_EVEN, ROW_ODD, ROW_SEL, HDR_BG,
)

ANIMAL_OPTS   = ["Cão", "Gato"]
SEXO_OPTS     = ["Macho", "Fêmea"]
PGTO_OPTS     = ["Pix", "Cartão", "Espécie"]
FILTRO_OPTS   = [("📅  Hoje","dia"),("📆  Este mês","mes"),
                 ("📅  Este ano","ano"),("📋  Todos","todos")]

PGTO_ICON = {"Pix": "📱", "Cartão": "💳", "Espécie": "💵"}


def _fmt_data(dt_str: str) -> str:
    """Convert 2026-05-05 17:03 → 05/05/2026 17:03"""
    try:
        date_part, time_part = dt_str[:16].split(" ")
        y, m, d = date_part.split("-")
        return f"{d}/{m}/{y} {time_part}"
    except Exception:
        return dt_str[:16]


def _fmt_peso(peso: float) -> str:
    return f"{peso:.3f}"


def _apply_tree_style():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Cast.Treeview",
        background=ROW_ODD, foreground=TEXT_D, rowheight=40,
        fieldbackground=ROW_ODD, borderwidth=0,
        font=("Segoe UI", 11), indent=0, padding=(0, 4))
    s.configure("Cast.Treeview.Heading",
        background=HDR_BG, foreground=ACCENT,
        font=("Segoe UI", 11, "bold"), relief="flat", padding=(4, 4))
    s.map("Cast.Treeview",
        background=[("selected", ROW_SEL)],
        foreground=[("selected", TEXT_D)])


class CastracoesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        _apply_tree_style()
        self._all_rows = []
        self._filtro   = "mes"
        self._build()
        self.load_data()

    def _build(self):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        hdr.pack(fill="x", padx=22, pady=(18, 10))
        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)
        ctk.CTkLabel(inner, text="✂  Castrações",
                     font=("Segoe UI", 17, "bold"), text_color=TEXT_D).pack(side="left")

        # Buttons
        ctk.CTkButton(inner, text="🗑️  Deletar Tudo", width=140, height=38,
                      font=("Segoe UI", 11, "bold"),
                      fg_color=DANGER, hover_color=DANGER_H,
                      corner_radius=9, command=self._delete_all).pack(side="right", padx=(6,0))
        ctk.CTkButton(inner, text="📋  Copiar Lista", width=140, height=38,
                      font=("Segoe UI", 11, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_H,
                      corner_radius=9, command=self._copy_list).pack(side="right", padx=(6,0))
        ctk.CTkButton(inner, text="＋  Nova Castração", width=165, height=38,
                      font=("Segoe UI", 12, "bold"),
                      fg_color=SUCCESS, hover_color=SUCCESS_H,
                      corner_radius=9, command=self._open_form).pack(side="right")

        # ── Filters ──
        flt = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, height=60)
        flt.pack(fill="x", padx=22, pady=(0, 8))
        flt.pack_propagate(False)
        fi = ctk.CTkFrame(flt, fg_color="transparent")
        fi.pack(fill="both", expand=True, padx=16)
        ctk.CTkLabel(fi, text="Período:", font=("Segoe UI", 11, "bold"),
                     text_color=TEXT_D).pack(side="left", padx=(0,10))
        self._flt_var = ctk.StringVar(value="📆  Este mês")
        for label, key in FILTRO_OPTS:
            ctk.CTkRadioButton(fi, text=label, variable=self._flt_var, value=label,
                               font=("Segoe UI", 11), text_color=TEXT_D,
                               fg_color=ACCENT, hover_color=ACCENT_H,
                               command=lambda k=key, l=label: self._set_filter(k, l)
                               ).pack(side="left", padx=10)

        # ── Table ──
        tbl_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14)
        tbl_card.pack(fill="both", expand=True, padx=22, pady=(0,8))

        cols = ("id","data","animal","sexo","peso","valor","pagamento")
        self.tree = ttk.Treeview(tbl_card, columns=cols, show="headings",
                                  selectmode="browse", style="Cast.Treeview")

        # Fixed widths, no stretch gap
        hdrs = [
            ("ID",         "id",         52, "w", False),
            ("Data/Hora",  "data",       148, "w", False),
            ("Animal",     "animal",      80, "w", False),
            ("Sexo",       "sexo",        80, "w", False),
            ("Peso (kg)",  "peso",        90, "w", False),
            ("Valor",      "valor",      105, "w", False),
            ("Pagamento",  "pagamento",  130, "w", True ),   # stretch
        ]
        for text, cid, width, anch, stretch in hdrs:
            self.tree.heading(cid, text=text, anchor=anch)
            self.tree.column(cid, width=width, minwidth=width,
                             anchor=anch, stretch=stretch)

        self.tree.tag_configure("even", background=ROW_EVEN)
        self.tree.tag_configure("odd",  background=ROW_ODD)

        # Block resize separators
        self.tree.bind("<Button-1>",
            lambda e: "break" if self.tree.identify_region(e.x,e.y)=="separator" else None)
        # Right-click context menu
        self.tree.bind("<Button-3>", self._right_click)

        vsb = ttk.Scrollbar(tbl_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        vsb.pack(side="right", fill="y", pady=10, padx=(0,6))

        # Context menu (right-click)
        self._ctx_menu = ctk.CTkFrame.__new__(ctk.CTkFrame)  # placeholder
        import tkinter as tk
        self._menu = tk.Menu(self, tearoff=0,
                             font=("Segoe UI", 11),
                             bg="white", fg=TEXT_D,
                             activebackground=ROW_SEL,
                             relief="flat", bd=1)
        self._menu.add_command(label="📋  Copiar este registro",
                               command=self._copy_selected)
        self._menu.add_command(label="✏️  Editar", command=self._edit)
        self._menu.add_separator()
        self._menu.add_command(label="🗑️  Excluir", command=self._delete)

        # ── Action bar ──
        act = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, height=58)
        act.pack(fill="x", padx=22, pady=(0,18))
        act.pack_propagate(False)
        ai = ctk.CTkFrame(act, fg_color="transparent")
        ai.pack(fill="both", expand=True, padx=16)
        ctk.CTkLabel(ai, text="Selecione um registro:",
                     font=("Segoe UI", 11), text_color=TEXT_M).pack(side="left")
        ctk.CTkButton(ai, text="✏️  Editar", width=110, height=34,
                      font=("Segoe UI", 11), fg_color=ACCENT, hover_color=ACCENT_H,
                      corner_radius=8, command=self._edit).pack(side="left", padx=(14,6))
        ctk.CTkButton(ai, text="🗑️  Excluir", width=110, height=34,
                      font=("Segoe UI", 11), fg_color=DANGER, hover_color=DANGER_H,
                      corner_radius=8, command=self._delete).pack(side="left")
        self._count_lbl = ctk.CTkLabel(ai, text="", font=("Segoe UI",11), text_color=TEXT_L)
        self._count_lbl.pack(side="right")

    # ── Data ──────────────────────────────────────────────────────────────────
    def _set_filter(self, key, label):
        self._filtro = key; self._flt_var.set(label); self.load_data()

    def load_data(self, _=None):
        from database import listar_castracoes
        self._all_rows = listar_castracoes(self._filtro)
        self._render()

    def on_resume(self): self.load_data()

    def _render(self):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self._all_rows):
            tag  = "even" if i % 2 == 0 else "odd"
            pgto = r.get("pagamento","Espécie")
            icon = PGTO_ICON.get(pgto, "💵")
            peso = _fmt_peso(r["peso_kg"]) if r["animal"] != "Gato" else "—"
            self.tree.insert("", "end", iid=str(r["id"]),
                values=(r["id"],
                        _fmt_data(r["criado_em"]),
                        r["animal"], r["sexo"],
                        peso,
                        f"R$ {r['valor']:.2f}",
                        f"{icon} {pgto}"),
                tags=(tag,))
        n = len(self._all_rows)
        self._count_lbl.configure(text=f"{n} registro{'s' if n!=1 else ''}")

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _selected_row(self):
        cid = self._selected_id()
        if cid is None: return None
        return next((r for r in self._all_rows if r["id"] == cid), None)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _open_form(self, data=None):
        CastracaoDialog(self, data=data, on_saved=self._on_saved)

    def _edit(self):
        row = self._selected_row()
        if not row: messagebox.showwarning("Aviso","Selecione um registro."); return
        self._open_form(data=row)

    def _delete(self):
        row = self._selected_row()
        if not row: messagebox.showwarning("Aviso","Selecione um registro."); return
        if messagebox.askyesno("Confirmar",
                               f"Excluir castração #{row['id']} "
                               f"({row['animal']}, {row['sexo']})?"):
            from database import excluir_castracao
            excluir_castracao(row["id"])
            self.load_data()

    def _delete_all(self):
        from database import deletar_todas_castracoes
        from database import listar_castracoes
        total = len(listar_castracoes("todos"))
        if total == 0:
            messagebox.showinfo("Vazio", "Nao ha castracoes registradas."); return
        msg1 = "Deletar PERMANENTEMENTE todas as " + str(total) + " castracoes? Tem certeza?"
        if not messagebox.askyesno("Atencao", msg1): return
        if not messagebox.askyesno("Confirmacao Final",
                                   "Esta acao NAO pode ser desfeita. Confirmar?"): return
        deletar_todas_castracoes()
        self.load_data()
        messagebox.showinfo("Concluido", "Todos os registros foram excluidos.")

    def _on_saved(self): self.load_data()

    def _right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self._menu.post(event.x_root, event.y_root)

    def _copy_selected(self):
        row = self._selected_row()
        if not row: return
        pgto = row.get("pagamento","Espécie")
        icon = PGTO_ICON.get(pgto,"💵")
        peso_txt = _fmt_peso(row["peso_kg"]) + " kg" if row["animal"] != "Gato" else "—"
        text = (
            f"✂ Castração #{row['id']}\n"
            f"📅 {_fmt_data(row['criado_em'])}\n"
            f"🐾 {row['animal']} · {row['sexo']}\n"
            f"⚖ Peso: {peso_txt}\n"
            f"💰 Valor: R$ {row['valor']:.2f}\n"
            f"{icon} Pagamento: {pgto}"
        )
        self.clipboard_clear(); self.clipboard_append(text)
        messagebox.showinfo("Copiado!",
                            "Registro copiado para a área de transferência.", parent=self)

    def _copy_list(self):
        if not self._all_rows:
            messagebox.showinfo("Vazio","Nenhum registro para copiar."); return

        from database import stats
        s = stats()

        lines = []
        lines.append("=" * 54)
        lines.append("       🐾  CÃO & GATO — CASTRAÇÕES")
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=-3)))
        lines.append(f"       {now.strftime('%d/%m/%Y %H:%M')}")
        lines.append("=" * 54)
        lines.append(f"{'ID':<4} {'Data/Hora':<17} {'Animal':<6} {'Sexo':<7} {'Peso':<8} {'Valor':<10} {'Pgto'}")
        lines.append("-" * 54)
        for r in self._all_rows:
            pgto = r.get("pagamento","Espécie")
            peso_txt = _fmt_peso(r["peso_kg"]) if r["animal"] != "Gato" else "—     "
            lines.append(
                f"{r['id']:<4} {_fmt_data(r['criado_em']):<17} "
                f"{r['animal']:<6} {r['sexo']:<7} "
                f"{peso_txt:<8} R${r['valor']:>7.2f}  {pgto}"
            )
        lines.append("=" * 54)
        # Totals
        total_val = sum(r["valor"] for r in self._all_rows)
        lines.append(f"  Total registros : {len(self._all_rows)}")
        lines.append(f"  Total arrecadado: R$ {total_val:.2f}")
        lines.append("=" * 54)
        lines.append("  Desenvolvido por Jonathan Nunes")

        text = "\n".join(lines)
        self.clipboard_clear(); self.clipboard_append(text)
        messagebox.showinfo("Lista Copiada!",
                            f"{len(self._all_rows)} registros copiados.\n"
                            "Cole em qualquer lugar (Ctrl+V).", parent=self)


# ── Form Dialog ───────────────────────────────────────────────────────────────
class CastracaoDialog(ctk.CTkToplevel):
    def __init__(self, parent, data=None, on_saved=None):
        super().__init__(parent)
        self._data     = data
        self._on_saved = on_saved
        title = "Editar Castração" if data else "Nova Castração"
        self.title(title)
        self.geometry("460x530")
        self.resizable(False, False)
        self.grab_set(); self.lift(); self.focus_force()
        self.configure(fg_color=CARD_BG)
        self._build()

    def _build(self):
        # Header bar
        hdr = ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="✂  " + self.title(),
                     font=("Segoe UI", 13, "bold"), text_color="white"
                     ).pack(side="left", padx=22, pady=12)

        form = ctk.CTkFrame(self, fg_color=CARD_BG)
        form.pack(fill="both", expand=True, padx=28, pady=(16, 0))

        def _lbl(t):
            ctk.CTkLabel(form, text=t, font=("Segoe UI", 10, "bold"),
                         text_color=TEXT_D, anchor="w").pack(fill="x", pady=(8, 1))

        # Animal
        _lbl("Animal")
        self._animal_var = ctk.StringVar(
            value=self._data["animal"] if self._data else "Cão")
        row_a = ctk.CTkFrame(form, fg_color="transparent")
        row_a.pack(fill="x")
        for opt in ANIMAL_OPTS:
            ctk.CTkRadioButton(row_a, text=opt, variable=self._animal_var, value=opt,
                               font=("Segoe UI", 12), text_color=TEXT_D,
                               fg_color=ACCENT, hover_color=ACCENT_H,
                               command=self._recalc).pack(side="left", padx=(0,20))

        # Sexo
        _lbl("Sexo")
        self._sexo_var = ctk.StringVar(
            value=self._data["sexo"] if self._data else "Macho")
        row_s = ctk.CTkFrame(form, fg_color="transparent")
        row_s.pack(fill="x")
        for opt in SEXO_OPTS:
            ctk.CTkRadioButton(row_s, text=opt, variable=self._sexo_var, value=opt,
                               font=("Segoe UI", 12), text_color=TEXT_D,
                               fg_color=ACCENT, hover_color=ACCENT_H
                               ).pack(side="left", padx=(0,20))

        # Peso
        _lbl("Peso (kg)")
        row_p = ctk.CTkFrame(form, fg_color="transparent")
        row_p.pack(fill="x")
        self._peso_var = ctk.StringVar(
            value=f"{self._data['peso_kg']:.3f}" if self._data and self._data["animal"] != "Gato" else "")
        self._peso_entry = ctk.CTkEntry(
            row_p, textvariable=self._peso_var,
            placeholder_text="Ex: 9.500", height=38,
            corner_radius=8, border_color="#D5D8DC", width=160)
        self._peso_entry.pack(side="left")
        self._peso_entry.bind("<KeyRelease>", lambda e: self._recalc())
        ctk.CTkLabel(row_p, text="kg", font=("Segoe UI", 12),
                     text_color=TEXT_M).pack(side="left", padx=8)

        # Valor
        _lbl("Valor (R$)  — calculado automaticamente")
        self._valor_var = ctk.StringVar(
            value=f"{self._data['valor']:.2f}" if self._data else "")
        ctk.CTkEntry(form, textvariable=self._valor_var,
                     placeholder_text="Ex: 200.00", height=38,
                     corner_radius=8, border_color="#D5D8DC").pack(fill="x")

        # Hint
        self._hint = ctk.CTkLabel(form, text="", font=("Segoe UI", 10),
                                   text_color=TEXT_M, anchor="w")
        self._hint.pack(fill="x", pady=(2, 0))

        # Pagamento
        _lbl("Forma de Pagamento")
        pgto_row = ctk.CTkFrame(form, fg_color="#F8FAFD", corner_radius=8,
                                 border_width=1, border_color="#E5E8EA")
        pgto_row.pack(fill="x", pady=(2, 0))
        pgto_inner = ctk.CTkFrame(pgto_row, fg_color="transparent")
        pgto_inner.pack(fill="x", padx=12, pady=10)

        cur_pgto = self._data.get("pagamento","Espécie") if self._data else "Espécie"
        self._pgto_var = ctk.StringVar(value=cur_pgto)
        for opt in PGTO_OPTS:
            icon = PGTO_ICON.get(opt,"")
            ctk.CTkRadioButton(
                pgto_inner, text=f"{icon} {opt}",
                variable=self._pgto_var, value=opt,
                font=("Segoe UI", 12), text_color=TEXT_D,
                fg_color=ACCENT, hover_color=ACCENT_H
            ).pack(side="left", padx=(0, 18))

        # Buttons
        bf = ctk.CTkFrame(self, fg_color=CARD_BG)
        bf.pack(fill="x", padx=28, pady=12)
        ctk.CTkButton(bf, text="Cancelar", width=120, height=38,
                      fg_color="#E5E8EA", text_color=TEXT_M, hover_color="#CBD2D9",
                      corner_radius=9, command=self.destroy).pack(side="right", padx=(6,0))
        ctk.CTkButton(bf, text="💾  Salvar", width=130, height=38,
                      fg_color=SUCCESS, hover_color=SUCCESS_H,
                      corner_radius=9, command=self._submit).pack(side="right")

        # Initial calc / lock
        self._recalc()

    def _recalc(self, _=None):
        import math
        from database import calcular_valor
        animal = self._animal_var.get()
        if animal == "Gato":
            self._peso_entry.configure(state="disabled", fg_color="#F0F0F0",
                                        placeholder_text="—")
            self._peso_var.set("")
            self._valor_var.set("100.00")
            self._hint.configure(text="Gato: R$ 100,00 fixo. Peso não necessário.")
            return
        else:
            self._peso_entry.configure(state="normal", fg_color="white",
                                        placeholder_text="Ex: 9.500")
        try:
            peso = float(self._peso_var.get().replace(",","."))
            if peso <= 0: raise ValueError
        except ValueError:
            self._hint.configure(text="")
            return
        valor     = calcular_valor(animal, peso)
        extra_kg  = math.floor(peso) - 10 if peso > 10 else 0
        self._valor_var.set(f"{valor:.2f}")
        if peso <= 10:
            self._hint.configure(text=f"Cão {peso:.3f} kg (≤ 10 kg): R$ 200,00")
        else:
            self._hint.configure(
                text=f"Cão {peso:.3f} kg: R$ 200,00 + {extra_kg} kg × R$10 = R$ {valor:.2f}")

    def _submit(self):
        animal  = self._animal_var.get()
        sexo    = self._sexo_var.get()
        pagamento = self._pgto_var.get()
        try:
            if animal == "Gato":
                peso  = 0.0
                valor = 100.0
            else:
                peso_str = self._peso_var.get().strip().replace(",",".")
                if not peso_str:
                    messagebox.showwarning("Peso obrigatório",
                                           "Informe o peso do cão.", parent=self); return
                peso = float(peso_str)
                if peso <= 0:
                    messagebox.showwarning("Peso inválido",
                                           "O peso deve ser maior que zero.", parent=self); return
                valor_str = self._valor_var.get().strip().replace(",",".")
                valor = float(valor_str) if valor_str else 0.0
        except ValueError as e:
            messagebox.showwarning("Inválido", f"Verifique os campos.\n{e}", parent=self); return
        try:
            if self._data:
                from database import _conn
                with _conn() as con:
                    con.execute(
                        "UPDATE castracoes SET animal=?,sexo=?,peso_kg=?,valor=?,pagamento=? WHERE id=?",
                        (animal, sexo, round(peso,3), round(valor,2), pagamento, self._data["id"])
                    )
            else:
                from database import adicionar_castracao
                adicionar_castracao(animal, sexo, peso, valor, pagamento)
            if self._on_saved: self._on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)
