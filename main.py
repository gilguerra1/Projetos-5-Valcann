import requests
import os
import json
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Dashboard Valcann",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Epics — Valcann")
st.caption("Dados consumidos diretamente do Jira via API REST v3")


@st.cache_data(ttl=300)
def buscar_epics():
    url = "https://cesar-projetos4.atlassian.net/rest/api/3/search/jql"
    auth = requests.auth.HTTPBasicAuth(os.getenv("EMAIL"), os.getenv("API_TOKEN"))
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = json.dumps({
        "jql": "updated >= -48h order by updated DESC",
        "fields": ["summary", "status", "assignee", "priority", "updated"],
        "maxResults": 50,
    })
    response = requests.post(url, data=payload, auth=auth, headers=headers)
    response.raise_for_status()
    dados = response.json()
    issues = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues]


@st.cache_data(ttl=300)
def buscar_vencendo_em_breve():
    url = "https://cesar-projetos4.atlassian.net/rest/api/3/search/jql"
    auth = requests.auth.HTTPBasicAuth(os.getenv("EMAIL"), os.getenv("API_TOKEN"))
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    hoje = date.today()
    limite = hoje + timedelta(days=5)
    jql = (
        f'statusCategory != Done '
        f'AND duedate >= "{hoje.isoformat()}" '
        f'AND duedate <= "{limite.isoformat()}" '
        f'ORDER BY duedate ASC'
    )
    payload = json.dumps({
        "jql": jql,
        "fields": ["summary", "status", "assignee", "priority", "duedate", "issuetype"],
        "maxResults": 50,
    })
    response = requests.post(url, data=payload, auth=auth, headers=headers)
    response.raise_for_status()
    dados = response.json()
    issues = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues]


def dias_restantes(duedate_str: str) -> int:
    return (date.fromisoformat(duedate_str) - date.today()).days


def badge_urgencia(dias: int) -> str:
    if dias == 0:
        return "🔴 Vence hoje"
    elif dias == 1:
        return "🟠 Amanhã"
    elif dias <= 3:
        return "🟡 Em breve"
    else:
        return "🟢 5 dias"


st.header("📋 Epics em Andamento")

with st.spinner("Buscando Epics no Jira..."):
    try:
        epics = buscar_epics()
        st.metric("Total de Epics em andamento", len(epics))
        st.divider()
        if not epics:
            st.info("Nenhum Epic encontrado.")
        else:
            tabela = []
            for issue in epics:
                fields = issue.get("fields", {})
                assignee = fields.get("assignee") or {}
                priority = fields.get("priority") or {}
                tabela.append({
                    "Chave":       issue.get("key", "—"),
                    "Resumo":      fields.get("summary", "Sem nome"),
                    "Status":      fields.get("status", {}).get("name", "—"),
                    "Responsável": assignee.get("displayName", "Não atribuído"),
                    "Prioridade":  priority.get("name", "—"),
                })
            st.dataframe(tabela, use_container_width=True)
    except requests.exceptions.HTTPError as err:
        st.error(f"Erro ao buscar dados do Jira: {err}")
    except Exception as err:
        st.error(f"Erro inesperado: {err}")


st.header("⏰ Atividades com Prazo nos Próximos 5 Dias")
st.caption(f"Hoje: **{date.today().strftime('%d/%m/%Y')}** — até **{(date.today() + timedelta(days=5)).strftime('%d/%m/%Y')}**")

with st.spinner("Buscando tarefas com prazo próximo..."):
    try:
        urgentes = buscar_vencendo_em_breve()
        if not urgentes:
            st.success("✅ Nenhuma tarefa vencendo nos próximos 5 dias!")
        else:
            dias_map = [dias_restantes(i["fields"]["duedate"]) for i in urgentes if i.get("fields", {}).get("duedate")]
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de tarefas urgentes", len(urgentes))
            col2.metric("Vencem hoje ou amanhã",     sum(1 for d in dias_map if d <= 1))
            col3.metric("Vencem em 2–5 dias",        sum(1 for d in dias_map if 2 <= d <= 5))
            st.divider()
            for issue in urgentes:
                fields     = issue.get("fields", {})
                duedate    = fields.get("duedate")
                summary    = fields.get("summary", "Sem nome")
                status     = fields.get("status", {}).get("name", "—")
                assignee   = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
                priority   = (fields.get("priority") or {}).get("name", "—")
                issue_type = (fields.get("issuetype") or {}).get("name", "—")
                key        = issue.get("key", "—")
                if not duedate:
                    continue
                dias = dias_restantes(duedate)
                with st.expander(f"{badge_urgencia(dias)}  |  {key} — {summary}", expanded=(dias == 0)):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"**📅 Prazo**\n\n{date.fromisoformat(duedate).strftime('%d/%m/%Y')}")
                    c2.markdown(f"**⏳ Dias restantes**\n\n{dias} dia(s)")
                    c3.markdown(f"**👤 Responsável**\n\n{assignee}")
                    c4.markdown(f"**🏷️ Tipo**\n\n{issue_type}")
                    st.markdown(f"**Status:** `{status}` &nbsp;&nbsp; **Prioridade:** `{priority}`")
                    st.markdown(f"[🔗 Abrir no Jira](https://cesar-projetos4.atlassian.net/browse/{key})")
    except requests.exceptions.HTTPError as err:
        st.error(f"Erro ao buscar tarefas urgentes: {err}")
    except Exception as err:
        st.error(f"Erro inesperado: {err}")