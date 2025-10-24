from typing import Any, Optional
import sys
import os
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))



from database_connection import DatabaseConnection
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("cuentas")

def get_db_connection():
    """Creates and returns a database connection, and connects."""
    db = DatabaseConnection()
    db.connect()
    return db

@mcp.tool()
def get_transactions(month: str = None, category_id: Optional[int] = None) -> Any:
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
def get_category_report(month: str = None) -> Any:
    """
    Obtiene un informe de transacciones por categoría, opcionalmente filtrado por mes (formato 'YYYY-MM').
    :param month: El mes para filtrar las transacciones (ej. '2025-07').
    :return: Un diccionario con el total por categoría.
    """
    db = get_db_connection()
    try:
        query = """
            SELECT
                c.id, c.name, SUM(m.importe) as total
            FROM movimientos m
            LEFT JOIN movements_categories mc ON m.id = mc.movement_id
            LEFT JOIN categories c ON mc.category_id = c.id
        """
        where_clauses = []
        where_params = []
        if month:
            where_clauses.append("strftime('%Y-%m', m.fecha) = ?")
            where_params.append(month)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " GROUP BY c.id ORDER BY c.name"

        categories_data = db.execute_query(query, where_params)
        return [{'id': row[0], 'name': row[1], 'total': row[2]} for row in categories_data]
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
def assign_category_to_transactions(transaction_ids: list[int], category_id: int) -> Any:
    """
    Asigna una categoría a una o varias transacciones.
    :param transaction_ids: La lista de IDs de las transacciones.
    :param category_id: El ID de la categoría a asignar.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        # Evitar duplicados: obtener las asignaciones existentes
        placeholders = ','.join(['?'] * len(transaction_ids))
        query = f"""SELECT movement_id FROM movements_categories 
                   WHERE movement_id IN ({placeholders}) AND category_id = ?"""
        existing = db.execute_query(query, transaction_ids + [category_id])
        existing_ids = {row[0] for row in existing}

        # Filtrar las transacciones que ya tienen la categoría asignada
        new_transaction_ids = [tid for tid in transaction_ids if tid not in existing_ids]

        if not new_transaction_ids:
            return {"success": False, "message": "La categoría ya está asignada a todas las transacciones seleccionadas."}

        # Insertar las nuevas asignaciones
        for transaction_id in new_transaction_ids:
            db.insert('movements_categories', {
                'movement_id': transaction_id,
                'category_id': category_id
            })
        
        return {"success": True, "message": f"Categoría asignada a {len(new_transaction_ids)} transacciones."}
    finally:
        db.close()

@mcp.tool()
def remove_category_from_transactions(transaction_ids: list[int], category_id: int) -> Any:
    """
    Elimina la asignación de una categoría a una o varias transacciones.
    :param transaction_ids: La lista de IDs de las transacciones.
    :param category_id: El ID de la categoría a eliminar de las transacciones.
    :return: Un diccionario con el resultado de la operación.
    """
    db = get_db_connection()
    try:
        placeholders = ','.join(['?'] * len(transaction_ids))
        where_clause = f"movement_id IN ({placeholders}) AND category_id = ?"
        params = transaction_ids + [category_id]
        
        rows_affected = db.delete(
            'movements_categories',
            where_clause,
            params
        )
        
        if rows_affected > 0:
            return {"success": True, "message": f"Categoría eliminada de {rows_affected} transacciones."}
        else:
            return {"success": False, "message": "No se encontró la asignación de categoría en las transacciones seleccionadas."}
    finally:
        db.close()

@mcp.tool()
def find_similar_transactions(description: str, amount: float, date: str, threshold: float = 0.8, top_k: Optional[int] = None) -> Any:
    """
    Encuentra transacciones similares basadas en la descripción, el importe y la fecha.
    Busca transacciones en el último año con descripciones y valores similares.
    También considera la similitud en el día de la semana, el día del mes y el día del año.

    :param description: La descripción de la transacción a comparar.
    :param amount: El importe de la transacción a comparar.
    :param date: La fecha de la transacción a comparar (formato 'YYYY-MM-DD').
    :param threshold: El umbral de similitud para la descripción (default: 0.8). No se tiene en cuenta con top_k.
    :param top_k: Numero de transacciones a devolver (opcional, si se especifica, limita el número de resultados).
    :return: Una lista de transacciones similares con sus categorías.
    """
    db = get_db_connection()
    try:
        # Obtener todas las transacciones del último año con sus categorías
        query = """
            SELECT
                m.id, m.fecha, m.descripcion, m.importe,
                c.id as category_id, c.name as category_name
            FROM movimientos m
            LEFT JOIN movements_categories mc ON m.id = mc.movement_id
            LEFT JOIN categories c ON mc.category_id = c.id
            WHERE m.fecha BETWEEN date(?, '-1 year') AND ?
        """
        transactions_data = db.execute_query(query, (date, date))

        # Agrupar transacciones y sus categorías
        transactions_dict = {}
        for row in transactions_data:
            trans_id = row[0]
            if trans_id not in transactions_dict:
                transactions_dict[trans_id] = {
                    'id': row[0],
                    'fecha': row[1],
                    'descripcion': row[2],
                    'importe': row[3],
                    'categories': []
                }
            if row[4] is not None:
                transactions_dict[trans_id]['categories'].append({
                    'id': row[4],
                    'name': row[5]
                })

        transactions = list(transactions_dict.values())
        
        similar_transactions = []
        for trans in transactions:
            # Calcular la similitud de la descripción
            desc_similarity = SequenceMatcher(None, description.lower(), trans['descripcion'].lower()).ratio()

            # Calcular la similitud del importe
            amount_similarity = 1 - abs(amount - trans['importe']) / max(abs(amount), abs(trans['importe']))

            # Calcular la similitud de la fecha
            trans_date = datetime.strptime(trans['fecha'], '%Y-%m-%d')
            search_date = datetime.strptime(date, '%Y-%m-%d')
            
            day_of_week_similarity = 1 if trans_date.weekday() == search_date.weekday() else 0
            day_of_month_similarity = 1 - abs(trans_date.day - search_date.day) / 30
            day_of_year_similarity = 1 - abs(trans_date.timetuple().tm_yday - search_date.timetuple().tm_yday) / 365
            
            date_similarity = (day_of_week_similarity + day_of_month_similarity + day_of_year_similarity) / 3

            # Calcular la puntuación de similitud total
            total_similarity = (desc_similarity + amount_similarity + date_similarity) / 3

            trans['similarity'] = total_similarity
            similar_transactions.append(trans)

        # Ordenar por similitud descendente
        similar_transactions.sort(key=lambda x: x['similarity'], reverse=True)

        if top_k is not None:
            similar_transactions = similar_transactions[:int(top_k)]
        else:
            similar_transactions = [x for x in similar_transactions if x['similarity'] >= threshold]

        return similar_transactions
    finally:
        db.close()

if __name__ == "__main__":
    mcp.run(transport='stdio')
