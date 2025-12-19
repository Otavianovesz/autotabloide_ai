<#
.SYNOPSIS
    Script de inicialização do AutoTabloide AI.
.DESCRIPTION
    Launcher oficial que garante a execução do main.py via Python.
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     AutoTabloide AI - Launcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$MainScript = Join-Path $ScriptDir "main.py"

# Verifica se Python está disponível
try {
    $PythonVer = python --version 2>&1
    Write-Host "[OK] $PythonVer detectado." -ForegroundColor Green
} catch {
    Write-Error "Python não encontrado no PATH. Instale Python 3.12+."
    exit 1
}

# Verifica existência do main.py
if (-not (Test-Path $MainScript)) {
    Write-Error "Arquivo main.py não encontrado em: $MainScript"
    exit 1
}

# Executa
Write-Host "Carregando aplicação..." -ForegroundColor Yellow
python $MainScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "A aplicação encerrou com erro (Código $LASTEXITCODE)." -ForegroundColor Red
    Read-Host "Pressione ENTER para fechar"
}
