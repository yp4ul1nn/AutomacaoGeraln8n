import os
import shutil
import zipfile
from datetime import datetime

import pandas as pd
from curl_cffi import requests


# ============================================================
# CONFIGURAÇÕES
# ============================================================

URL_ZIP = "https://infosiga.detran.sp.gov.br/painel/download/file/dados_infosiga.zip"
CIDADE = "DIADEMA"

# Pasta onde este programa está salvo
PASTA_BASE = os.path.dirname(os.path.abspath(__file__))

# Arquivos temporários
ZIP_TEMP = os.path.join(PASTA_BASE, "dados_infosiga.zip")
PASTA_EXTRAIDA = os.path.join(PASTA_BASE, "dados_infosiga")

# Arquivos CSV finais
ANO = datetime.now().year
ARQUIVO_PESSOAS = os.path.join(
    PASTA_BASE, f"Infosiga_{CIDADE}_Pessoas_{ANO}.csv"
)
ARQUIVO_SINISTROS = os.path.join(
    PASTA_BASE, f"Infosiga_{CIDADE}_Sinistros_{ANO}.csv"
)


# ============================================================
# 1. BAIXAR O ZIP
# ============================================================

def baixar_arquivo():
    print("Baixando dados do Infosiga...")

    resposta = requests.get(
        URL_ZIP,
        impersonate="chrome",
        timeout=120
    )
    resposta.raise_for_status()

    with open(ZIP_TEMP, "wb") as arquivo:
        arquivo.write(resposta.content)

    print("Download concluído.")


# ============================================================
# 2. EXTRAIR O ZIP
# ============================================================

def extrair_arquivo():
    print("Extraindo arquivos...")

    if os.path.exists(PASTA_EXTRAIDA):
        shutil.rmtree(PASTA_EXTRAIDA)

    os.makedirs(PASTA_EXTRAIDA, exist_ok=True)

    with zipfile.ZipFile(ZIP_TEMP, "r") as zip_ref:
        zip_ref.extractall(PASTA_EXTRAIDA)

    print("Extração concluída.")


# ============================================================
# 3. LOCALIZAR OS ARQUIVOS DE DADOS
# ============================================================

def localizar_arquivos():
    arquivos = []

    for raiz, _, nomes in os.walk(PASTA_EXTRAIDA):
        for nome in nomes:
            caminho = os.path.join(raiz, nome)
            extensao = os.path.splitext(nome)[1].lower()

            if extensao in [".csv", ".xlsx", ".xls"]:
                arquivos.append(caminho)

    print("\nArquivos encontrados:")
    for arquivo in arquivos:
        print(" -", arquivo)

    return arquivos


# ============================================================
# 4. LER OS ARQUIVOS DE ORIGEM
# ============================================================

def ler_arquivo(caminho):
    extensao = os.path.splitext(caminho)[1].lower()

    try:
        if extensao == ".csv":
            # Tenta ler CSV separado por ponto e vírgula em UTF-8,
            # depois Latin-1 e, por último, tenta detectar vírgulas.
            try:
                return pd.read_csv(
                    caminho,
                    sep=";",
                    encoding="utf-8",
                    low_memory=False
                )
            except (UnicodeDecodeError, pd.errors.ParserError):
                try:
                    return pd.read_csv(
                        caminho,
                        sep=";",
                        encoding="latin1",
                        low_memory=False
                    )
                except (UnicodeDecodeError, pd.errors.ParserError):
                    return pd.read_csv(
                        caminho,
                        encoding="latin1",
                        low_memory=False
                    )

        if extensao in [".xlsx", ".xls"]:
            return pd.read_excel(caminho)

        return None

    except Exception as erro:
        print(f"Erro ao ler {caminho}: {erro}")
        return None


# ============================================================
# 5. IDENTIFICAR PESSOAS E SINISTROS
# ============================================================

def identificar_tipo_arquivo(caminho):
    nome = os.path.basename(caminho).lower()

    if "pessoa" in nome:
        return "pessoas"

    if "sinistro" in nome:
        return "sinistros"

    return None


