"""
database.py — SQLite local, sem dependências externas.
Banco criado automaticamente na pasta do executável/script.
"""
import os
import sys
import sqlite3
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

# ── Caminho do banco ──────────────────────────────────────────────────────────
def _db_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "castracoes.db")

DB_PATH = _db_path()

# ── Fuso Maceió ──────────────────────────────────────────────────────────────
TZ = timezone(timedelta(hours=-3))


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ── Setup ─────────────────────────────────────────────────────────────────────
def init_db():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS castracoes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            animal      TEXT    NOT NULL CHECK(animal IN ('Cão','Gato')),
            sexo        TEXT    NOT NULL CHECK(sexo   IN ('Macho','Fêmea')),
            peso_kg     REAL    NOT NULL,
            valor       REAL    NOT NULL,
            criado_em   TEXT    NOT NULL,
            pagamento   TEXT    NOT NULL DEFAULT 'Espécie'
        );
        """)
        # Add pagamento column to existing DBs (idempotent)
        try:
            con.execute("ALTER TABLE castracoes ADD COLUMN pagamento TEXT NOT NULL DEFAULT 'Espécie'")
        except Exception:
            pass  # column already exists
        # Seed admin user table (for login only)
        con.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            login    TEXT NOT NULL UNIQUE,
            senha    TEXT NOT NULL
        );
        """)
        # Insert default admin if not exists
        con.execute(
            "INSERT OR IGNORE INTO usuarios (login, senha) VALUES (?, ?)",
            ("admin", "admin")
        )


# ── Pricing logic ─────────────────────────────────────────────────────────────
def calcular_valor(animal: str, peso_kg: float) -> float:
    """
    Gato:  sempre R$ 100,00 (independente do sexo/peso)
    Cão:   até 10 kg → R$ 200,00
           acima de 10 kg → R$ 200,00 + (peso - 10) * R$ 10,00 por kg excedente
    """
    if animal == "Gato":
        return 100.0
    else:  # Cão
        if peso_kg <= 10:
            return 200.0
        # Cobrar por kg INTEIRO acima de 10 (ex: 13,5kg = 3kg extra = R$30)
        import math
        extra_kg = math.floor(peso_kg) - 10
        return 200.0 + extra_kg * 10.0


# ── Auth ──────────────────────────────────────────────────────────────────────
def verificar_login(login: str, senha: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT id FROM usuarios WHERE login=? AND senha=?", (login, senha)
        ).fetchone()
        return row is not None


# ── CRUD Castrações ───────────────────────────────────────────────────────────
def adicionar_castracao(animal: str, sexo: str, peso_kg: float, valor: float, pagamento: str = "Espécie") -> int:
    agora = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO castracoes (animal, sexo, peso_kg, valor, pagamento, criado_em) VALUES (?,?,?,?,?,?)",
            (animal, sexo, round(peso_kg, 3), round(valor, 2), pagamento, agora)
        )
        return cur.lastrowid


def listar_castracoes(filtro: str = "mes") -> list[dict]:
    """
    filtro: 'dia' | 'semana' | 'mes' | 'todos'
    Retorna lista de dicts ordenada do mais recente para o mais antigo.
    """
    hoje  = datetime.now(TZ)
    if filtro == "dia":
        desde = hoje.strftime("%Y-%m-%d") + " 00:00:00"
    elif filtro == "mes":
        desde = hoje.strftime("%Y-%m") + "-01 00:00:00"
    elif filtro == "ano":
        desde = hoje.strftime("%Y") + "-01-01 00:00:00"
    else:
        desde = "2000-01-01 00:00:00"

    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM castracoes WHERE criado_em >= ? ORDER BY id ASC",
            (desde,)
        ).fetchall()
        return [dict(r) for r in rows]


def excluir_castracao(cid: int):
    with _conn() as con:
        con.execute("DELETE FROM castracoes WHERE id=?", (cid,))


def stats() -> dict:
    """Returns counts and totals for dia, semana, mes."""
    hoje  = datetime.now(TZ)
    dia   = hoje.strftime("%Y-%m-%d") + " 00:00:00"
    ini_m = hoje.strftime("%Y-%m") + "-01 00:00:00"
    ini_a = hoje.strftime("%Y") + "-01-01 00:00:00"

    with _conn() as con:
        def _q(desde):
            r = con.execute(
                "SELECT COUNT(*) as n, COALESCE(SUM(valor),0) as total "
                "FROM castracoes WHERE criado_em >= ?", (desde,)
            ).fetchone()
            return {"count": r["n"], "total": r["total"]}

        return {
            "dia": _q(dia),
            "mes": _q(ini_m),
            "ano": _q(ini_a),
        }


def financeiro_por_semana() -> dict:
    """
    Returns weekly totals for the current and previous month.
    Each month is split into 4 weeks (days 1-7, 8-14, 15-21, 22-31).
    """
    now   = datetime.now(TZ)
    year  = now.year
    month = now.month

    # Previous month
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    MESES_PT = ["","Jan","Fev","Mar","Abr","Mai","Jun",
                "Jul","Ago","Set","Out","Nov","Dez"]

    def _weekly_totals(y, m):
        weeks = [(1,7),(8,14),(15,21),(22,31)]
        totals = []
        with _conn() as con:
            for d1, d2 in weeks:
                desde = f"{y:04d}-{m:02d}-{d1:02d} 00:00:00"
                ate   = f"{y:04d}-{m:02d}-{d2:02d} 23:59:59"
                row   = con.execute(
                    "SELECT COALESCE(SUM(valor),0) as t FROM castracoes "
                    "WHERE criado_em BETWEEN ? AND ?", (desde, ate)
                ).fetchone()
                totals.append(round(row["t"], 2))
        return totals

    return {
        "mes_anterior": _weekly_totals(prev_year, prev_month),
        "mes_atual":    _weekly_totals(year, month),
        "labels": ["S1","S2","S3","S4"],
        "mes_atual_nome":    MESES_PT[month],
        "mes_anterior_nome": MESES_PT[prev_month],
    }


def deletar_todas_castracoes():
    """Delete all castration records permanently."""
    with _conn() as con:
        con.execute("DELETE FROM castracoes")
        con.execute("DELETE FROM sqlite_sequence WHERE name='castracoes'")
