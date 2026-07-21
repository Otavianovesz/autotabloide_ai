"""
Manutenção — os botões de "consertar sozinho" (FASE 3, Bloco H)
===============================================================
R-134 verificar instalação · R-135 compactar banco · R-129 integridade do
acervo com QUARENTENA (nunca apagar) · R-133 contador de erros por função ·
R-132 perfil de máquina fraca (liga 4 chaves de uma vez).
"""

from __future__ import annotations

from pathlib import Path

from app.core.paths import SystemRoot

PASTA_QUARENTENA = "_quarentena"


# --- R-134: verificar instalação -------------------------------------------------

def verificar_instalacao(raiz=None) -> list[dict]:
    """Teste de fumaça embutido: [{nome, ok, essencial, detalhe}].
    Essenciais: banco, pastas, fontes. A IA é OPCIONAL (o app degrada
    com aviso) — fora do ar não é instalação quebrada."""
    root = SystemRoot(raiz) if raiz is not None else SystemRoot()
    itens: list[dict] = []

    # banco: abre e passa no quick_check
    try:
        from sqlalchemy import text

        from app.core.database import Database
        db = Database(root).init()
        try:
            with db.Session() as s:
                r = s.execute(text("PRAGMA quick_check")).scalar()
            ok, det = (r == "ok"), ("íntegro" if r == "ok" else str(r))
        finally:
            db.engine.dispose()
    except Exception as exc:
        ok, det = False, f"não abriu: {exc}"
    itens.append({"nome": "Banco de dados", "ok": ok, "essencial": True,
                  "detalhe": det})

    # pastas da raiz
    faltam = [p for p in ("biblioteca_imagens", "layouts", "fontes",
                          "backups", "selos")
              if not (root.raiz / p).exists()]
    itens.append({"nome": "Pastas do estúdio", "ok": not faltam,
                  "essencial": True,
                  "detalhe": ("todas no lugar" if not faltam
                              else "faltando: " + ", ".join(faltam))})

    # fontes (o fallback do desenho)
    tem_roboto = (root.fontes / "Roboto-Regular.ttf").exists()
    itens.append({"nome": "Fontes", "ok": tem_roboto, "essencial": True,
                  "detalhe": ("Roboto presente" if tem_roboto else
                              "Roboto-Regular.ttf não está em fontes/ — "
                              "textos usarão a fonte de emergência")})

    # IA local (opcional)
    try:
        from app.ai.client import ClienteOpenAICompat
        cli = ClienteOpenAICompat()
        viva = cli.disponivel()
        det = ("respondendo" if viva else
               "fora do ar ou desligada — o app funciona no modo "
               "determinístico, com avisos")
    except Exception as exc:
        viva, det = False, str(exc)
    itens.append({"nome": "IA local (opcional)", "ok": viva,
                  "essencial": False, "detalhe": det})
    return itens


# --- R-135: compactar banco -------------------------------------------------------

def compactar_banco(raiz=None) -> tuple[int, int]:
    """VACUUM; devolve (bytes antes, bytes depois)."""
    from sqlalchemy import text

    from app.core.database import Database
    root = SystemRoot(raiz) if raiz is not None else SystemRoot()
    arquivo = root.caminho_banco
    antes = arquivo.stat().st_size if arquivo.exists() else 0
    db = Database(root).init()
    try:
        with db.engine.connect() as con:
            con.execute(text("VACUUM"))
    finally:
        db.engine.dispose()
    depois = arquivo.stat().st_size if arquivo.exists() else 0
    return antes, depois


# --- R-129: integridade do acervo -------------------------------------------------

