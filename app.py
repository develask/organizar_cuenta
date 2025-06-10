from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import HTTPException as StarletteHTTPException
from typing import List, Optional
from database_connection import DatabaseConnection
import uvicorn
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import io
import os

app = FastAPI(title="Transaction Categorizer")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve test file for development
@app.get("/test-ajax", response_class=HTMLResponse)
async def test_ajax(request: Request):
    with open("test_ajax.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)

# Templates directory
templates = Jinja2Templates(directory="templates")

# Custom error handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error_code": 404, "error_message": "Page not found"},
            status_code=404
        )
    elif exc.status_code == 400:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error_code": 400, "error_message": exc.detail},
            status_code=400
        )
    elif exc.status_code == 500:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error_code": 500, "error_message": "Internal server error"},
            status_code=500
        )
    else:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error_code": exc.status_code, "error_message": exc.detail},
            status_code=exc.status_code
        )

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

# Function to process Excel file
def process_excel_file(file_content: bytes):
    """
    Process uploaded Excel file and return DataFrame
    """
    try:
        # Read Excel file from bytes
        df_dict = pd.read_excel(io.BytesIO(file_content), sheet_name=None)
        
        # Try to find the correct sheet
        sheet_name = None
        if 'Listado' in df_dict:
            sheet_name = 'Listado'
        elif len(df_dict) == 1:
            # If there's only one sheet, use it
            sheet_name = list(df_dict.keys())[0]
        else:
            # Try to find a sheet with data
            for name, sheet_df in df_dict.items():
                if not sheet_df.empty:
                    sheet_name = name
                    break
        
        if sheet_name is None:
            raise ValueError("No valid sheet found in the Excel file")
        
        df = df_dict[sheet_name]
        
        # Try different approaches to find the header row
        header_row = None
        
        print(f"Looking for header row in {len(df)} rows...")
        
        # First, try the original approach (row 5 for euskera format)
        if len(df) > 5:
            potential_headers = df.iloc[5]
            headers_str = ' '.join([str(cell).lower() for cell in potential_headers if pd.notna(cell)])
            print(f"Row 5 headers: {headers_str}")
            if any(col in headers_str for col in ['data', 'azalpena', 'balio-data']):
                header_row = 5
                print("Found euskera headers in row 5")
        
        # If not found, look for Spanish headers in the first few rows
        if header_row is None:
            for i in range(min(10, len(df))):  # Check first 10 rows
                row = df.iloc[i]
                row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
                print(f"Row {i}: {row_str}")
                if any(col in row_str for col in ['fecha', 'concepto', 'importe', 'saldo']):
                    header_row = i
                    print(f"Found spanish headers in row {i}")
                    break
        
        if header_row is None:
            raise ValueError("Could not find header row with expected columns")
        
        # Set column names and data
        columns = df.iloc[header_row]
        df.columns = columns
        df = df.iloc[header_row + 1:]
        
        # Remove rows with all NaN values
        df = df.dropna(how='all')
        
        # Reset the index
        df.reset_index(drop=True, inplace=True)
        
        # Validate that we have the minimum required columns and determine format
        required_columns_euskera = ['data', 'azalpena', 'balio-data', 'eragiketaren zenbatekoa', 'saldoa']
        required_columns_spanish = ['fecha', 'concepto', 'fecha valor', 'importe', 'saldo']
        
        # Get column names as strings
        column_names = [str(col).lower() for col in df.columns if pd.notna(col)]
        print(f"Final column names: {column_names}")
        
        # Check which format we have
        has_euskera = all(req_col.lower() in column_names for req_col in required_columns_euskera)
        has_spanish = all(req_col.lower() in column_names for req_col in required_columns_spanish)
        
        print(f"Has euskera columns: {has_euskera}")
        print(f"Has spanish columns: {has_spanish}")
        
        if not has_euskera and not has_spanish:
            available_cols = [str(col) for col in df.columns if pd.notna(col)]
            raise ValueError(f"Missing expected columns. Found columns: {', '.join(available_cols)}")
        
        # Validate we have data rows
        if len(df) == 0:
            raise ValueError("No data rows found in the Excel file after processing")
        
        format_type = 'euskera' if has_euskera else 'spanish'
        print(f"Detected format: {format_type}")
        
        return df, format_type
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        raise ValueError(f"Error processing Excel file: {str(e)}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, month: Optional[str]= None, category_id: Optional[int] = None, db: DatabaseConnection = Depends(get_db)):
    # Get all transactions
    # Get all transactions with their categories in a single query
    query ="""
        SELECT 
            m.id, m.fecha, m.fecha_valor, m.descripcion, m.importe, m.saldo,
            c.id as category_id, c.name as category_name, c.description as category_description
        FROM movimientos m
        LEFT JOIN movements_categories mc ON m.id = mc.movement_id
        LEFT JOIN categories c ON mc.category_id = c.id
    """

    where_clauses = []
    where_params = []
    if month:
        where_clauses.append("strftime('%Y-%m', m.fecha) = ?")
        where_params.append(month)
    if category_id and category_id > 0:
        where_clauses.append("c.id = ?")
        where_params.append(category_id)
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
        query += " GROUP BY m.id, c.id"
    query += " ORDER BY m.id, c.id"
    
    transactions_data = db.execute_query(query, where_params)

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
        {"request": request, "transactions": transactions_list, "categories": categories_list, "current_year": datetime.now().year, "month": month, "category_id": category_id}
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

@app.post("/api/transactions/{transaction_id}/categorize")
async def categorize_transaction_ajax(
    transaction_id: int,
    category_id: int = Form(...),
    db: DatabaseConnection = Depends(get_db)
):
    try:
        # Check if this categorization already exists
        existing = db.select(
            'movements_categories', 
            where='movement_id = ? AND category_id = ?', 
            where_params=(transaction_id, category_id)
        )
        
        if existing:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Category already assigned to this transaction"}
            )
        
        # Insert the new categorization
        db.insert('movements_categories', {
            'movement_id': transaction_id,
            'category_id': category_id
        })
        
        # Get the category details to return
        category = db.select(
            'categories',
            where='id = ?',
            where_params=(category_id,)
        )
        
        if category:
            category_data = {
                'id': category[0][0],
                'name': category[0][1],
                'description': category[0][2]
            }
            
            return JSONResponse(content={
                "success": True,
                "message": "Category added successfully",
                "category": category_data
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Category not found"}
            )
            
    except Exception as e:
        print(f"Error categorizing transaction: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error"}
        )

