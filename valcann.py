# ============================================================
# VALCANN — Ferramentas Jira | Projetos 5
# ============================================================
# Arquivo unificado com todas as funcionalidades:
#   1. jira_api()              — testa conexão e lista Epics
#   2. contador_atualizadas_48h() — tickets atualizados (48h)
#   3. contador_flagged()      — tarefas com impedimento
#   4. porcentagem_projetos()  — % de progresso por projeto
#   5. dashboard()             — dashboard Streamlit
#
# USO (CLI):
#   python valcann.py [jira_api|48h|flagged|progresso]
#
# USO (Dashboard):
#   streamlit run valcann.py
#
# PRÉ-REQUISITO:
#   Arquivo .env na raiz com EMAIL e API_TOKEN preenchidos.
# ============================================================

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# CONFIGURAÇÃO COMPARTILHADA
# ------------------------------------------------------------
DOMAIN  = "cesar-projetos4"
URL     = f"https://{DOMAIN}.atlassian.net/rest/api/3/search/jql"
AUTH    = requests.auth.HTTPBasicAuth(os.getenv("EMAIL"), os.getenv("API_TOKEN"))
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# Mapeamento de categoria de status → rótulo legível
# Usa o campo 'key' (sempre em inglês/padronizado), não o 'name' (localizado)
CATEGORIAS = {
    "todo":          "A Fazer",
    "indeterminate": "Em Andamento",
    "done":          "Concluído",
    "undefined":     "A Fazer",
}


# ── 1. JIRA API ───────────────────────────────────────────────
def jira_api():
    """Testa a conexão com o Jira e lista Epics em aberto."""
    payload = json.dumps({
        "jql": "issuetype = Epic AND statusCategory != Done",
        "fields": ["summary", "status", "assignee", "priority"],
        "maxResults": 50,
    })
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS)
    response.raise_for_status()
    dados  = response.json()
    issues = dados.get("results", []) or dados.get("issues", [])
    print(f"Sucesso! Projetos encontrados: {len(issues)}")
    for item in issues:
        fields = item.get("fields", {})
        print(
            f"Projeto: {fields.get('summary')} | "
            f"Status: {fields.get('status', {}).get('name', '—')}"
        )


# ── 2. CONTADOR DE TICKETS ATUALIZADOS NAS ÚLTIMAS 48H ───────
def contador_atualizadas_48h():
    """Busca e exibe todas as issues atualizadas nas últimas 48 horas."""
    payload = json.dumps({
        "jql": "updated >= -48h ORDER BY updated DESC",
        "fields": ["summary", "status", "assignee", "priority",
                   "issuetype", "project", "updated"],
        "maxResults": 100,
    })
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS)
    response.raise_for_status()
    dados      = response.json()
    issues_raw = dados.get("results") or dados.get("issues", [])
    issues     = [item.get("issue", item) for item in issues_raw]

    total = len(issues)
    print("=" * 60)
    print("  CONTADOR DE TICKETS ATUALIZADOS NAS ÚLTIMAS 48 HORAS")
    print(f"  Total de issues encontradas: {total}")
    print("=" * 60)

    if total == 0:
        print("  Nenhuma issue atualizada nas últimas 48 horas.")
        return

    for i, issue in enumerate(issues, start=1):
        fields      = issue.get("fields", {})
        chave       = issue.get("key", "—")
        resumo      = fields.get("summary", "Sem título")
        status      = fields.get("status", {}).get("name", "—")
        projeto     = fields.get("project", {}).get("name", "—")
        tipo        = fields.get("issuetype", {}).get("name", "—")
        responsavel = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
        prioridade  = (fields.get("priority") or {}).get("name", "—")
        atualizado  = fields.get("updated", "—")

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


# ── 3. CONTADOR DE TAREFAS FLAGGED ───────────────────────────
def contador_flagged():
    """Busca e exibe todas as issues marcadas com impedimento (Flagged)."""
    payload = json.dumps({
        "jql": "cf[10021] = Impediment ORDER BY created DESC",
        "fields": ["summary", "status", "assignee", "priority",
                   "issuetype", "project", "customfield_10021"],
        "maxResults": 100,
    })
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS)
    response.raise_for_status()
    dados      = response.json()
    issues_raw = dados.get("results") or dados.get("issues", [])
    issues     = [item.get("issue", item) for item in issues_raw]

    total = len(issues)
    print("=" * 60)
    print("  CONTADOR DE TAREFAS FLAGGED")
    print(f"  Total de impedimentos encontrados: {total}")
    print("=" * 60)

    if total == 0:
        print("  Nenhuma tarefa flagged no momento.")
        return

    for i, issue in enumerate(issues, start=1):
        fields      = issue.get("fields", {})
        chave       = issue.get("key", "—")
        resumo      = fields.get("summary", "Sem título")
        status      = fields.get("status", {}).get("name", "—")
        projeto     = fields.get("project", {}).get("name", "—")
        tipo        = fields.get("issuetype", {}).get("name", "—")
        responsavel = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
        prioridade  = (fields.get("priority") or {}).get("name", "—")
        flag_raw    = fields.get("customfield_10021") or []
        flag_label  = flag_raw[0].get("value", "Impediment") if flag_raw else "Impediment"

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


# ── 4. PORCENTAGEM DE PROGRESSO POR PROJETO ──────────────────
def porcentagem_projetos():
    """Busca todas as issues e exibe o percentual de progresso por projeto."""

    def _buscar_todas():
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
            raw   = dados.get("results") or dados.get("issues", [])
            todas.extend([item.get("issue", item) for item in raw])
            next_page_token = dados.get("nextPageToken")
            if not next_page_token:
                break
        return todas

    def _barra(pct, largura=20):
        preenchido = int(largura * pct / 100)
        return "[" + "█" * preenchido + "░" * (largura - preenchido) + "]"

    issues   = _buscar_todas()
    projetos = {}

    for issue in issues:
        fields  = issue.get("fields", {})
        projeto = fields.get("project", {}).get("name", "Desconhecido")
        cat_raw = fields.get("status", {}).get("statusCategory", {}).get("key", "todo")
        cat     = CATEGORIAS.get(cat_raw, "A Fazer")
        if projeto not in projetos:
            projetos[projeto] = {"A Fazer": 0, "Em Andamento": 0, "Concluído": 0}
        projetos[projeto][cat] = projetos[projeto].get(cat, 0) + 1

    total_geral     = 0
    concluido_geral = 0

    print("=" * 65)
    print("  PORCENTAGEM DE PROGRESSO — TODOS OS PROJETOS")
    print("=" * 65)

    for nome, contagens in sorted(projetos.items()):
        a_fazer      = contagens.get("A Fazer", 0)
        em_andamento = contagens.get("Em Andamento", 0)
        concluido    = contagens.get("Concluído", 0)
        total        = a_fazer + em_andamento + concluido

        total_geral     += total
        concluido_geral += concluido

        pct_done = (concluido / total * 100) if total else 0
        print(f"\n  Projeto : {nome}")
        print(f"  Total   : {total} issue(s)  |  "
              f"A Fazer: {a_fazer}  |  "
              f"Em Andamento: {em_andamento}  |  "
              f"Concluído: {concluido}")
        print(f"  Progresso: {_barra(pct_done)} {pct_done:.1f}%")

    pct_geral = (concluido_geral / total_geral * 100) if total_geral else 0
    print("\n" + "=" * 65)
    print("  RESUMO GERAL")
    print(f"  Total de issues : {total_geral}")
    print(f"  Concluídas      : {concluido_geral}")
    print(f"  Progresso geral : {_barra(pct_geral)} {pct_geral:.1f}%")
    print("=" * 65)


# ── 5. DASHBOARD STREAMLIT ────────────────────────────────────

# --- Funções de busca com cache (usadas pelo dashboard) ---

@st.cache_data(ttl=300)
def _buscar_atualizadas_48h():
    payload = json.dumps({
        "jql": "updated >= -48h ORDER BY updated DESC",
        "fields": ["summary", "status", "assignee", "priority",
                   "issuetype", "project", "updated"],
        "maxResults": 100,
    })
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS, timeout=15)
    response.raise_for_status()
    dados      = response.json()
    issues_raw = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues_raw]


@st.cache_data(ttl=300)
def _buscar_flagged_dash():
    payload = json.dumps({
        "jql": "cf[10021] = Impediment ORDER BY created DESC",
        "fields": ["summary", "status", "assignee", "priority",
                   "issuetype", "project", "customfield_10021"],
        "maxResults": 100,
    })
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS, timeout=15)
    response.raise_for_status()
    dados      = response.json()
    issues_raw = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues_raw]


@st.cache_data(ttl=600)
def _buscar_progresso_dash():
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
        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        raw   = dados.get("results") or dados.get("issues", [])
        todas.extend([item.get("issue", item) for item in raw])
        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break
    return todas


@st.cache_data(ttl=300)
def _buscar_vencendo_em_breve():
    hoje   = date.today()
    limite = hoje + timedelta(days=5)
    jql    = (
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
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS, timeout=15)
    response.raise_for_status()
    dados  = response.json()
    issues = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues]