_EXT_FOTO = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def verificar_acervo(raiz=None) -> dict:
    """{orfas: [Path rel], sem_arquivo: [(id, nome, caminho)]} — fotos no
    disco sem produto apontando, e produtos cuja foto sumiu."""
    from app.core.database import Database
    from app.core.models import Produto
    root = SystemRoot(raiz) if raiz is not None else SystemRoot()
    bib = root.biblioteca_imagens

    usados: set[str] = set()
    sem_arquivo: list[tuple[int, str, str]] = []
    db = Database(root).init()
    try:
        with db.Session() as s:
            for p in s.query(Produto).all():
                caminhos = [p.caminho_imagem] if p.caminho_imagem else []
                try:
                    import json
                    extras = json.loads(p.imagens_json or "[]")
                    caminhos += [e for e in extras if isinstance(e, str)]
                except Exception:
                    pass
                for c in caminhos:
                    rel = str(c).replace("\\", "/").strip("/")
                    usados.add(rel.lower())
                if p.caminho_imagem and not (bib / p.caminho_imagem).exists():
                    sem_arquivo.append((p.id, p.nome_sanitizado,
                                        p.caminho_imagem))
    finally:
        db.engine.dispose()

    orfas: list[Path] = []
    if bib.exists():
        for arq in bib.rglob("*"):
            if not arq.is_file() or arq.suffix.lower() not in _EXT_FOTO:
                continue
            rel = arq.relative_to(bib).as_posix()
            # OS F11.5 #63/#82: _genericas são fotos de FAMÍLIA por convenção
            # de caminho (F10) — nunca órfãs, mesmo sem produto apontando
            if rel.split("/")[0] in (PASTA_QUARENTENA, "_upscale_cartaz",
                                     "_genericas"):
                continue                    # quarentena/cache/genéricas ficam
            if rel.lower() not in usados:
                orfas.append(arq.relative_to(bib))
    return {"orfas": orfas, "sem_arquivo": sem_arquivo}


def quarentenar_orfas(orfas: list[Path], raiz=None) -> int:
    """Move as órfãs para biblioteca_imagens/_quarentena/ preservando a
    subpasta — NUNCA apaga (R-129). Devolve quantas moveu."""
    import shutil
    root = SystemRoot(raiz) if raiz is not None else SystemRoot()
    bib = root.biblioteca_imagens
    movidas = 0
    for rel in orfas:
        origem = bib / rel
        if not origem.exists():
            continue
        destino = bib / PASTA_QUARENTENA / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.exists():                # nome repetido: sufixo
            destino = destino.with_name(destino.stem + "_2" + destino.suffix)
        shutil.move(str(origem), str(destino))
        movidas += 1
    return movidas


# --- R-133: contador local de erros por função ------------------------------------

def registrar_erro(funcao: str, raiz=None) -> None:
    """Incrementa o contador da função na Config (nunca levanta — um
    contador jamais pode piorar o erro que está contando)."""
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = (Database(SystemRoot(raiz)) if raiz is not None
              else Database()).init()
        try:
            with db.Session() as s:
                cfg = ConfigRepositorio(s)
                mapa = dict(cfg.get("erros.contadores") or {})
                chave = str(funcao)[:120] or "desconhecida"
                mapa[chave] = int(mapa.get(chave, 0)) + 1
                cfg.set("erros.contadores", mapa)
                s.commit()
        finally:
            db.engine.dispose()
    except Exception:
        pass


def top_erros(n: int = 3, raiz=None) -> list[tuple[str, int]]:
    try:
        from app.core.database import Database
        from app.core.repositories import ConfigRepositorio
        db = (Database(SystemRoot(raiz)) if raiz is not None
              else Database()).init()
        try:
            with db.Session() as s:
                mapa = ConfigRepositorio(s).get("erros.contadores") or {}
        finally:
            db.engine.dispose()
        return sorted(((k, int(v)) for k, v in mapa.items()),
                      key=lambda kv: -kv[1])[:n]
    except Exception:
        return []


# --- R-132: perfil de máquina fraca -----------------------------------------------

CHAVES_MAQUINA_FRACA = {
    "aparencia.animacoes": "reduzidas",
    "aparencia.transparencias": "reduzidas",
    "ia.usar": False,
    "imagem.upscale_auto": False,
}


def ativar_perfil_maquina_fraca(ligar: bool, raiz=None) -> None:
    """Liga (ou desfaz) as 4 chaves DE UMA VEZ — o PC do mercado.
    Desligar devolve os padrões (animações ligadas, IA ligada, upscale
    ligado, transparências normais)."""
    from app.core.database import Database
    from app.core.repositories import ConfigRepositorio
    padroes = {"aparencia.animacoes": "ligadas",
               "aparencia.transparencias": "normais",
               "ia.usar": True,
               "imagem.upscale_auto": True}
    db = (Database(SystemRoot(raiz)) if raiz is not None
          else Database()).init()
    try:
        with db.Session() as s:
            cfg = ConfigRepositorio(s)
            valores = CHAVES_MAQUINA_FRACA if ligar else padroes
            for chave, valor in valores.items():
                cfg.set(chave, valor)
            cfg.set("aparencia.maquina_fraca", bool(ligar))
            s.commit()
    finally:
        db.engine.dispose()
    try:
        from app.qt.design.animacoes import recarregar_config
        recarregar_config()
    except Exception:
        pass
