"""
Script de Verificação Automatizada - AutoTabloide AI
Verifica instalações, dependências e configurações do sistema
"""

import sys
import platform
from pathlib import Path
from typing import List, Tuple

# Cores para output (com fallback para Windows)
class Colors:
    GREEN = '\033[92m' if platform.system() != 'Windows' else ''
    RED = '\033[91m' if platform.system() != 'Windows' else ''
    YELLOW = '\033[93m' if platform.system() != 'Windows' else ''
    BLUE = '\033[94m' if platform.system() != 'Windows' else ''
    RESET = '\033[0m' if platform.system() != 'Windows' else ''

def check_mark(status: bool) -> str:
    """Retorna um checkmark ou X baseado no status"""
    if platform.system() == 'Windows':
        return '[OK]' if status else '[X]'
    return '✅' if status else '❌'

def warning_mark() -> str:
    """Retorna um símbolo de aviso"""
    if platform.system() == 'Windows':
        return '[!]'
    return '⚠️'

class SystemVerifier:
    """Verifica a integridade do sistema AutoTabloide AI"""
    
    def __init__(self):
        self.root = Path.cwd() / "AutoTabloide_System_Root"
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
        
    def print_header(self, text: str):
        """Imprime cabeçalho de seção"""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
    
    def check_directory_structure(self) -> bool:
        """Verifica estrutura de diretórios"""
        self.print_header("Verificando Estrutura de Diretórios")
        
        required_dirs = [
            "bin",
            "config",
            "database",
            "snapshots",
            "assets/store",
            "assets/profiles",
            "staging",
            "temp_render",
            "library/svg_source",
            "library/thumbnails",
            "workspace/projects",
            "logs",
        ]
        
        all_ok = True
        for dir_path in required_dirs:
            full_path = self.root / dir_path
            exists = full_path.exists()
            status = check_mark(exists)
            
            if exists:
                print(f"{status} {dir_path}")
                self.successes.append(f"Diretório {dir_path} existe")
            else:
                print(f"{Colors.RED}{status} {dir_path} - FALTANDO{Colors.RESET}")
                self.issues.append(f"Diretório {dir_path} não encontrado")
                all_ok = False
        
        return all_ok
    
    def check_critical_binaries(self) -> bool:
        """Verifica binários críticos"""
        self.print_header("Verificando Binários Críticos")
        
        bin_dir = self.root / "bin"
        
        # SQLite-vec
        vec_binary = bin_dir / "vec0.dll" if platform.system() == "Windows" else bin_dir / "vec0.so"
        vec_exists = vec_binary.exists()
        
        # Ghostscript
        gs_binary = bin_dir / "gswin64c.exe" if platform.system() == "Windows" else bin_dir / "gs"
        gs_exists = gs_binary.exists()
        
        print(f"{check_mark(vec_exists)} sqlite-vec: {vec_binary.name}")
        if vec_exists:
            size_kb = vec_binary.stat().st_size / 1024
            print(f"   Tamanho: {size_kb:.1f} KB")
            self.successes.append("sqlite-vec extension presente")
        else:
            self.issues.append("sqlite-vec extension não encontrada")
        
        print(f"{check_mark(gs_exists)} Ghostscript: {gs_binary.name}")
        if not gs_exists:
            print(f"{Colors.RED}   CRÍTICO: Sistema não pode inicializar sem Ghostscript{Colors.RESET}")
            self.issues.append("Ghostscript não encontrado (CRÍTICO)")
        else:
            self.successes.append("Ghostscript presente")
        
        return vec_exists and gs_exists
    
    def check_icc_profile(self) -> bool:
        """Verifica perfil de cor ICC"""
        self.print_header("Verificando Perfil de Cor ICC")
        
        icc_file = self.root / "assets" / "profiles" / "CoatedFOGRA39.icc"
        exists = icc_file.exists()
        
        print(f"{check_mark(exists)} CoatedFOGRA39.icc")
        
        if not exists:
            print(f"{Colors.YELLOW}   {warning_mark()} Gerenciamento de cores comprometido{Colors.RESET}")
            self.warnings.append("Perfil de cor ICC não encontrado")
        else:
            self.successes.append("Perfil de cor ICC presente")
        
        return exists
    
    def check_python_environment(self) -> bool:
        """Verifica ambiente Python"""
        self.print_header("Verificando Ambiente Python")
        
        # Versão Python
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"{check_mark(True)} Python: {py_version}")
        
        if sys.version_info.major != 3 or sys.version_info.minor != 12:
            print(f"{Colors.YELLOW}   {warning_mark()} Recomendado: Python 3.12.x{Colors.RESET}")
            self.warnings.append(f"Versão Python {py_version} (recomendado: 3.12.x)")
        
        # Ambiente virtual
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        print(f"{check_mark(in_venv)} Ambiente Virtual: {'Ativo' if in_venv else 'Não detectado'}")
        
        if not in_venv:
            print(f"{Colors.YELLOW}   {warning_mark()} Recomendado usar ambiente virtual (poetry shell){Colors.RESET}")
            self.warnings.append("Executando fora de ambiente virtual")
        
        return True
    
    def check_python_imports(self) -> Tuple[int, int]:
        """Testa importações Python críticas"""
        self.print_header("Testando Importações Python")
        
        imports = [
            ("sqlalchemy", "SQLAlchemy (ORM)"),
            ("aiosqlite", "AsyncIO SQLite"),
            ("lxml", "XML/HTML Parser"),
            ("llama_cpp", "Llama CPP (AI)"),
            ("flet", "Flet (UI)"),
            ("PIL", "Pillow (Imagens)"),
            ("pypdf", "PyPDF (PDF)"),
            ("loguru", "Loguru (Logs)"),
            ("pydantic", "Pydantic (Validação)"),
        ]
        
        optional_imports = [
            ("cairosvg", "CairoSVG (SVG Rendering)"),
        ]
        
        success = 0
        total = len(imports)
        
        for module, name in imports:
            try:
                __import__(module)
                print(f"{check_mark(True)} {name}")
                success += 1
            except ImportError as e:
                print(f"{Colors.RED}{check_mark(False)} {name} - {str(e)}{Colors.RESET}")
                self.issues.append(f"Falha ao importar {name}")
        
        print(f"\n{Colors.BLUE}Importações Opcionais:{Colors.RESET}")
        for module, name in optional_imports:
            try:
                __import__(module)
                print(f"{check_mark(True)} {name}")
            except (ImportError, OSError) as e:
                print(f"{Colors.YELLOW}{warning_mark()} {name} - Requer Cairo nativo{Colors.RESET}")
                self.warnings.append(f"{name} não disponível (requer Cairo)")
        
        return success, total
    
    def print_summary(self, imports_ok: int, imports_total: int):
        """Imprime resumo final"""
        self.print_header("Resumo da Verificação")
        
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        print(f"{Colors.GREEN}Sucessos: {len(self.successes)}{Colors.RESET}")
        print(f"{Colors.YELLOW}Avisos: {total_warnings}{Colors.RESET}")
        print(f"{Colors.RED}Problemas Críticos: {total_issues}{Colors.RESET}")
        print(f"\nImportações Python: {imports_ok}/{imports_total}")
        
        if self.issues:
            print(f"\n{Colors.RED}Problemas Críticos:{Colors.RESET}")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}Avisos:{Colors.RESET}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        # Status final
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        if total_issues == 0:
            print(f"{Colors.GREEN}[OK] SISTEMA PRONTO PARA USO{Colors.RESET}")
            return 0
        elif total_issues <= 2:
            print(f"{Colors.YELLOW}{warning_mark()} SISTEMA PARCIALMENTE CONFIGURADO - Acao Necessaria{Colors.RESET}")
            return 1
        else:
            print(f"{Colors.RED}❌ SISTEMA NÃO CONFIGURADO - Múltiplos Problemas{Colors.RESET}")
            return 2
    
    def run(self) -> int:
        """Executa verificação completa"""
        print(f"{Colors.BLUE}")
        print("=" * 60)
        print("     AutoTabloide AI - Verificacao do Sistema")
        print("=" * 60)
        print(f"{Colors.RESET}")
        
        # Verifica se raiz existe
        if not self.root.exists():
            print(f"{Colors.RED}ERRO: AutoTabloide_System_Root não encontrado!{Colors.RESET}")
            print("Execute 'python setup.py' primeiro.")
            return 3
        
        # Executa verificações
        self.check_directory_structure()
        self.check_critical_binaries()
        self.check_icc_profile()
        self.check_python_environment()
        imports_ok, imports_total = self.check_python_imports()
        
        # Resumo
        return self.print_summary(imports_ok, imports_total)

if __name__ == "__main__":
    verifier = SystemVerifier()
    exit_code = verifier.run()
    sys.exit(exit_code)
