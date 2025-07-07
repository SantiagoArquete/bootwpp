from flask import Flask, request
import json
import os
import re
import requests

app = Flask(__name__)
ARQUIVO = 'gastos.json'
VERIFY_TOKEN = "meu_token_seguro_123"  # Mesmo usado no painel da Meta

# ---------- GESTÃO DE GASTOS ----------

def carregar_gastos():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, 'r') as f:
            return json.load(f)
    return []

def salvar_gastos(gastos):
    with open(ARQUIVO, 'w') as f:
        json.dump(gastos, f, indent=2)

def extrair_valor(texto):
    match = re.search(r'(\d+(?:[.,]\d+)?)', texto)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

# ---------- WHATSAPP WEBHOOK ----------

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    mode = request.args.get("hub.mode")
    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

@app.route('/webhook', methods=['POST'])
def receber_mensagem():
    data = request.get_json()
    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                mensagens = value.get("messages", [])
                if mensagens:
                    mensagem = mensagens[0]
                    texto = mensagem.get("text", {}).get("body")
                    numero = mensagem.get("from")  # ID do remetente que enviou a msg
                    processar_mensagem(texto, numero)
    return "OK", 200


ACCESS_TOKEN = "EAAGxq5gRglUBPEq7BfgVBZCKDoBL1eXuMeTv3eQB3rZAR1XqTOpOfHZBEdLAmKi4ACZAGHhIratfoiEPZBY6NyjY4ACnQdrk7JlhmsHI722huTrtLgDoaIUHAHZATykihuYvkPqg0FWaSwnFKAKDVB1ZAmZBZA8fSRvgGwHu129RolJCvIZBZBQJWZAGbqZBZC6Cc0rwKSZCGNW9uBHjsgQwtZBPE40RzBYzkxwIoTy7duVfEiw31oCeIZAqR"
ID_NUMERO_REMETENTE = "603104219564006"

def processar_mensagem(texto, numero):
    valor = extrair_valor(texto)
    if valor is None:
        enviar_resposta(numero, 'Mensagem inválida. Envie algo como "gastei 30 no mercado".')
        return

    descricao = texto.replace(str(valor), '').strip()
    gastos = carregar_gastos()
    gastos.append({'descricao': descricao, 'valor': valor})
    salvar_gastos(gastos)

    resposta = f"Ok, os R${valor:.2f} gastos {descricao} foram anotados!"
    enviar_resposta(numero, resposta)
# ---------- STATUS ----------

def enviar_resposta(numero, mensagem):
    url = f"https://graph.facebook.com/v18.0/{ID_NUMERO_REMETENTE}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensagem}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Resposta enviada:", response.status_code, response.text)


@app.route('/', methods=['GET'])
def status():
    return "Bot de finanças rodando!"

# ---------- INICIAR ----------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
