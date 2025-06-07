from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from database_connection import DatabaseConnection
import uvicorn
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Transaction Categorizer")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")

# Pydantic models
class Category(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

class Transaction(BaseModel):
    id: int
    fecha: str
    fecha_valor: str
    descripcion: str
    importe: float
    saldo: float
    categories: List[Category] = []

# Database dependency
def get_db():
    db = DatabaseConnection()
    db.connect()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: DatabaseConnection = Depends(get_db)):
    # Get all transactions
    # Get all transactions with their categories in a single query
    transactions_data = db.execute_query("""
        SELECT 
            m.id, m.fecha, m.fecha_valor, m.descripcion, m.importe, m.saldo,
            c.id as category_id, c.name as category_name, c.description as category_description
        FROM movimientos m
        LEFT JOIN movements_categories mc ON m.id = mc.movement_id
        LEFT JOIN categories c ON mc.category_id = c.id
        ORDER BY m.id, c.id
    """)
    
    # Group transactions and their categories
    transactions_dict = {}
    for row in transactions_data:
        trans_id = row[0]
        if trans_id not in transactions_dict:
            transactions_dict[trans_id] = {
                'id': row[0],
                'fecha': row[1],
                'fecha_valor': row[2],
                'descripcion': row[3],
                'importe': row[4],
                'saldo': row[5],
                'categories': []
            }
        
        # Add category if it exists
        if row[6] is not None:  # category_id
            transactions_dict[trans_id]['categories'].append({
                'id': row[6],
                'name': row[7],
                'description': row[8]
            })
    
    transactions_list = list(transactions_dict.values())
    
    # Get all categories
    categories = db.select('categories')
    categories_list = [{'id': c[0], 'name': c[1], 'description': c[2]} for c in categories]
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "transactions": transactions_list, "categories": categories_list}
    )

@app.get("/categories", response_class=HTMLResponse)
async def list_categories(request: Request, db: DatabaseConnection = Depends(get_db)):
    categories = db.select('categories')
    categories_list = [{'id': c[0], 'name': c[1], 'description': c[2]} for c in categories]
    
    return templates.TemplateResponse(
        "categories.html", 
        {"request": request, "categories": categories_list}
    )

@app.post("/categories")
async def create_category(
    name: str = Form(...),
    description: str = Form(None),
    db: DatabaseConnection = Depends(get_db)
):
    db.insert('categories', {'name': name, 'description': description})
    return RedirectResponse(url="/categories", status_code=303)

@app.post("/categories/{category_id}/delete")
async def delete_category(
    category_id: int,
    db: DatabaseConnection = Depends(get_db)
):
    # First delete from movements_categories
    db.delete('movements_categories', 'category_id = ?', (category_id,))
    # Then delete the category
    db.delete('categories', 'id = ?', (category_id,))
    return RedirectResponse(url="/categories", status_code=303)

@app.post("/transactions/{transaction_id}/categorize")
async def categorize_transaction(
    transaction_id: int,
    category_id: int = Form(...),
    db: DatabaseConnection = Depends(get_db)
):
    # Check if this categorization already exists
    existing = db.select(
        'movements_categories', 
        where='movement_id = ? AND category_id = ?', 
        where_params=(transaction_id, category_id)
    )
    
    if not existing:
        db.insert('movements_categories', {
            'movement_id': transaction_id,
            'category_id': category_id
        })
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/transactions/{transaction_id}/remove-category/{category_id}")
async def remove_category_from_transaction(
    transaction_id: int,
    category_id: int,
    db: DatabaseConnection = Depends(get_db)
):
    db.delete(
        'movements_categories', 
        'movement_id = ? AND category_id = ?', 
        (transaction_id, category_id)
    )
    return RedirectResponse(url="/", status_code=303)

@app.get("/transactions/filter", response_class=HTMLResponse)
async def filter_transactions(
    request: Request,
    month: Optional[str] = None,
    category_id: Optional[int] = None,
    db: DatabaseConnection = Depends(get_db)
):
    query = "SELECT * FROM movimientos WHERE 1=1"
    params = []
    
    if month:
        query += " AND strftime('%m', fecha) = ?"
        params.append(month)
    
    transactions = db.execute_query(query, tuple(params))
    
    transactions_list = []
    for t in transactions:
        transaction = {
            'id': t[0],
            'fecha': t[1],
            'fecha_valor': t[2],
            'descripcion': t[3],
            'importe': t[4],
            'saldo': t[5]
        }
        
        # Get categories for this transaction
        categories = db.execute_query("""
            SELECT c.id, c.name, c.description 
            FROM categories c
            JOIN movements_categories mc ON c.id = mc.category_id
            WHERE mc.movement_id = ?
        """, (transaction['id'],))
        
        transaction['categories'] = [
            {'id': c[0], 'name': c[1], 'description': c[2]} for c in categories
        ]
        
        # Filter by category if specified
        if category_id is not None:
            if any(c['id'] == category_id for c in transaction['categories']):
                transactions_list.append(transaction)
        else:
            transactions_list.append(transaction)
    
    # Get all categories for the dropdown
    categories = db.select('categories')
    categories_list = [{'id': c[0], 'name': c[1], 'description': c[2]} for c in categories]
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "transactions": transactions_list, 
            "categories": categories_list,
            "selected_month": month,
            "selected_category": category_id
        }
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)