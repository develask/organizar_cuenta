# Organizador de Movimientos Bancarios

Un proyecto personal para gestionar y categorizar mis movimientos bancarios de forma organizada y visual.

## 📋 Descripción

Esta aplicación web me permite importar mis extractos bancarios (archivos Excel) y categorizarlos automáticamente para tener un mejor control de mis finanzas personales. La aplicación está construida con Python y utiliza una base de datos SQLite para almacenar los datos.

## ✨ Características

- **Importación de datos**: Lectura automática de archivos Excel con movimientos bancarios
- **Base de datos**: Almacenamiento persistente con SQLite
- **Categorización**: Sistema de categorías personalizables para organizar gastos
- **Interfaz web**: Interfaz moderna con Bootstrap para visualizar y gestionar movimientos
- **Filtros**: Filtrado por mes y categoría
- **Análisis**: Jupyter Notebook para análisis de datos con pandas

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python, FastAPI
- **Base de datos**: SQLite
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Análisis de datos**: Pandas, Jupyter Notebook
- **Procesamiento de archivos**: Pandas para leer archivos Excel

## 📁 Estructura del Proyecto

```
├── app.py                  # Aplicación web principal (FastAPI)
├── database_connection.py  # Clase para manejo de base de datos
├── main.py                # Script principal para inicialización
├── read_file.py           # Utilidades para leer archivos Excel
├── movimientos.ipynb      # Notebook para análisis de datos
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

3. **Análisis de datos** (opcional):
```bash
jupyter notebook movimientos.ipynb
```

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
- Soporte para archivos Excel (.xls)
- Procesamiento automático de formato bancario
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