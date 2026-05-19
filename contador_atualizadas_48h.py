# ============================================================
# CONTADOR DE TICKETS ATUALIZADOS — Valcann | Projetos 5
# ============================================================
# Busca todas as issues do Jira atualizadas nas últimas 48 horas
# e exibe um contador total, além dos detalhes de cada tarefa.
#
# COMO RODAR:
#   python contador_atualizadas_48h.py
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
# Seleciona apenas issues atualizadas nas últimas 48 horas.
# ------------------------------------------------------------
PAYLOAD = json.dumps({
    "jql": "updated >= -48h ORDER BY updated DESC",
    "fields": [
        "summary",
        "status",
        "assignee",
        "priority",
        "issuetype",
        "project",
        "updated",
    ],
    "maxResults": 100,
})


# ------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ------------------------------------------------------------

def buscar_atualizadas_48h():
    """Faz a requisição ao Jira e retorna a lista de issues atualizadas."""
    response = requests.post(URL, data=PAYLOAD, auth=AUTH, headers=HEADERS)
    response.raise_for_status()

    dados = response.json()
    issues = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues]


def contar_e_exibir(issues):
    """Imprime o contador total e os detalhes de cada issue atualizada."""
    total = len(issues)
    print("=" * 60)
    print("  CONTADOR DE TICKETS ATUALIZADOS NAS ÚLTIMAS 48 HORAS")
    print(f"  Total de issues encontradas: {total}")
    print("=" * 60)

    if total == 0:
        print("  Nenhuma issue atualizada nas últimas 48 horas.")
        return

    for i, issue in enumerate(issues, start=1):
        fields = issue.get("fields", {})
        chave = issue.get("key", "—")
        resumo = fields.get("summary", "Sem título")
        status = fields.get("status", {}).get("name", "—")
        projeto = fields.get("project", {}).get("name", "—")
        tipo = fields.get("issuetype", {}).get("name", "—")
        responsavel = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
        prioridade = (fields.get("priority") or {}).get("name", "—")
        atualizado = fields.get("updated", "—")

        print(f"\n  [{i:02d}] {chave} — {resumo}")
        print(f"       Projeto    : {projeto}")
        print(f"       Tipo       : {tipo}")
        print(f"       Status     : {status}")
        print(f"       Responsável: {responsavel}")
        print(f"       Prioridade : {prioridade}")
        print(f"       Atualizado : {atualizado}")

    print("\n" + "=" * 60)
    print(f"  Resumo: {total} issue(s) atualizada(s) nas últimas 48 horas.")
    print("=" * 60)


# ------------------------------------------------------------
# PONTO DE ENTRADA
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        issues = buscar_atualizadas_48h()
        contar_e_exibir(issues)
    except requests.exceptions.HTTPError as err:
        print(f"Erro HTTP ao conectar ao Jira: {err}")
    except requests.exceptions.ConnectionError:
        print("Erro de conexão. Verifique sua internet ou o domínio Jira.")
    except Exception as err:
        print(f"Erro inesperado: {err}")
