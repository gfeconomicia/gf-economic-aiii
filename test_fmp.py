import os
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("FMP_API_KEY", "").strip()
if not key:
    print("FMP_API_KEY não configurada. Copie .env.example para .env e preencha a variável.")
    raise SystemExit(1)

today = datetime.now(timezone.utc).date().isoformat()
url = "https://financialmodelingprep.com/stable/economic-calendar"
try:
    response = requests.get(url, params={"from": today, "to": today, "apikey": key}, timeout=20)
    print("HTTP:", response.status_code)
    if response.status_code == 200:
        try:
            payload = response.json()
        except ValueError:
            print("A resposta não veio em JSON.")
            raise SystemExit(2)
        if isinstance(payload, list):
            print("Conexão FMP: OK")
            print("Eventos retornados:", len(payload))
            if payload:
                print("Primeiro evento:", payload[0].get("event", "sem nome"))
            else:
                print("A API respondeu corretamente, mas não retornou eventos para hoje.")
        else:
            print("A API respondeu, mas o formato não é a lista esperada.")
            print(str(payload)[:400])
    elif response.status_code in (401, 403):
        print("A chave foi rejeitada ou seu plano não tem acesso a este endpoint.")
        print("Não compartilhe a chave. Confira o plano e a permissão do Economic Calendar na FMP.")
        print(response.text[:300])
    elif response.status_code == 429:
        print("Limite de chamadas atingido. Aguarde a renovação do limite.")
    else:
        print("Resposta:", response.text[:400])
except requests.RequestException as exc:
    print("Falha de rede:", exc)
