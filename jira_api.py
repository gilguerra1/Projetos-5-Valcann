import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configurações
DOMAIN = "cesar-projetos4"

URL = f"https://{DOMAIN}.atlassian.net/rest/api/3/search/jql"

AUTH = requests.auth.HTTPBasicAuth(
    os.getenv('EMAIL'),
    os.getenv('API_TOKEN')
)

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Query JQL
payload = json.dumps({
    "jql": "issuetype = Epic AND statusCategory != Done",
    "fields": ["summary", "status", "assignee", "priority"],
    "maxResults": 50
})

try:
    response = requests.post(
        URL,
        data=payload,
        auth=AUTH,
        headers=HEADERS
    )

    response.raise_for_status()

    dados = response.json()

    issues = dados.get('results', []) or dados.get('issues', [])

    print(f"Sucesso! Projetos encontrados: {len(issues)}")

    for item in issues:
        fields = item.get('fields', {})

        print(
            f"Projeto: {fields.get('summary')} | "
            f"Status: {fields.get('status').get('name')}"
        )

except Exception as e:
    print(f"Erro na conexão: {e}")