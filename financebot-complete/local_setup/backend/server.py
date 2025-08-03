from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from datetime import datetime, timedelta
import asyncio
import httpx
import json
import re
from bson import ObjectId
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'financial_bot')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY:
    print("⚠️ AVISO: Configure TELEGRAM_BOT_TOKEN e GROQ_API_KEY no arquivo .env")

app = FastAPI(title="FinanceBot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
try:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    transactions_collection = db.transactions
    users_collection = db.users
    categories_collection = db.categories
    print(f"✅ Conectado ao MongoDB: {MONGO_URL}")
except Exception as e:
    print(f"❌ Erro ao conectar no MongoDB: {e}")

# Pydantic models
class Transaction(BaseModel):
    id: Optional[str] = None
    user_id: str
    amount: float
    description: str
    category: str
    type: str  # "income" or "expense"
    date: datetime
    telegram_message_id: Optional[int] = None

class User(BaseModel):
    id: Optional[str] = None
    telegram_id: int
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    balance: float = 0.0
    created_at: datetime

class TelegramWebhook(BaseModel):
    update_id: int
    message: Dict[str, Any]

# Default categories
DEFAULT_CATEGORIES = {
    "expense": [
        "Alimentação", "Transporte", "Moradia", "Saúde", "Educação", 
        "Entretenimento", "Roupas", "Tecnologia", "Impostos", "Outros"
    ],
    "income": [
        "Salário", "Freelance", "Investimentos", "Vendas", "Presentes", "Outros"
    ]
}

# Initialize default categories
async def init_categories():
    for type_cat, categories in DEFAULT_CATEGORIES.items():
        for category in categories:
            existing = categories_collection.find_one({"name": category, "type": type_cat})
            if not existing:
                categories_collection.insert_one({
                    "id": str(uuid.uuid4()),
                    "name": category,
                    "type": type_cat,
                    "created_at": datetime.utcnow()
                })

# Groq API integration for NLP
async def process_message_with_groq(message_text: str) -> Dict[str, Any]:
    """Process user message using Groq to extract financial information"""
    
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY não configurada")
        return {"is_transaction": False}
    
    system_prompt = """
    Você é um assistente especializado em identificar e extrair informações financeiras de mensagens em português.
    
    PRIMEIRO: Determine se a mensagem é uma TRANSAÇÃO FINANCEIRA ou apenas uma PERGUNTA/COMANDO:
    
    TRANSAÇÕES FINANCEIRAS (processar):
    - "Paguei R$ 500 de aluguel"
    - "Gastei 50 no supermercado" 
    - "Recebi R$ 2000 de salário"
    - "Comprei um livro por R$ 30"
    
    NÃO SÃO TRANSAÇÕES (ignorar):
    - Perguntas: "quanto gastei?", "qual meu saldo?", "como está meu orçamento?"
    - Comandos: "zerar registro", "limpar dados", "ajuda", "help"
    - Conversas: "oi", "tchau", "obrigado"
    - Frases sem valores monetários específicos
    
    Se for uma TRANSAÇÃO FINANCEIRA, extraia:
    - amount: valor numérico (apenas números, sem R$ ou símbolos)
    - type: "income" para receitas ou "expense" para gastos/despesas
    - description: descrição curta da transação
    - category: categoria mais apropriada
    
    Categorias de despesa: Alimentação, Transporte, Moradia, Saúde, Educação, Entretenimento, Roupas, Tecnologia, Impostos, Outros
    Categorias de receita: Salário, Freelance, Investimentos, Vendas, Presentes, Outros
    
    IMPORTANTE: Se amount for 0 ou não conseguir extrair valor válido, retorne "not_transaction"
    
    Responda APENAS em formato JSON:
    {"is_transaction": true/false, "amount": 0.0, "type": "expense|income", "description": "...", "category": "..."}
    
    Se NÃO for transação: {"is_transaction": false, "response": "Esta é uma pergunta/comando, não uma transação financeira."}
    """
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message_text}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    parsed_response = json.loads(json_match.group())
                    
                    # Validate transaction
                    if parsed_response.get("is_transaction") and parsed_response.get("amount", 0) > 0:
                        return parsed_response
                    else:
                        return {"is_transaction": False}
                else:
                    return {"is_transaction": False}
            else:
                print(f"Groq API error: {response.status_code} - {response.text}")
                return {"is_transaction": False}
                
    except Exception as e:
        print(f"Error processing with Groq: {e}")
        return {"is_transaction": False}

