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

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'financial_bot')
TELEGRAM_BOT_TOKEN = "8373321103:AAFbHiYeac2GcHyt2PABJcbSKJZYLE5qgEg"
GROQ_API_KEY = "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"

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
transactions_collection = db.transactions
users_collection = db.users
categories_collection = db.categories

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
    
    system_prompt = """
    Você é um assistente especializado em extrair informações financeiras de mensagens em português.
    Extraia as seguintes informações da mensagem do usuário:
    - amount: valor numérico (apenas números, sem R$ ou símbolos)
    - type: "income" para receitas ou "expense" para gastos/despesas
    - description: descrição curta da transação
    - category: categoria mais apropriada (escolha entre as opções fornecidas)
    
    Categorias de despesa: Alimentação, Transporte, Moradia, Saúde, Educação, Entretenimento, Roupas, Tecnologia, Impostos, Outros
    Categorias de receita: Salário, Freelance, Investimentos, Vendas, Presentes, Outros
    
    Responda APENAS em formato JSON válido:
    {"amount": 0.0, "type": "expense|income", "description": "...", "category": "..."}
    
    Exemplos:
    "Paguei R$ 500 de aluguel" -> {"amount": 500.0, "type": "expense", "description": "aluguel", "category": "Moradia"}
    "Recebi R$ 2000 de salário" -> {"amount": 2000.0, "type": "income", "description": "salário", "category": "Salário"}
    "Gastei 50 no supermercado" -> {"amount": 50.0, "type": "expense", "description": "supermercado", "category": "Alimentação"}
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
                    "max_tokens": 150
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            else:
                print(f"Groq API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"Error processing with Groq: {e}")
        return None

# Helper functions
def get_or_create_user(telegram_user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get existing user or create new one"""
    telegram_id = telegram_user_data["id"]
    
    user = users_collection.find_one({"telegram_id": telegram_id})
    if not user:
        user_data = {
            "id": str(uuid.uuid4()),
            "telegram_id": telegram_id,
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

async def send_telegram_message(chat_id: int, text: str):
    """Send message to Telegram user"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# API Routes

@app.get("/")
async def root():
    return {"message": "Financial Bot API is running"}

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
        
        # Skip commands
        if message_text.startswith('/'):
            if message_text == '/start':
                welcome_text = """
🤖 <b>Bem-vindo ao Bot de Gestão Financeira!</b>

📝 <b>Como usar:</b>
• Digite suas transações em linguagem natural
• Exemplo: "Paguei R$ 500 de aluguel"
• Exemplo: "Recebi R$ 2000 de salário"
• Exemplo: "Gastei 50 no supermercado"

📊 Veja seus gráficos e relatórios no painel web!

💡 <b>Dica:</b> Seja específico nas descrições para melhor categorização automática.
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
        
        # Process message with Groq
        processed = await process_message_with_groq(message_text)
        
        if not processed:
            await send_telegram_message(
                chat_id, 
                "❌ Não consegui entender sua mensagem. Tente algo como:\n'Paguei R$ 100 no supermercado' ou 'Recebi R$ 1500 de freelance'"
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
{type_emoji} <b>{type_text} registrada!</b>

💰 <b>Valor:</b> R$ {processed['amount']:.2f}
📝 <b>Descrição:</b> {processed['description']}
🏷️ <b>Categoria:</b> {processed['category']}
💼 <b>Saldo atual:</b> R$ {new_balance:.2f}

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

@app.get("/api/dashboard/{telegram_id}")
async def get_dashboard(telegram_id: int):
    """Get dashboard data for specific user"""
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
    print("✅ Financial Bot API started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)