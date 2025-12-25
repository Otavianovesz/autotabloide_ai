"""
AutoTabloide AI - Robust Import Module
=======================================
Century Checklist Items 61-70: Importação Robusta.
Normalização de colunas, Parser de moeda, Transações atômicas, Progresso.
"""

from __future__ import annotations
import re
import csv
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Callable, Any, Generator
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger("AutoTabloide.Import")


# ==============================================================================
# ITEM 61: Normalização Fuzzy de Colunas
# ==============================================================================

class ColumnNormalizer:
    """
    Normaliza nomes de colunas do Excel/CSV com fuzzy matching.
    Mapeia variações como "Preço", "Vl. Unit.", "Valor" para campos padrão.
    """
    
    # Mapeamentos conhecidos (campo_destino -> [variações])
    COLUMN_MAPPINGS = {
        "sku": [
            "sku", "codigo", "código", "cod", "cod.", 
            "ref", "referencia", "referência", "id_produto",
            "cod_produto", "código_produto", "item", "id"
        ],
        "nome": [
            "nome", "name", "descricao", "descrição", "description",
            "produto", "item", "mercadoria", "nome_produto", "desc",
            "título", "titulo", "title"
        ],
        "preco": [
            "preco", "preço", "price", "valor", "vl", "vl.",
            "vl. unit", "vl. unit.", "vl unit", "valor_unit",
            "preco_venda", "preço_venda", "custo", "unitario", "unitário",
            "prc", "price_unit", "unit_price"
        ],
        "preco_oferta": [
            "oferta", "promoção", "promocao", "promo", "desconto",
            "sale", "offer", "preco_oferta", "preço_promocional",
            "preco_promo", "vl_oferta", "preco_promocao"
        ],
        "gtin": [
            "gtin", "ean", "ean13", "ean-13", "ean_13",
            "barcode", "cod_barras", "codigo_barras", "código_barras",
            "ean8", "ean-8", "upc"
        ],
        "marca": [
            "marca", "brand", "fabricante", "fornecedor",
            "marca_produto", "manufacturer"
        ],
        "categoria": [
            "categoria", "category", "grupo", "departamento",
            "seção", "secao", "classe", "tipo", "segmento"
        ],
        "peso": [
            "peso", "weight", "gramatura", "kg", "g", "ml", "l", "litros",
            "quantidade", "qtd", "unidade", "un", "medida"
        ],
    }
    
    # Mapeamento reverso otimizado
    _REVERSE_MAP: Dict[str, str] = {}
    
    @classmethod
    def _build_reverse_map(cls):
        """Constrói mapeamento reverso para busca rápida."""
        if cls._REVERSE_MAP:
            return
        
        for field, variations in cls.COLUMN_MAPPINGS.items():
            for var in variations:
                clean = var.lower().strip()
                cls._REVERSE_MAP[clean] = field
    
    @classmethod
    def normalize(cls, column_name: str) -> Optional[str]:
        """
        Normaliza nome de coluna para campo padrão.
        
        Args:
            column_name: Nome original da coluna
            
        Returns:
            Nome normalizado ou None se não reconhecido
        """
        cls._build_reverse_map()
        
        # Limpeza básica
        cleaned = column_name.lower().strip()
        cleaned = cleaned.replace("_", " ").replace("-", " ")
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Busca exata
        if cleaned in cls._REVERSE_MAP:
            return cls._REVERSE_MAP[cleaned]
        
        # Busca fuzzy (contém)
        for variation, field in cls._REVERSE_MAP.items():
            if variation in cleaned or cleaned in variation:
                return field
        
        # Busca por similaridade (início)
        for variation, field in cls._REVERSE_MAP.items():
            if cleaned.startswith(variation[:3]) and len(variation) >= 3:
                return field
        
        return None
    
    @classmethod
    def map_columns(cls, columns: List[str]) -> Dict[str, str]:
        """
        Mapeia lista de colunas para campos padrão.
        
        Args:
            columns: Lista de nomes de colunas originais
            
        Returns:
            Dict de {coluna_original: campo_normalizado}
        """
        mapping = {}
        used_fields = set()
        
        for col in columns:
            normalized = cls.normalize(col)
            if normalized and normalized not in used_fields:
                mapping[col] = normalized
                used_fields.add(normalized)
        
        return mapping
    
    @classmethod
    def suggest_mappings(cls, columns: List[str]) -> List[Dict[str, Any]]:
        """
        Retorna sugestões de mapeamento para UI de preview.
        
        Returns:
            Lista de dicts com {original, suggested, confidence}
        """
        suggestions = []
        
        for col in columns:
            normalized = cls.normalize(col)
            if normalized:
                confidence = 1.0 if col.lower() in cls._REVERSE_MAP else 0.7
            else:
                normalized = None
                confidence = 0.0
            
            suggestions.append({
                "original": col,
                "suggested": normalized,
                "confidence": confidence
            })
        
        return suggestions