# Helper functions
def get_or_create_user(telegram_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get existing user or create new one"""
    telegram_id = telegram_user_data["id"]
    
    user = users_collection.find_one({"telegram_id": telegram_id})
    if not user:
        user_data = {
            "id": str(uuid.uuid4()),
            "telegram_id": telegram_id,
            "email": None,  # Will be set later
            "first_name": telegram_user_data.get("first_name"),
            "last_name": telegram_user_data.get("last_name"),
            "username": telegram_user_data.get("username"),
            "balance": 0.0,
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(user_data)
        return user_data
    return user

def update_user_balance(user_id: str, amount: float, transaction_type: str):
    """Update user balance based on transaction"""
    multiplier = 1 if transaction_type == "income" else -1
    users_collection.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount * multiplier}}
    )

def clear_user_data(telegram_id: int):
    """Clear all user transactions and reset balance"""
    user = users_collection.find_one({"telegram_id": telegram_id})
    if user:
        # Delete all transactions
        transactions_collection.delete_many({"user_id": user["id"]})
        # Reset balance
        users_collection.update_one(
            {"id": user["id"]},
            {"$set": {"balance": 0.0}}
        )
        return True
    return False

def get_user_summary(telegram_id: int) -> str:
    """Get user financial summary"""
    user = users_collection.find_one({"telegram_id": telegram_id})
    if not user:
        return "Você ainda não possui transações registradas."
    
    # Get current month transactions
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    transactions = list(transactions_collection.find({
        "user_id": user["id"],
        "date": {"$gte": start_of_month}
    }))
    
    if not transactions:
        return f"💰 Saldo atual: R$ {user['balance']:.2f}\n📊 Nenhuma transação este mês."
    
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    
    return f"""💰 *Resumo Financeiro - {datetime.now().strftime('%B/%Y')}*

💵 Receitas: R$ {income:.2f}
💸 Despesas: R$ {expense:.2f}
💼 Saldo atual: R$ {user['balance']:.2f}
📊 Resultado mensal: R$ {income - expense:.2f}

📈 Total de transações: {len(transactions)}"""

async def send_telegram_message(chat_id: int, text: str):
    """Send message to Telegram user"""
    if not TELEGRAM_BOT_TOKEN:
        print(f"Mensagem para {chat_id}: {text}")
        return
        
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
            )
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# API Routes

@app.get("/")
async def root():
    return {"message": "FinanceBot API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mongodb": "connected" if client else "disconnected",
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN),
        "groq_configured": bool(GROQ_API_KEY)
    }

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Telegram webhook"""
    try:
        data = await request.json()
        
        if "message" not in data:
            return {"ok": True}
            
        message = data["message"]
        if "text" not in message:
            return {"ok": True}
            
        chat_id = message["chat"]["id"]
        user_data = message["from"]
        message_text = message["text"]
        message_id = message["message_id"]
        
        # Handle commands
        if message_text.startswith('/'):
            if message_text == '/start':
                welcome_text = """🤖 *Bem-vindo ao Bot de Gestão Financeira!*

📝 *Como usar:*
• Digite suas transações em linguagem natural
• Exemplo: "Paguei R$ 500 de aluguel"
• Exemplo: "Recebi R$ 2000 de salário"

📧 *IMPORTANTE:* Na primeira utilização, envie seu email assim:
`email: seuemail@gmail.com`

📊 Comandos úteis:
• `resumo` - Ver seu resumo financeiro
• `zerar` - Limpar todos os registros
• `email: seu@email.com` - Definir/alterar email

📊 Acesse o painel web com seu email!
                """
                await send_telegram_message(chat_id, welcome_text)
            return {"ok": True}
        
        # Process in background
        background_tasks.add_task(process_financial_message, user_data, message_text, chat_id, message_id)
        
        return {"ok": True}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"ok": True}

