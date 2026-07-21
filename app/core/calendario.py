"""
Calendário promocional anual (FASE 12, Bloco B — R-148)
=======================================================
As datas que movem o varejo — Páscoa (móvel, algoritmo de Gauss), Dia das
Mães/Pais, São João, Black Friday, Natal… — cada uma com cor e um KIT
sugerido (nome do evento + chamada). O calendário CONVERSA com os Eventos
(F2/F3): a data comemorativa vira um evento normal do app com um clique.
Lembretes LOCAIS e desligáveis (`calendario.lembretes` na Config — nada de
notificação intrusiva). Sugestão, nunca imposição.
"""

from __future__ import annotations

from datetime import date, timedelta


def _pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo de Gauss/Meeus — determinístico)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7          # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


def _n_esimo_domingo(ano: int, mes: int, n: int) -> date:
    d = date(ano, mes, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)    # o 1º domingo
    return d + timedelta(weeks=n - 1)


def _black_friday(ano: int) -> date:
    """A sexta após a 4ª quinta de novembro."""
    d = date(ano, 11, 1)
    d += timedelta(days=(3 - d.weekday()) % 7)    # a 1ª quinta
    return d + timedelta(weeks=3, days=1)


def datas_do_ano(ano: int) -> list[dict]:
    """As datas comemorativas do varejo no ano, em ordem — cada uma com
    {nome, data, cor, chamada (o kit sugerido)}."""
    pascoa = _pascoa(ano)
    return sorted([
        {"nome": "Ano Novo", "data": date(ano, 1, 1), "cor": "#F59E0B",
         "chamada": "Comece o ano economizando"},
        {"nome": "Carnaval", "data": pascoa - timedelta(days=47),
         "cor": "#8B5CF6", "chamada": "Ofertas pra cair na folia"},
        {"nome": "Páscoa", "data": pascoa, "cor": "#B45309",
         "chamada": "Chocolates e almoço de Páscoa"},
        {"nome": "Dia das Mães", "data": _n_esimo_domingo(ano, 5, 2),
         "cor": "#EC4899", "chamada": "O almoço dela começa aqui"},
        {"nome": "São João", "data": date(ano, 6, 24), "cor": "#DC2626",
         "chamada": "Arraiá de ofertas juninas"},
        {"nome": "Dia dos Pais", "data": _n_esimo_domingo(ano, 8, 2),
         "cor": "#2563EB", "chamada": "O churrasco do pai"},
        {"nome": "Dia das Crianças", "data": date(ano, 10, 12),
         "cor": "#F97316", "chamada": "A festa da criançada"},
        {"nome": "Black Friday", "data": _black_friday(ano),
         "cor": "#111111", "chamada": "Os menores preços do ano"},
        {"nome": "Natal", "data": date(ano, 12, 25), "cor": "#16A34A",
         "chamada": "A ceia completa em um lugar só"},
    ], key=lambda d: d["data"])


def proximas_datas(hoje: date | None = None, dias: int = 45) -> list[dict]:
    """As comemorativas nos próximos `dias` (para o lembrete do Início) —
    cada uma com "faltam" preenchido."""
    hoje = hoje or date.today()
    janela: list[dict] = []
    for ano in (hoje.year, hoje.year + 1):
        for d in datas_do_ano(ano):
            delta = (d["data"] - hoje).days
            if 0 <= delta <= dias:
                janela.append({**d, "faltam": delta})
    return sorted(janela, key=lambda d: d["faltam"])


def lembretes_ligados() -> bool:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                return ConfigRepositorio(s).get(
                    "calendario.lembretes", True) is not False
        finally:
            db.engine.dispose()
    except Exception:
        return True


def criar_evento_comemorativo(data_info: dict) -> int:
    """A data vira um EVENTO normal do app (F2/F3) — com a cor da data e o
    dia certo. Devolve o id do evento (idempotente pelo nome)."""
    from app.core.database import Database
    from app.qt.telas.eventos import criar_evento
    db = Database().init()
    try:
        with db.Session() as s:
            ev = criar_evento(s, data_info["nome"])
            if hasattr(ev, "cor") and not getattr(ev, "cor", None):
                ev.cor = data_info.get("cor")
            s.commit()
            return ev.id
    finally:
        db.engine.dispose()
