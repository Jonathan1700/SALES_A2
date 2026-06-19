# SALES_A2

Proyecto Django para gestión de ventas.

## Funcionalidades

Gestión de marcas, grupos, proveedores, productos, clientes y facturas. Además, el listado de **Productos** incluye:

### Búsqueda y filtros por columna

El listado de productos permite filtrar por cada columna de la consulta, con el control adecuado según el tipo de dato:

| Columna     | Control                        |
|-------------|--------------------------------|
| Nombre      | Texto (búsqueda parcial)       |
| Marca       | Lista desplegable              |
| Grupo       | Lista desplegable              |
| Proveedor   | Lista desplegable              |
| Estado      | Lista (Todos / Activo / Inactivo) |
| Precio      | Rango numérico (mín / máx)     |
| Stock       | Rango numérico (mín / máx)     |

Los botones **Buscar** y **Limpiar** aplican o reinician los filtros.

### Paginación

Los resultados se paginan (configurable con `paginate_by` en la vista). La navegación conserva los filtros activos al cambiar de página.

### Exportación a PDF y Excel

Cada listado puede exportar **los registros filtrados** (no solo la página actual) mediante los botones **Listado PDF** y **Listado Excel**.

La lógica está centralizada en un mixin genérico reutilizable: [`ExportListMixin`](Sales_A2/billing/mixins.py). Para habilitar la exportación en cualquier `ListView` basta con heredar del mixin y declarar las columnas:

```python
from .mixins import ExportListMixin

class ProductListView(ExportListMixin, LoginRequiredMixin, ListView):
    export_title = 'Productos'
    export_fields = [
        ('Nombre', 'name'),                 # atributo simple
        ('Marca', 'brand.name'),            # atributo anidado
        ('Precio', lambda o: f'{o.unit_price:.2f}'),  # callable
        ('Estado', lambda o: 'Activo' if o.is_active else 'Inactivo'),
    ]
```

Luego se añaden los botones en la plantilla apuntando a `?<filtros>&export=pdf` o `?<filtros>&export=excel`.

> Requiere las dependencias `openpyxl` (Excel) y `reportlab` (PDF), incluidas en `requirements.txt`.

### Imagen del producto y página de detalle

Cada producto puede tener una **imagen**, que se muestra en el listado y en una nueva página de detalle.

**1. Modelo** — se añadió el campo `image` al modelo `Product` ([models.py](Sales_A2/billing/models.py)):

```python
image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Imagen')
```

- `upload_to='products/'`: las imágenes subidas se guardan en `media/products/`.
- `blank=True, null=True`: la imagen es **opcional**; un producto puede no tener imagen.
- Requiere la librería **Pillow** (ya incluida en `requirements.txt`).

**2. Archivos media (configuración)** — para que Django guarde y muestre las imágenes subidas ([settings.py](Sales_A2/config/settings.py)):

```python
MEDIA_URL = '/media/'              # URL pública desde la que se sirven las imágenes
MEDIA_ROOT = BASE_DIR / 'media'    # carpeta física donde se guardan los archivos
```

Y en [config/urls.py](Sales_A2/config/urls.py) se sirven esos archivos en modo desarrollo (`DEBUG=True`):

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

> El formulario de producto ([product_form.html](Sales_A2/billing/templates/billing/product_form.html)) usa `enctype="multipart/form-data"`, obligatorio para poder **subir archivos**. El campo `image` se añadió al `ProductForm` ([forms.py](Sales_A2/billing/forms.py)).

**3. Columna "Imagen" en el listado** ([product_list.html](Sales_A2/billing/templates/billing/product_list.html)):

- Nueva columna que muestra una **miniatura** (48×48 px) de cada producto.
- Si el producto no tiene imagen, muestra un texto amigable **"Sin imagen"**.

**4. Botón "Ver detalle"** — cada fila del listado tiene un botón que abre la página de detalle del producto seleccionado.

**5. Página de detalle** ([product_detail.html](Sales_A2/billing/templates/billing/product_detail.html), vista `ProductDetailView` en [views.py](Sales_A2/billing/views.py), ruta `products/<id>/`):

- Diseño **responsivo de dos columnas** con Bootstrap:
  - **Izquierda:** imagen del producto centrada y a buen tamaño (placeholder si no hay imagen).
  - **Derecha:** todos los datos del producto (marca, grupo, precio, stock, proveedores, estado, fechas) con etiquetas claras.
- Tarjeta (`card`) con **sombra suave**, espaciado cómodo y estilo tipo panel administrativo.
- Botones para **Editar** y **Regresar** al listado.
- Se adapta a **dispositivos móviles** (las dos columnas se apilan en pantallas pequeñas).

> Como se agregó un campo nuevo al modelo, hay que aplicar migraciones (ver el paso 5 de la siguiente sección). La carpeta `media/` se crea automáticamente al subir la primera imagen.

### Columnas visibles personalizables (listado + exportaciones)

