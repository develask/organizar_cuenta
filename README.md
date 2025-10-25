# Organizador de Movimientos Bancarios

Un proyecto personal para gestionar y categorizar mis movimientos bancarios de forma organizada y visual.

## 📋 Descripción

Esta aplicación web me permite importar mis extractos bancarios (archivos Excel) y categorizarlos automáticamente para tener un mejor control de mis finanzas personales. La aplicación está construida con Python y utiliza una base de datos SQLite para almacenar los datos.

## ✨ Características

- **Importación de datos**: Lectura automática de archivos Excel con movimientos bancarios
- **Subida de archivos**: Interfaz web con drag & drop para subir archivos Excel
- **Validación de datos**: Detección automática de duplicados y validación de formato
- **Base de datos**: Almacenamiento persistente con SQLite
- **Categorización**: Sistema de categorías personalizables para organizar gastos
- **Interfaz web**: Interfaz moderna con Bootstrap para visualizar y gestionar movimientos
- **Filtros**: Filtrado por mes y categoría
- **Manejo de errores**: Páginas de error personalizadas y validación robusta

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python, FastAPI
- **Base de datos**: SQLite
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Análisis de datos**: Pandas
- **Procesamiento de archivos**: Pandas para leer archivos Excel

## 📁 Estructura del Proyecto

```
├── app.py                  # Aplicación web principal (FastAPI)
├── database_connection.py  # Clase para manejo de base de datos
├── main.py                # Script principal para inicialización
├── read_file.py           # Utilidades para leer archivos Excel
├── static/                # Archivos estáticos (CSS, JS)
│   ├── css/
│   └── js/
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   └── categories.html
└── movimientos/           # Directorio de datos (gitignored)
```

## 🚀 Instalación y Uso

### Prerrequisitos
- Python 3.8+
- pip

### Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/organizar_cuenta.git
cd organizar_cuenta
```

2. Crea un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install fastapi uvicorn pandas openpyxl sqlite3
```

### Ejecución

1. **Inicializar la base de datos**:
```bash
python main.py
```

2. **Ejecutar la aplicación web**:
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:8000`

### Despliegue con Docker (opcional)

1. Construye la imagen:
   ```bash
   docker build -t organizar_cuenta .
   ```
2. Arranca el contenedor (la web y el MCP HTTP se ejecutan juntos) con volumen persistente para la base de datos:
   ```bash
   docker run -d \
     --name organizar_cuenta \
     -p 8000:8000 \
     -p 8800:8800 \
     -e APP_PORT=8000 \
     -e DATABASE_PATH=/data/movimientos.db \
     -e MCP_TRANSPORT=sse \
     -e MCP_PORT=8800 \
     -e MCP_ALLOWED_ORIGINS=* \
     -v organizar_cuenta_data:/data \
     organizar_cuenta
   ```
3. Alternativamente, usa docker compose:
   ```bash
   docker compose up -d
   ```
   El archivo `docker-compose.yml` expone la web en el puerto 8000, el MCP HTTP en 8800 y monta el volumen `organizar_cuenta_data` para el archivo SQLite.

### MCP expuesto vía HTTP/SSE

El servidor MCP ahora se ofrece mediante HTTP usando SSE, por lo que cualquier cliente compatible puede conectarse a `http://localhost:8800` (o al host/puerto que configures). Variables de entorno relevantes:

- `MCP_TRANSPORT`: por defecto `sse`. Asigna `stdio` si quieres volver al modo anterior.
- `MCP_HOST`: host a enlazar, por defecto `0.0.0.0`.
- `MCP_PORT`: puerto expuesto (8800 por defecto).
- `MCP_ALLOWED_ORIGINS`: lista separada por comas de orígenes permitidos (`*` permite todos).

Exponiendo el puerto 8800 en tu infraestructura podrás acceder al MCP desde internet o limitarlo a tu red privada ajustando estas variables.

## 📋 Instrucciones de Uso

### Subir Archivos Excel

1. **Accede a la página de subida**: Navega a `/upload` o haz clic en "Upload Excel" en la barra de navegación
2. **Prepara tu archivo**: Asegúrate de que tu archivo Excel tenga:
   - Una hoja llamada "Listado"
   - Cabeceras en la fila 6 (índice 5): data, azalpena, balio-data, eragiketaren zenbatekoa, saldoa
   - Datos a partir de la fila 8
3. **Sube el archivo**: Arrastra y suelta el archivo o haz clic para seleccionarlo

### Gestión de Categorías

1. **Crear categorías**: Ve a `/categories` y añade nuevas categorías
2. **Asignar categorías**: En la lista de movimientos, usa "Add Category" para cada transacción
3. **Filtrar por categoría**: Usa los filtros en la página principal

### Formato de Archivo Excel

Tu archivo Excel puede tener cualquiera de estos formatos:

#### Formato Euskera (formato original)
```
Cualquier fila: data | azalpena | balio-data | eragiketaren zenbatekoa | saldoa
```

#### Formato Español (nuevo soporte)
```
Cualquier fila: fecha | concepto | fecha valor | importe | saldo
```

**La aplicación detecta automáticamente:**
- El nombre de la hoja (prefiere "Listado" pero acepta cualquier hoja con datos)
- La fila donde están las cabeceras (busca automáticamente)
- El formato de las columnas (euskera o español)

**Ejemplo de datos:**
- **Fecha**: 2025/06/10 o 10/06/2025
- **Descripción/Concepto**: Descripción del movimiento
- **Fecha valor**: 2025/06/10 o 10/06/2025
- **Importe**: -25.50 (negativo para gastos, positivo para ingresos)
- **Saldo**: 1000.00 (saldo resultante)

## 📊 Funcionalidades

### Gestión de Movimientos
- Visualización de todos los movimientos bancarios
- Información detallada: fecha, descripción, importe, saldo
- Filtrado por mes y categoría

### Sistema de Categorías
- Creación de categorías personalizadas
- Asignación múltiple de categorías por movimiento
- Gestión completa de categorías (crear, eliminar)

### Importación de Datos
- Soporte para archivos Excel (.xls, .xlsx)
- Interfaz drag & drop para subida de archivos
- Procesamiento automático de formato bancario
- Detección y omisión automática de duplicados
- Validación robusta de datos con manejo de errores
- Limpieza y normalización de datos

## 🔒 Privacidad y Seguridad

- Los datos financieros se mantienen localmente
- No se envían datos a servicios externos
- Base de datos SQLite local para máxima privacidad
- Archivos de datos excluidos del control de versiones

## 📝 Notas Personales

Este proyecto surgió de la necesidad de tener un mejor control sobre mis finanzas personales. La categorización automática y la interfaz visual me ayudan a entender mejor mis patrones de gasto y optimizar mi presupuesto.

## 🤝 Contribuciones

Este es un proyecto personal, pero si encuentras algún bug o tienes sugerencias, siéntete libre de abrir un issue.

## 📄 Licencia

Este proyecto es de uso personal. Siéntete libre de usar el código como referencia para tus propios proyectos financieros.
