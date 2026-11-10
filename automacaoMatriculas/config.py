"""
Módulo de Configuração do Projeto: Automação de Matrículas Escolares – Diadema/SP (Março 2026)
Define caminhos, parâmetros da fonte oficial de dados, mapeamentos de variáveis e logging.
"""

import os
import sys
import logging
from pathlib import Path

# --- DIRETÓRIOS DO PROJETO ---
BASE_DIR = Path(__file__).resolve().parent
DIR_DADOS_ORIGINAIS = BASE_DIR / "dados_originais"
DIR_DADOS_TRATADOS = BASE_DIR / "dados_tratados"
DIR_RELATORIOS = BASE_DIR / "relatorios"
DIR_LOGS = BASE_DIR / "logs"

# Criação garantida dos diretórios
for directory in [DIR_DADOS_ORIGINAIS, DIR_DADOS_TRATADOS, DIR_RELATORIOS, DIR_LOGS]:
    directory.mkdir(parents=True, exist_ok=True)

# --- ARQUIVOS ORIGINAIS ---
FILE_CICLO_ORIGINAL = DIR_DADOS_ORIGINAIS / "MIEST_Ciclo_03_2026.csv"
FILE_TURNO_ORIGINAL = DIR_DADOS_ORIGINAIS / "MIEST_Turno_03_2026.csv"
FILE_DICIONARIO_ORIGINAL = DIR_DADOS_ORIGINAIS / "Dicionario_MIEST.xlsx"

# --- ARQUIVOS TRATADOS ---
FILE_CICLO_TRATADO = DIR_DADOS_TRATADOS / "Matriculas_Diadema_Ciclo.csv"
FILE_TURNO_TRATADO = DIR_DADOS_TRATADOS / "Matriculas_Diadema_Turno.csv"
FILE_CONSOLIDADO_EXCEL = DIR_DADOS_TRATADOS / "Matriculas_Diadema_Consolidado.xlsx"

# --- RELATÓRIOS ---
FILE_RELATORIO_QUALIDADE = DIR_RELATORIOS / "Relatorio_Qualidade.xlsx"
FILE_DICIONARIO_VARIAVEIS = DIR_RELATORIOS / "Dicionario_Variaveis.xlsx"
FILE_RESUMO_TXT = DIR_RELATORIOS / "Resumo_Matriculas.txt"

# --- LOGS ---
FILE_LOG = DIR_LOGS / "automacao_matriculas.log"

# --- FONTES OFICIAIS DE DADOS ---
URL_PORTAL_DADOS_ABERTOS = "https://dados.educacao.sp.gov.br/dataset/miest-matr%C3%ADcula-inicial-da-educa%C3%A7%C3%A3o-b%C3%A1sica-do-estado-de-s%C3%A3o-paulo"
URL_CKAN_PACKAGE_API = "https://dados.educacao.sp.gov.br/api/3/action/package_show?id=miest-matr%C3%ADcula-inicial-da-educa%C3%A7%C3%A3o-b%C3%A1sica-do-estado-de-s%C3%A3o-paulo"

URLS_DOWNLOAD = {
    "MIEST_Ciclo_03_2026.csv": "https://dados.educacao.sp.gov.br/sites/default/files/MIEST%20CICLO%20-%2003%202026.csv",
    "MIEST_Turno_03_2026.csv": "https://dados.educacao.sp.gov.br/sites/default/files/MIEST%20TURNO%20-%2003%202026.csv",
    "Dicionario_MIEST.xlsx": "https://dados.educacao.sp.gov.br/sites/default/files/DICION%C3%81RIO_MIEST_0.xlsx"
}

URL_OBSERVATORIO_DIADEMA = "https://observatorio.diadema.sp.gov.br/bi-escolas-de-diadema/"

# --- PARÂMETROS DE VALIDAÇÃO DE DIADEMA ---
MUN_NOME_OFICIAL = "DIADEMA"
CODMUN_SED_DIADEMA = 286          # Código oficial SED do município de Diadema
CODIGO_IBGE_DIADEMA_7 = 3513801   # Código IBGE 7 dígitos
CODIGO_IBGE_DIADEMA_6 = 351380    # Código IBGE 6 dígitos

# --- CODIFICAÇÃO E DELIMITADOR DAS FONTES ORIGINAIS ---
CSV_ENCODING_ORIGINAL = "latin1"
CSV_DELIMITER_ORIGINAL = ";"
CSV_ENCODING_SAIDA = "utf-8-sig"  # Compatibilidade direta com Excel no Windows

