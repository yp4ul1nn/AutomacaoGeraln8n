# Script PowerShell: Execucao e Teste da Automacao de Matriculas Diadema (Marco 2026)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $scriptDir

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "   AUTOMAÇÃO DE MATRÍCULAS ESCOLARES – DIADEMA/SP – MARÇO DE 2026" -ForegroundColor Cyan
Write-Host "   Pipeline ETL de Dados Educacionais Oficiais (SEDUC/SP)" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Verificando instalação do Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host " Python detectado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Python não foi encontrado no sistema ou não está no PATH." -ForegroundColor Red
    Write-Host "Pressione qualquer tecla para sair..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host ""

Write-Host "[2/3] Verificando dependências necessárias..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host " Dependências verificadas." -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] Executando pipeline completo de automação..." -ForegroundColor Yellow
Write-Host "-----------------------------------------------------------------------" -ForegroundColor Gray
python main.py
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=======================================================================" -ForegroundColor Cyan
if ($exitCode -eq 0) {
    Write-Host "     PROCESSO FINALIZADO COM SUCESSO!" -ForegroundColor Green
    Write-Host "=======================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Arquivos gerados diretamente nesta pasta:" -ForegroundColor White
    Write-Host " - Matriculas_Diadema_Ciclo_Marco_2026.csv" -ForegroundColor Gray
    Write-Host " - Matriculas_Diadema_Turno_Marco_2026.csv" -ForegroundColor Gray
    Write-Host " - Indicadores_Educacionais_Diadema_Marco_2026.csv" -ForegroundColor Gray
    Write-Host " - Relatorio_Qualidade_Diadema_Marco_2026.txt" -ForegroundColor Gray
} else {
    Write-Host "     PROCESSO FINALIZADO COM ERROS (Código: $exitCode)" -ForegroundColor Red
    Write-Host "=======================================================================" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Pressione qualquer tecla para finalizar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