async def process_financial_message(user_data: Dict, message_text: str, chat_id: int, message_id: int):
    """Process financial message in background"""
    try:
        # Get or create user
        user = get_or_create_user(user_data)
        telegram_id = user_data["id"]
        
        # Handle special commands
        if message_text.lower() in ['zerar', 'zerar registro', 'limpar', 'reset']:
            success = clear_user_data(telegram_id)
            if success:
                await send_telegram_message(
                    chat_id, 
                    "🗑️ *Registros limpos com sucesso!*\n\nTodos os seus dados financeiros foram removidos e seu saldo foi zerado."
                )
            else:
                await send_telegram_message(chat_id, "❌ Erro ao limpar registros.")
            return
        
        # Handle email setup
        if message_text.lower().startswith('email:'):
            email = message_text.split(':', 1)[1].strip()
            if '@' in email and '.' in email:
                users_collection.update_one(
                    {"id": user["id"]},
                    {"$set": {"email": email}}
                )
                await send_telegram_message(
                    chat_id,
                    f"✅ *Email definido com sucesso!*\n\nEmail: {email}\n\n📊 Agora você pode acessar o painel web usando este email."
                )
            else:
                await send_telegram_message(chat_id, "❌ Email inválido. Use: email: seu@email.com")
            return
        
        # Handle summary request
        if any(word in message_text.lower() for word in ['resumo', 'saldo', 'quanto', 'gastei', 'relatório']):
            summary = get_user_summary(telegram_id)
            await send_telegram_message(chat_id, summary)
            return
        
        # Process message with Groq
        processed = await process_message_with_groq(message_text)
        
        if not processed.get("is_transaction", False):
            await send_telegram_message(
                chat_id, 
                "🤔 Não identifiquei isso como uma transação financeira.\n\n💡 *Exemplos de transações:*\n• Paguei R$ 100 no supermercado\n• Recebi R$ 1500 de freelance\n\n📊 Para ver seu resumo, digite `resumo`"
            )
            return
        
        # Create transaction
        transaction_data = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "amount": processed["amount"],
            "description": processed["description"],
            "category": processed["category"],
            "type": processed["type"],
            "date": datetime.utcnow(),
            "telegram_message_id": message_id
        }
        
        # Save transaction
        transactions_collection.insert_one(transaction_data)
        
        # Update balance
        update_user_balance(user["id"], processed["amount"], processed["type"])
        
        # Get updated balance
        updated_user = users_collection.find_one({"id": user["id"]})
        new_balance = updated_user["balance"]
        
        # Send confirmation
        type_emoji = "💰" if processed["type"] == "income" else "💸"
        type_text = "Receita" if processed["type"] == "income" else "Despesa"
        
        confirmation = f"""
{type_emoji} *{type_text} registrada!*

💰 *Valor:* R$ {processed['amount']:.2f}
📝 *Descrição:* {processed['description']}
🏷️ *Categoria:* {processed['category']}
💼 *Saldo atual:* R$ {new_balance:.2f}

📊 Veja seus gráficos no painel web!
        """
        
        await send_telegram_message(chat_id, confirmation)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await send_telegram_message(chat_id, "❌ Erro interno. Tente novamente.")