El usuario puede elegir **qué columnas ver** en el listado de productos, y esa misma selección se respeta en las exportaciones a PDF y Excel. Todo parte de **una única fuente de configuración** para no duplicar lógica.

**1. Única fuente de columnas** — definida en `ProductListView` ([views.py](Sales_A2/billing/views.py)) como `COLUMN_DEFS`: una lista de `(key, etiqueta, accessor)`. La tabla HTML, el PDF y el Excel leen de aquí, así que **siempre muestran y exportan exactamente la misma información**.

```python
COLUMN_DEFS = [
    ('image',      'Imagen',         lambda o: 'Con imagen' if o.image else 'Sin imagen'),
    ('name',       'Nombre',         'name'),
    ('description','Descripción',    lambda o: o.description or '-'),
    ('brand',      'Marca',          'brand.name'),
    # ... precio, stock, proveedores, estado, fecha creación
]
DEFAULT_COLUMNS = ['image', 'name', 'brand', 'group', 'price', 'stock', 'suppliers', 'is_active']
```

**2. Botón "Seleccionar columnas"** — en el listado abre un **modal** Bootstrap con un checklist (varias columnas en pantallas grandes, responsive). Incluye:

- **Aplicar:** guarda la selección y recarga la tabla.
- **Restablecer configuración:** vuelve a las columnas por defecto.
- **Seleccionar todo** (alterna marcar / quitar todo).
- Contador en vivo: *"Mostrando X de Y columnas"*.
- **Mínimo obligatorio de 1 columna** (validado en el navegador *y* en el servidor).

**3. Persistencia (sesión)** — la selección se guarda en `request.session` (clave `product_visible_columns`). Por eso se recuerda mientras el usuario navega por el módulo, y las exportaciones (que son peticiones aparte) usan exactamente las mismas columnas. El método `get_visible_columns()` es la fuente de verdad; `get_export_fields()` la reutiliza para el PDF/Excel.

**4. Exportaciones adaptativas** — la lógica vive en [`ExportListMixin`](Sales_A2/billing/mixins.py):

- **PDF:** se genera **solo con las columnas visibles**. Se adapta automáticamente:
  - pocas columnas → página **vertical** y tabla **centrada**;
  - muchas columnas → **horizontal (landscape)**, **fuente más pequeña** y **ancho de columna proporcional** que reparte el espacio disponible.
- **Excel:** exporta las **mismas columnas, en el mismo orden**, con **ancho automático** y encabezados con formato profesional.

**5. Imagen por defecto** — cuando un producto no tiene imagen, el listado muestra un **placeholder** ([no-image.svg](Sales_A2/billing/static/billing/img/no-image.svg)) en vez de un hueco vacío.

> Los filtros de búsqueda activos se conservan al aplicar columnas y al exportar.

### Formulario de producto mejorado (crear / editar)

`ProductCreateView` y `ProductUpdateView` comparten un **único** formulario `ProductForm` ([forms.py](Sales_A2/billing/forms.py)). Toda la configuración (widgets, estilos, ayudas, validación) vive en el formulario, **no en las vistas** — sin duplicar lógica entre crear y editar.

**Formulario centralizado** — `ProductForm` define para cada campo: widget Bootstrap, `placeholder`, `help_text`, clases consistentes y `error_messages` amigables.

**Validación de `unit_price`** — en servidor con `clean_unit_price()`:

```python
def clean_unit_price(self):
    price = self.cleaned_data.get('unit_price')
    if price is not None and price <= 0:
        raise forms.ValidationError('El precio unitario debe ser mayor que cero.')
    return price
```

- Rechaza `0`, negativos y texto; acepta `1`, `10.50`, `999.99`.
- En el frontend: `min="0.01"` + validación inmediata (marca el campo y muestra el mensaje sin esperar a guardar).

**Diseño dos columnas** ([product_form.html](Sales_A2/billing/templates/billing/product_form.html)) tipo panel administrativo:

- **Izquierda — Información:** nombre, marca, grupo, precio, stock, proveedores, descripción, estado.
- **Derecha — Imagen y resumen:** selector de imagen, **vista previa** y **balance** calculado.
- Cards con sombra suave, espaciado uniforme, responsive.

**Vista previa de imagen** — al seleccionar un archivo se muestra de inmediato (con `URL.createObjectURL`). En edición se ve la imagen actual y se actualiza al reemplazarla. Si no hay imagen, usa el placeholder por defecto.

**Balance calculado** — `Producto.balance` es una **propiedad** ([models.py](Sales_A2/billing/models.py)), no se almacena:

```python
@property
def balance(self):
    return (self.unit_price * self.stock).quantize(Decimal('0.01'))
```

- En el formulario se muestra en un campo **solo lectura** que se recalcula en vivo (`precio × stock`) al cambiar precio o stock, con formato monetario.
- En el **listado** se añadió la columna **Balance**, totalmente integrada con la selección dinámica de columnas y las exportaciones **PDF/Excel** (misma fuente `COLUMN_DEFS`).

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