@app.post("/api/transactions/{transaction_id}/remove-category/{category_id}")
async def remove_category_from_transaction_ajax(
    transaction_id: int,
    category_id: int,
    db: DatabaseConnection = Depends(get_db)
):
    try:
        # Remove the categorization
        rows_affected = db.delete(
            'movements_categories', 
            'movement_id = ? AND category_id = ?', 
            (transaction_id, category_id)
        )
        
        if rows_affected > 0:
            return JSONResponse(content={
                "success": True,
                "message": "Category removed successfully"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Category assignment not found"}
            )
            
    except Exception as e:
        print(f"Error removing category: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error"}
        )

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html", 
        {"request": request}
    )

@app.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    db: DatabaseConnection = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xls, .xlsx) are allowed")
    
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    try:
        # Read file content
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size too large. Maximum allowed size is 10MB")
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Process Excel file
        df, format_type = process_excel_file(content)
        
        # Insert data into database
        inserted_count = 0
        duplicate_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Clean and validate data based on format
                if format_type == 'euskera':
                    fecha = str(row['data']).replace('/', '-') if pd.notna(row['data']) else None
                    fecha_valor = str(row['balio-data']).replace('/', '-') if pd.notna(row['balio-data']) else None
                    descripcion = str(row['azalpena']).strip() if pd.notna(row['azalpena']) else None
                    importe_col = 'eragiketaren zenbatekoa'
                    saldo_col = 'saldoa'
                else:  # spanish format
                    # Handle Spanish date format (DD/MM/YYYY) and convert to YYYY-MM-DD
                    fecha_raw = str(row['fecha']) if pd.notna(row['fecha']) else None
                    fecha_valor_raw = str(row['fecha valor']) if pd.notna(row['fecha valor']) else None
                    
                    # Convert DD/MM/YYYY to YYYY-MM-DD
                    fecha = None
                    fecha_valor = None
                    
                    if fecha_raw and fecha_raw != 'nan':
                        try:
                            # Try to parse DD/MM/YYYY format
                            if '/' in fecha_raw:
                                parts = fecha_raw.split('/')
                                if len(parts) == 3:
                                    day, month, year = parts
                                    fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        except:
                            fecha = fecha_raw.replace('/', '-')
                    
                    if fecha_valor_raw and fecha_valor_raw != 'nan':
                        try:
                            # Try to parse DD/MM/YYYY format
                            if '/' in fecha_valor_raw:
                                parts = fecha_valor_raw.split('/')
                                if len(parts) == 3:
                                    day, month, year = parts
                                    fecha_valor = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        except:
                            fecha_valor = fecha_valor_raw.replace('/', '-')
                    
                    descripcion = str(row['concepto']).strip() if pd.notna(row['concepto']) else None
                    importe_col = 'importe'
                    saldo_col = 'saldo'
                
                # Convert amounts to float, handling different formats
                try:
                    importe = float(str(row[importe_col]).replace(',', '.')) if pd.notna(row[importe_col]) else 0.0
                    saldo = float(str(row[saldo_col]).replace(',', '.')) if pd.notna(row[saldo_col]) else 0.0
                except (ValueError, TypeError):
                    print(f"Error converting amounts in row {index + 1}: importe={row[importe_col]}, saldo={row[saldo_col]}")
                    error_count += 1
                    continue
                
                # Skip rows with invalid data
                if not fecha or not descripcion:
                    print(f"Skipping row {index + 1}: missing required data")
                    error_count += 1
                    continue
                
                # Check if movement already exists (by fecha, descripcion, and importe)
                existing = db.select(
                    'movimientos',
                    where='fecha = ? AND descripcion = ? AND importe = ? and saldo = ?',
                    where_params=(fecha, descripcion, importe, saldo)
                )
                
                if not existing:
                    # Insert new movement
                    movement_data = {
                        'fecha': fecha,
                        'fecha_valor': fecha_valor,
                        'descripcion': descripcion,
                        'importe': importe,
                        'saldo': saldo
                    }
                    
                    db.insert('movimientos', movement_data)
                    inserted_count += 1
                else:
                    print(f"Duplicate found in row {index + 1}: {fecha} | {descripcion} | {importe}")
                    duplicate_count += 1
                    
            except Exception as row_error:
                print(f"Error processing row {index + 1}: {row_error}")
                error_count += 1
                continue
        
        # Build success message
        success_params = f"upload_success=true&inserted={inserted_count}&duplicates={duplicate_count}"
        if error_count > 0:
            success_params += f"&errors={error_count}"
        
        # Redirect with success message
        return RedirectResponse(
            url=f"/?{success_params}", 
            status_code=303
        )
        
    except ValueError as e:
        # Handle processing errors
        error_msg = str(e).replace("Error processing Excel file: ", "")
        raise HTTPException(status_code=400, detail=f"File processing error: {error_msg}")
    except Exception as e:
        print(f"Unexpected error uploading file: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the file")