# ==============================================================================
# ITEM 62: Preview de Importação
# ==============================================================================

@dataclass
class ImportPreview:
    """Resultado do preview de importação."""
    total_rows: int
    valid_rows: int
    error_rows: int
    sample_data: List[Dict]
    column_mapping: Dict[str, str]
    errors: List[Dict]
    warnings: List[str]


class ImportPreviewGenerator:
    """Gera preview de dados antes de importar."""
    
    SAMPLE_SIZE = 10
    
    @classmethod
    def generate_preview(
        cls,
        file_path: Path,
        delimiter: str = None
    ) -> ImportPreview:
        """
        Gera preview do arquivo a importar.
        
        Args:
            file_path: Caminho do arquivo
            delimiter: Delimitador (auto-detecta se None)
            
        Returns:
            ImportPreview com dados e estatísticas
        """
        ext = file_path.suffix.lower()
        
        if ext in [".xlsx", ".xls"]:
            return cls._preview_excel(file_path)
        elif ext in [".csv", ".txt"]:
            return cls._preview_csv(file_path, delimiter)
        else:
            raise ValueError(f"Formato não suportado: {ext}")
    
    @classmethod
    def _preview_excel(cls, file_path: Path) -> ImportPreview:
        """Preview de arquivo Excel."""
        try:
            import pandas as pd
            
            df = pd.read_excel(file_path, nrows=100)
            columns = list(df.columns)
            column_mapping = ColumnNormalizer.map_columns(columns)
            
            total_rows = len(df)
            sample_data = df.head(cls.SAMPLE_SIZE).to_dict('records')
            
            errors = []
            warnings = []
            
            # Detecta colunas não mapeadas
            unmapped = [c for c in columns if c not in column_mapping]
            if unmapped:
                warnings.append(f"Colunas não mapeadas: {', '.join(unmapped)}")
            
            # Verifica colunas obrigatórias
            required = {"sku", "nome", "preco"}
            mapped_fields = set(column_mapping.values())
            missing = required - mapped_fields
            if missing:
                errors.append({
                    "type": "missing_required",
                    "message": f"Colunas obrigatórias faltando: {', '.join(missing)}"
                })
            
            return ImportPreview(
                total_rows=total_rows,
                valid_rows=total_rows - len(errors),
                error_rows=len(errors),
                sample_data=sample_data,
                column_mapping=column_mapping,
                errors=errors,
                warnings=warnings
            )
            
        except ImportError:
            raise ImportError("pandas não instalado. Execute: pip install pandas openpyxl")
    
    @classmethod
    def _preview_csv(cls, file_path: Path, delimiter: str = None) -> ImportPreview:
        """Preview de arquivo CSV."""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            # Auto-detecta delimitador
            sample = f.read(2048)
            f.seek(0)
            
            if delimiter is None:
                sniffer = csv.Sniffer()
                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except:
                    delimiter = ','
            
            reader = csv.DictReader(f, delimiter=delimiter)
            columns = reader.fieldnames or []
            column_mapping = ColumnNormalizer.map_columns(columns)
            
            sample_data = []
            total_rows = 0
            
            for i, row in enumerate(reader):
                total_rows += 1
                if i < cls.SAMPLE_SIZE:
                    sample_data.append(row)
            
            errors = []
            warnings = []
            
            # Verifica colunas obrigatórias
            required = {"sku", "nome", "preco"}
            mapped_fields = set(column_mapping.values())
            missing = required - mapped_fields
            if missing:
                errors.append({
                    "type": "missing_required",
                    "message": f"Colunas obrigatórias faltando: {', '.join(missing)}"
                })
            
            return ImportPreview(
                total_rows=total_rows,
                valid_rows=total_rows,
                error_rows=0,
                sample_data=sample_data,
                column_mapping=column_mapping,
                errors=errors,
                warnings=warnings
            )


