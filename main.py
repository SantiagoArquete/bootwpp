from flask import Flask, request, jsonify
import json
import os
import re

app = Flask(__name__)
ARQUIVO = 'gastos.json'
VERIFY_TOKEN = "meu_token_seguro_123"  # Use o mesmo valor que você colocou na plataforma Meta

# -------------------- GESTÃO DE GASTOS --------------------

def carregar_gastos():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, 'r') as f:
            return json.load(f)
    return []

def salvar_gastos(gastos):
    with open(ARQUIVO, 'w') as f:
        json.dump(gastos, f, indent=2)

@app.route('/', methods=['GET'])
def status():
    return "Bot de finanças rodando!"

@app.route('/gasto', methods=['POST'])
def registrar_gasto():
    data = request.json
    mensagem = data.get('mensagem', '')
    valor = extrair_valor(mensagem)
    
    if valor is None:
        return jsonify({'resposta': 'Mensagem inválida. Envie algo como "gastei 30 no mercado".'})
    
    descricao = mensagem.replace(str(valor), '').strip()
    gastos = carregar_gastos()
    gastos.append({'descricao': descricao, 'valor': valor})
    salvar_gastos(gastos)
    
    total = sum(item['valor'] for item in gastos)
    return jsonify({'resposta': f'Anotado: "{descricao}" por R${valor:.2f}. Total: R${total:.2f}'})

def extrair_valor(texto):
    match = re.search(r'(\d+(?:[.,]\d+)?)', texto)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

# -------------------- WHATSAPP WEBHOOK VERIFICATION --------------------

@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    mode = request.args.get("hub.mode")

    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Erro de verificação", 403

# -------------------- FLASK RUN --------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