@app.get("/download-template")
async def download_template():
    """Download an Excel template file"""
    try:
        # Create a sample DataFrame with the correct structure
        sample_data = {
            'data': ['2025/06/10', '2025/06/11', '2025/06/12'],
            'azalpena': ['Sample transaction 1', 'Sample transaction 2', 'Sample transaction 3'],
            'balio-data': ['2025/06/10', '2025/06/11', '2025/06/12'],
            'eragiketaren zenbatekoa': [-25.50, 100.00, -12.30],
            'saldoa': [1000.00, 1100.00, 1087.70]
        }
        
        # Create DataFrame
        df = pd.DataFrame(sample_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        # Create a workbook with proper structure
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Create empty rows for the header structure
            empty_df = pd.DataFrame([[None] * 5] * 5)  # 5 empty rows
            empty_df.to_excel(writer, sheet_name='Listado', index=False, header=False, startrow=0)
            
            # Add the column headers in row 6 (index 5)
            header_df = pd.DataFrame([['data', 'azalpena', 'balio-data', 'eragiketaren zenbatekoa', 'saldoa']])
            header_df.to_excel(writer, sheet_name='Listado', index=False, header=False, startrow=5)
            
            # Add an empty row
            empty_row = pd.DataFrame([[None] * 5])
            empty_row.to_excel(writer, sheet_name='Listado', index=False, header=False, startrow=6)
            
            # Add sample data starting from row 8 (index 7)
            df.to_excel(writer, sheet_name='Listado', index=False, header=False, startrow=7)
        
        output.seek(0)
        
        # Return the file
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename="movimientos_template.xlsx"'}
        )
        
    except Exception as e:
        print(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Error creating template file")

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)