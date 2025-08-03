# FinanceBot - Execução Local

## 📋 Pré-requisitos

- Python 3.8+
- Node.js 16+
- MongoDB (local ou Docker)

## 🚀 Configuração

### 1. Backend (FastAPI)

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 2. Frontend (React)

```bash
# Instalar dependências
yarn install
# ou
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local
# Edite o arquivo .env.local
```

### 3. MongoDB

#### Opção A: MongoDB Local
```bash
# Instalar MongoDB Community Edition
# https://docs.mongodb.com/manual/installation/

# Iniciar MongoDB
mongod
```

#### Opção B: Docker
```bash
# Executar MongoDB em container
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

## 🔧 Configuração do Bot

### 1. Criar Bot no Telegram
1. Abra o Telegram
2. Procure por @BotFather
3. Digite `/newbot`
4. Siga as instruções
5. Copie o token gerado

### 2. Configurar Webhook (Para produção)
```bash
curl -X POST "https://api.telegram.org/bot{SEU_TOKEN}/setWebhook" \
-H "Content-Type: application/json" \
-d '{"url": "https://seu-dominio.com/api/telegram/webhook"}'
```

### 3. Para desenvolvimento local (sem webhook)
- Use ngrok para expor localhost
- Configure o webhook com a URL do ngrok

## 🎯 Executar o Sistema

### 1. Iniciar Backend
```bash
cd backend
source venv/bin/activate
python server.py
# Ou usando uvicorn
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### 2. Iniciar Frontend
```bash
cd frontend
yarn start
# ou
npm start
```

O sistema estará disponível em:
- Frontend: http://localhost:3000
- Backend: http://localhost:8001

## 🔑 Configurações Importantes

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=financial_bot
TELEGRAM_BOT_TOKEN=seu_token_aqui
GROQ_API_KEY=sua_chave_groq_aqui
```

### Frontend (.env.local)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🤖 Uso do Bot

1. Inicie uma conversa com seu bot no Telegram
2. Envie `/start`
3. Configure seu email: `email: seu@email.com`
4. Comece a enviar transações:
   - "Paguei R$ 500 de aluguel"
   - "Recebi R$ 2000 de salário"
   - "Gastei 50 no supermercado"

## 📊 Comandos do Bot

- `/start` - Iniciar bot
- `email: seu@email.com` - Definir email
- `resumo` - Ver resumo financeiro
- `zerar` - Limpar todos os registros
- Qualquer transação em linguagem natural

## 🛠️ Solução de Problemas

### Bot não responde
- Verifique se o token está correto
- Verifique se o webhook está configurado
- Para dev local, use ngrok ou polling

### Erro de conexão MongoDB
- Verifique se o MongoDB está rodando
- Verifique a URL de conexão no .env

### Erro da API Groq
- Verifique se a chave da API está correta
- Verifique se há créditos na conta Groq

## 📦 Estrutura do Projeto

```
financebot/
├── backend/
│   ├── server.py
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.js
    │   ├── App.css
    │   └── components/
    ├── package.json
    └── .env.example
```

## 🔄 Atualizações

Para atualizar o sistema:
1. Pull das mudanças do repositório
2. Atualizar dependências: `pip install -r requirements.txt` e `yarn install`
3. Reiniciar os serviços

## 📝 Logs

Para visualizar logs:
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend logs
# Visíveis no console do navegador
```

## 🎨 Personalização

### Adicionar novas categorias
Edite `DEFAULT_CATEGORIES` em `server.py`

### Modificar interface
Edite os componentes em `frontend/src/components/`

### Ajustar IA
Modifique o `system_prompt` na função `process_message_with_groq`

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs
2. Consulte a documentação das APIs
3. Teste os endpoints individualmente