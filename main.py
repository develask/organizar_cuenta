from database_connection import DatabaseConnection
from read_file import read_file




# with DatabaseConnection() as db:
#     movimientos_file = 'movimientos/movimientos.xls'
#     df = read_file(movimientos_file)
    
#     if df is not None:
#         # Insert data into the database
#         for index, row in df['Listado'].iterrows():
#             insert_query = """
#             INSERT INTO movimientos (fecha, fecha_valor, descripcion, importe, saldo)
#             VALUES (?, ?, ?, ?, ?);
#             """
#             db.insert('movimientos', {
#                 'fecha': row['data'].replace('/', '-'),
#                 'fecha_valor': row['balio-data'].replace('/', '-'),
#                 'descripcion': row['azalpena'],
#                 'importe': row['eragiketaren zenbatekoa'],
#                 'saldo': row['saldoa']
#             })
        
#         db.commit()
#         print("Movements data inserted successfully.")
#     else:
#         print("Failed to read the file.")

with DatabaseConnection() as db:
    # ver movimentos de marzo
    for movement in db.select('movimientos',
                                where="strftime('%m', fecha) = ?",
                                where_params=('03',)):
        print(dict(movement))