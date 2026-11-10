"""
Módulo de Indicadores: Automação de Matrículas Escolares – Diadema/SP (Março 2026)
Calcula e estrutura todos os indicadores educacionais solicitados,
estatísticas descritivas, distribuições percentuais e comparações entre unidades.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from config import (
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


def calcular_todos_indicadores(df_ciclo: pd.DataFrame, df_turno: pd.DataFrame) -> Dict[str, Any]:
    """
    Consolida o cálculo de todos os indicadores quantitativos e percentuais
    a partir das bases tratadas de Ciclo e Turno.
    """
    logger.info("Calculando indicadores educacionais de Diadema/SP (Março 2026)...")

    # 1. Indicadores Gerais e Globais
    total_matriculas = int(df_ciclo["TOTAL_MATRICULAS"].sum())
    total_classes = int(df_ciclo["TOTAL_CLASSES"].sum())
    total_salas = int(df_ciclo["SALAS_AULA"].sum())
    total_escolas = int(df_ciclo["CODESC"].nunique())

    media_matriculas_escola = float(df_ciclo["TOTAL_MATRICULAS"].mean())
    mediana_matriculas_escola = float(df_ciclo["TOTAL_MATRICULAS"].median())
    desvio_matriculas_escola = float(df_ciclo["TOTAL_MATRICULAS"].std())
    max_matriculas_escola = int(df_ciclo["TOTAL_MATRICULAS"].max())
    min_matriculas_escola = int(df_ciclo["TOTAL_MATRICULAS"].min())

    media_alunos_por_turma = float(total_matriculas / total_classes) if total_classes > 0 else 0.0

    # 2. Distribuição por Rede de Ensino (Dependência Administrativa)
    rede_df = df_ciclo.groupby("DESC_DEPADM").agg(
        escolas=("CODESC", "nunique"),
        matriculas=("TOTAL_MATRICULAS", "sum"),
        classes=("TOTAL_CLASSES", "sum"),
        salas=("SALAS_AULA", "sum")
    ).reset_index()
    rede_df["percentual_matriculas"] = (rede_df["matriculas"] / total_matriculas) * 100
    rede_df["percentual_escolas"] = (rede_df["escolas"] / total_escolas) * 100
    rede_df = rede_df.sort_values(by="matriculas", ascending=False)

    # 3. Distribuição por Etapas e Modalidades de Ensino
    etapas_dict = {
        "Educação Infantil (Creche e Pré-Escola)": int(df_ciclo["MATR_INFANTIL"].sum()),
        "Ensino Fundamental - Anos Iniciais (1º ao 5º ano)": int(df_ciclo["MATR_FUND_ANOS_INICIAIS"].sum()),
        "Ensino Fundamental - Anos Finais (6º ao 9º ano)": int(df_ciclo["MATR_FUND_ANOS_FINAIS"].sum()),
        "Ensino Fundamental (Total)": int(df_ciclo["MATR_FUNDAMENTAL_TOTAL"].sum()),
        "Ensino Médio Regular": int(df_ciclo["MATR_MEDIO_REGULAR"].sum()),
        "Ensino Médio - Novotec": int(df_ciclo["MATR_NOVOTEC"].sum()),
        "Educação Profissional": int(df_ciclo["MATR_PROFISSIONAL"].sum()),
        "Educação de Jovens e Adultos (EJA)": int(df_ciclo["MATR_EJA"].sum()),
        "Educação Especial / Atendimento Complementar": int(df_ciclo["MATR_ESPECIAL_COMPL"].sum())
    }

    # 4. Distribuição por Turno de Funcionamento (a partir da base Turno)
    turno_df = df_turno.groupby(["TURNO", "DESC_TURNO"]).agg(
        registros=("CODESC", "count"),
        escolas_com_turno=("CODESC", "nunique"),
        matriculas=("TOTAL_MATRICULAS", "sum"),
        classes=("TOTAL_CLASSES", "sum")
    ).reset_index()
    total_turno_matr = df_turno["TOTAL_MATRICULAS"].sum()
    turno_df["percentual"] = (turno_df["matriculas"] / total_turno_matr) * 100
    turno_df = turno_df.sort_values(by="matriculas", ascending=False)

    # 5. Maiores e Menores Unidades Escolares por Matrículas
    cols_escola = ["CODESC", "NOMESC", "DESC_DEPADM", "BAIESC", "TOTAL_MATRICULAS", "TOTAL_CLASSES"]
    top_10_maiores = df_ciclo[cols_escola].sort_values(by="TOTAL_MATRICULAS", ascending=False).head(10).to_dict("records")
    top_10_menores = df_ciclo[cols_escola].sort_values(by="TOTAL_MATRICULAS", ascending=True).head(10).to_dict("records")

    # 6. Distribuição por Bairros (Top 10 Bairros com mais matrículas)
    bairro_df = df_ciclo.groupby("BAIESC").agg(
        escolas=("CODESC", "nunique"),
        matriculas=("TOTAL_MATRICULAS", "sum")
    ).reset_index().sort_values(by="matriculas", ascending=False)
    bairro_df["percentual"] = (bairro_df["matriculas"] / total_matriculas) * 100
    top_bairros = bairro_df.head(10).to_dict("records")

    # 7. Verificação de suporte a variáveis demográficas (sexo, idade)
    demografia_status = {
        "suporte_sexo": False,
        "suporte_idade": False,
        "motivo": (
            "A base pública MIEST da SEDUC/SP organiza as matrículas agrupadas por unidade escolar, "
            "turma, série/ano e turno, não disponibilizando campos de desagregação individual por sexo ou idade. "
            "Em conformidade com as diretrizes do projeto, não foram gerados indicadores sem suporte na fonte."
        )
    }

    indicadores = {
        "gerais": {
            "total_matriculas": total_matriculas,
            "total_escolas": total_escolas,
            "total_classes": total_classes,
            "total_salas_aula": total_salas,
            "media_matriculas_por_escola": round(media_matriculas_escola, 2),
            "mediana_matriculas_por_escola": round(mediana_matriculas_escola, 2),
            "desvio_padrao_matriculas": round(desvio_matriculas_escola, 2),
            "maior_escola_matriculas": max_matriculas_escola,
            "menor_escola_matriculas": min_matriculas_escola,
            "media_alunos_por_turma": round(media_alunos_por_turma, 2)
        },
        "por_rede": rede_df.to_dict("records"),
        "por_etapa": etapas_dict,
        "por_turno": turno_df.to_dict("records"),
        "top_10_maiores_escolas": top_10_maiores,
        "top_10_menores_escolas": top_10_menores,
        "top_bairros": top_bairros,
        "demografia_status": demografia_status
    }

    logger.info("Indicadores calculados com sucesso.")
    return indicadores


def gerar_texto_resumo_indicadores(indicadores: Dict[str, Any]) -> str:
    """Gera representação textual formatada de todos os indicadores calculados."""
    g = indicadores["gerais"]
    et = indicadores["por_etapa"]

    linhas = []
    linhas.append("=" * 80)
    linhas.append("RESUMO EXECUTIVO: MATRÍCULAS ESCOLARES DE DIADEMA/SP – MARÇO DE 2026")
    linhas.append("Fonte Oficial: SEDUC-SP / MIEST (Matrícula Inicial da Educação Básica)")
    linhas.append("=" * 80)
    linhas.append("")
    linhas.append("1. INDICADORES GLOBAIS:")
    linhas.append(f" - Total de Matrículas Ativas: {g['total_matriculas']:,}".replace(",", "."))
    linhas.append(f" - Unidades Escolares Únicas: {g['total_escolas']}")
    linhas.append(f" - Total de Turmas / Classes Físicas: {g['total_classes']:,}".replace(",", "."))
    linhas.append(f" - Total de Salas de Aula Físicas: {g['total_salas_aula']:,}".replace(",", "."))
    linhas.append(f" - Média de Alunos por Escola: {g['media_matriculas_por_escola']:.1f}")
    linhas.append(f" - Mediana de Alunos por Escola: {g['mediana_matriculas_por_escola']:.1f}")
    linhas.append(f" - Média de Alunos por Turma: {g['media_alunos_por_turma']:.1f}")
    linhas.append("")

    linhas.append("2. DISTRIBUIÇÃO POR REDE DE ENSINO (DEPENDÊNCIA ADMINISTRATIVA):")
    linhas.append(f"{'Rede de Ensino':<22} | {'Escolas':<7} | {'Matrículas':<11} | {'% Part.'}")
    linhas.append("-" * 55)
    for r in indicadores["por_rede"]:
        matr_str = f"{r['matriculas']:,}".replace(",", ".")
        linhas.append(f"{r['DESC_DEPADM']:<22} | {r['escolas']:<7} | {matr_str:<11} | {r['percentual_matriculas']:>6.2f}%")
    linhas.append("")

    linhas.append("3. DISTRIBUIÇÃO POR ETAPAS E MODALIDADES DE ENSINO:")
    total_m = g["total_matriculas"]
    for etapa, qtd in et.items():
        pct = (qtd / total_m) * 100
        qtd_str = f"{qtd:,}".replace(",", ".")
        linhas.append(f" - {etapa:<55}: {qtd_str:>7} ({pct:>5.2f}%)")
    linhas.append("")

    linhas.append("4. DISTRIBUIÇÃO POR TURNO DE FUNCIONAMENTO:")
    linhas.append(f"{'Turno':<18} | {'Escolas':<7} | {'Matrículas':<11} | {'% Part.'}")
    linhas.append("-" * 50)
    for t in indicadores["por_turno"]:
        matr_str = f"{t['matriculas']:,}".replace(",", ".")
        linhas.append(f"{t['DESC_TURNO']:<18} | {t['escolas_com_turno']:<7} | {matr_str:<11} | {t['percentual']:>6.2f}%")
    linhas.append("")

    linhas.append("5. MAIORES UNIDADES ESCOLARES (TOP 5 EM MATRÍCULAS):")
    for i, esc in enumerate(indicadores["top_10_maiores_escolas"][:5], 1):
        matr_str = f"{esc['TOTAL_MATRICULAS']:,}".replace(",", ".")
        linhas.append(f" {i}. {esc['NOMESC']} ({esc['DESC_DEPADM']}) - {esc['BAIESC']}: {matr_str} alunos ({esc['TOTAL_CLASSES']} turmas)")
    linhas.append("")

    linhas.append("6. NOTA METODOLÓGICA E COBERTURA:")
    linhas.append(" - Os dados refletem a Matrícula Inicial (MIEST) apurada em março de 2026.")
    linhas.append(" - A base cobre a rede Estadual (SE e Centro Paula Souza), Municipal e Privada.")
    linhas.append(f" - {indicadores['demografia_status']['motivo']}")
    linhas.append("=" * 80)

    return "\n".join(linhas)


if __name__ == "__main__":
    from config import setup_logging, FILE_CICLO_TRATADO, FILE_TURNO_TRATADO
    setup_logging()
    df_c = pd.read_csv(FILE_CICLO_TRATADO, sep=";", encoding="utf-8-sig")
    df_t = pd.read_csv(FILE_TURNO_TRATADO, sep=";", encoding="utf-8-sig")
    ind = calcular_todos_indicadores(df_c, df_t)
    print(gerar_texto_resumo_indicadores(ind))

