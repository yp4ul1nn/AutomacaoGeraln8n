"""
Módulo de Coleta: Automação de Matrículas Escolares – Diadema/SP (Março 2026)
Responsável por baixar os dados oficiais do portal de Dados Abertos de SP
e inspecionar fontes complementares (Observatório Diadema).
"""

import os
import requests
import urllib3
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from config import (
    DIR_DADOS_ORIGINAIS,
    FILE_CICLO_ORIGINAL,
    FILE_TURNO_ORIGINAL,
    FILE_DICIONARIO_ORIGINAL,
    URLS_DOWNLOAD,
    URL_PORTAL_DADOS_ABERTOS,
    URL_CKAN_PACKAGE_API,
    URL_OBSERVATORIO_DIADEMA
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger("AutomacaoMatriculasDiadema")


def baixar_arquivo(url: str, destino: Path, chunk_size: int = 1024 * 1024) -> bool:
    """
    Baixa um arquivo via streaming com barra de progresso em log e tratamento de exceções.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    logger.info(f"Iniciando download de {url} -> {destino.name}...")
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=90, verify=False)
        response.raise_for_status()

        total_bytes = int(response.headers.get("content-length", 0))
        downloaded = 0

        temp_dest = destino.with_suffix(".tmp")
        with open(temp_dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        # Se download foi bem sucedido, renomeia arquivo temporário
        if temp_dest.exists():
            temp_dest.replace(destino)

        size_mb = destino.stat().st_size / (1024 * 1024)
        logger.info(f"Sucesso: {destino.name} baixado ({size_mb:.2f} MB).")
        return True
    except Exception as e:
        logger.error(f"Erro ao baixar {destino.name} da URL {url}: {e}")
        temp_dest = destino.with_suffix(".tmp")
        if temp_dest.exists():
            temp_dest.unlink(missing_ok=True)
        return False


def coletar_arquivos_oficiais(force_download: bool = False) -> Dict[str, Path]:
    """
    Coordena o download dos três arquivos oficiais do MIEST 03/2026.
    Retorna dicionário com caminhos dos arquivos confirmados.
    """
    logger.info("Verificando disponibilidade dos arquivos oficiais do MIEST...")
    caminhos = {
        "ciclo": FILE_CICLO_ORIGINAL,
        "turno": FILE_TURNO_ORIGINAL,
        "dicionario": FILE_DICIONARIO_ORIGINAL
    }

    map_arquivos = {
        "MIEST_Ciclo_03_2026.csv": FILE_CICLO_ORIGINAL,
        "MIEST_Turno_03_2026.csv": FILE_TURNO_ORIGINAL,
        "Dicionario_MIEST.xlsx": FILE_DICIONARIO_ORIGINAL
    }

    for filename, filepath in map_arquivos.items():
        url = URLS_DOWNLOAD[filename]
        # Se arquivo já existe e possui tamanho > 0 e não foi forçado o download, reutiliza
        if filepath.exists() and filepath.stat().st_size > 0 and not force_download:
            size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(f"Arquivo existente mantido: {filepath.name} ({size_mb:.2f} MB).")
        else:
            sucesso = baixar_arquivo(url, filepath)
            if not sucesso or not filepath.exists() or filepath.stat().st_size == 0:
                raise RuntimeError(f"Falha crítica na coleta do arquivo obrigatório: {filename}")

    return caminhos


def inspecionar_observatorio_diadema() -> Dict[str, Any]:
    """
    Acessa a fonte complementar Observatório Diadema para levantar
    indicadores e estrutura visual de apresentação.
    """
    logger.info(f"Consultando fonte complementar: {URL_OBSERVATORIO_DIADEMA}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resultado = {
        "url": URL_OBSERVATORIO_DIADEMA,
        "status_code": None,
        "acessivel": False,
        "tecnologia": "Google Looker Studio Embed",
        "looker_url": None,
        "dimensoes_identificadas": [
            "ESCOLA", "DEPENDÊNCIA", "TIPO ESCOLA", "ENDEREÇO", "BAIRRO",
            "E. INF", "E. FUND", "ENS MÉD", "ED COMPL", "NOVO TEC", "EJA", "ED PROF", "TOTAL"
        ],
        "observacoes": (
            "O painel do Observatório utiliza os dados do MIEST de Março/2026. "
            "A visualização é feita via Looker Studio embutido em iframe."
        )
    }

    try:
        r = requests.get(URL_OBSERVATORIO_DIADEMA, headers=headers, timeout=20, verify=False)
        resultado["status_code"] = r.status_code
        if r.status_code == 200:
            resultado["acessivel"] = True
            logger.info("Observatório Diadema acessado com sucesso (Status 200).")
            # Extração de iframe do Looker Studio
            import re
            looker_match = re.search(r'src=[\'"](https://lookerstudio\.google\.com[^\'"]+)[\'"]', r.text)
            if looker_match:
                resultado["looker_url"] = looker_match.group(1)
                logger.info(f"Painel Looker Studio identificado: {resultado['looker_url']}")
        else:
            logger.warning(f"Observatório retornou status {r.status_code}.")
    except Exception as e:
        logger.warning(f"Não foi possível acessar o Observatório Diadema diretamente: {e}. Prosseguindo com dados do MIEST.")

    return resultado


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()
    coletar_arquivos_oficiais(force_download=False)
    info_obs = inspecionar_observatorio_diadema()
    print("Info Observatório:", info_obs)

