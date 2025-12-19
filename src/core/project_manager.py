"""
AutoTabloide AI - Gerenciador de Projetos
==========================================
Gestão de workspaces conforme Vol. V, Cap. 3-4.
Serialização, autosave, empacotamento para transporte.
"""

import os
import json
import hashlib
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
import zipfile

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import ProjetoSalvo, LayoutMeta, Produto
from src.core.repositories import ProjectRepository, LayoutRepository, ProductRepository, AuditRepository
from src.core.models import TipoAcao, TipoEntidade

logger = logging.getLogger("ProjectManager")


class ProjectManager:
    """
    Gerenciador de Projetos (Workspaces).
    
    Conforme Vol. V, Cap. 3:
    - Serialização com snapshot imutável
    - Autosave com debounce
    - Empacotamento para transporte
    - Fidelidade histórica (overrides)
    """
    
    def __init__(self, session: AsyncSession, system_root: str):
        self.session = session
        self.system_root = Path(system_root)
        self.projects_dir = self.system_root / "projects"
        self.packages_dir = self.system_root / "packages"
        
        # Cria diretórios
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.packages_dir, exist_ok=True)
        
        # Repositórios
        self.project_repo = ProjectRepository(session)
        self.layout_repo = LayoutRepository(session)
        self.product_repo = ProductRepository(session)
        self.audit_repo = AuditRepository(session)
        
        # Controle de autosave
        self._autosave_tasks: Dict[int, asyncio.Task] = {}
        self._dirty_projects: set = set()

    # ==========================================================================
    # CRIAÇÃO E CARREGAMENTO
    # ==========================================================================

    async def create_project(
        self,
        name: str,
        layout_id: int,
        author_id: str = None
    ) -> ProjetoSalvo:
        """
        Cria novo projeto vazio.
        
        Args:
            name: Nome do projeto
            layout_id: ID do layout base
            author_id: Identificador do autor (opcional)
            
        Returns:
            Projeto criado
        """
        # Verifica se layout existe
        layout = await self.layout_repo.get_by_id(layout_id)
        if not layout:
            raise ValueError(f"Layout {layout_id} nao encontrado")
        
        # Cria projeto
        project = await self.project_repo.create(
            nome=name,
            layout_id=layout_id,
            author_id=author_id
        )
        
        # Registra auditoria
        await self.audit_repo.log(
            entity_type=TipoEntidade.PROJETO.value,
            entity_id=project.id,
            action_type=TipoAcao.CREATE.value,
            description=f"Projeto '{name}' criado"
        )
        
        logger.info(f"Projeto criado: {project.id} - {name}")
        return project

    async def load_project(self, project_id: int) -> Dict[str, Any]:
        """
        Carrega projeto com dados expandidos.
        
        Aplica fidelidade histórica: usa dados do snapshot,
        não os valores atuais do banco.
        
        Returns:
            Dict com estrutura:
            {
                "project": ProjetoSalvo,
                "layout": LayoutMeta,
                "slots": {slot_id: {dados completos}},
                "is_dirty": bool
            }
        """
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Projeto {project_id} nao encontrado")
        
        layout = await self.layout_repo.get_by_id(project.layout_id)
        
        # Slots com dados do snapshot (fidelidade histórica)
        slots = {}
        saved_slots = project.get_slots()
        overrides = project.get_overrides()
        
        for slot_id, slot_data in saved_slots.items():
            # Dados do snapshot + overrides
            merged = {**slot_data, **overrides.get(slot_id, {})}
            slots[slot_id] = merged
        
        return {
            "project": project,
            "layout": layout,
            "slots": slots,
            "is_dirty": bool(project.is_dirty)
        }

    # ==========================================================================
    # SALVAMENTO
    # ==========================================================================

    async def save_project(
        self,
        project_id: int,
        slots: Dict[str, Dict],
        overrides: Dict[str, Dict] = None
    ) -> bool:
        """
        Salva estado do projeto.
        
        Conforme Vol. V, Cap. 3.1:
        - Cria snapshot IMUTÁVEL dos dados no momento do save
        - Overrides são preservados separadamente
        
        Args:
            project_id: ID do projeto
            slots: Estado atual dos slots
            overrides: Edições manuais (opcional)
            
        Returns:
            True se salvou com sucesso
        """
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Projeto {project_id} nao encontrado")
        
        if project.is_locked:
            raise PermissionError("Projeto esta travado para edicao")
        
        # Calcula hash do layout para verificação futura
        layout = await self.layout_repo.get_by_id(project.layout_id)
        layout_hash = layout.integrity_hash if layout else None
        
        # Enriquece slots com dados completos do produto
        enriched_slots = await self._enrich_slots(slots)
        
        # Salva snapshot
        await self.project_repo.save_snapshot(
            projeto_id=project_id,
            slots=enriched_slots,
            overrides=overrides,
            layout_hash=layout_hash
        )
        
        # Remove do set de dirty
        self._dirty_projects.discard(project_id)
        
        # Registra auditoria
        await self.audit_repo.log(
            entity_type=TipoEntidade.PROJETO.value,
            entity_id=project_id,
            action_type=TipoAcao.UPDATE.value,
            description="Projeto salvo"
        )
        
        logger.info(f"Projeto {project_id} salvo")
        return True

    async def _enrich_slots(self, slots: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Enriquece slots com dados completos do produto.
        
        Garante que o snapshot contenha TODOS os dados necessários
        para renderização futura, mesmo se o produto mudar no banco.
        """
        enriched = {}
        
        for slot_id, slot_data in slots.items():
            produto_id = slot_data.get("produto_id")
            
            if produto_id:
                # Busca produto atual
                produto = await self.product_repo.get_by_id(produto_id)
                
                if produto:
                    # Cria snapshot completo
                    enriched[slot_id] = {
                        "produto_id": produto.id,
                        "sku": produto.sku_origem,
                        "nome_sanitizado": produto.nome_sanitizado,
                        "marca": produto.marca_normalizada,
                        "peso": produto.detalhe_peso,
                        "categoria": produto.categoria,
                        "preco_venda_atual": float(produto.preco_venda_atual),
                        "preco_referencia": float(produto.preco_referencia) if produto.preco_referencia else None,
                        "images": produto.get_images(),
                        "snapshot_timestamp": datetime.now().isoformat()
                    }
                else:
                    # Produto não encontrado, mantém dados originais
                    enriched[slot_id] = slot_data
            else:
                # Slot sem produto
                enriched[slot_id] = slot_data
        
        return enriched

    # ==========================================================================
    # AUTOSAVE COM DEBOUNCE
    # ==========================================================================

    def mark_dirty(self, project_id: int, slots: Dict[str, Dict]):
        """
        Marca projeto como modificado e agenda autosave.
        
        Conforme Vol. V, Cap. 4 - Debounce de 3 segundos.
        """
        self._dirty_projects.add(project_id)
        
        # Cancela task anterior se existir
        if project_id in self._autosave_tasks:
            self._autosave_tasks[project_id].cancel()
        
        # Agenda nova task com debounce
        async def _debounced_save():
            await asyncio.sleep(3)  # 3 segundos de debounce
            try:
                await self.save_project(project_id, slots)
                logger.debug(f"Autosave executado para projeto {project_id}")
            except Exception as e:
                logger.error(f"Falha no autosave: {e}")
        
        self._autosave_tasks[project_id] = asyncio.create_task(_debounced_save())

    def is_dirty(self, project_id: int) -> bool:
        """Verifica se projeto tem alterações não salvas."""
        return project_id in self._dirty_projects

    async def flush_autosave(self, project_id: int):
        """Força execução imediata do autosave pendente."""
        if project_id in self._autosave_tasks:
            task = self._autosave_tasks[project_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        if self.is_dirty(project_id):
            # Busca estado atual e salva
            project = await self.project_repo.get_by_id(project_id)
            if project:
                await self.save_project(project_id, project.get_slots())

    # ==========================================================================
    # EMPACOTAMENTO PARA TRANSPORTE
    # ==========================================================================

    async def export_package(
        self,
        project_id: int,
        output_path: Optional[str] = None,
        include_images: bool = True
    ) -> str:
        """
        Empacota projeto para transporte.
        
        Conforme Vol. V, Cap. 4.2:
        - Cria .zip com JSON de metadados + imagens
        - Totalmente portável entre máquinas
        
        Args:
            project_id: ID do projeto
            output_path: Caminho do .zip de saída
            include_images: Se deve incluir imagens do vault
            
        Returns:
            Caminho do arquivo .zip criado
        """
        # Carrega projeto
        data = await self.load_project(project_id)
        project = data["project"]
        layout = data["layout"]
        slots = data["slots"]
        
        # Define caminho de saída
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() else "_" for c in project.nome_projeto)
            output_path = str(self.packages_dir / f"{safe_name}_{timestamp}.zip")
        
        # Prepara manifest
        manifest = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "project": {
                "uuid": project.uuid,
                "nome": project.nome_projeto,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "layout_path": layout.arquivo_fonte if layout else None,
                "layout_hash": project.layout_integrity_hash
            },
            "slots": slots,
            "overrides": project.get_overrides(),
            "images": []
        }
        
        # Cria ZIP
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Adiciona manifest
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            
            # Adiciona layout SVG se existir
            if layout and layout.arquivo_fonte:
                layout_path = Path(layout.arquivo_fonte)
                if layout_path.exists():
                    zf.write(layout_path, f"layout/{layout_path.name}")
            
            # Adiciona imagens
            if include_images:
                images_added = set()
                
                for slot_id, slot_data in slots.items():
                    images = slot_data.get("images", [])
                    
                    for img_hash in images:
                        if img_hash in images_added:
                            continue
                        
                        # Busca no vault
                        img_path = self._find_vault_image(img_hash)
                        if img_path and Path(img_path).exists():
                            ext = Path(img_path).suffix
                            zf.write(img_path, f"images/{img_hash}{ext}")
                            manifest["images"].append(img_hash)
                            images_added.add(img_hash)
            
            # Atualiza manifest com lista de imagens
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        
        logger.info(f"Pacote exportado: {output_path}")
        return output_path

    def _find_vault_image(self, file_hash: str) -> Optional[str]:
        """Localiza imagem no vault pelo hash."""
        vault_dir = self.system_root / "vault" / "images"
        subdir = vault_dir / file_hash[:2] / file_hash[2:4]
        
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            path = subdir / f"{file_hash}{ext}"
            if path.exists():
                return str(path)
        
        return None

    async def import_package(self, package_path: str) -> int:
        """
        Importa pacote de transporte.
        
        Args:
            package_path: Caminho do .zip
            
        Returns:
            ID do projeto importado
        """
        package_path = Path(package_path)
        if not package_path.exists():
            raise FileNotFoundError(f"Pacote nao encontrado: {package_path}")
        
        # Extrai para diretório temporário
        temp_dir = self.projects_dir / f"_import_{uuid4().hex[:8]}"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(package_path, 'r') as zf:
                zf.extractall(temp_dir)
            
            # Lê manifest
            manifest_path = temp_dir / "manifest.json"
            if not manifest_path.exists():
                raise ValueError("Pacote invalido: manifest.json nao encontrado")
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Cria projeto
            project_info = manifest.get("project", {})
            
            # Busca ou cria layout
            layout_id = 1  # Fallback - TODO: implementar busca/criação de layout
            
            project = await self.project_repo.create(
                nome=project_info.get("nome", "Projeto Importado"),
                layout_id=layout_id
            )
            
            # Restaura slots
            slots = manifest.get("slots", {})
            overrides = manifest.get("overrides", {})
            
            await self.project_repo.save_snapshot(
                projeto_id=project.id,
                slots=slots,
                overrides=overrides,
                layout_hash=project_info.get("layout_hash")
            )
            
            # Importa imagens para vault
            images_dir = temp_dir / "images"
            if images_dir.exists():
                vault_dir = self.system_root / "vault" / "images"
                
                for img_file in images_dir.iterdir():
                    if img_file.is_file():
                        file_hash = img_file.stem
                        subdir = vault_dir / file_hash[:2] / file_hash[2:4]
                        os.makedirs(subdir, exist_ok=True)
                        
                        dest = subdir / img_file.name
                        if not dest.exists():
                            shutil.copy2(img_file, dest)
            
            logger.info(f"Pacote importado como projeto {project.id}")
            
            # Registra auditoria
            await self.audit_repo.log(
                entity_type=TipoEntidade.PROJETO.value,
                entity_id=project.id,
                action_type=TipoAcao.IMPORT.value,
                description=f"Projeto importado de {package_path.name}"
            )
            
            return project.id
            
        finally:
            # Limpa diretório temporário
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ==========================================================================
    # DUPLICAÇÃO
    # ==========================================================================

    async def duplicate_project(self, project_id: int, new_name: str) -> ProjetoSalvo:
        """
        Cria cópia profunda de um projeto.
        
        Args:
            project_id: ID do projeto original
            new_name: Nome para o novo projeto
            
        Returns:
            Novo projeto criado
        """
        new_project = await self.project_repo.duplicate(project_id, new_name)
        
        # Registra auditoria
        await self.audit_repo.log(
            entity_type=TipoEntidade.PROJETO.value,
            entity_id=new_project.id,
            action_type=TipoAcao.CREATE.value,
            description=f"Projeto duplicado de #{project_id}"
        )
        
        logger.info(f"Projeto {project_id} duplicado como {new_project.id}")
        return new_project

    # ==========================================================================
    # LISTAGEM
    # ==========================================================================

    async def list_recent(self, limit: int = 20) -> List[Dict]:
        """
        Lista projetos recentes com preview.
        
        Returns:
            Lista de dicts com info básica de cada projeto
        """
        projects = await self.project_repo.list_recent(limit=limit)
        
        result = []
        for p in projects:
            layout = await self.layout_repo.get_by_id(p.layout_id)
            
            result.append({
                "id": p.id,
                "uuid": p.uuid,
                "nome": p.nome_projeto,
                "layout_nome": layout.nome_amigavel if layout else "N/A",
                "layout_tipo": layout.tipo_midia if layout else "N/A",
                "last_modified": p.last_modified.isoformat() if p.last_modified else None,
                "is_locked": bool(p.is_locked),
                "is_dirty": bool(p.is_dirty),
                "slot_count": len(p.get_slots())
            })
        
        return result

    async def delete_project(self, project_id: int):
        """Remove um projeto."""
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(f"Projeto {project_id} nao encontrado")
        
        if project.is_locked:
            raise PermissionError("Projeto travado nao pode ser excluido")
        
        # Registra auditoria ANTES de deletar
        await self.audit_repo.log(
            entity_type=TipoEntidade.PROJETO.value,
            entity_id=project_id,
            action_type=TipoAcao.DELETE.value,
            diff={"nome": project.nome_projeto},
            description=f"Projeto '{project.nome_projeto}' excluido"
        )
        
        await self.project_repo.delete(project_id)
        logger.info(f"Projeto {project_id} excluido")