# --- MAPEAMENTOS DESCRITIVOS (DICIONÁRIO MIEST) ---
TURNO_MAP = {
    1: "Manhã",
    2: "Intermediário",
    3: "Tarde",
    4: "Vespertino",
    5: "Noite",
    6: "Integral"
}

DEPADM_MAP = {
    1: "Estadual - SE",
    2: "Municipal",
    3: "Privada",
    4: "Federal",
    5: "Estadual - Outros"
}

CATEG_MAP = {
    1: "Escolas Regulares",
    2: "Classes Vinculadas"
}

# --- GRUPOS DE ETAPAS DE ENSINO (COLUNAS DE ALUNOS) ---
COLUNAS_INFANTIL = [
    "ALUNOSEICRECHE",
    "ALUNOSEIPRE_ESCOLA",
    "ALUNOSEI_MULTI"
]

COLUNAS_FUND_AI = [
    "ALUNOSEF1ANO",
    "ALUNOSEF2ANO",
    "ALUNOSEF3ANO",
    "ALUNOSEF4ANO",
    "ALUNOSEF5ANO"
]

COLUNAS_FUND_AF = [
    "ALUNOSEF6ANO",
    "ALUNOSEF7ANO",
    "ALUNOSEF8ANO",
    "ALUNOSEF9ANO"
]

COLUNAS_FUNDAMENTAL = COLUNAS_FUND_AI + COLUNAS_FUND_AF

COLUNAS_MEDIO_REGULAR = [
    "ALUNOSEM1SERIE",
    "ALUNOSEM2SERIE",
    "ALUNOSEM3SERIE",
    "ALUNOSEM4SERIE",
    "ALUNOSEMNS"
]

COLUNAS_NOVOTEC = [
    "ALUNOSNOVOTEC1SERIE",
    "ALUNOSNOVOTEC2SERIE",
    "ALUNOSNOVOTEC3SERIE"
]

COLUNAS_PROFISSIONAL = [
    "ALUNOSPROF"
]

COLUNAS_EJA = [
    "ALUNOSEJA1CI",
    "ALUNOSEJA2CI",
    "ALUNOSEJA1CII",
    "ALUNOSEJA2CII",
    "ALUNOSEJA3CII",
    "ALUNOSEJA4CII",
    "ALUNOSEJA1_2CII",
    "ALUNOSEJA3_4CII",
    "ALUNOSEJA1EM",
    "ALUNOSEJA2EM",
    "ALUNOSEJA3EM",
    "ALUNOSEJA4EM",
    "ALUNOSEJASEMI1A4",
    "ALUNOSEJASEMI5A8",
    "ALUNOSEJASEMIEM",
    "ALUNOSCEEJA_I",
    "ALUNOSCEEJA_II",
    "ALUNOSCEEJA_EM",
    "ALUNOSPROEJA1CII",
    "ALUNOSPROEJA2CII",
    "ALUNOSPROEJA3CII",
    "ALUNOSPROEJA4CII",
    "ALUNOSPROEJA1EM",
    "ALUNOSPROEJA2EM",
    "ALUNOSPROEJA3EM",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_EF_1TERMO",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_EF_2TERMO",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_EF_3TERMO",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_EF_4TERMO",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_1TERMO_SEM",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_2TERMO_SEM",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_3TERMO_SEM",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_4TERMO_SEM",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_5TERMO_SEM",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_6TERMO_SEM_CONCL",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_1TERMO_ANUAL",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_2TERMO_ANUAL",
    "ALUNOSEJA_TEC_INTEGRADO_PROFIS_MEDIO_3TERMO_ANUAL_CONCL"
]

COLUNAS_ESPECIAL_COMPLEMENTAR = [
    "ALUNOSEC",
    "ALUNOSPROJOVEM",
    "ALUNOSEE",
    "ALUNOS_SR"
]

# Configuração de Logging Centralizado
def setup_logging():
    """Configura o logger com saídas para arquivo e console."""
    logger = logging.getLogger("AutomacaoMatriculasDiadema")
    logger.setLevel(logging.INFO)
    
    # Limpa handlers anteriores para evitar duplicações em múltiplas execuções
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formato do log
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler
    fh = logging.FileHandler(FILE_LOG, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

