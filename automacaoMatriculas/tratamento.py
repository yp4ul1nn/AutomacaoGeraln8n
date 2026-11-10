"""
Módulo de Tratamento e Limpeza: Automação de Matrículas Escolares – Diadema/SP (Março 2026)
Executa a padronização, limpeza, enriquecimento, cálculo de agregados e exportação
dos dados filtrados para Diadema/SP (Ciclo e Turno).
"""

import os
import logging
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

from config import (
    FILE_CICLO_ORIGINAL,
    FILE_TURNO_ORIGINAL,
    FILE_CICLO_TRATADO,
    FILE_TURNO_TRATADO,
    FILE_CONSOLIDADO_EXCEL,
    CODMUN_SED_DIADEMA,
    MUN_NOME_OFICIAL,
    CODIGO_IBGE_DIADEMA_7,
    CSV_ENCODING_ORIGINAL,
    CSV_DELIMITER_ORIGINAL,
    CSV_ENCODING_SAIDA,
    TURNO_MAP,
    DEPADM_MAP,
    CATEG_MAP,
    COLUNAS_INFANTIL,
    COLUNAS_FUND_AI,
    COLUNAS_FUND_AF,
    COLUNAS_FUNDAMENTAL,
    COLUNAS_MEDIO_REGULAR,
    COLUNAS_NOVOTEC,
    COLUNAS_PROFISSIONAL,
    COLUNAS_EJA,
    COLUNAS_ESPECIAL_COMPLEMENTAR
)

logger = logging.getLogger("AutomacaoMatriculasDiadema")


def ler_base_original(caminho_csv: Path) -> pd.DataFrame:
    """Lê arquivo CSV original com parâmetros otimizados e tratamento de encoding."""
    logger.info(f"Carregando arquivo CSV original: {caminho_csv.name}...")
    df = pd.read_csv(
        caminho_csv,
        sep=CSV_DELIMITER_ORIGINAL,
        encoding=CSV_ENCODING_ORIGINAL,
        low_memory=False
    )
    # Padronização de nomes de colunas (remoção de espaços)
    df.columns = [str(c).strip() for c in df.columns]
    logger.info(f"Arquivo {caminho_csv.name} carregado com {len(df):,} linhas e {len(df.columns)} colunas.")
    return df


