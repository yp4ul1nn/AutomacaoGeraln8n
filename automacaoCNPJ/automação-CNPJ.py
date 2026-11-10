import csv
import io
import json
import os
import re
import time
import zipfile
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURAÇÕES
# ============================================================

TOKEN = os.getenv("RECEITA_FEDERAL_WEBDAV_TOKEN", "YggdBLfdninEJX9").strip()

WEBDAV = "https://arquivos.receitafederal.gov.br/public.php/webdav/"
CODIGO_DIADEMA = "6377"

# Usa a pasta onde este main.py está localizado.
PASTA = Path(__file__).resolve().parent
DOWNLOADS = PASTA / "downloads"
CSV_FINAL = PASTA / "CNPJ_Diadema.csv"
MANIFESTO = DOWNLOADS / "manifesto_downloads.json"

LOTE_CSV = 50000
TENTATIVAS = 4
ESPERA_INICIAL = 3

COLUNAS = [
    "CNPJ Completo",
    "IDENTIFICADOR MATRIZ/FILIAL",
    "NOME FANTASIA",
    "SITUAÇÃO CADASTRAL",
    "DATA SITUAÇÃO CADASTRAL",
    "ANO SITUAÇÃO CADASTRAL",
    "MOTIVO SITUAÇÃO CADASTRAL",
    "NOME DA CIDADE NO EXTERIOR",
    "PAIS",
    "DATA DE INÍCIO ATIVIDADE",
    "ANO INÍCIO ATIVIDADE",
    "CNAE FISCAL PRINCIPAL",
    "CNAE FISCAL SECUNDÁRIA",
    "TIPO DE LOGRADOURO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "UF",
    "MUNICÍPIO",
    "DDD 1",
    "TELEFONE 1",
    "DDD 2",
    "TELEFONE 2",
    "DDD DO FAX",
    "FAX",
    "CORREIO ELETRÔNICO",
    "SITUACAO ESPECIAL",
    "DATA SITUACAO ESPECIAL",
    "RAZAO SOCIAL",
    "NATUREZA JURIDICA",
    "QUALIFICACAO RESPONSAVEL",
    "CAPITAL SOCIAL",
    "PORTE EMPRESA",
    "ENTE FEDERADO",
    "DESCRIÇÃO CNAE PRINCIPAL",
    "DESCRIÇÃO NATUREZA JURÍDICA",
]


# ============================================================
# PASTAS E CONEXÃO HTTP
# ============================================================

def criar_pastas():
    PASTA.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)


def criar_sessao():
    sessao = requests.Session()
    sessao.auth = (TOKEN, "")
    sessao.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Connection": "keep-alive",
    })

    politica_retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset([
            "GET", "HEAD", "OPTIONS", "PROPFIND"
        ]),
        respect_retry_after_header=True,
    )

    adaptador = HTTPAdapter(
        max_retries=politica_retry,
        pool_connections=10,
        pool_maxsize=10,
    )
    sessao.mount("https://", adaptador)
    sessao.mount("http://", adaptador)
    return sessao


def executar_com_retentativas(funcao, descricao):
    ultimo_erro = None

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            return funcao()
        except (requests.RequestException, OSError) as erro:
            ultimo_erro = erro

            if tentativa == TENTATIVAS:
                break

            espera = ESPERA_INICIAL * (2 ** (tentativa - 1))
            espera += random.uniform(0, 1)

            print(
                f"\nFalha em {descricao}: {erro}\n"
                f"Tentativa {tentativa}/{TENTATIVAS}. "
                f"Nova tentativa em {espera:.1f}s..."
            )
            time.sleep(espera)

    raise RuntimeError(
        f"Falha após {TENTATIVAS} tentativas: {descricao}"
    ) from ultimo_erro


# ============================================================
# WEBDAV E METADADOS REMOTOS
# ============================================================

def listar_pasta(sessao, caminho=""):
    url = WEBDAV + quote(caminho.strip("/"), safe="/")
    if not url.endswith("/"):
        url += "/"

    corpo = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<d:propfind xmlns:d="DAV:">'
        '<d:prop><d:resourcetype/>'
        '<d:getcontentlength/><d:getlastmodified/>'
        '<d:getetag/></d:prop>'
        '</d:propfind>'
    )

    def requisicao():
        resposta = sessao.request(
            "PROPFIND",
            url,
            headers={"Depth": "1"},
            data=corpo,
            timeout=(30, 120),
        )
        if resposta.status_code not in (200, 207):
            raise RuntimeError(
                f"Falha ao listar {url}: HTTP {resposta.status_code}"
            )
        return resposta

    resposta = executar_com_retentativas(
        requisicao, f"listagem WebDAV: {caminho or 'raiz'}"
    )

    raiz = ET.fromstring(resposta.content)
    ns = {"d": "DAV:"}
    itens = []

    for item in raiz.findall("d:response", ns):
        href = item.findtext("d:href", default="", namespaces=ns)
        nome = requests.utils.unquote(href.rstrip("/").split("/")[-1])

        if not nome:
            continue

        prop = item.find("d:propstat/d:prop", ns)
        if prop is None:
            continue

        tipo = prop.find("d:resourcetype/d:collection", ns)

        itens.append({
            "nome": nome,
            "pasta": tipo is not None,
            "tamanho": prop.findtext(
                "d:getcontentlength", default="", namespaces=ns
            ),
            "atualizado": prop.findtext(
                "d:getlastmodified", default="", namespaces=ns
            ),
            "etag": prop.findtext(
                "d:getetag", default="", namespaces=ns
            ),
        })

    return itens


