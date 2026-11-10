@echo off
title Automacao de Matriculas Escolares - Diadema/SP (Marco 2026)
chcp 65001 >nul

cd /d "%~dp0"

echo =======================================================================
echo    AUTOMAÇÃO DE MATRÍCULAS ESCOLARES – DIADEMA/SP – MARÇO DE 2026
echo    Pipeline ETL de Dados Educacionais Oficiais (SEDUC/SP)
echo =======================================================================
echo.

echo [1/3] Verificando instalacao do Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no sistema ou nao esta no PATH.
    echo Por favor, instale o Python ou configure as variaveis de ambiente.
    echo.
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] Verificando dependencias necessarias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [AVISO] Houve um problema ao verificar as dependencias via pip.
    echo Tentando prosseguir com as bibliotecas instaladas...
)
echo.

echo [3/3] Executando pipeline completo de automacao...
echo =======================================================================
python main.py

echo.
echo =======================================================================
echo      PROCESSO FINALIZADO COM SUCESSO!
echo =======================================================================
echo.
echo Os arquivos gerados estao disponiveis diretamente nesta pasta:
echo  - Matriculas_Diadema_Ciclo_Marco_2026.csv
echo  - Matriculas_Diadema_Turno_Marco_2026.csv
echo  - Indicadores_Educacionais_Diadema_Marco_2026.csv
echo  - Relatorio_Qualidade_Diadema_Marco_2026.txt
echo.
pause