def filtrar_diadema(df: pd.DataFrame, nome_base: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filtra estritamente os registros de Diadema/SP utilizando duplo critério:
    CODMUN == 286 (código SED) e MUN == 'DIADEMA'.
    Retorna o DataFrame filtrado e métricas do filtro.
    """
    total_original = len(df)
    
    # Validação de presença das colunas essenciais
    if "CODMUN" not in df.columns or "MUN" not in df.columns:
        raise ValueError(f"Colunas de identificação municipal ausentes na base {nome_base}.")

    # Filtro composto e seguro
    mask_codmun = pd.to_numeric(df["CODMUN"], errors="coerce") == CODMUN_SED_DIADEMA
    mask_mun = df["MUN"].astype(str).str.strip().str.upper() == MUN_NOME_OFICIAL

    df_filtrado = df[mask_codmun & mask_mun].copy()
    total_filtrado = len(df_filtrado)
    total_descartado = total_original - total_filtrado

    logger.info(
        f"[{nome_base}] Registros originais: {total_original:,} | "
        f"Diadema encontrados: {total_filtrado:,} | "
        f"Descartados: {total_descartado:,}"
    )

    metricas = {
        "base": nome_base,
        "total_original": total_original,
        "total_diadema": total_filtrado,
        "total_descartado": total_descartado
    }
    return df_filtrado, metricas


def limpar_e_enriquecer_dados(df: pd.DataFrame, is_turno: bool = False) -> pd.DataFrame:
    """
    Realiza a padronização e higienização dos dados de Diadema:
    - Conversão de coordenadas (DS_LONGITUDE, DS_LATITUDE) para numérico
    - Preenchimento e tipagem das colunas numéricas de matrículas e classes
    - Padronização de strings (textos em maiúsculas sem espaços múltiplos)
    - Enriquecimento com código IBGE, descrições de rede, categoria e turno
    - Cálculo de subtotais por etapa educacional sem sobreposição
    """
    df = df.copy()

    # 1. Código IBGE e Validação
    df["COD_IBGE"] = CODIGO_IBGE_DIADEMA_7

    # 2. Higienização de strings principais
    cols_texto = ["NOMESC", "ENDESC", "BAIESC", "DISTR", "MUN", "DE", "NOMEDEP"]
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    # 3. Conversão de coordenadas geográficas
    for col_geo in ["DS_LONGITUDE", "DS_LATITUDE"]:
        if col_geo in df.columns:
            df[col_geo] = pd.to_numeric(
                df[col_geo].astype(str).str.replace(",", "."),
                errors="coerce"
            )

    # 4. Colunas de Matrículas (ALUNOS*)
    cols_alunos = [c for c in df.columns if c.startswith("ALUNOS")]
    for col in cols_alunos:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.int64)

    # 5. Colunas de Classes (CLASSES*)
    cols_classes = [c for c in df.columns if c.startswith("CLASSES")]
    for col in cols_classes:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.int64)

    # 6. Salas de aula
    if "SALAS_AULA" in df.columns:
        df["SALAS_AULA"] = pd.to_numeric(df["SALAS_AULA"], errors="coerce").fillna(0).astype(np.int64)

    # 7. Flags binárias (FLAG-*)
    cols_flag = [c for c in df.columns if c.startswith("FLAG-")]
    for col in cols_flag:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.int64)

    # 8. Decodificação descritiva
    if "DEPADM" in df.columns:
        df["DESC_DEPADM"] = df["DEPADM"].map(DEPADM_MAP).fillna("Outra/Não Definida")
    if "CATEG" in df.columns:
        df["DESC_CATEG"] = df["CATEG"].map(CATEG_MAP).fillna("Outra")

    if is_turno and "TURNO" in df.columns:
        df["TURNO"] = pd.to_numeric(df["TURNO"], errors="coerce").fillna(0).astype(np.int64)
        df["DESC_TURNO"] = df["TURNO"].map(TURNO_MAP).fillna("Outro")

    # 9. Cálculo de Subtotais por Etapa Educacional (sem dupla contagem)
    # Apenas colunas existentes no dataframe são consideradas
    def cols_existentes(lista):
        return [c for c in lista if c in df.columns]

    df["MATR_INFANTIL"] = df[cols_existentes(COLUNAS_INFANTIL)].sum(axis=1)
    df["MATR_FUND_ANOS_INICIAIS"] = df[cols_existentes(COLUNAS_FUND_AI)].sum(axis=1)
    df["MATR_FUND_ANOS_FINAIS"] = df[cols_existentes(COLUNAS_FUND_AF)].sum(axis=1)
    df["MATR_FUNDAMENTAL_TOTAL"] = df["MATR_FUND_ANOS_INICIAIS"] + df["MATR_FUND_ANOS_FINAIS"]
    df["MATR_MEDIO_REGULAR"] = df[cols_existentes(COLUNAS_MEDIO_REGULAR)].sum(axis=1)
    df["MATR_NOVOTEC"] = df[cols_existentes(COLUNAS_NOVOTEC)].sum(axis=1)
    df["MATR_PROFISSIONAL"] = df[cols_existentes(COLUNAS_PROFISSIONAL)].sum(axis=1)
    df["MATR_EJA"] = df[cols_existentes(COLUNAS_EJA)].sum(axis=1)
    df["MATR_ESPECIAL_COMPL"] = df[cols_existentes(COLUNAS_ESPECIAL_COMPLEMENTAR)].sum(axis=1)

    # Total geral de matrículas da linha
    df["TOTAL_MATRICULAS"] = df[cols_alunos].sum(axis=1)
    df["TOTAL_CLASSES"] = df[cols_classes].sum(axis=1)

    return df


def executar_tratamento() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executa o fluxo completo de carregamento, filtragem, tratamento
    e persistência das bases Ciclo e Turno de Diadema/SP.
    """
    logger.info("=== INICIANDO ETAPA DE TRATAMENTO DOS DADOS ===")

    # 1. Carregamento dos dados brutos
    df_ciclo_raw = ler_base_original(FILE_CICLO_ORIGINAL)
    df_turno_raw = ler_base_original(FILE_TURNO_ORIGINAL)

    # 2. Filtragem de Diadema
    df_ciclo_dia, meta_c = filtrar_diadema(df_ciclo_raw, "MIEST Ciclo")
    df_turno_dia, meta_t = filtrar_diadema(df_turno_raw, "MIEST Turno")

    # 3. Tratamento e enriquecimento
    df_ciclo_tratado = limpar_e_enriquecer_dados(df_ciclo_dia, is_turno=False)
    df_turno_tratado = limpar_e_enriquecer_dados(df_turno_dia, is_turno=True)

    # 4. Exportação dos CSVs tratados
    logger.info(f"Salvando CSV tratado: {FILE_CICLO_TRATADO.name}...")
    df_ciclo_tratado.to_csv(FILE_CICLO_TRATADO, sep=";", index=False, encoding=CSV_ENCODING_SAIDA)

    logger.info(f"Salvando CSV tratado: {FILE_TURNO_TRATADO.name}...")
    df_turno_tratado.to_csv(FILE_TURNO_TRATADO, sep=";", index=False, encoding=CSV_ENCODING_SAIDA)

    # 5. Exportação da Planilha Consolidada Excel
    exportar_excel_consolidado(df_ciclo_tratado, df_turno_tratado, FILE_CONSOLIDADO_EXCEL)

    metricas_tratamento = {
        "ciclo": meta_c,
        "turno": meta_t,
        "escolas_unicas_ciclo": df_ciclo_tratado["CODESC"].nunique(),
        "escolas_unicas_turno": df_turno_tratado["CODESC"].nunique(),
        "total_matriculas_ciclo": int(df_ciclo_tratado["TOTAL_MATRICULAS"].sum()),
        "total_matriculas_turno": int(df_turno_tratado["TOTAL_MATRICULAS"].sum()),
    }

    logger.info("Tratamento concluído com sucesso!")
    return df_ciclo_tratado, df_turno_tratado, metricas_tratamento


def exportar_excel_consolidado(df_c: pd.DataFrame, df_t: pd.DataFrame, caminho_excel: Path):
    """
    Gera o arquivo Excel consolidado com múltiplas abas analíticas,
    estruturadas e formatadas para consulta de gestores e analistas.
    """
    logger.info(f"Gerando arquivo Excel consolidado: {caminho_excel.name}...")

    # Visão 1: Tabela Resumo das Escolas (Ciclo)
    cols_resumo_c = [
        "CODESC", "CODIGO INEP", "NOMESC", "DESC_DEPADM", "DESC_CATEG", "BAIESC", "ENDESC",
        "SALAS_AULA", "TOTAL_CLASSES",
        "MATR_INFANTIL", "MATR_FUND_ANOS_INICIAIS", "MATR_FUND_ANOS_FINAIS",
        "MATR_FUNDAMENTAL_TOTAL", "MATR_MEDIO_REGULAR", "MATR_NOVOTEC",
        "MATR_PROFISSIONAL", "MATR_EJA", "MATR_ESPECIAL_COMPL",
        "TOTAL_MATRICULAS"
    ]
    cols_exist_c = [c for c in cols_resumo_c if c in df_c.columns]
    df_escolas_ciclo = df_c[cols_exist_c].sort_values(by="TOTAL_MATRICULAS", ascending=False)

    # Visão 2: Tabela Resumo das Escolas por Turno
    cols_resumo_t = [
        "CODESC", "NOMESC", "DESC_DEPADM", "TURNO", "DESC_TURNO",
        "MATR_INFANTIL", "MATR_FUNDAMENTAL_TOTAL", "MATR_MEDIO_REGULAR",
        "MATR_NOVOTEC", "MATR_PROFISSIONAL", "MATR_EJA", "MATR_ESPECIAL_COMPL",
        "TOTAL_MATRICULAS"
    ]
    cols_exist_t = [c for c in cols_resumo_t if c in df_t.columns]
    df_escolas_turno = df_t[cols_exist_t].sort_values(by=["NOMESC", "TURNO"])

    # Visão 3: Agregação por Rede de Ensino
    agg_rede = df_c.groupby("DESC_DEPADM").agg(
        Qtd_Escolas=("CODESC", "nunique"),
        Total_Salas=("SALAS_AULA", "sum"),
        Total_Classes=("TOTAL_CLASSES", "sum"),
        Educacao_Infantil=("MATR_INFANTIL", "sum"),
        Ensino_Fundamental=("MATR_FUNDAMENTAL_TOTAL", "sum"),
        Ensino_Medio_Regular=("MATR_MEDIO_REGULAR", "sum"),
        NovoTec=("MATR_NOVOTEC", "sum"),
        Educacao_Profissional=("MATR_PROFISSIONAL", "sum"),
        EJA=("MATR_EJA", "sum"),
        Ed_Especial_Compl=("MATR_ESPECIAL_COMPL", "sum"),
        Total_Matriculas=("TOTAL_MATRICULAS", "sum")
    ).reset_index()
    agg_rede["Participacao_Pct"] = (agg_rede["Total_Matriculas"] / agg_rede["Total_Matriculas"].sum()) * 100

    # Visão 4: Agregação por Turno de Funcionamento
    agg_turno = df_t.groupby(["TURNO", "DESC_TURNO"]).agg(
        Qtd_Registros=("CODESC", "count"),
        Qtd_Escolas_Atendidas=("CODESC", "nunique"),
        Total_Matriculas=("TOTAL_MATRICULAS", "sum")
    ).reset_index()
    agg_turno["Participacao_Pct"] = (agg_turno["Total_Matriculas"] / agg_turno["Total_Matriculas"].sum()) * 100

    # Visão 5: Agregação Geral de Etapas de Ensino
    totais_etapas = {
        "Etapa / Categoria de Ensino": [
            "Educação Infantil (Creche + Pré-Escola)",
            "Ensino Fundamental - Anos Iniciais (1º ao 5º ano)",
            "Ensino Fundamental - Anos Finais (6º ao 9º ano)",
            "Ensino Fundamental - Total",
            "Ensino Médio Regular (1ª a 4ª série / NS)",
            "Ensino Médio - Novotec (Habilitação Técnica)",
            "Educação Profissional",
            "Educação de Jovens e Adultos (EJA Fundamental e Médio)",
            "Educação Especial e Atendimento Complementar",
            "TOTAL GERAL DE MATRÍCULAS"
        ],
        "Total de Matrículas": [
            int(df_c["MATR_INFANTIL"].sum()),
            int(df_c["MATR_FUND_ANOS_INICIAIS"].sum()),
            int(df_c["MATR_FUND_ANOS_FINAIS"].sum()),
            int(df_c["MATR_FUNDAMENTAL_TOTAL"].sum()),
            int(df_c["MATR_MEDIO_REGULAR"].sum()),
            int(df_c["MATR_NOVOTEC"].sum()),
            int(df_c["MATR_PROFISSIONAL"].sum()),
            int(df_c["MATR_EJA"].sum()),
            int(df_c["MATR_ESPECIAL_COMPL"].sum()),
            int(df_c["TOTAL_MATRICULAS"].sum())
        ]
    }
    df_etapas = pd.DataFrame(totais_etapas)
    total_base = df_c["TOTAL_MATRICULAS"].sum()
    df_etapas["Percentual_Sobre_Total"] = (df_etapas["Total de Matrículas"] / total_base) * 100

    # Escrita no Excel com formatação OpenPyXL
    with pd.ExcelWriter(caminho_excel, engine="openpyxl") as writer:
        df_etapas.to_excel(writer, sheet_name="Resumo Etapas", index=False)
        agg_rede.to_excel(writer, sheet_name="Por Rede de Ensino", index=False)
        agg_turno.to_excel(writer, sheet_name="Por Turno", index=False)
        df_escolas_ciclo.to_excel(writer, sheet_name="Escolas - Ciclo", index=False)
        df_escolas_turno.to_excel(writer, sheet_name="Escolas - Turno", index=False)

    logger.info(f"Excel consolidado gravado com sucesso: {caminho_excel.name}")


if __name__ == "__main__":
    from config import setup_logging
    setup_logging()
    c, t, m = executar_tratamento()
    print("Métricas do tratamento:", m)