# ============================================================
# 6. ENCONTRAR A COLUNA DE MUNICÍPIO E FILTRAR DIADEMA
# ============================================================

def encontrar_coluna_cidade(df):
    possibilidades = [
        "municipio",
        "município",
        "cidade",
        "municipio acidente",
        "município acidente",
        "cidade acidente",
    ]

    colunas = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for possibilidade in possibilidades:
        if possibilidade in colunas:
            return colunas[possibilidade]

    for coluna in df.columns:
        nome = str(coluna).strip().lower()
        if "municip" in nome or "cidade" in nome:
            return coluna

    return None


def filtrar_diadema(df):
    coluna_cidade = encontrar_coluna_cidade(df)

    if coluna_cidade is None:
        print("Não foi encontrada coluna de município/cidade.")
        print("Colunas encontradas:", list(df.columns))
        return pd.DataFrame(columns=df.columns)

    print(f"Coluna utilizada para cidade: {coluna_cidade}")

    filtro = (
        df[coluna_cidade]
        .astype(str)
        .str.strip()
        .str.upper()
        .eq(CIDADE.upper())
    )

    resultado = df.loc[filtro].copy()

    print(f"Registros encontrados em {CIDADE}: {len(resultado)}")
    return resultado


# ============================================================
# 7. SALVAR OS RESULTADOS EM CSV
# ============================================================

def salvar_csv(df, caminho, descricao):
    print(f"\nSalvando arquivo CSV de {descricao}...")

    # utf-8-sig ajuda a abrir caracteres acentuados corretamente
    # em programas como o Excel. O separador ; é comum no Brasil.
    df.to_csv(
        caminho,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    print(f"Arquivo criado: {caminho}")
    print(f"Registros salvos: {len(df)}")


# ============================================================
# 8. PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("       INFOSIGA - FILTRO DE DIADEMA")
    print("=" * 60)

    try:
        baixar_arquivo()
        extrair_arquivo()
        arquivos = localizar_arquivos()

        df_pessoas = pd.DataFrame()
        df_sinistros = pd.DataFrame()

        for arquivo in arquivos:
            tipo = identificar_tipo_arquivo(arquivo)

            if tipo is None:
                continue

            print(f"\nProcessando: {arquivo}")
            df = ler_arquivo(arquivo)

            if df is None:
                continue

            print(f"Total de registros na origem: {len(df)}")
            df_filtrado = filtrar_diadema(df)

            if tipo == "pessoas":
                if df_pessoas.empty:
                    df_pessoas = df_filtrado
                else:
                    df_pessoas = pd.concat(
                        [df_pessoas, df_filtrado],
                        ignore_index=True
                    )

            elif tipo == "sinistros":
                if df_sinistros.empty:
                    df_sinistros = df_filtrado
                else:
                    df_sinistros = pd.concat(
                        [df_sinistros, df_filtrado],
                        ignore_index=True
                    )

        salvar_csv(df_pessoas, ARQUIVO_PESSOAS, "Pessoas")
        salvar_csv(df_sinistros, ARQUIVO_SINISTROS, "Sinistros")

        print("\n" + "=" * 60)
        print("PROCESSO FINALIZADO")
        print("=" * 60)
        print(f"\nPessoas: {len(df_pessoas)} registros")
        print(f"Sinistros: {len(df_sinistros)} registros")
        print(f"\nCSV Pessoas: {ARQUIVO_PESSOAS}")
        print(f"CSV Sinistros: {ARQUIVO_SINISTROS}")

    except Exception as erro:
        print("\n" + "=" * 60)
        print("ERRO NA AUTOMAÇÃO")
        print("=" * 60)
        print(f"{type(erro).__name__}: {erro}")
        raise

    finally:
        # Remove o ZIP temporário. A pasta extraída é mantida
        # para facilitar a conferência dos arquivos de origem.
        try:
            if os.path.exists(ZIP_TEMP):
                os.remove(ZIP_TEMP)
        except OSError as erro:
            print(f"Aviso: não foi possível excluir o ZIP temporário: {erro}")


if __name__ == "__main__":
    main()
