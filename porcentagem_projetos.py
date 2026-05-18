# ============================================================
# PORCENTAGEM DE PROGRESSO POR PROJETO — Valcann | Projetos 5
# ============================================================
# Busca TODAS as issues do Jira, agrupa por projeto e calcula:
#   - % concluída (Done)
#   - % em andamento (In Progress)
#   - % a fazer (To Do)
#   - Porcentagem geral de conclusão de todos os projetos juntos
#
# COMO RODAR:
#   python porcentagem_projetos.py
#   docker compose run --rm dashboard python porcentagem_projetos.py
# ============================================================

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# CONFIGURAÇÃO — conforme Seção 3 do manual
# ------------------------------------------------------------
DOMAIN  = "cesar-projetos4"
URL     = f"https://{DOMAIN}.atlassian.net/rest/api/3/search/jql"
AUTH    = requests.auth.HTTPBasicAuth(os.getenv("EMAIL"), os.getenv("API_TOKEN"))
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# ------------------------------------------------------------
# MAPEAMENTO DE STATUS CATEGORY → rótulo legível
# Jira usa três categorias fixas internamente.
# ------------------------------------------------------------
CATEGORIAS = {
    "To Do":       "A Fazer",
    "In Progress": "Em Andamento",
    "Done":        "Concluído",
}


# ------------------------------------------------------------
# BUSCA COM PAGINAÇÃO
# A API retorna no máximo 100 resultados por chamada.
# Paginamos até buscar todas as issues.
# ------------------------------------------------------------
def buscar_todas_issues():
    """
    Retorna lista completa de issues de todos os projetos.
    O endpoint /search/jql usa nextPageToken para paginação
    (não startAt como no endpoint legado /search).
    """
    todas           = []
    next_page_token = None

    while True:
        body = {
            "jql": 'statusCategory in ("To Do", "In Progress", "Done") ORDER BY project ASC',
            "fields": ["summary", "status", "project", "issuetype"],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token

        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS)
        response.raise_for_status()
        dados = response.json()

        issues = dados.get("results") or dados.get("issues", [])
        issues = [item.get("issue", item) for item in issues]
        todas.extend(issues)

        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break

    return todas


# ------------------------------------------------------------
# PROCESSAMENTO — agrupa por projeto e conta por categoria
# ------------------------------------------------------------
def processar(issues):
    """
    Retorna dicionário:
      { "Nome do Projeto": {"A Fazer": n, "Em Andamento": n, "Concluído": n} }
    """
    projetos = {}

    for issue in issues:
        fields  = issue.get("fields", {})
        projeto = fields.get("project", {}).get("name", "Desconhecido")
        cat_raw = fields.get("status", {}).get("statusCategory", {}).get("name", "To Do")
        cat     = CATEGORIAS.get(cat_raw, cat_raw)

        if projeto not in projetos:
            projetos[projeto] = {"A Fazer": 0, "Em Andamento": 0, "Concluído": 0}

        projetos[projeto][cat] = projetos[projeto].get(cat, 0) + 1

    return projetos


# ------------------------------------------------------------
# EXIBIÇÃO
# ------------------------------------------------------------
def barra(pct, largura=20):
    """Gera uma barra de progresso textual."""
    preenchido = int(largura * pct / 100)
    return "[" + "█" * preenchido + "░" * (largura - preenchido) + "]"


def exibir(projetos):
    total_geral    = 0
    concluido_geral = 0

    print("=" * 65)
    print("  PORCENTAGEM DE PROGRESSO — TODOS OS PROJETOS")
    print("=" * 65)

    for nome, contagens in sorted(projetos.items()):
        a_fazer     = contagens.get("A Fazer", 0)
        em_andamento = contagens.get("Em Andamento", 0)
        concluido   = contagens.get("Concluído", 0)
        total       = a_fazer + em_andamento + concluido

        total_geral     += total
        concluido_geral += concluido

        pct_done = (concluido / total * 100) if total else 0

        print(f"\n  Projeto : {nome}")
        print(f"  Total   : {total} issue(s)  |  "
              f"A Fazer: {a_fazer}  |  "
              f"Em Andamento: {em_andamento}  |  "
              f"Concluído: {concluido}")
        print(f"  Progresso: {barra(pct_done)} {pct_done:.1f}%")

    # --- Resumo geral ---
    pct_geral = (concluido_geral / total_geral * 100) if total_geral else 0

    print("\n" + "=" * 65)
    print(f"  RESUMO GERAL")
    print(f"  Total de issues : {total_geral}")
    print(f"  Concluídas      : {concluido_geral}")
    print(f"  Progresso geral : {barra(pct_geral)} {pct_geral:.1f}%")
    print("=" * 65)


# ------------------------------------------------------------
# PONTO DE ENTRADA
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        issues   = buscar_todas_issues()
        projetos = processar(issues)
        exibir(projetos)
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP ao conectar ao Jira: {err}")
        try:
            print(f"Detalhe: {err.response.json()}")
        except Exception:
            print(f"Detalhe: {err.response.text}")
    except requests.exceptions.ConnectionError:
        print("Erro de conexão. Verifique sua internet ou o domínio Jira.")
    except Exception as err:
        print(f"Erro inesperado: {err}")