# Web API routes
@app.get("/api/transactions")
async def get_transactions(user_id: Optional[str] = None, limit: int = 50):
    """Get transactions for web dashboard"""
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
            
        transactions = list(transactions_collection.find(query).sort("date", -1).limit(limit))
        
        # Convert ObjectId to string and format data
        for transaction in transactions:
            if "_id" in transaction:
                del transaction["_id"]
            transaction["date"] = transaction["date"].isoformat()
            
        return {"transactions": transactions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/email/{email}")
async def get_dashboard_by_email(email: str):
    """Get dashboard data for specific user by email"""
    try:
        # Get user by email
        user = users_collection.find_one({"email": email})
        if not user:
            return {
                "user": None,
                "balance": 0,
                "transactions": [],
                "categories": {},
                "monthly_summary": {}
            }
        
        user_id = user["id"]
        
        # Get recent transactions
        transactions = list(transactions_collection.find({"user_id": user_id}).sort("date", -1).limit(100))
        
        # Format transactions
        formatted_transactions = []
        for t in transactions:
            if "_id" in t:
                del t["_id"]
            t["date"] = t["date"].isoformat()
            formatted_transactions.append(t)
        
        # Calculate category totals
        categories = {}
        for t in transactions:
            cat = t["category"]
            t_type = t["type"]
            amount = t["amount"]
            
            if cat not in categories:
                categories[cat] = {"income": 0, "expense": 0, "type": t_type}
                
            categories[cat][t_type] += amount
        
        # Calculate monthly summary (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        monthly_transactions = [t for t in transactions if datetime.fromisoformat(t["date"]) > thirty_days_ago]
        
        monthly_income = sum(t["amount"] for t in monthly_transactions if t["type"] == "income")
        monthly_expense = sum(t["amount"] for t in monthly_transactions if t["type"] == "expense")
        
        return {
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user.get("email"),
                "balance": user["balance"]
            },
            "balance": user["balance"],
            "transactions": formatted_transactions,
            "categories": categories,
            "monthly_summary": {
                "income": monthly_income,
                "expense": monthly_expense,
                "net": monthly_income - monthly_expense
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/{telegram_id}")
async def get_dashboard(telegram_id: int):
    """Get dashboard data for specific user (legacy endpoint)"""
    try:
        # Get user
        user = users_collection.find_one({"telegram_id": telegram_id})
        if not user:
            return {
                "user": None,
                "balance": 0,
                "transactions": [],
                "categories": {},
                "monthly_summary": {}
            }
        
        user_id = user["id"]
        
        # Get recent transactions
        transactions = list(transactions_collection.find({"user_id": user_id}).sort("date", -1).limit(100))
        
        # Format transactions
        formatted_transactions = []
        for t in transactions:
            if "_id" in t:
                del t["_id"]
            t["date"] = t["date"].isoformat()
            formatted_transactions.append(t)
        
        # Calculate category totals
        categories = {}
        for t in transactions:
            cat = t["category"]
            t_type = t["type"]
            amount = t["amount"]
            
            if cat not in categories:
                categories[cat] = {"income": 0, "expense": 0, "type": t_type}
                
            categories[cat][t_type] += amount
        
        # Calculate monthly summary (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        monthly_transactions = [t for t in transactions if datetime.fromisoformat(t["date"]) > thirty_days_ago]
        
        monthly_income = sum(t["amount"] for t in monthly_transactions if t["type"] == "income")
        monthly_expense = sum(t["amount"] for t in monthly_transactions if t["type"] == "expense")
        
        return {
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user.get("email"),
                "balance": user["balance"]
            },
            "balance": user["balance"],
            "transactions": formatted_transactions,
            "categories": categories,
            "monthly_summary": {
                "income": monthly_income,
                "expense": monthly_expense,
                "net": monthly_income - monthly_expense
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
async def get_categories():
    """Get all categories"""
    try:
        categories = list(categories_collection.find({}))
        for cat in categories:
            if "_id" in cat:
                del cat["_id"]
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize app
@app.on_event("startup")
async def startup_event():
    await init_categories()
    print("✅ FinanceBot API started successfully")
    print(f"📊 Dashboard: http://localhost:3000")
    print(f"🔗 API: http://localhost:8001")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)