from typing import Any, Optional
import sys
import os

# Add project root (/Users/mikel/projects/organizar_cuenta) to the Python path to allow importing database_connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Move working directory to the project root
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))




from database_connection import DatabaseConnection
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cuentas")

def get_db_connection():
    """Creates and returns a database connection, and connects."""
    db = DatabaseConnection()
    db.connect()
    return db

@mcp.tool()
def get_transactions(month: Optional[str] = None, category_id: Optional[int] = None) -> Any:
    """
    Obtiene las transacciones, opcionalmente filtradas por mes (formato 'YYYY-MM') y/o ID de categoría.
    Esta función replica la lógica de consulta de la ruta principal de la aplicación web.
    :param month: El mes para filtrar las transacciones (ej. '2025-07').
    :param category_id: El ID de la categoría para filtrar las transacciones.
    :return: Una lista de transacciones con sus categorías.
    """
    db = get_db_connection()
    try:
        query = """
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
            # This GROUP BY is in the original app.py logic inside the if-clause
            query += " GROUP BY m.id, c.id"

        query += " ORDER BY m.fecha DESC, m.id DESC"

        transactions_data = db.execute_query(query, where_params)

        transactions_dict = {}
        for row in transactions_data:
            trans_id = row[0]
            if trans_id not in transactions_dict:
                transactions_dict[trans_id] = {
                    'id': row[0], 'fecha': row[1], 'fecha_valor': row[2],
                    'descripcion': row[3], 'importe': row[4], 'saldo': row[5],
                    'categories': []
                }
            if row[6] is not None:
                transactions_dict[trans_id]['categories'].append({
                    'id': row[6], 'name': row[7], 'description': row[8]
                })
        return list(transactions_dict.values())
    finally:
        db.close()

@mcp.tool()
def get_categories() -> Any:
    """
    Obtiene una lista de todas las categorías, ordenadas por nombre.
    :return: Una lista de diccionarios, cada uno representando una categoría.
    """
    db = get_db_connection()
    try:
        categories = db.select('categories')
        categories_list = [{'id': c[0], 'name': c[1], 'description': c[2]} for c in categories]
        categories_list.sort(key=lambda c: c['name'].lower())
        return categories_list
    finally:
        db.close()

@mcp.tool()
def create_category(name: str, description: Optional[str] = None) -> Any:
    """
    Crea una nueva categoría.
    :param name: El nombre de la nueva categoría.
    :param description: La descripción opcional de la categoría.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        db.insert('categories', {'name': name, 'description': description})
        return {"success": True, "message": f"Categoría '{name}' creada exitosamente."}
    finally:
        db.close()

@mcp.tool()
def update_category(category_id: int, name: str, description: Optional[str] = None) -> Any:
    """
    Actualiza una categoría existente.
    :param category_id: El ID de la categoría a actualizar.
    :param name: El nuevo nombre para la categoría.
    :param description: La nueva descripción para la categoría.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        db.update(
            'categories',
            {'name': name, 'description': description},
            'id = ?',
            (category_id,)
        )
        return {"success": True, "message": f"Categoría con ID {category_id} actualizada."}
    finally:
        db.close()

@mcp.tool()
def delete_category(category_id: int) -> Any:
    """
    Elimina una categoría y sus asignaciones a transacciones.
    :param category_id: El ID de la categoría a eliminar.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        db.delete('movements_categories', 'category_id = ?', (category_id,))
        db.delete('categories', 'id = ?', (category_id,))
        return {"success": True, "message": f"Categoría con ID {category_id} eliminada."}
    finally:
        db.close()

@mcp.tool()
def assign_category_to_transaction(transaction_id: int, category_id: int) -> Any:
    """
    Asigna una categoría a una transacción.
    :param transaction_id: El ID de la transacción.
    :param category_id: El ID de la categoría a asignar.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        existing = db.select(
            'movements_categories',
            where='movement_id = ? AND category_id = ?',
            where_params=(transaction_id, category_id)
        )
        if existing:
            return {"success": False, "message": "La categoría ya está asignada a esta transacción."}

        db.insert('movements_categories', {
            'movement_id': transaction_id,
            'category_id': category_id
        })
        return {"success": True, "message": "Categoría asignada exitosamente."}
    finally:
        db.close()

@mcp.tool()
def remove_category_from_transaction(transaction_id: int, category_id: int) -> Any:
    """
    Elimina la asignación de una categoría a una transacción.
    :param transaction_id: El ID de la transacción.
    :param category_id: El ID de la categoría a eliminar de la transacción.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        rows_affected = db.delete(
            'movements_categories',
            'movement_id = ? AND category_id = ?',
            (transaction_id, category_id)
        )
        if rows_affected > 0:
            return {"success": True, "message": "Categoría eliminada de la transacción."}
        else:
            return {"success": False, "message": "No se encontró la asignación de categoría."}
    finally:
        db.close()

if __name__ == "__main__":
    mcp.run(transport='stdio')