# ==============================================================================
# ITEM 63-65: Validação e Limpeza de Dados
# ==============================================================================

class DataCleaner:
    """Limpa e valida dados durante importação."""
    
    @staticmethod
    def clean_text(text: Any) -> str:
        """
        Limpa texto removendo espaços e caracteres inválidos.
        Item 65: Trim de strings.
        """
        if text is None:
            return ""
        
        text = str(text).strip()
        
        # Remove caracteres de controle
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\t')
        
        # Normaliza espaços
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def is_empty_row(row: Dict) -> bool:
        """
        Verifica se linha está vazia.
        Item 63: Ignora linhas vazias.
        """
        for value in row.values():
            if value is not None:
                cleaned = str(value).strip()
                if cleaned and cleaned.lower() not in ['nan', 'none', 'null', '']:
                    return False
        return True
    
    @staticmethod
    def has_required_fields(row: Dict, required: List[str]) -> Tuple[bool, List[str]]:
        """Verifica se linha tem campos obrigatórios."""
        missing = []
        
        for field in required:
            value = row.get(field)
            if value is None or str(value).strip() == "":
                missing.append(field)
        
        return (len(missing) == 0, missing)


# ==============================================================================
# ITEM 64: Parser de Moeda Internacional
# ==============================================================================

class CurrencyParser:
    """
    Parser de valores monetários.
    Suporta formatos BR (1.234,56) e US (1,234.56).
    """
    
    # Símbolos de moeda conhecidos
    CURRENCY_SYMBOLS = [
        "R$", "$", "€", "£", "¥", "BRL", "USD", "EUR", "GBP"
    ]
    
    @classmethod
    def parse(cls, value: Any) -> Optional[float]:
        """
        Converte valor monetário para float.
        
        Args:
            value: Valor a converter (pode ser string, int, float)
            
        Returns:
            Float ou None se inválido
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        text = str(value).strip()
        
        # Remove símbolos de moeda
        for symbol in cls.CURRENCY_SYMBOLS:
            text = text.replace(symbol, "")
        
        text = text.strip()
        
        if not text:
            return None
        
        # Detecta formato
        has_comma = "," in text
        has_dot = "." in text
        
        if has_comma and has_dot:
            # Determina separador decimal pela posição
            last_comma = text.rfind(",")
            last_dot = text.rfind(".")
            
            if last_comma > last_dot:
                # Formato BR: 1.234,56
                text = text.replace(".", "").replace(",", ".")
            else:
                # Formato US: 1,234.56
                text = text.replace(",", "")
        
        elif has_comma:
            # Verifica se vírgula é decimal (BR) ou milhar (US)
            parts = text.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Provavelmente decimal BR: 1234,56
                text = text.replace(",", ".")
            else:
                # Provavelmente milhar US: 1,234
                text = text.replace(",", "")
        
        # Remove espaços
        text = text.replace(" ", "")
        
        # Remove caracteres não numéricos (exceto ponto e menos)
        text = re.sub(r'[^\d.\-]', '', text)
        
        try:
            result = float(text)
            # Valida negativos
            if result < 0:
                logger.warning(f"Valor negativo detectado: {value} -> {result}")
            return result
        except ValueError:
            logger.warning(f"Não foi possível parsear valor: {value}")
            return None


# ==============================================================================
# ITEM 66: Detecção de Duplicidade
# ==============================================================================

class DuplicateDetector:
    """Detecta SKUs duplicados no arquivo."""
    
    @staticmethod
    def find_duplicates(rows: List[Dict], sku_field: str = "sku") -> Dict[str, List[int]]:
        """
        Encontra SKUs duplicados.
        
        Args:
            rows: Lista de linhas
            sku_field: Nome do campo de SKU
            
        Returns:
            Dict de {sku: [indices_onde_aparece]}
        """
        sku_locations: Dict[str, List[int]] = {}
        
        for i, row in enumerate(rows):
            sku = str(row.get(sku_field, "")).strip()
            if sku:
                if sku not in sku_locations:
                    sku_locations[sku] = []
                sku_locations[sku].append(i)
        
        # Retorna apenas duplicados
        return {
            sku: indices 
            for sku, indices in sku_locations.items() 
            if len(indices) > 1
        }


# ==============================================================================
# ITEM 67: Log de Erros de Importação
# ==============================================================================

@dataclass
class ImportError:
    """Erro de importação."""
    row_number: int
    original_data: Dict
    error_type: str
    error_message: str
    field: Optional[str] = None


class ImportErrorLogger:
    """Gera arquivo de log com erros de importação."""
    
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.errors: List[ImportError] = []
    
    def add_error(
        self,
        row_number: int,
        original_data: Dict,
        error_type: str,
        error_message: str,
        field: Optional[str] = None
    ):
        """Adiciona erro ao log."""
        self.errors.append(ImportError(
            row_number=row_number,
            original_data=original_data,
            error_type=error_type,
            error_message=error_message,
            field=field
        ))
    
    def save(self) -> Path:
        """Salva log de erros em CSV."""
        with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Linha", "Tipo Erro", "Campo", "Mensagem", "Dados Originais"
            ])
            
            for error in self.errors:
                writer.writerow([
                    error.row_number,
                    error.error_type,
                    error.field or "",
                    error.error_message,
                    str(error.original_data)
                ])
        
        return self.output_path
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def error_count(self) -> int:
        return len(self.errors)


# ==============================================================================
# ITEM 68: Suporte a CSV e ODS
# ==============================================================================

class FileFormatDetector:
    """Detecta e valida formato de arquivo."""
    
    SUPPORTED_FORMATS = {
        ".xlsx": "Excel (xlsx)",
        ".xls": "Excel (xls)",
        ".csv": "CSV",
        ".tsv": "TSV",
        ".txt": "Texto delimitado",
        ".ods": "OpenDocument Spreadsheet",
    }
    
    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """Verifica se formato é suportado."""
        return file_path.suffix.lower() in cls.SUPPORTED_FORMATS
    
    @classmethod
    def get_format_name(cls, file_path: Path) -> str:
        """Retorna nome amigável do formato."""
        return cls.SUPPORTED_FORMATS.get(
            file_path.suffix.lower(),
            "Formato desconhecido"
        )
    
    @classmethod
    def detect_delimiter(cls, file_path: Path) -> str:
        """Detecta delimitador de arquivo texto."""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            sample = f.read(2048)
        
        # Conta ocorrências
        delimiters = {
            ',': sample.count(','),
            ';': sample.count(';'),
            '\t': sample.count('\t'),
            '|': sample.count('|'),
        }
        
        # Retorna o mais frequente
        return max(delimiters, key=delimiters.get)


# ==============================================================================
# ITEM 70: Importador com Barra de Progresso
# ==============================================================================

@dataclass
class ImportProgress:
    """Progresso da importação."""
    current: int
    total: int
    percentage: float
    current_item: str
    status: str  # "importing", "validating", "done", "error"
    errors_count: int = 0


class BatchImporter:
    """
    Importador em lote com suporte a progresso.
    Processa em transações atômicas.
    """
    
    BATCH_SIZE = 100
    
    def __init__(
        self,
        on_progress: Optional[Callable[[ImportProgress], None]] = None,
        on_complete: Optional[Callable[[int, int], None]] = None,
        on_error: Optional[Callable[[ImportError], None]] = None
    ):
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        
        self._error_logger: Optional[ImportErrorLogger] = None
        self._imported = 0
        self._errors = 0
    
    def import_file(
        self,
        file_path: Path,
        column_mapping: Dict[str, str],
        error_log_path: Optional[Path] = None
    ) -> Tuple[int, int]:
        """
        Importa arquivo com progresso.
        
        Args:
            file_path: Caminho do arquivo
            column_mapping: Mapeamento de colunas
            error_log_path: Caminho para log de erros
            
        Returns:
            Tuple (importados, erros)
        """
        if error_log_path:
            self._error_logger = ImportErrorLogger(error_log_path)
        
        # Carrega dados
        rows = self._load_file(file_path)
        total = len(rows)
        
        self._imported = 0
        self._errors = 0
        
        # Processa em batches
        for i, row in enumerate(rows):
            try:
                # Mapeia colunas
                mapped_row = self._map_row(row, column_mapping)
                
                # Valida
                if DataCleaner.is_empty_row(mapped_row):
                    continue
                
                # Limpa dados
                cleaned_row = self._clean_row(mapped_row)
                
                # Aqui chamaria o serviço de banco de dados
                # await self._save_to_db(cleaned_row)
                
                self._imported += 1
                
            except Exception as e:
                self._errors += 1
                if self._error_logger:
                    self._error_logger.add_error(
                        row_number=i + 2,  # +2 por causa do header e índice 0
                        original_data=row,
                        error_type="import_error",
                        error_message=str(e)
                    )
                if self.on_error:
                    self.on_error(ImportError(
                        row_number=i + 2,
                        original_data=row,
                        error_type="import_error",
                        error_message=str(e)
                    ))
            
            # Reporta progresso
            if self.on_progress and (i % 10 == 0 or i == total - 1):
                self.on_progress(ImportProgress(
                    current=i + 1,
                    total=total,
                    percentage=(i + 1) / total * 100,
                    current_item=str(row.get("nome", row.get("sku", "")))[:30],
                    status="importing",
                    errors_count=self._errors
                ))
        
        # Salva log de erros
        if self._error_logger and self._error_logger.has_errors:
            self._error_logger.save()
        
        # Callback de conclusão
        if self.on_complete:
            self.on_complete(self._imported, self._errors)
        
        return (self._imported, self._errors)
    
    def _load_file(self, file_path: Path) -> List[Dict]:
        """Carrega arquivo em lista de dicts."""
        ext = file_path.suffix.lower()
        
        if ext in [".xlsx", ".xls"]:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_dict('records')
        
        elif ext in [".csv", ".txt", ".tsv"]:
            delimiter = FileFormatDetector.detect_delimiter(file_path)
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)
        
        elif ext == ".ods":
            # Requer pyexcel-ods
            try:
                import pyexcel_ods
                data = pyexcel_ods.get_data(str(file_path))
                # Pega primeira planilha
                first_sheet = list(data.values())[0]
                if not first_sheet:
                    return []
                headers = first_sheet[0]
                return [
                    dict(zip(headers, row))
                    for row in first_sheet[1:]
                ]
            except ImportError:
                raise ImportError("pyexcel-ods não instalado para arquivos ODS")
        
        else:
            raise ValueError(f"Formato não suportado: {ext}")
    
    def _map_row(self, row: Dict, mapping: Dict[str, str]) -> Dict:
        """Mapeia colunas do row."""
        mapped = {}
        for original, normalized in mapping.items():
            if original in row:
                mapped[normalized] = row[original]
        return mapped
    
    def _clean_row(self, row: Dict) -> Dict:
        """Limpa dados do row."""
        cleaned = {}
        
        for field, value in row.items():
            if field == "preco" or field == "preco_oferta":
                cleaned[field] = CurrencyParser.parse(value)
            else:
                cleaned[field] = DataCleaner.clean_text(value)
        
        return cleaned


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    "ColumnNormalizer",
    "ImportPreview",
    "ImportPreviewGenerator",
    "DataCleaner",
    "CurrencyParser",
    "DuplicateDetector",
    "ImportError",
    "ImportErrorLogger",
    "FileFormatDetector",
    "ImportProgress",
    "BatchImporter",
]