@st.cache_data(ttl=300)
def _buscar_em_atraso():
    """Busca issues com duedate vencido que ainda não foram concluídas."""
    hoje = date.today()
    jql  = (
        f'duedate < "{hoje.isoformat()}" '
        f'AND statusCategory != Done '
        f'ORDER BY duedate ASC'
    )
    payload = json.dumps({
        "jql": jql,
        "fields": ["summary", "status", "assignee", "priority",
                   "duedate", "issuetype", "project"],
        "maxResults": 200,
    })
    response = requests.post(URL, data=payload, auth=AUTH, headers=HEADERS, timeout=15)
    response.raise_for_status()
    dados  = response.json()
    issues = dados.get("results") or dados.get("issues", [])
    return [item.get("issue", item) for item in issues]


@st.cache_data(ttl=600)
def _buscar_gestores():
    """Retorna mapeamento project_key → {name, lead} via /rest/api/3/project."""
    url      = f"https://{DOMAIN}.atlassian.net/rest/api/3/project"
    response = requests.get(url, auth=AUTH, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return {
        p["key"]: {
            "name": p.get("name", p["key"]),
            "lead": (p.get("lead") or {}).get("displayName", "Sem gestor"),
        }
        for p in response.json()
    }


@st.cache_data(ttl=600)
def _buscar_por_lider():
    """Busca todas as issues para a aba Por Gestor (inclui project.key para lookup do lead)."""
    todas           = []
    next_page_token = None
    while True:
        body = {
            "jql": "issuetype = Epic ORDER BY project ASC",
            "fields": ["summary", "status", "assignee", "priority",
                       "issuetype", "project", "duedate", "updated"],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        raw   = dados.get("results") or dados.get("issues", [])
        todas.extend([item.get("issue", item) for item in raw])
        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break
    return todas


@st.cache_data(ttl=600)
def _buscar_tasks_epics():
    """Busca todas as tasks/stories filhas de Epics (classic: customfield_10014; next-gen: parent)."""
    todas           = []
    next_page_token = None
    while True:
        body = {
            "jql": "issuetype not in (Epic, Sub-task) ORDER BY project ASC",
            "fields": ["summary", "status", "assignee", "priority",
                       "issuetype", "project", "duedate", "updated",
                       "parent", "customfield_10014"],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        raw   = dados.get("results") or dados.get("issues", [])
        todas.extend([item.get("issue", item) for item in raw])
        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break
    return todas


@st.cache_data(ttl=600)
def _buscar_subtasks():
    """Busca todas as sub-tarefas com o campo parent para agrupar por história."""
    todas           = []
    next_page_token = None
    while True:
        body = {
            "jql": "issuetype in subTaskIssueTypes() ORDER BY parent ASC",
            "fields": ["summary", "status", "assignee", "priority",
                       "issuetype", "project", "duedate", "updated", "parent"],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        raw   = dados.get("results") or dados.get("issues", [])
        todas.extend([item.get("issue", item) for item in raw])
        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break
    return todas


@st.cache_data(ttl=300)
def _buscar_issues_projeto(project_key: str):
    """Busca todas as issues de um projeto específico com campos detalhados."""
    todas           = []
    next_page_token = None
    while True:
        body = {
            "jql": f'project = "{project_key}" ORDER BY updated DESC',
            "fields": [
                "summary", "status", "assignee", "priority",
                "issuetype", "duedate", "updated", "created",
                "customfield_10021",
            ],
            "maxResults": 100,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        raw   = dados.get("results") or dados.get("issues", [])
        todas.extend([item.get("issue", item) for item in raw])
        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break
    return todas


@st.cache_data(ttl=300)
def _buscar_historico_projeto(project_key: str):
    """Busca issues com changelog expandido para montar histórico de movimentações."""
    todas           = []
    next_page_token = None
    while True:
        body = {
            "jql": f'project = "{project_key}" ORDER BY updated DESC',
            "fields": ["summary", "status", "issuetype"],
            "expand": "changelog",
            "maxResults": 50,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        response = requests.post(URL, data=json.dumps(body), auth=AUTH, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        raw   = dados.get("results") or dados.get("issues", [])
        todas.extend([item.get("issue", item) for item in raw])
        next_page_token = dados.get("nextPageToken")
        if not next_page_token:
            break
    return todas


# --- Helpers visuais ---

def _dias_restantes(duedate_str: str) -> int:
    return (date.fromisoformat(duedate_str) - date.today()).days


def _cor_prioridade(p: str) -> str:
    return {
        "Highest": "#BF2600", "High": "#FF5630",
        "Medium":  "#FF991F", "Low":  "#00B8D9", "Lowest": "#6554C0",
    }.get(p, "#42526E")


def _cor_status(s: str) -> str:
    sl = s.lower()
    if any(x in sl for x in ("done", "conclu", "closed", "resolved")):
        return "#00875A"
    if any(x in sl for x in ("progress", "andamento", "review", "doing", "testing")):
        return "#0052CC"
    return "#42526E"


def _badge(texto: str, bg: str, fg: str = "white") -> str:
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:12px;font-size:0.75rem;font-weight:600;'
        f'margin-right:4px;display:inline-block">{texto}</span>'
    )


def _card_issue(issue: dict, show_flag: bool = False) -> str:
    fields      = issue.get("fields", {})
    chave       = issue.get("key", "—")
    resumo      = fields.get("summary", "Sem título")
    status_name = fields.get("status", {}).get("name", "—")
    projeto     = fields.get("project", {}).get("name", "—")
    tipo        = fields.get("issuetype", {}).get("name", "—")
    responsavel = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
    prioridade  = (fields.get("priority") or {}).get("name", "—")
    atualizado  = fields.get("updated", "")
    duedate     = fields.get("duedate", "")

    if atualizado:
        try:
            dt             = datetime.fromisoformat(atualizado.replace("Z", "+00:00"))
            atualizado_fmt = dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            atualizado_fmt = atualizado[:10]
    else:
        atualizado_fmt = "—"

    cor_p      = _cor_prioridade(prioridade)
    cor_s      = _cor_status(status_name)
    flag_badge = ""

    if show_flag:
        flag_raw   = fields.get("customfield_10021") or []
        flag_label = flag_raw[0].get("value", "Impediment") if flag_raw else "Impediment"
        flag_badge = _badge(f"⚑ {flag_label}", "#FFEBE6", "#BF2600")

    due_info = ""
    if duedate:
        dias    = _dias_restantes(duedate)
        cor_due = "#BF2600" if dias <= 0 else "#FF5630" if dias <= 1 else "#FF991F" if dias <= 3 else "#006644"
        due_info = (
            f'<span style="color:{cor_due};font-size:0.8rem">'
            f'📅 {date.fromisoformat(duedate).strftime("%d/%m/%Y")} ({dias}d)</span> &nbsp;'
        )

    return (
        f'<div class="issue-card" style="border-left-color:{cor_s}">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap">'
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
        f'<a href="https://cesar-projetos4.atlassian.net/browse/{chave}" target="_blank" '
        f'style="font-weight:700;color:#4C6EF5;text-decoration:none;font-size:0.88rem;'
        f'background:#EEF2FF;padding:2px 8px;border-radius:6px">{chave}</a>'
        f'{_badge(status_name, cor_s)}{_badge(prioridade, cor_p)}{flag_badge}'
        f'</div>'
        f'<span style="font-size:0.73rem;color:#ADB5BD;white-space:nowrap">🕒 {atualizado_fmt}</span>'
        f'</div>'
        f'<p style="margin:8px 0 6px;font-size:0.95rem;color:#1A1D2E;font-weight:600;line-height:1.4">{resumo}</p>'
        f'<div style="display:flex;flex-wrap:wrap;gap:14px;font-size:0.78rem;color:#8993A4">'
        f'<span style="display:flex;align-items:center;gap:4px"><span style="opacity:0.6">📁</span>{projeto}</span>'
        f'<span style="display:flex;align-items:center;gap:4px"><span style="opacity:0.6">🏷️</span>{tipo}</span>'
        f'<span style="display:flex;align-items:center;gap:4px"><span style="opacity:0.6">👤</span>{responsavel}</span>'
        f'{due_info}'
        f'</div>'
        f'</div>'
    )


def dashboard():
    """Dashboard Streamlit dinâmico — Valcann Jira."""
    st.set_page_config(page_title="Valcann · Jira", page_icon="🚀", layout="wide")

    # ── CSS global ──────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    html, body, [class*="css"], .stMarkdown, p, span, div { font-family: 'Inter', -apple-system, sans-serif !important; }

    [data-testid="stAppViewContainer"] > .main { background: #F0F2F8; }
    [data-testid="stStatusWidget"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .block-container { padding-top: 1.2rem !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D0F1A 0%, #141627 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown { color: rgba(255,255,255,0.75) !important; }
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #4C6EF5 0%, #3B5BDB 100%) !important;
        color: white !important; font-weight: 700; width: 100%;
        border-radius: 10px; border: none; padding: 0.65rem 1rem;
        box-shadow: 0 4px 16px rgba(76,110,245,0.4);
        transition: all 0.25s ease; letter-spacing: 0.02em;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(76,110,245,0.5) !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] * { color: #172B4D !important; }
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] * { color: #172B4D !important; }

    /* ── Tabs ── */
    div[data-testid="stTabs"] [role="tablist"] {
        background: white; border-radius: 14px; padding: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07); gap: 3px; border-bottom: none;
    }
    div[data-testid="stTabs"] [role="tab"] {
        font-weight: 600; border-radius: 10px; padding: 6px 18px;
        color: #6B778C; transition: all 0.2s; border: none;
    }
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #4C6EF5 0%, #3B5BDB 100%);
        color: white !important; box-shadow: 0 4px 14px rgba(76,110,245,0.35);
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: white; border-radius: 16px;
        padding: 1.4rem 1.6rem;
        box-shadow: 0 2px 14px rgba(0,0,0,0.06);
        position: relative; overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid rgba(0,0,0,0.04);
    }
    .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(0,0,0,0.1); }
    .kpi-val { font-size: 2.6rem; font-weight: 900; line-height: 1; margin-bottom: 6px; }
    .kpi-lbl { font-size: 0.72rem; color: #8993A4; font-weight: 700;
               text-transform: uppercase; letter-spacing: 0.08em; }
    .kpi-accent { position: absolute; width: 100px; height: 100px; border-radius: 50%;
                  filter: blur(40px); opacity: 0.12; bottom: -30px; right: -10px; }

    /* ── Issue Cards ── */
    .issue-card {
        background: white; border-radius: 12px; padding: 14px 18px;
        margin-bottom: 10px; border-left: 4px solid #DFE1E6;
        box-shadow: 0 1px 8px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s, transform 0.2s;
        border-top: 1px solid rgba(0,0,0,0.04);
    }
    .issue-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.1); transform: translateX(2px); }

    /* ── Progress Cards ── */
    .proj-card {
        background: white; border-radius: 14px; padding: 16px 20px;
        margin-bottom: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid rgba(0,0,0,0.04);
        transition: box-shadow 0.2s;
    }
    .proj-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.1); }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background: white; border-radius: 12px; padding: 1rem 1.2rem;
        box-shadow: 0 1px 8px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.04);
    }
    /* ── Expanders ── */
    .streamlit-expanderHeader { background: white !important; border-radius: 10px !important; }
    div[data-testid="stExpander"] { border: none !important; background: transparent; }

    /* ── Botão Atualizar (header) ── */
    [data-testid="stMainBlockContainer"] .stButton > button {
        background: white !important;
        color: #4C6EF5 !important;
        border: 1.5px solid #4C6EF5 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.45rem 1rem !important;
        transition: all 0.2s ease !important;
        white-space: nowrap;
    }
    [data-testid="stMainBlockContainer"] .stButton > button:hover {
        background: #EEF2FF !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(76,110,245,0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Sidebar ─────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div style="padding:1rem 0 0.5rem">'
            '<span style="font-size:1.6rem;font-weight:900;color:white;letter-spacing:-0.03em">Valcann</span>'
            '<span style="font-size:0.72rem;color:rgba(255,255,255,0.4);display:block;'
            'text-transform:uppercase;letter-spacing:0.12em;margin-top:2px">Jira Dashboard</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0.5rem 0 1rem">', unsafe_allow_html=True)

        st.markdown('<div style="margin-top:1.2rem"></div>', unsafe_allow_html=True)
        intervalos = {"5 min": 300, "10 min": 600, "15 min": 900, "30 min": 1800}
        intervalo_label = st.selectbox("Auto-refresh", list(intervalos.keys()), index=1)
        intervalo_seg   = intervalos[intervalo_label]

        st.markdown(
            f'<div style="margin-top:auto;padding:1rem 0 0.5rem;font-size:0.72rem;'
            f'color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.08em">'
            f'⏱ {datetime.now(tz=timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")}</div>',
            unsafe_allow_html=True,
        )

    # Auto-refresh via JavaScript
    st.markdown(
        f'<script>setTimeout(function(){{window.location.reload()}},{intervalo_seg*1000});</script>',
        unsafe_allow_html=True,
    )

    # ── Cabeçalho ───────────────────────────────────────────────
    _TZ_BRT = timezone(timedelta(hours=-3))
    agora = datetime.now(tz=_TZ_BRT).strftime("%d/%m/%Y  %H:%M")
    col_hd_title, col_hd_ts, col_hd_btn = st.columns([3, 1.4, 0.7])
    with col_hd_title:
        st.markdown(
            f'<div style="padding-bottom:0.8rem">'
            f'<h1 style="margin:0;font-size:1.6rem;font-weight:900;color:#0D0F1A;letter-spacing:-0.03em">'
            f'Visão Geral dos Projetos</h1>'
            f'<p style="margin:3px 0 0;font-size:0.85rem;color:#8993A4;font-weight:500">'
            f'Jira · {DOMAIN}.atlassian.net</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_hd_ts:
        st.markdown(
            f'<div style="background:white;border-radius:10px;padding:8px 14px;'
            f'box-shadow:0 1px 6px rgba(0,0,0,0.07);font-size:0.8rem;color:#6B778C;'
            f'font-weight:600;margin-top:4px">'
            f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
            f'background:#00B341;margin-right:6px;box-shadow:0 0 0 3px rgba(0,179,65,0.2)"></span>'
            f'Ao vivo · {agora}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_hd_btn:
        if st.button("⟳  Atualizar", use_container_width=True, key="btn_atualizar_header"):
            st.cache_data.clear()
            st.toast("Dados sincronizados com o Jira!", icon="✅")
            st.rerun()
    st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

    # ── Carrega todos os dados em paralelo ──────────────────────
    erros        = {}
    atualizadas  = []
    flagged      = []
    urgentes     = []
    em_atraso    = []
    todas_issues = []
    issues_lider = []
    gestores_map  = {}
    tasks_epics   = []
    subtasks      = []

    try:
        for nome, fn in [
                ("atividade",   _buscar_atualizadas_48h),
                ("flagged",     _buscar_flagged_dash),
                ("urgentes",    _buscar_vencendo_em_breve),
                ("em_atraso",   _buscar_em_atraso),
                ("progresso",   _buscar_progresso_dash),
                ("lider",       _buscar_por_lider),
                ("tasks_epics", _buscar_tasks_epics),
                ("subtasks",    _buscar_subtasks),
            ]:
                try:
                    resultado = fn()
                    if nome == "atividade":   atualizadas  = resultado
                    elif nome == "flagged":   flagged      = resultado
                    elif nome == "urgentes":  urgentes     = resultado
                    elif nome == "em_atraso": em_atraso    = resultado
                    elif nome == "lider":     issues_lider = resultado
                    elif nome == "tasks_epics": tasks_epics = resultado
                    elif nome == "subtasks":    subtasks    = resultado
                    else:                    todas_issues = resultado
                except Exception as e:
                    erros[nome] = str(e)
        # Busca gestores separadamente (retorna dict)
        try:
            gestores_map = _buscar_gestores()
        except Exception as e:
            erros["gestores"] = str(e)
    except Exception as e:
        st.error(f"Erro crítico ao carregar dados: {e}")
        st.exception(e)
        return

    if erros:
        for k, msg in erros.items():
            st.error(f"Erro ao buscar **{k}**: {msg}")

    # ── Calcula progresso ───────────────────────────────────────
    projetos_data   = {}
    for issue in todas_issues:
        fields  = issue.get("fields", {})
        proj    = fields.get("project", {}).get("name", "Desconhecido")
        cat_raw = fields.get("status", {}).get("statusCategory", {}).get("key", "todo")
        cat     = CATEGORIAS.get(cat_raw, "A Fazer")  # categorias desconhecidas → A Fazer
        if proj not in projetos_data:
            projetos_data[proj] = {"A Fazer": 0, "Em Andamento": 0, "Concluído": 0}
        projetos_data[proj][cat] += 1

    total_geral     = sum(sum(c.values()) for c in projetos_data.values())
    concluido_geral = sum(c.get("Concluído", 0) for c in projetos_data.values())
    pct_geral       = round((concluido_geral / total_geral * 100) if total_geral else 0, 1)
    total_epicos    = sum(
        1 for i in todas_issues
        if (i.get("fields", {}).get("issuetype") or {}).get("name", "") == "Epic"
    )
    total_tasks_prog = total_geral - total_epicos

    # ── Tabs ────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📊 Acompanhamento Geral",
        "👤 Por Responsável",
        "🔍 Detalhes do Projeto",
    ])

    # ─ Tab 1: Acompanhamento Geral ──────────────────────────────
    with tab1:

        # ── KPI Cards ───────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        kpi_items = [
            (c1, len(atualizadas), "Atualizadas (48h)",   "#4C6EF5", "#EEF2FF", "🔄"),
            (c2, len(flagged),     "Impedimentos Ativos", "#E03131", "#FFF5F5", "🚩"),
            (c3, len(urgentes),    "Vencem em 5 dias",    "#E67700", "#FFF9DB", "⏰"),
            (c4, f"{pct_geral}%",  "Progresso Geral",     "#2F9E44", "#EBFBEE", "📈"),
        ]
        for col, val, label, cor, bg, icon in kpi_items:
            with col:
                st.markdown(
                    f'<div class="kpi-card">'
                    f'<div class="kpi-accent" style="background:{cor}"></div>'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
                    f'<div>'
                    f'<div class="kpi-val" style="color:{cor}">{val}</div>'
                    f'<div class="kpi-lbl">{label}</div>'
                    f'</div>'
                    f'<div style="background:{bg};border-radius:12px;width:48px;height:48px;'
                    f'display:flex;align-items:center;justify-content:center;font-size:1.4rem">'
                    f'{icon}</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Sub-abas do Acompanhamento Geral ─────────────────────
        sub1, sub2, sub3, sub4, sub5 = st.tabs([
            "📈 Progresso por Projeto",
            "🚩 Impedimentos",
            "⏰ Prazos Próximos",
            "🔄 Atividade Recente (48h)",
            "⚠️ Em Atraso",
        ])

        # ── Sub-aba 1: Progresso por Projeto ─────────────────────
        with sub1:
            if not projetos_data:
                st.info("Sem dados de progresso disponíveis.")
            else:
                col_g1, col_g2, col_g3, col_g4 = st.columns(4)
                col_g1.metric("🗂️ Total de Épicos",  total_epicos)
                col_g2.metric("📋 Total de Tasks",   total_tasks_prog)
                col_g3.metric("✅ Concluídas",        concluido_geral)
                col_g4.metric("📈 Progresso Geral",  f"{pct_geral}%")
                st.markdown("---")

                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">'
                    f'<span style="min-width:180px;font-weight:700;color:#172B4D">🏁 Geral</span>'
                    f'<div style="flex:1;height:20px;background:#DFE1E6;border-radius:10px;overflow:hidden">'
                    f'<div style="width:{pct_geral}%;height:100%;background:linear-gradient(90deg,#00875A,#36B37E);border-radius:10px"></div>'
                    f'</div>'
                    f'<span style="min-width:52px;text-align:right;font-weight:800;color:#00875A">{pct_geral}%</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                proj_ordenados = sorted(
                    projetos_data.items(),
                    key=lambda x: -(x[1].get("Concluído", 0) / max(sum(x[1].values()), 1)),
                )
                barras = []
                for nome, cnts in proj_ordenados:
                    a_fazer      = cnts.get("A Fazer", 0)
                    em_andamento = cnts.get("Em Andamento", 0)
                    concluido    = cnts.get("Concluído", 0)
                    total        = a_fazer + em_andamento + concluido
                    pct          = round((concluido / total * 100) if total else 0, 1)
                    pct_af       = round((a_fazer      / total * 100) if total else 0, 1)
                    pct_em       = round((em_andamento / total * 100) if total else 0, 1)
                    pct_co       = round((concluido    / total * 100) if total else 0, 1)
                    cor_pct      = "#2F9E44" if pct >= 75 else "#E67700" if pct >= 40 else "#E03131"
                    barras.append(
                        f'<div class="proj-card">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                        f'<span style="font-weight:700;color:#1A1D2E;font-size:0.95rem">{nome}</span>'
                        f'<div style="display:flex;align-items:center;gap:16px">'
                        f'<span style="font-size:0.75rem;color:#ADB5BD">'
                        f'<span style="color:#E8EAED;font-weight:700">{a_fazer}</span> a fazer &nbsp;·&nbsp; '
                        f'<span style="color:#4C6EF5;font-weight:700">{em_andamento}</span> em andamento &nbsp;·&nbsp; '
                        f'<span style="color:#2F9E44;font-weight:700">{concluido}</span> concluído'
                        f'</span>'
                        f'<span style="font-size:0.9rem;font-weight:900;color:{cor_pct};'
                        f'background:{"#EBFBEE" if pct >= 75 else "#FFF9DB" if pct >= 40 else "#FFF5F5"};'
                        f'padding:2px 10px;border-radius:20px">{pct}%</span>'
                        f'</div></div>'
                        f'<div style="height:8px;border-radius:20px;overflow:hidden;background:#F0F2F8;display:flex">'
                        f'<div style="width:{pct_co}%;background:linear-gradient(90deg,#2F9E44,#40C057)" title="Concluído"></div>'
                        f'<div style="width:{pct_em}%;background:linear-gradient(90deg,#4C6EF5,#748FFC)" title="Em Andamento"></div>'
                        f'<div style="width:{pct_af}%;background:#E8EAED" title="A Fazer"></div>'
                        f'</div>'
                        f'</div>'
                    )
                st.markdown("".join(barras), unsafe_allow_html=True)
                st.markdown(
                    '<div style="display:flex;gap:20px;font-size:0.75rem;color:#ADB5BD;margin-top:8px;'
                    'font-weight:600;text-transform:uppercase;letter-spacing:0.06em">'
                    '<span><span style="color:#2F9E44">■</span> Concluído</span>'
                    '<span><span style="color:#4C6EF5">■</span> Em Andamento</span>'
                    '<span><span style="color:#E8EAED">■</span> A Fazer</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

        # ── Sub-aba 2: Impedimentos ───────────────────────────────
        with sub2:
            if not flagged:
                st.success("✅ Nenhum impedimento ativo no momento!")
            else:
                st.markdown(f"**{len(flagged)} tarefa(s)** com impedimento ativo")
                por_projeto = {}
                for issue in flagged:
                    proj = issue.get("fields", {}).get("project", {}).get("name", "—")
                    por_projeto.setdefault(proj, []).append(issue)
                grupos_html = []
                for proj_nome, issues_proj in sorted(por_projeto.items()):
                    qtd  = len(issues_proj)
                    suf  = 's' if qtd > 1 else ''
                    cards_html = "".join(_card_issue(i, show_flag=True) for i in issues_proj)
                    grupos_html.append(
                        f'<details open style="background:white;border-radius:14px;padding:14px 18px;'
                        f'margin-bottom:12px;box-shadow:0 2px 10px rgba(0,0,0,0.06);'
                        f'border:1px solid rgba(0,0,0,0.04)">'
                        f'<summary style="font-weight:700;color:#1A1D2E;cursor:pointer;font-size:0.95rem;'
                        f'list-style:none;padding:4px 0">'
                        f'{proj_nome} &nbsp;·&nbsp; <span style="color:#E03131;font-weight:800">{qtd}</span> impedimento{suf}'
                        f'</summary>'
                        f'<div style="margin-top:12px">{cards_html}</div>'
                        f'</details>'
                    )
                st.markdown("".join(grupos_html), unsafe_allow_html=True)

        # ── Sub-aba 3: Prazos Próximos ────────────────────────────
        with sub3:
            hoje   = date.today()
            limite = hoje + timedelta(days=5)
            st.caption(
                f"Hoje: **{hoje.strftime('%d/%m/%Y')}** — "
                f"até **{limite.strftime('%d/%m/%Y')}**"
            )
            if not urgentes:
                st.success("✅ Nenhuma tarefa vencendo nos próximos 5 dias!")
            else:
                dias_map = [
                    _dias_restantes(i["fields"]["duedate"])
                    for i in urgentes
                    if i.get("fields", {}).get("duedate")
                ]
                c1, c2, c3 = st.columns(3)
                c1.metric("Total urgentes",     len(urgentes))
                c2.metric("Vencem hoje/amanhã", sum(1 for d in dias_map if d <= 1))
                c3.metric("Vencem em 2–5 dias", sum(1 for d in dias_map if 2 <= d <= 5))
                st.markdown("---")
                urgentes_ord = sorted(
                    [(i, _dias_restantes(i["fields"]["duedate"]))
                     for i in urgentes if i.get("fields", {}).get("duedate")],
                    key=lambda x: x[1],
                )
                cards = []
                for issue, dias in urgentes_ord:
                    fields     = issue.get("fields", {})
                    duedate    = fields.get("duedate")
                    summary    = fields.get("summary", "Sem nome")
                    status     = fields.get("status", {}).get("name", "—")
                    assignee   = (fields.get("assignee") or {}).get("displayName", "Não atribuído")
                    priority   = (fields.get("priority") or {}).get("name", "—")
                    issue_type = (fields.get("issuetype") or {}).get("name", "—")
                    key        = issue.get("key", "—")
                    if dias <= 0:   cor_borda, emoji = "#BF2600", "🔴"
                    elif dias == 1: cor_borda, emoji = "#FF5630", "🟠"
                    elif dias <= 3: cor_borda, emoji = "#FF991F", "🟡"
                    else:           cor_borda, emoji = "#00875A", "🟢"
                    cor_p = _cor_prioridade(priority)
                    cor_s = _cor_status(status)
                    prazo_fmt = date.fromisoformat(duedate).strftime("%d/%m/%Y")
                    suffix    = "s" if dias != 1 else ""
                    cards.append(
                        f'<div style="background:white;border-radius:8px;padding:14px 18px;margin-bottom:12px;'
                        f'border-left:5px solid {cor_borda};box-shadow:0 2px 8px rgba(0,0,0,0.07)">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px">'
                        f'<div>{emoji} '
                        f'<a href="https://cesar-projetos4.atlassian.net/browse/{key}" target="_blank" '
                        f'style="font-weight:700;color:#0052CC;text-decoration:none">{key}</a>&nbsp;'
                        f'{_badge(status, cor_s)}{_badge(priority, cor_p)}'
                        f'</div>'
                        f'<span style="font-size:0.85rem;font-weight:700;color:{cor_borda}">'
                        f'📅 {prazo_fmt} &nbsp;({dias} dia{suffix})'
                        f'</span></div>'
                        f'<p style="margin:6px 0 4px;font-size:0.95rem;color:#172B4D;font-weight:500">{summary}</p>'
                        f'<div style="font-size:0.8rem;color:#6B778C;display:flex;flex-wrap:wrap;gap:14px">'
                        f'<span>🏷️ {issue_type}</span><span>👤 {assignee}</span>'
                        f'<a href="https://cesar-projetos4.atlassian.net/browse/{key}" target="_blank" '
                        f'style="color:#0052CC;font-weight:600;text-decoration:none">🔗 Abrir no Jira</a>'
                        f'</div></div>'
                    )
                st.markdown("".join(cards), unsafe_allow_html=True)

        # ── Sub-aba 4: Atividade Recente ──────────────────────────
        with sub4:
            st.markdown(f"**{len(atualizadas)} issues** atualizadas nas últimas 48 horas")
            if not atualizadas:
                st.info("Nenhuma issue atualizada nas últimas 48 horas.")
            else:
                projetos_48h = sorted({i.get("fields", {}).get("project", {}).get("name", "—") for i in atualizadas})
                priors_48h   = sorted({(i.get("fields", {}).get("priority") or {}).get("name", "—") for i in atualizadas})
                col_f1, col_f2 = st.columns(2)
                filtro_proj  = col_f1.multiselect("Filtrar por Projeto",    projetos_48h, placeholder="Todos")
                filtro_prior = col_f2.multiselect("Filtrar por Prioridade", priors_48h,   placeholder="Todas")
                issues_filtradas = [
                    i for i in atualizadas
                    if (not filtro_proj  or i.get("fields", {}).get("project", {}).get("name") in filtro_proj)
                    and (not filtro_prior or (i.get("fields", {}).get("priority") or {}).get("name") in filtro_prior)
                ]
                st.caption(f"Exibindo {len(issues_filtradas)} de {len(atualizadas)} issues")
                st.markdown(
                    "".join(_card_issue(i) for i in issues_filtradas),
                    unsafe_allow_html=True,
                )

        # ── Sub-aba 5: Em Atraso ──────────────────────────────────
        with sub5:
            if not em_atraso:
                st.success("✅ Nenhuma tarefa em atraso no momento!")
            else:
                projetos_atr = sorted({i.get("fields", {}).get("project", {}).get("name", "—") for i in em_atraso})
                priors_atr   = sorted({(i.get("fields", {}).get("priority") or {}).get("name", "—") for i in em_atraso})
                col_fa1, col_fa2 = st.columns(2)
                filtro_proj_a  = col_fa1.multiselect("Filtrar por Projeto",    projetos_atr, placeholder="Todos",  key="atr1_proj")
                filtro_prior_a = col_fa2.multiselect("Filtrar por Prioridade", priors_atr,   placeholder="Todas",  key="atr1_prio")
                em_atr_fil = [
                    i for i in em_atraso
                    if (not filtro_proj_a  or i.get("fields", {}).get("project", {}).get("name") in filtro_proj_a)
                    and (not filtro_prior_a or (i.get("fields", {}).get("priority") or {}).get("name") in filtro_prior_a)
                ]
                em_atr_ord = sorted(em_atr_fil, key=lambda x: x.get("fields", {}).get("duedate", "9999"))
                st.markdown(
                    f"**{len(em_atraso)} tarefa(s)** com prazo vencido — "
                    f"exibindo **{len(em_atr_ord)}**"
                )
                st.markdown("".join(_card_issue(i) for i in em_atr_ord), unsafe_allow_html=True)

    # ─ Tab 2: Por Responsável (Epics + Tasks filhas) ─────────────
    with tab2:
        if not issues_lider:
            st.info("Sem dados de assignees disponíveis.")
        else:
            def _cat_issue(issue):
                k = issue.get("fields", {}).get("status", {}).get("statusCategory", {}).get("key", "todo")
                return CATEGORIAS.get(k, "A Fazer")

            # epic_key → [tasks/stories]
            epic_to_tasks = {}
            for task in tasks_epics:
                flds     = task.get("fields", {})
                epic_key = flds.get("customfield_10014") or (flds.get("parent") or {}).get("key")
                if epic_key:
                    epic_to_tasks.setdefault(epic_key, []).append(task)

            # story_key → [subtasks]
            story_to_subtasks = {}
            for st_issue in subtasks:
                parent_key = (st_issue.get("fields", {}).get("parent") or {}).get("key")
                if parent_key:
                    story_to_subtasks.setdefault(parent_key, []).append(st_issue)

            # Coleta assignees únicos dos Epics
            assignees = sorted({
                (i.get("fields", {}).get("assignee") or {}).get("displayName", "Não atribuído")
                for i in issues_lider
            })

            col_sel, _ = st.columns([1, 3])
            with col_sel:
                assignee_sel = st.selectbox(
                    "👤 Responsável",
                    ["Todos"] + assignees,
                    help="Selecione um responsável para ver seus Epics e tasks",
                )

            # Filtra Epics pelo assignee selecionado
            if assignee_sel == "Todos":
                epics_a = issues_lider
            else:
                epics_a = [
                    i for i in issues_lider
                    if (i.get("fields", {}).get("assignee") or {}).get("displayName", "Não atribuído") == assignee_sel
                ]

            # KPIs baseados nos Epics filtrados
            total_epics = len(epics_a)
            conc_epics  = sum(1 for i in epics_a if _cat_issue(i) == "Concluído")
            and_epics   = sum(1 for i in epics_a if _cat_issue(i) == "Em Andamento")
            # Total de tasks filhas dos epics filtrados
            total_tasks = sum(len(epic_to_tasks.get(i.get("key", ""), [])) for i in epics_a)
            pct_epics   = round((conc_epics / total_epics * 100) if total_epics else 0, 1)
            # Impedimentos filtrados pelo responsável selecionado
            if assignee_sel == "Todos":
                impedimentos_resp = flagged
            else:
                impedimentos_resp = [
                    i for i in flagged
                    if (i.get("fields", {}).get("assignee") or {}).get("displayName", "Não atribuído") == assignee_sel
                ]
            # Tarefas em atraso filtradas pelo responsável selecionado
            if assignee_sel == "Todos":
                em_atraso_resp = em_atraso
            else:
                em_atraso_resp = [
                    i for i in em_atraso
                    if (i.get("fields", {}).get("assignee") or {}).get("displayName", "Não atribuído") == assignee_sel
                ]

            # ── Sub-abas da aba Por Responsável ──────────────────────────
            sub_a, sub_b, sub_c, sub_d = st.tabs(["📊 Resumo", "📌 Epics & Tasks", "🚩 Impedimentos", "⚠️ Em Atraso"])

            with sub_a:
                c1a, c2a, c3a, c4a, c5a, c6a = st.columns(6)
                kpi_resp = [
                    (c1a, total_epics,            "Epics",             "#6554C0", "#F3F0FF", "🗂️"),
                    (c2a, total_tasks,            "Tasks Associadas",  "#4C6EF5", "#EEF2FF", "📋"),
                    (c3a, conc_epics,             "Epics Concluídos",  "#2F9E44", "#EBFBEE", "✅"),
                    (c4a, f"{pct_epics}%",        "% Concluído",       "#2F9E44", "#EBFBEE", "📈"),
                    (c5a, len(impedimentos_resp), "Impedimentos",      "#E03131", "#FFF5F5", "🚩"),
                    (c6a, len(em_atraso_resp),    "Em Atraso",         "#C92A2A", "#FFF0F0", "⚠️"),
                ]
                for col_a, val_a, lbl_a, cor_a, bg_a, icon_a in kpi_resp:
                    with col_a:
                        st.markdown(
                            f'<div class="kpi-card">'
                            f'<div class="kpi-accent" style="background:{cor_a}"></div>'
                            f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
                            f'<div>'
                            f'<div class="kpi-val" style="color:{cor_a}">{val_a}</div>'
                            f'<div class="kpi-lbl">{lbl_a}</div>'
                            f'</div>'
                            f'<div style="background:{bg_a};border-radius:12px;width:44px;height:44px;'
                            f'display:flex;align-items:center;justify-content:center;font-size:1.3rem">'
                            f'{icon_a}</div>'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            with sub_b:
                col_fp, col_fs = st.columns(2)
                projs_e = sorted({i.get("fields", {}).get("project", {}).get("name", "—") for i in epics_a})
                stats_e = sorted({i.get("fields", {}).get("status", {}).get("name", "—") for i in epics_a})
                fil_proj_e   = col_fp.multiselect("Filtrar por Projeto", projs_e, placeholder="Todos", key="e_proj")
                fil_status_e = col_fs.multiselect("Filtrar por Status",  stats_e, placeholder="Todos", key="e_status")

                epics_filtrados = [
                    i for i in epics_a
                    if (not fil_proj_e   or i.get("fields", {}).get("project", {}).get("name") in fil_proj_e)
                    and (not fil_status_e or i.get("fields", {}).get("status",  {}).get("name") in fil_status_e)
                ]

                st.caption(f"Exibindo {len(epics_filtrados)} Epics")
                st.markdown("---")

            with sub_c:
                if not impedimentos_resp:
                    st.success("✅ Nenhum impedimento ativo para este responsável!")
                else:
                    label_resp = f"responsável **{assignee_sel}**" if assignee_sel != "Todos" else "todos os responsáveis"
                    st.markdown(f"**{len(impedimentos_resp)} impedimento(s)** ativo(s) para {label_resp}")
                    por_projeto_imp = {}
                    for issue in impedimentos_resp:
                        proj = issue.get("fields", {}).get("project", {}).get("name", "—")
                        por_projeto_imp.setdefault(proj, []).append(issue)
                    grupos_imp_html = []
                    for proj_nome_imp, issues_imp in sorted(por_projeto_imp.items()):
                        qtd_imp = len(issues_imp)
                        suf_imp = 's' if qtd_imp > 1 else ''
                        cards_imp = "".join(_card_issue(i, show_flag=True) for i in issues_imp)
                        grupos_imp_html.append(
                            f'<details open style="background:white;border-radius:14px;padding:14px 18px;'
                            f'margin-bottom:12px;box-shadow:0 2px 10px rgba(0,0,0,0.06);'
                            f'border:1px solid rgba(0,0,0,0.04)">'
                            f'<summary style="font-weight:700;color:#1A1D2E;cursor:pointer;font-size:0.95rem;'
                            f'list-style:none;padding:4px 0">'
                            f'{proj_nome_imp} &nbsp;·&nbsp; <span style="color:#E03131;font-weight:800">{qtd_imp}</span> impedimento{suf_imp}'
                            f'</summary>'
                            f'<div style="margin-top:12px">{cards_imp}</div>'
                            f'</details>'
                        )
                    st.markdown("".join(grupos_imp_html), unsafe_allow_html=True)

            with sub_d:
                if not em_atraso_resp:
                    st.success("✅ Nenhuma tarefa em atraso para este responsável!")
                else:
                    label_resp_a = f"responsável **{assignee_sel}**" if assignee_sel != "Todos" else "todos os responsáveis"
                    st.markdown(f"**{len(em_atraso_resp)} tarefa(s)** em atraso para {label_resp_a}")
                    em_atr_resp_ord = sorted(em_atraso_resp, key=lambda x: x.get("fields", {}).get("duedate", "9999"))
                    st.markdown("".join(_card_issue(i) for i in em_atr_resp_ord), unsafe_allow_html=True)

            with sub_b:

                por_projeto_e = {}
                for epic in epics_filtrados:
                    pnome = epic.get("fields", {}).get("project", {}).get("name", "Desconhecido")
                    por_projeto_e.setdefault(pnome, []).append(epic)

                for proj_nome in sorted(por_projeto_e.keys()):
                    st.markdown(f"#### 📁 {proj_nome}")
                    for epic in por_projeto_e[proj_nome]:
                        efields   = epic.get("fields", {})
                        ekey      = epic.get("key", "—")
                        esummary  = efields.get("summary", "Sem título")
                        estatus   = efields.get("status", {}).get("name", "—")
                        epriority = (efields.get("priority") or {}).get("name", "—")
                        eassignee = (efields.get("assignee") or {}).get("displayName", "Não atribuído")
                        cor_s_e   = _cor_status(estatus)
                        cor_p_e   = _cor_prioridade(epriority)
                        tasks_do_epic = epic_to_tasks.get(ekey, [])
                        n_tasks   = len(tasks_do_epic)
                        n_conc    = sum(1 for t in tasks_do_epic if _cat_issue(t) == "Concluído")
                        n_and     = sum(1 for t in tasks_do_epic if _cat_issue(t) == "Em Andamento")
                        pct_e     = round((n_conc / n_tasks * 100) if n_tasks else 0, 1)

                        # Monta HTML de tasks e subtasks
                        if n_tasks > 0:
                            pct_af_e = round(((n_tasks - n_conc - n_and) / n_tasks * 100), 1)
                            pct_em_e = round((n_and / n_tasks * 100), 1)
                            pct_co_e = round((n_conc / n_tasks * 100), 1)
                            barra_e = (
                                f'<div style="display:flex;height:10px;border-radius:6px;overflow:hidden;'
                                f'background:#F4F5F7;margin:8px 0 12px">'
                                f'<div style="width:{pct_co_e}%;background:#00875A"></div>'
                                f'<div style="width:{pct_em_e}%;background:#0052CC"></div>'
                                f'<div style="width:{pct_af_e}%;background:#DFE1E6"></div>'
                                f'</div>'
                            )
                            tasks_html = ""
                            for task in tasks_do_epic:
                                tkey  = task.get("key", "—")
                                subs  = story_to_subtasks.get(tkey, [])
                                tasks_html += _card_issue(task)
                                if subs:
                                    for sub in subs:
                                        sk     = sub.get("key", "—")
                                        sf     = sub.get("fields", {})
                                        ss_nam = sf.get("summary", "—")
                                        ss_st  = sf.get("status", {}).get("name", "—")
                                        ss_as  = (sf.get("assignee") or {}).get("displayName", "Não atribuído")
                                        ss_pr  = (sf.get("priority") or {}).get("name", "—")
                                        cor_ss = _cor_status(ss_st)
                                        cor_ps = _cor_prioridade(ss_pr)
                                        tasks_html += (
                                            f'<div style="margin:0 0 6px 24px;background:#F8F9FA;'
                                            f'border-radius:6px;padding:8px 12px;'
                                            f'border-left:3px solid {cor_ss}">'
                                            f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
                                            f'<span style="font-size:0.75rem;color:#6B778C">↳</span>'
                                            f'<a href="https://cesar-projetos4.atlassian.net/browse/{sk}" '
                                            f'target="_blank" style="font-weight:700;color:#0052CC;'
                                            f'font-size:0.82rem;text-decoration:none">{sk}</a>'
                                            f'{_badge(ss_st, cor_ss)}{_badge(ss_pr, cor_ps)}'
                                            f'</div>'
                                            f'<p style="margin:4px 0 2px 18px;font-size:0.85rem;color:#172B4D">{ss_nam}</p>'
                                            f'<span style="margin-left:18px;font-size:0.75rem;color:#6B778C">👤 {ss_as}</span>'
                                            f'</div>'
                                        )
                            inner_html = (
                                f'{_badge(estatus, cor_s_e)}{_badge(epriority, cor_p_e)}'
                                f'&nbsp;<span style="font-size:0.82rem;color:#6B778C">👤 {eassignee}</span>'
                                f'&nbsp;&nbsp;<a href="https://cesar-projetos4.atlassian.net/browse/{ekey}" '
                                f'target="_blank" style="font-size:0.82rem;color:#0052CC">🔗 Abrir no Jira</a>'
                                f'{barra_e}{tasks_html}'
                            )
                        else:
                            inner_html = (
                                f'{_badge(estatus, cor_s_e)}{_badge(epriority, cor_p_e)}'
                                f'&nbsp;<span style="font-size:0.82rem;color:#6B778C">👤 {eassignee}</span>'
                                f'&nbsp;&nbsp;<a href="https://cesar-projetos4.atlassian.net/browse/{ekey}" '
                                f'target="_blank" style="font-size:0.82rem;color:#0052CC">🔗 Abrir no Jira</a>'
                                f'<p style="color:#8993A4;font-size:0.85rem;margin:8px 0 0">Nenhuma task associada a este Epic.</p>'
                            )

                        label_exp = (
                            f"[{ekey}] {esummary}  ·  "
                            f"{estatus}  ·  {n_tasks} tasks  ·  {pct_e}% concluído"
                        )
                        st.markdown(
                            f'<details style="background:white;border-radius:12px;padding:12px 16px;'
                            f'margin-bottom:10px;box-shadow:0 1px 8px rgba(0,0,0,0.06);'
                            f'border:1px solid rgba(0,0,0,0.04)">'
                            f'<summary style="font-weight:600;color:#1A1D2E;cursor:pointer;font-size:0.9rem;'
                            f'list-style:none;padding:2px 0">{label_exp}</summary>'
                            f'<div style="margin-top:10px">{inner_html}</div>'
                            f'</details>',
                            unsafe_allow_html=True,
                        )

    # ─ Tab 3: Detalhes do Projeto ────────────────────────────────
    with tab3:
        if not gestores_map:
            st.info("Sem projetos disponíveis.")
        else:
            proj_opcoes = {v["name"]: k for k, v in gestores_map.items()}
            nomes_todos = sorted(proj_opcoes.keys())

            col_sel6, _ = st.columns([1, 3])
            with col_sel6:
                sel = st.selectbox(
                    "🔍 Selecione o projeto",
                    options=nomes_todos,
                    index=0,
                    key="proj_searchbox",
                )
            proj_nome_sel = sel if sel in proj_opcoes else nomes_todos[0]
            proj_key_sel  = proj_opcoes[proj_nome_sel]
            issues_proj_det = []
            issues_hist_det = []
            erro_proj       = None

            with st.spinner(f"Carregando '{proj_nome_sel}'..."):
                try:
                    issues_proj_det = _buscar_issues_projeto(proj_key_sel)
                except Exception as e:
                    erro_proj = str(e)
                try:
                    issues_hist_det = _buscar_historico_projeto(proj_key_sel)
                except Exception as e:
                    if not erro_proj:
                        erro_proj = str(e)

            if erro_proj:
                st.error(f"Erro ao carregar dados do projeto: {erro_proj}")
            elif not issues_proj_det:
                st.info("Nenhuma issue encontrada para este projeto.")
            else:
                hoje_det   = date.today()
                limite_det = hoje_det + timedelta(days=5)
                n_af = n_em = n_co = n_imp = n_prazo = 0

                for issue in issues_proj_det:
                    fields  = issue.get("fields", {})
                    cat_raw = fields.get("status", {}).get("statusCategory", {}).get("key", "todo")
                    cat     = CATEGORIAS.get(cat_raw, "A Fazer")
                    if cat == "A Fazer":        n_af  += 1
                    elif cat == "Em Andamento": n_em  += 1
                    elif cat == "Concluído":    n_co  += 1
                    if fields.get("customfield_10021"):
                        n_imp += 1
                    due_s = fields.get("duedate", "")
                    if due_s and cat != "Concluído":
                        try:
                            if hoje_det <= date.fromisoformat(due_s) <= limite_det:
                                n_prazo += 1
                        except Exception:
                            pass

                total_det = len(issues_proj_det)
                pct_det   = round((n_co / total_det * 100) if total_det else 0, 1)

                atraso_det = [
                    i for i in issues_proj_det
                    if i.get("fields", {}).get("duedate")
                    and _dias_restantes(i["fields"]["duedate"]) < 0
                    and CATEGORIAS.get(
                        i.get("fields", {}).get("status", {}).get("statusCategory", {}).get("key", "todo"),
                        "A Fazer"
                    ) != "Concluído"
                ]
                n_atraso_det = len(atraso_det)

                # ── Sub-abas do Detalhes do Projeto ──────────────────────
                sub_p1, sub_p2, sub_p3, sub_p4 = st.tabs(["📊 Resumo", "🕐 Histórico de Movimentação", "🚩 Impedimentos", "⚠️ Em Atraso"])

                with sub_p1:
                    c1d, c2d, c3d, c4d, c5d, c6d = st.columns(6)
                    for col_d, val_d, lbl_d, cor_d in [
                        (c1d, n_af,          "📋 A Fazer",         "#6554C0"),
                        (c2d, n_em,          "🔄 Em Andamento",    "#0052CC"),
                        (c3d, n_co,          "✅ Concluídas",      "#00875A"),
                        (c4d, n_imp,         "🚩 Impedimentos",    "#BF2600"),
                        (c5d, n_prazo,       "⏰ Prazos a Vencer", "#FF991F"),
                        (c6d, n_atraso_det,  "⚠️ Em Atraso",       "#C92A2A"),
                    ]:
                        with col_d:
                            st.markdown(
                                f'<div class="kpi-card" style="border-top:4px solid {cor_d}">'
                                f'<div class="kpi-val" style="color:{cor_d}">{val_d}</div>'
                                f'<div class="kpi-lbl">{lbl_d}</div></div>',
                                unsafe_allow_html=True,
                            )

                    st.markdown("<br>", unsafe_allow_html=True)
                    pct_af_d = round((n_af / total_det * 100) if total_det else 0, 1)
                    pct_em_d = round((n_em / total_det * 100) if total_det else 0, 1)
                    pct_co_d = round((n_co / total_det * 100) if total_det else 0, 1)
                    st.markdown(
                        f'<div style="background:white;border-radius:10px;padding:20px 24px;'
                        f'margin-bottom:6px;box-shadow:0 1px 6px rgba(0,0,0,0.07)">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                        f'<span style="font-weight:700;font-size:1rem;color:#172B4D">{proj_nome_sel}</span>'
                        f'<span style="font-size:0.82rem;color:#6B778C">'
                        f'{total_det} issues &nbsp;·&nbsp; '
                        f'<span style="color:#6554C0">●</span> {n_af} A Fazer &nbsp;'
                        f'<span style="color:#0052CC">●</span> {n_em} Em Andamento &nbsp;'
                        f'<span style="color:#00875A">●</span> {n_co} Concluído'
                        f'</span></div>'
                        f'<div style="display:flex;height:26px;border-radius:13px;overflow:hidden;background:#F4F5F7">'
                        f'<div style="width:{pct_co_d}%;background:linear-gradient(90deg,#00875A,#36B37E)" '
                        f'title="Concluído: {n_co}"></div>'
                        f'<div style="width:{pct_em_d}%;background:linear-gradient(90deg,#0052CC,#2684FF)" '
                        f'title="Em Andamento: {n_em}"></div>'
                        f'<div style="width:{pct_af_d}%;background:#DFE1E6" title="A Fazer: {n_af}"></div>'
                        f'</div>'
                        f'<div style="text-align:right;font-size:1.3rem;font-weight:800;color:#00875A;margin-top:8px">'
                        f'{pct_det}% concluído</div>'
                        f'</div>'
                        f'<div style="display:flex;gap:20px;font-size:0.8rem;color:#6B778C;margin-bottom:20px">'
                        f'<span><span style="color:#00875A">█</span> Concluído ({pct_co_d}%)</span>'
                        f'<span><span style="color:#0052CC">█</span> Em Andamento ({pct_em_d}%)</span>'
                        f'<span><span style="color:#6554C0">█</span> A Fazer ({pct_af_d}%)</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # ── Botão Gerar Relatório ─────────────────────────────
                    st.markdown("<br>", unsafe_allow_html=True)
                    impedimentos_rel = [
                        i for i in issues_proj_det
                        if i.get("fields", {}).get("customfield_10021")
                    ]

                    def _gerar_relatorio_html():
                        gerado_em = datetime.now(tz=timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
                        linhas_issues = ""
                        for issue in issues_proj_det:
                            f        = issue.get("fields", {})
                            key      = issue.get("key", "—")
                            summary  = f.get("summary", "—")
                            status   = f.get("status", {}).get("name", "—")
                            tipo     = (f.get("issuetype") or {}).get("name", "—")
                            resp     = (f.get("assignee") or {}).get("displayName", "Não atribuído")
                            prio     = (f.get("priority") or {}).get("name", "—")
                            due      = f.get("duedate", "") or "—"
                            flag_raw = f.get("customfield_10021") or []
                            flag     = flag_raw[0].get("value", "Impediment") if flag_raw else ""
                            flag_td  = f'<td style="color:#BF2600;font-weight:600">⚑ {flag}</td>' if flag else "<td>—</td>"
                            linhas_issues += (
                                f"<tr>"
                                f'<td><a href="https://cesar-projetos4.atlassian.net/browse/{key}" '
                                f'target="_blank">{key}</a></td>'
                                f"<td>{summary}</td>"
                                f"<td>{tipo}</td>"
                                f"<td>{status}</td>"
                                f"<td>{resp}</td>"
                                f"<td>{prio}</td>"
                                f"<td>{due}</td>"
                                f"{flag_td}"
                                f"</tr>\n"
                            )
                        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório — {proj_nome_sel}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; color: #172B4D; }}
  h1 {{ color: #0052CC; }} h2 {{ color: #0052CC; border-bottom: 2px solid #DFE1E6; padding-bottom:6px; }}
  .kpi {{ display:flex; gap:24px; flex-wrap:wrap; margin:20px 0; }}
  .kpi-box {{ background:#F4F5F7; border-radius:8px; padding:14px 20px; min-width:120px; text-align:center; }}
  .kpi-val {{ font-size:2rem; font-weight:800; }}
  .kpi-lbl {{ font-size:0.8rem; color:#6B778C; margin-top:4px; }}
  .bar-wrap {{ height:20px; background:#DFE1E6; border-radius:10px; overflow:hidden; margin:10px 0; }}
  .bar-co {{ height:100%; background:#00875A; display:inline-block; }}
  .bar-em {{ height:100%; background:#0052CC; display:inline-block; }}
  .bar-af {{ height:100%; background:#DFE1E6; display:inline-block; }}
  table {{ border-collapse:collapse; width:100%; margin-top:16px; font-size:0.85rem; }}
  th {{ background:#0052CC; color:white; padding:8px 12px; text-align:left; }}
  td {{ padding:7px 12px; border-bottom:1px solid #DFE1E6; }}
  tr:hover {{ background:#F4F5F7; }}
  a {{ color:#0052CC; }}
  .footer {{ margin-top:40px; font-size:0.78rem; color:#6B778C; }}
</style>
</head>
<body>
<h1>📊 Relatório do Projeto</h1>
<h2>{proj_nome_sel}</h2>
<p style="color:#6B778C">Gerado em: {gerado_em}</p>

<h2>Resumo</h2>
<div class="kpi">
  <div class="kpi-box"><div class="kpi-val" style="color:#172B4D">{total_det}</div><div class="kpi-lbl">Total de Issues</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#6554C0">{n_af}</div><div class="kpi-lbl">A Fazer</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#0052CC">{n_em}</div><div class="kpi-lbl">Em Andamento</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#00875A">{n_co}</div><div class="kpi-lbl">Concluídas</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#BF2600">{n_imp}</div><div class="kpi-lbl">Impedimentos</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#FF991F">{n_prazo}</div><div class="kpi-lbl">Prazos a Vencer</div></div>
</div>
<p><strong>Progresso geral: {pct_det}% concluído</strong></p>
<div class="bar-wrap">
  <span class="bar-co" style="width:{pct_co_d}%"></span><span class="bar-em" style="width:{pct_em_d}%"></span><span class="bar-af" style="width:{pct_af_d}%"></span>
</div>

<h2>Todas as Issues</h2>
<table>
  <tr><th>Chave</th><th>Resumo</th><th>Tipo</th><th>Status</th><th>Responsável</th><th>Prioridade</th><th>Prazo</th><th>Impedimento</th></tr>
  {linhas_issues}
</table>

<div class="footer">Valcann Dashboard · Domínio: {DOMAIN} · Relatório gerado automaticamente</div>
</body>
</html>"""

                    html_rel = _gerar_relatorio_html()
                    nome_arquivo = f"relatorio_{proj_key_sel}_{date.today().isoformat()}.html"
                    st.download_button(
                        label="📄 Gerar Relatório",
                        data=html_rel.encode("utf-8"),
                        file_name=nome_arquivo,
                        mime="text/html",
                        use_container_width=False,
                    )
                    eventos = []
                    for issue in issues_hist_det:
                        ikey      = issue.get("key", "—")
                        isummary  = issue.get("fields", {}).get("summary", "Sem título")
                        changelog = issue.get("changelog", {})
                        histories = changelog.get("histories") or changelog.get("values", [])
                        for hist in histories:
                            criado_str = hist.get("created", "")
                            autor      = (hist.get("author") or {}).get("displayName", "Sistema")
                            for item_h in hist.get("items", []):
                                if item_h.get("field", "").lower() == "status":
                                    try:
                                        dt_ev  = datetime.fromisoformat(criado_str.replace("Z", "+00:00"))
                                        dt_loc = dt_ev.replace(tzinfo=None)
                                    except Exception:
                                        dt_loc = None
                                    eventos.append({
                                        "data":   dt_loc,
                                        "issue":  ikey,
                                        "resumo": isummary,
                                        "de":     item_h.get("fromString", "—"),
                                        "para":   item_h.get("toString",   "—"),
                                        "autor":  autor,
                                    })

                    if not eventos:
                        st.info(
                            "Nenhum histórico de movimentação disponível. "
                            "O Jira pode não estar retornando o changelog para este projeto."
                        )
                    else:
                        eventos.sort(key=lambda x: x["data"] or datetime.min, reverse=True)
                        datas_ev    = [e["data"].date() for e in eventos if e["data"]]
                        data_min_ev = min(datas_ev) if datas_ev else date.today()
                        data_max_ev = max(datas_ev) if datas_ev else date.today()

                        col_h1, col_h2, col_h3 = st.columns([1, 1, 2])
                        with col_h1:
                            filtro_ini = st.date_input(
                                "📅 De",
                                value=data_min_ev,
                                min_value=data_min_ev,
                                max_value=data_max_ev,
                                key="hist_ini",
                            )
                        with col_h2:
                            filtro_fim = st.date_input(
                                "📅 Até",
                                value=data_max_ev,
                                min_value=data_min_ev,
                                max_value=data_max_ev,
                                key="hist_fim",
                            )

                        evs_fil = [
                            e for e in eventos
                            if e["data"] and filtro_ini <= e["data"].date() <= filtro_fim
                        ]
                        st.caption(f"Exibindo **{len(evs_fil)}** movimentação(ões) no período")

                        if not evs_fil:
                            st.info("Nenhuma movimentação no período selecionado.")
                        else:
                            cards_h = []
                            for ev in evs_fil:
                                data_fmt = ev["data"].strftime("%d/%m/%Y %H:%M") if ev["data"] else "—"
                                cor_de   = _cor_status(ev["de"])
                                cor_para = _cor_status(ev["para"])
                                cards_h.append(
                                    f'<div style="background:white;border-radius:8px;padding:12px 16px;'
                                    f'margin-bottom:8px;border-left:3px solid #0052CC;'
                                    f'box-shadow:0 1px 4px rgba(0,0,0,0.06)">'
                                    f'<div style="display:flex;justify-content:space-between;'
                                    f'align-items:center;flex-wrap:wrap;gap:6px">'
                                    f'<div>'
                                    f'<a href="https://cesar-projetos4.atlassian.net/browse/{ev["issue"]}" '
                                    f'target="_blank" style="font-weight:700;color:#0052CC;'
                                    f'font-size:0.88rem;text-decoration:none">{ev["issue"]}</a>'
                                    f'&nbsp;&nbsp;{_badge(ev["de"], cor_de)} '
                                    f'<span style="color:#6B778C;font-size:0.9rem">→</span> '
                                    f'{_badge(ev["para"], cor_para)}'
                                    f'</div>'
                                    f'<span style="font-size:0.75rem;color:#6B778C">'
                                    f'🕒 {data_fmt} &nbsp;·&nbsp; 👤 {ev["autor"]}</span>'
                                    f'</div>'
                                    f'<p style="margin:5px 0 0;font-size:0.85rem;color:#172B4D">'
                                    f'{ev["resumo"]}</p>'
                                    f'</div>'
                                )
                            st.markdown("".join(cards_h), unsafe_allow_html=True)

                with sub_p3:
                    impedimentos_proj = [
                        i for i in issues_proj_det
                        if i.get("fields", {}).get("customfield_10021")
                    ]
                    if not impedimentos_proj:
                        st.success("✅ Nenhum impedimento ativo neste projeto!")
                    else:
                        st.markdown(f"**{len(impedimentos_proj)} impedimento(s)** ativo(s) em **{proj_nome_sel}**")
                        st.markdown("---")
                        st.markdown(
                            "".join(_card_issue(i, show_flag=True) for i in impedimentos_proj),
                            unsafe_allow_html=True,
                        )

                with sub_p4:
                    if not atraso_det:
                        st.success("✅ Nenhuma tarefa em atraso neste projeto!")
                    else:
                        st.markdown(f"**{n_atraso_det} tarefa(s)** com prazo vencido em **{proj_nome_sel}**")
                        st.markdown("---")
                        atraso_det_ord = sorted(atraso_det, key=lambda x: x.get("fields", {}).get("duedate", "9999"))
                        st.markdown(
                            "".join(_card_issue(i) for i in atraso_det_ord),
                            unsafe_allow_html=True,
                        )


# ── PONTO DE ENTRADA ──────────────────────────────────────────
_CLI_COMMANDS = {
    "jira_api":  jira_api,
    "48h":       contador_atualizadas_48h,
    "flagged":   contador_flagged,
    "progresso": porcentagem_projetos,
}

# Detecta contexto Streamlit e renderiza o dashboard
_in_streamlit = False
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx as _get_ctx
    _in_streamlit = _get_ctx() is not None
except Exception:
    pass

if _in_streamlit:
    dashboard()

if __name__ == "__main__":
    # Não executa CLI quando já estamos dentro do contexto Streamlit
    _em_streamlit = False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx as _ctx_check
        _em_streamlit = _ctx_check() is not None
    except Exception:
        pass

    if not _em_streamlit:
        cmd = sys.argv[1] if len(sys.argv) > 1 else None
        if cmd in _CLI_COMMANDS:
            try:
                _CLI_COMMANDS[cmd]()
            except requests.exceptions.HTTPError as err:
                print(f"Erro HTTP ao conectar ao Jira: {err}")
            except requests.exceptions.ConnectionError:
                print("Erro de conexão. Verifique sua internet ou o domínio Jira.")
            except Exception as err:
                print(f"Erro inesperado: {err}")
        else:
            print("Uso: python valcann.py [jira_api|48h|flagged|progresso]")
            print("Dashboard: streamlit run valcann.py")
