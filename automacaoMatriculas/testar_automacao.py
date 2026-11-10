"""
Script de Teste e Validação da Automação de Matrículas Escolares - Diadema/SP (Março 2026)
Verifica se todos os arquivos foram gerados, se os totais batem e se a base está 100% íntegra.
"""

import sys
from pathlib import Path
import pandas as pd

PASTA = Path(__file__).resolve().parent

CSV_CICLO = PASTA / "Matriculas_Diadema_Ciclo_Marco_2026.csv"
CSV_TURNO = PASTA / "Matriculas_Diadema_Turno_Marco_2026.csv"
CSV_INDICADORES = PASTA / "Indicadores_Educacionais_Diadema_Marco_2026.csv"
TXT_RELATORIO = PASTA / "Relatorio_Qualidade_Diadema_Marco_2026.txt"

def testar():
    print("=" * 75)
    print("   TESTE DE VALIDAÇÃO: automacaoMatriculas (Março/2026)")
    print("=" * 75)
    
    erros = []

    # 1. Verificar se main.py executa
    print("\n[1/4] Executando main.py...")
    try:
        from main import main as executar_main
        executar_main()
        print("  [OK] main.py executou com sucesso.")
    except Exception as e:
        print(f"  [FALHA] Erro na execução do main.py: {e}")
        erros.append(f"Execução: {e}")

    # 2. Verificar existência dos arquivos de saída
    print("\n[2/4] Verificando arquivos de saída gerados na pasta raiz...")
    arquivos = [CSV_CICLO, CSV_TURNO, CSV_INDICADORES, TXT_RELATORIO]
    for arq in arquivos:
        if arq.exists() and arq.stat().st_size > 0:
            kb = arq.stat().st_size / 1024
            print(f"  [OK] {arq.name} ({kb:.1f} KB)")
        else:
            print(f"  [FALHA] Arquivo ausente ou vazio: {arq.name}")
            erros.append(f"Arquivo ausente: {arq.name}")

    # 3. Validar consistência quantitativa
    print("\n[3/4] Validando consistência quantitativa dos dados...")
    try:
        df_c = pd.read_csv(CSV_CICLO, sep=";", encoding="utf-8-sig")
        df_t = pd.read_csv(CSV_TURNO, sep=";", encoding="utf-8-sig")
        df_i = pd.read_csv(CSV_INDICADORES, sep=";", encoding="utf-8-sig")

        escolas = df_c["CODESC"].nunique()
        turnos = len(df_t)
        matr_c = int(df_c["TOTAL_MATRICULAS"].sum())
        matr_t = int(df_t["TOTAL_MATRICULAS"].sum())

        print(f"  - Escolas únicas em Ciclo: {escolas} (Esperado: 201)")
        print(f"  - Registros de Turno: {turnos} (Esperado: 414)")
        print(f"  - Matrículas em Ciclo: {matr_c:,}".replace(",", ".") + " (Esperado: 83.968)")
        print(f"  - Matrículas em Turno: {matr_t:,}".replace(",", ".") + " (Esperado: 83.968)")

        assert escolas == 201, f"Total de escolas diferente do esperado ({escolas})"
        assert turnos == 414, f"Total de turnos diferente do esperado ({turnos})"
        assert matr_c == 83968, f"Total de matrículas em Ciclo incorreto ({matr_c})"
        assert matr_t == 83968, f"Total de matrículas em Turno incorreto ({matr_t})"
        assert matr_c == matr_t, "Divergência entre somas de Ciclo e Turno!"
        print("  [OK] Todos os números batem 100% com a base oficial e o Observatório!")
    except Exception as e:
        print(f"  [FALHA] Erro na validação dos dados: {e}")
        erros.append(f"Validação: {e}")

    # 4. Validar integridade do relatório TXT
    print("\n[4/4] Verificando conteúdo do relatório TXT...")
    try:
        with open(TXT_RELATORIO, "r", encoding="utf-8") as f:
            conteudo = f.read()
        assert "RELATÓRIO DE QUALIDADE" in conteudo
        assert "83.968" in conteudo or "83968" in conteudo
        print("  [OK] Relatório TXT formatado e completo.")
    except Exception as e:
        print(f"  [FALHA] Erro no relatório TXT: {e}")
        erros.append(f"Relatório TXT: {e}")

    print("\n" + "=" * 75)
    if not erros:
        print("   RESULTADO: TODOS OS TESTES FORAM APROVADOS! (100% OK)")
    else:
        print(f"   RESULTADO: {len(erros)} ERROS DETECTADOS.")
    print("=" * 75 + "\n")

    return 0 if not erros else 1

if __name__ == "__main__":
    sys.exit(testar())
