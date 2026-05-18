# ============================================================
# EXEMPLO DE DASHBOARD - Valcann | Projetos 5
# ============================================================
# Este arquivo serve como referência para os integrantes do grupo.
#
# COMO RODAR LOCALMENTE:
#   1. Copie o arquivo .env.example para .env e preencha as credenciais
#   2. pip install -r requirements.txt
#   3. streamlit run main.py
#
# COMO RODAR COM DOCKER:
#   docker compose up --build
# ============================================================

import requests
import os
import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# Streamlit permite definir título, ícone e layout da aba.
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Valcann",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Epics — Valcann")
st.caption("Dados consumidos diretamente do Jira via API REST v3")

# ------------------------------------------------------------
# FUNÇÃO DE BUSCA NO JIRA
# Separar a lógica de API em funções facilita testes e reuso.
# O decorator @st.cache_data evita chamadas repetidas enquanto
# o usuário navega — melhora muito a performance do dashboard.
# ------------------------------------------------------------
@st.cache_data(ttl=300)  # Cache de 5 minutos
def buscar_epics():
    """
    Busca todos os Epics não concluídos no Jira.
    Retorna uma lista de issues ou lança exceção em caso de erro.
    """
    url = "https://cesar-projetos4.atlassian.net/rest/api/3/search/jql"
    auth = requests.auth.HTTPBasicAuth(os.getenv("EMAIL"), os.getenv("API_TOKEN"))
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "jql": "updated >= -48h order by updated DESC",
        "fields": ["summary", "status", "assignee", "priority", "updated"],
        "maxResults": 50,
    })

    response = requests.post(url, data=payload, auth=auth, headers=headers)
    response.raise_for_status()

    dados = response.json()

    # O endpoint /jql pode retornar os dados em 'results' ou 'issues'
    issues = dados.get("results") or dados.get("issues", [])

    # Normaliza: em alguns casos os campos vêm dentro de 'issue'
    return [item.get("issue", item) for item in issues]


# ------------------------------------------------------------
# RENDERIZAÇÃO DO DASHBOARD
# Toda a lógica de exibição fica aqui, separada da busca.
# ------------------------------------------------------------
with st.spinner("Buscando dados no Jira..."):
    try:
        epics = buscar_epics()

        # --- Métricas resumidas no topo ---
        total = len(epics)
        st.metric("Total de Epics em andamento", total)
        st.divider()

        if not epics:
            st.info("Nenhum Epic encontrado.")
        else:
            # --- Tabela com os Epics ---
            # Aqui montamos uma lista de dicionários para exibir como tabela
            tabela = []
            for issue in epics:
                fields = issue.get("fields", {})
                assignee = fields.get("assignee") or {}
                priority = fields.get("priority") or {}
                tabela.append({
                    "Chave": issue.get("key", "—"),
                    "Resumo": fields.get("summary", "Sem nome"),
                    "Status": fields.get("status", {}).get("name", "—"),
                    "Responsável": assignee.get("displayName", "Não atribuído"),
                    "Prioridade": priority.get("name", "—"),
                    "Atualizado em": fields.get("updated", "—"),
                })

            # st.dataframe exibe uma tabela interativa com filtros e ordenação
            st.dataframe(tabela, use_container_width=True)

    except requests.exceptions.HTTPError as err:
        # Exibe o erro de forma amigável no dashboard, sem travar a app
        st.error(f"Erro ao buscar dados do Jira: {err}")
    except Exception as err:
        st.error(f"Erro inesperado: {err}")