def encontrar_mes(sessao):
    itens = listar_pasta(sessao)

    meses = [
        item["nome"]
        for item in itens
        if item["pasta"]
        and re.fullmatch(r"\d{4}-\d{2}", item["nome"])
    ]

    if not meses:
        raise RuntimeError(
            "Não encontrei pastas mensais no formato AAAA-MM."
        )

    return sorted(meses)[-1]


def carregar_manifesto():
    if not MANIFESTO.exists():
        return {}

    try:
        with open(MANIFESTO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError):
        print("Aviso: manifesto inválido; será reconstruído.")
        return {}


def salvar_manifesto(manifesto):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    temporario = MANIFESTO.with_suffix(".tmp")

    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(manifesto, arquivo, ensure_ascii=False, indent=2)

    temporario.replace(MANIFESTO)


def assinatura_remota(item):
    if not item:
        return None

    assinatura = {
        "tamanho": str(item.get("tamanho", "") or ""),
        "atualizado": str(item.get("atualizado", "") or ""),
        "etag": str(item.get("etag", "") or ""),
    }

    return assinatura if any(assinatura.values()) else None


def zip_valido(caminho):
    if not caminho.exists():
        return False

    try:
        if not zipfile.is_zipfile(caminho):
            return False

        with zipfile.ZipFile(caminho) as arquivo:
            return arquivo.testzip() is None and bool(arquivo.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


# ============================================================
# DOWNLOAD COM RETENTATIVAS E SUBSTITUIÇÃO SEGURA
# ============================================================

def baixar(sessao, mes, nome, item_remoto=None):
    destino = DOWNLOADS / mes / nome
    destino.parent.mkdir(parents=True, exist_ok=True)

    manifesto = carregar_manifesto()
    chave = f"{mes}/{nome}"
    assinatura_atual = assinatura_remota(item_remoto)
    registro = manifesto.get(chave, {})
    assinatura_anterior = registro.get("assinatura_remota")

    local_valido = zip_valido(destino)

    if (
        local_valido
        and assinatura_atual is not None
        and assinatura_atual == assinatura_anterior
    ):
        print(f"Sem atualização: {nome}")
        return destino

    if local_valido and assinatura_atual is None:
        print(
            f"Metadados remotos indisponíveis para {nome}; "
            "reutilizando ZIP local válido."
        )
        return destino

    url = WEBDAV + quote(f"{mes}/{nome}", safe="/")
    temporario = destino.with_name(destino.name + ".part")

    print(f"\nBaixando {nome}...")

    for tentativa in range(1, TENTATIVAS + 1):
        temporario.unlink(missing_ok=True)

        try:
            with sessao.get(
                url, stream=True, timeout=(45, 300)
            ) as resposta:
                resposta.raise_for_status()
                total = int(resposta.headers.get("content-length", 0))
                recebido = 0
                ultimo_progresso = -1

                with open(temporario, "wb") as arquivo:
                    for bloco in resposta.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if not bloco:
                            continue

                        arquivo.write(bloco)
                        recebido += len(bloco)

                        if total:
                            progresso = int(recebido * 100 / total)
                            if progresso != ultimo_progresso:
                                print(
                                    f"\r{nome}: {progresso}% "
                                    f"({recebido / 1024**2:.0f} MB)",
                                    end="",
                                    flush=True,
                                )
                                ultimo_progresso = progresso

            print()

            if not zip_valido(temporario):
                raise RuntimeError(
                    f"Arquivo ZIP inválido ou incompleto: {nome}"
                )

            # Só substitui o arquivo antigo depois de validar o novo.
            temporario.replace(destino)

            manifesto[chave] = {
                "assinatura_remota": assinatura_atual,
                "baixado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            salvar_manifesto(manifesto)

            print(f"Download concluído: {nome}")
            return destino

        except Exception as erro:
            temporario.unlink(missing_ok=True)

            if tentativa == TENTATIVAS:
                raise RuntimeError(
                    f"Não foi possível baixar {nome} "
                    f"após {TENTATIVAS} tentativas."
                ) from erro

            espera = ESPERA_INICIAL * (2 ** (tentativa - 1))
            espera += random.uniform(0, 1)
            print(
                f"\nErro ao baixar {nome}: {erro}\n"
                f"Tentativa {tentativa}/{TENTATIVAS}. "
                f"Aguardando {espera:.1f}s..."
            )
            time.sleep(espera)

    raise RuntimeError(f"Falha inesperada no download de {nome}.")


# ============================================================
# LEITURA DOS ARQUIVOS ZIP EM LOTES
# ============================================================

def ler_zip_em_lotes(caminho, tamanho=LOTE_CSV):
    with zipfile.ZipFile(caminho) as arquivo_zip:
        nomes = [
            nome for nome in arquivo_zip.namelist()
            if not nome.endswith("/")
        ]

        if not nomes:
            raise RuntimeError(f"ZIP vazio: {caminho}")

        with arquivo_zip.open(nomes[0]) as arquivo:
            texto = io.TextIOWrapper(
                arquivo, encoding="latin1", newline=""
            )
            leitor = csv.reader(texto, delimiter=";")

            try:
                while True:
                    lote = []

                    try:
                        for _ in range(tamanho):
                            lote.append(next(leitor))
                    except StopIteration:
                        pass

                    if not lote:
                        break

                    yield lote
            finally:
                texto.close()


def carregar_cnaes(caminho):
    mapa = {}

    for lote in ler_zip_em_lotes(caminho, 20000):
        for linha in lote:
            if len(linha) >= 2:
                codigo = linha[0].strip().zfill(7)
                mapa[codigo] = linha[1].strip()

    print(f"CNAEs encontrados: {len(mapa):,}")
    return mapa


def carregar_naturezas(caminho):
    """Carrega o código e a descrição da natureza jurídica do Naturezas.zip."""
    mapa = {}

    for lote in ler_zip_em_lotes(caminho, 20000):
        for linha in lote:
            if len(linha) >= 2:
                codigo = linha[0].strip().zfill(4)
                descricao = linha[1].strip()
                if codigo:
                    mapa[codigo] = descricao

    print(f"Naturezas jurídicas encontradas: {len(mapa):,}")
    return mapa


# ============================================================
# FILTRAGEM E CRUZAMENTO DOS DADOS
# ============================================================

def filtrar_estabelecimentos(arquivos):
    selecionados = {}
    total = 0

    for arquivo in arquivos:
        print(f"\nAnalisando {arquivo.name}...")

        for lote in ler_zip_em_lotes(arquivo):
            total += len(lote)

            for linha in lote:
                if len(linha) < 30:
                    continue

                if linha[20].strip().zfill(4) != CODIGO_DIADEMA:
                    continue

                base = linha[0].strip().zfill(8)
                ordem = linha[1].strip().zfill(4)
                digito = linha[2].strip().zfill(2)
                cnpj = base + ordem + digito

                selecionados[cnpj] = linha

        print(
            "Estabelecimentos de Diadema encontrados: "
            f"{len(selecionados):,}"
        )

    print(f"Registros examinados: {total:,}")
    return selecionados


def carregar_empresas(arquivos, bases_necessarias):
    empresas = {}

    for arquivo in arquivos:
        print(f"\nCruzando {arquivo.name}...")

        for lote in ler_zip_em_lotes(arquivo):
            for linha in lote:
                if len(linha) < 7:
                    continue

                base = linha[0].strip().zfill(8)

                if base in bases_necessarias:
                    empresas[base] = linha

    print(f"Empresas encontradas: {len(empresas):,}")
    return empresas


def extrair_ano(data):
    """Retorna os quatro primeiros dígitos da data AAAAMMDD, se válidos."""
    valor = str(data or "").strip()
    if len(valor) >= 4 and valor[:4].isdigit():
        ano = valor[:4]
        # O cadastro pode usar "0" ou zeros para datas inexistentes.
        if ano != "0000":
            return ano
    return ""


def montar_registro(cnpj, estab, empresa, cnaes, naturezas):
    cnae_principal = estab[11].strip().zfill(7)

    if empresa is None:
        empresa = [""] * 7
    else:
        empresa = empresa + [""] * max(0, 7 - len(empresa))

    return [
        cnpj,
        estab[3],
        estab[4],
        estab[5],
        estab[6],
        extrair_ano(estab[6]),
        estab[7],
        estab[8],
        estab[9],
        estab[10],
        extrair_ano(estab[10]),
        cnae_principal,
        estab[12],
        estab[13],
        estab[14],
        estab[15],
        estab[16],
        estab[17],
        estab[18],
        estab[19],
        "Diadema",
        estab[21],
        estab[22],
        estab[23],
        estab[24],
        estab[25],
        estab[26],
        estab[27],
        estab[28],
        estab[29],
        empresa[1],
        empresa[2],
        empresa[3],
        empresa[4],
        empresa[5],
        empresa[6],
        cnaes.get(cnae_principal, ""),
        naturezas.get(empresa[2].strip().zfill(4), "") if empresa[2].strip() else "",
    ]


def gerar_csv(estabelecimentos, empresas, cnaes, naturezas):
    temporario = CSV_FINAL.with_suffix(".tmp")

    print("\nGerando tabela consolidada...")

    try:
        with open(
            temporario, "w", encoding="utf-8-sig", newline=""
        ) as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(COLUNAS)

            for cnpj, estab in estabelecimentos.items():
                base = estab[0].strip().zfill(8)
                escritor.writerow(
                    montar_registro(
                        cnpj, estab, empresas.get(base), cnaes, naturezas
                    )
                )

        # O CSV anterior permanece até a geração do novo terminar.
        temporario.replace(CSV_FINAL)
    finally:
        temporario.unlink(missing_ok=True)

    print(f"CSV gerado: {CSV_FINAL}")
    print(f"Registros exportados: {len(estabelecimentos):,}")



# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    inicio = time.time()
    criar_pastas()

    if not TOKEN:
        raise RuntimeError(
            "Token WebDAV não configurado. No PowerShell, execute:\n"
            '$env:RECEITA_FEDERAL_WEBDAV_TOKEN = "SEU_TOKEN_VALIDO"'
        )

    sessao = criar_sessao()

    print("Procurando a pasta mensal mais recente...")
    mes = encontrar_mes(sessao)
    print(f"Mês selecionado: {mes}")

    itens = listar_pasta(sessao, mes)
    arquivos_remotos = {
        item["nome"]: item
        for item in itens
        if not item["pasta"]
    }

    nomes = set(arquivos_remotos)

    nomes_empresas = [
        f"Empresas{i}.zip"
        for i in range(10)
        if f"Empresas{i}.zip" in nomes
    ]
    nomes_estabelecimentos = [
        f"Estabelecimentos{i}.zip"
        for i in range(10)
        if f"Estabelecimentos{i}.zip" in nomes
    ]

    if len(nomes_empresas) != 10:
        raise RuntimeError(
            f"Esperava 10 arquivos de empresas; encontrei "
            f"{len(nomes_empresas)}. A geração do CSV será interrompida."
        )

    if len(nomes_estabelecimentos) != 10:
        raise RuntimeError(
            f"Esperava 10 arquivos de estabelecimentos; encontrei "
            f"{len(nomes_estabelecimentos)}. A geração do CSV será interrompida."
        )

    if "Cnaes.zip" not in nomes:
        raise RuntimeError(
            "Cnaes.zip não foi encontrado. "
            "A geração do CSV será interrompida."
        )

    if "Naturezas.zip" not in nomes:
        raise RuntimeError(
            "Naturezas.zip não foi encontrado. "
            "A geração do CSV será interrompida."
        )

    empresas = [
        baixar(
            sessao, mes, nome, arquivos_remotos.get(nome)
        )
        for nome in nomes_empresas
    ]

    estabelecimentos = [
        baixar(
            sessao, mes, nome, arquivos_remotos.get(nome)
        )
        for nome in nomes_estabelecimentos
    ]

    arquivo_cnae = baixar(
        sessao, mes, "Cnaes.zip",
        arquivos_remotos.get("Cnaes.zip"),
    )

    arquivo_naturezas = baixar(
        sessao, mes, "Naturezas.zip",
        arquivos_remotos.get("Naturezas.zip"),
    )

    cnaes = carregar_cnaes(arquivo_cnae)
    naturezas = carregar_naturezas(arquivo_naturezas)
    registros = filtrar_estabelecimentos(estabelecimentos)

    if not registros:
        raise RuntimeError(
            "Nenhum estabelecimento foi encontrado para Diadema. "
            "A geração do CSV será interrompida."
        )

    bases = {
        linha[0].strip().zfill(8)
        for linha in registros.values()
    }

    dados_empresas = carregar_empresas(empresas, bases)

    gerar_csv(registros, dados_empresas, cnaes, naturezas)

    duracao = time.time() - inicio
    print(f"\nAutomação concluída em {duracao / 60:.1f} minutos.")


if __name__ == "__main__":
    import traceback

    try:
        main()
    except Exception as erro:
        print("\n" + "=" * 60)
        print("ERRO NA AUTOMAÇÃO")
        print("=" * 60)
        print(f"{type(erro).__name__}: {erro}")
        traceback.print_exc()
        print("=" * 60)
