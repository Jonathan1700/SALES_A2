# SALES_A2

Proyecto Django para gestión de ventas.

## Cómo ejecutar el proyecto

### 1. Clonar el repositorio

```cmd
git clone https://github.com/Jonathan1700/SALES_A2.git
cd SALES_A2/Sales_A2
```

### 2. Crear el entorno virtual

```cmd
py -m venv ent_sales_A2
```

> Si `py` no funciona, usa `python` en su lugar.

### 3. Activar el entorno virtual

```cmd
ent_sales_A2\Scripts\activate.bat
```

### 4. Instalar las dependencias

```cmd
pip install -r requirements.txt
```

### 5. Aplicar las migraciones

```cmd
ent_sales_A2\Scripts\python.exe manage.py migrate
```

### 6. Ejecutar el servidor

```cmd
ent_sales_A2\Scripts\python.exe manage.py runserver
```

Abre el navegador en: http://127.0.0.1:8000
