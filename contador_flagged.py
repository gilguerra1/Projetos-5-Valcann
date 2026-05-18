# ============================================================
# CONTADOR DE TAREFAS FLAGGED — Valcann | Projetos 5
# ============================================================
# Busca todas as issues do Jira que possuem o campo Flagged
# (customfield_10021) preenchido com "Impediment" e exibe
# um contador total, além dos detalhes de cada tarefa.
#
# COMO RODAR:
#   python contador_flagged.py
#
# PRÉ-REQUISITO:
#   Arquivo .env na raiz com EMAIL e API_TOKEN preenchidos.
# ============================================================

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# CONFIGURAÇÃO — conforme Seção 3 do manual
# ------------------------------------------------------------
DOMAIN = "cesar-projetos4"
URL = f"https://{DOMAIN}.atlassian.net/rest/api/3/search/jql"
AUTH = requests.auth.HTTPBasicAuth(os.getenv("EMAIL"), os.getenv("API_TOKEN"))
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# ------------------------------------------------------------
# QUERY JQL
# "Flagged" = Impediment seleciona somente issues marcadas
# com a bandeira de impedimento no Jira.
# cf[10021] é o alias numérico de customfield_10021.
# ------------------------------------------------------------
PAYLOAD = json.dumps({
    "jql": 'cf[10021] = Impediment ORDER BY created DESC',
    "fields": [
        "summary",
        "status",
        "assignee",
        "priority",
        "issuetype",
        "project",
        "customfield_10021",   # campo Flagged / Impediment
    ],
    "maxResults": 100,
})


# ------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ------------------------------------------------------------
def buscar_flagged():
    """
    Faz a requisição ao Jira e retorna a lista de issues flagged.
    Lança requests.HTTPError em caso de resposta não-2xx.
    """
    response = requests.post(URL, data=PAYLOAD, auth=AUTH, headers=HEADERS)
    response.raise_for_status()

    dados = response.json()
    # O endpoint /jql pode devolver os itens em 'results' ou 'issues'
    issues = dados.get("results") or dados.get("issues", [])
    # Normaliza: alguns wrappers colocam os dados dentro de 'issue'
    return [item.get("issue", item) for item in issues]


def contar_e_exibir(issues):
    """
    Imprime o contador total e os detalhes de cada tarefa flagged.
    """
    total = len(issues)
    print("=" * 60)
    print(f"  CONTADOR DE TAREFAS FLAGGED")
    print(f"  Total de impedimentos encontrados: {total}")
    print("=" * 60)

    if total == 0:
        print("  Nenhuma tarefa flagged no momento.")
        return

    for i, issue in enumerate(issues, start=1):
        fields   = issue.get("fields", {})
        chave    = issue.get("key", "—")
        resumo   = fields.get("summary", "Sem título")
        status   = fields.get("status", {}).get("name", "—")
        projeto  = fields.get("project", {}).get("name", "—")
        tipo     = fields.get("issuetype", {}).get("name", "—")
        responsavel = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
        prioridade  = (fields.get("priority") or {}).get("name", "—")

        # customfield_10021 é uma lista de objetos; exibe o label do primeiro
        flag_raw   = fields.get("customfield_10021") or []
        flag_label = flag_raw[0].get("value", "Impediment") if flag_raw else "Impediment"

        print(f"\n  [{i:02d}] {chave} — {resumo}")
        print(f"       Projeto    : {projeto}")
        print(f"       Tipo       : {tipo}")
        print(f"       Status     : {status}")
        print(f"       Responsável: {responsavel}")
        print(f"       Prioridade : {prioridade}")
        print(f"       Flag       : {flag_label}")

    print("\n" + "=" * 60)
    print(f"  Resumo: {total} tarefa(s) com impedimento ativo.")
    print("=" * 60)


# ------------------------------------------------------------
# PONTO DE ENTRADA
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        issues = buscar_flagged()
        contar_e_exibir(issues)
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP ao conectar ao Jira: {err}")
    except requests.exceptions.ConnectionError:
        print("Erro de conexão. Verifique sua internet ou o domínio Jira.")
    except Exception as err:
        print(f"Erro inesperado: {err}")
