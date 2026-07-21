"""
Verificar atualização (FASE 12, Bloco A — R-127)
================================================
Honesto e nunca intrusivo: um botão "Verificar atualização" na aba Sobre.
Com uma URL de releases configurada (Config `app.url_atualizacao`, um JSON
{"versao": "1.1", "novidades": ["…"]}), compara com a versão local e mostra
as novidades EM PT-BR. Sem URL, sem rede ou com resposta estranha → mensagem
honesta ("não deu para verificar — o app segue normal"), nunca trava, nunca
mente, nunca obriga (passos 8-9).
"""

from __future__ import annotations

VERSAO_ATUAL = "1.0"


def _url_configurada() -> str | None:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = Database().init()
        try:
            with db.Session() as s:
                url = ConfigRepositorio(s).get("app.url_atualizacao")
        finally:
            db.engine.dispose()
        url = (str(url).strip() if url else "")
        return url if url.startswith(("http://", "https://")) else None
    except Exception:
        return None


def verificar_atualizacao(url: str | None = None,
                          timeout: float = 6.0) -> dict:
    """Devolve {"disponivel": bool, "versao": str|None, "novidades": [str],
    "mensagem": PT-BR}. NUNCA levanta — toda falha vira a mensagem honesta.
    `url` explícita vence a Config (o teste injeta o caminho)."""
    alvo = url or _url_configurada()
    if not alvo:
        return {"disponivel": False, "versao": None, "novidades": [],
                "mensagem": ("A verificação automática não está configurada "
                             f"— você está na versão {VERSAO_ATUAL} e o app "
                             "segue funcionando 100% offline.")}
    try:
        import requests
        resp = requests.get(alvo, timeout=timeout)
        resp.raise_for_status()
        dados = resp.json()
        remota = str(dados.get("versao") or "").strip()
        if not remota:
            raise ValueError("sem campo 'versao'")
    except Exception:
        return {"disponivel": False, "versao": None, "novidades": [],
                "mensagem": ("Não deu para verificar agora (sem conexão ou "
                             "o endereço não respondeu). O app segue normal "
                             f"na versão {VERSAO_ATUAL} — tente de novo "
                             "quando houver internet.")}

    def _tupla(v: str) -> tuple:
        try:
            return tuple(int(p) for p in v.split("."))
        except ValueError:
            return (0,)

    if _tupla(remota) > _tupla(VERSAO_ATUAL):
        novidades = [str(n) for n in (dados.get("novidades") or [])][:10]
        return {"disponivel": True, "versao": remota, "novidades": novidades,
                "mensagem": (f"Há uma versão nova ({remota}). Novidades:\n"
                             + "\n".join(f"• {n}" for n in novidades)
                             if novidades else
                             f"Há uma versão nova ({remota}).")}
    return {"disponivel": False, "versao": remota, "novidades": [],
            "mensagem": f"Você já está na versão mais recente "
                        f"({VERSAO_ATUAL})."}
