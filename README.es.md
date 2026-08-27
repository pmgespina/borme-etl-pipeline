🌐 [English](README.md) | Español

# Proyecto Borme Data Pipeline

Este proyecto implementa un **pipeline de datos ETL** completo y automatizado para obtener información sobre la constitución de nuevas empresas en España a partir del **Boletín Oficial del Registro Mercantil (BORME)**.

El sistema es capaz de rastrear la web del BOE, descargar los boletines oficiales en PDF, extraer la información no estructurada (texto plano) y transformarla en datos estructurados y limpios (CSV) listos para su análisis.

## Estructura del Proyecto

El proyecto sigue una arquitectura modular donde un orquestador (`__main__.py`) coordina a los distintos módulos especializados:

```text
practicafinal/
├── assets/
│   └── mappings.json        # Diccionarios para normalizar provincias, vías y tipos de sociedad.
├── data/
│   ├── inputs/              # Archivos de entrada opcionales.
│   ├── logs/                # Registros de ejecución (historial de errores y procesos).
│   └── outputs/             # Resultados generados:
│       ├── urls_borme.txt
│       ├── pdfs_borme/
│       ├── empresas_borme.json
│       └── empresas_constitucion_limpio.csv
├── src/
│   ├── __main__.py          # Punto de entrada (Orquestador).
│   ├── spider.py            # Buscador de enlaces.
│   ├── fetcher.py           # Descargador de archivos.
│   ├── crawler.py           # Extractor de información (PDF -> JSON).
│   └── wrangler.py          # Limpiador de datos (JSON -> CSV).
├── requirements.txt         # Lista de dependencias externas.
└── README.md                # Documentación del proyecto.
```

## Descripción de los Módulos (`src/`)

### 1. `__main__.py`

Es el punto de entrada único. Utiliza `argparse` para gestionar los argumentos de línea de comandos y `logging` para registrar la actividad. Coordina las llamadas a los demás scripts.

### 2. `spider.py`

Se conecta a la web del BOE para una fecha específica.

* **Función:** Analiza el HTML del día y extrae las URLs de los PDFs provinciales.
* **Modo Append:** Guarda las URLs en `data/outputs/urls_borme.txt` añadiéndolas al final sin borrar las anteriores (ideal para bucles de varios días).

### 3. `fetcher.py`

Lee la lista de URLs generada por el spider.

* **Función:** Descarga los PDFs uno a uno en `data/outputs/pdfs_borme/`, comprobando previamente que el archivo de URLs existe. Incluye pausas para no saturar el servidor.

### 4. `crawler.py`

El motor de procesamiento de texto.

* **Función:** Lee los PDFs usando `pypdf`. Detecta bloques de texto correspondientes a empresas y extrae campos en bruto (Nombre, Capital, Domicilio, Fecha).
* **Salida:** Genera un JSON sucio (`empresas_borme.json`) con Constituciones, Extinciones y otros actos.

### 5. `wrangler.py`

El refinador de datos.

* **Filtro:** Selecciona únicamente los actos de **"Constitución"**.
* **Limpieza:** Normaliza fechas (DD-MM-YYYY) y dinero (float).
* **Algoritmo de Domicilios:** Utiliza **Expresiones Regulares (Regex)** avanzadas con 5 estrategias de prioridad para separar direcciones complejas (Tipo de vía, Nombre, Número, Ciudad), gestionando casos sin comas, con kilómetros, bloques, etc.
* **Salida:** Genera el entregable final: `empresas_constitucion_limpio.csv`.

## Librerías y Dependencias

### ¿Por qué `requirements.txt` es tan corto?

El archivo `requirements.txt` solo contiene:

* `requests`
* `beautifulsoup4`
* `pypdf`

### ¿Dónde están `json`, `csv`, `os`, `re` o `time`?

No es necesario instalarlas, ya vienen instaladas en la Biblioteca Estándar de Python por defecto.

## Instalación

Este proyecto requiere **Python 3.x**.

1. **Crear un entorno virtual:**
```bash
python3 -m venv venv
source venv/bin/activate
```


2. **Instalar dependencias externas:**
```bash
pip install -r requirements.txt
```


## Guía de Ejecución:

Para cumplir con el objetivo de obtener las empresas constituidas en **Septiembre de 2025**, sigue estos pasos exactos desde la carpeta raíz del proyecto:

### PASO 1: Spider (Recopilar URLs de todo el mes)

Ejecutamos un bucle para rastrear del día 1 al 30.
*(Nota: Si tienes un archivo `urls_borme.txt` antiguo, bórralo antes para evitar duplicados)*.

```bash
rm data/outputs/urls_borme.txt  # Opcional: Limpiar ejecución anterior
for i in {01..30}; do python3 src/__main__.py -p spider -d 202509$i; done
```

### PASO 2: Fetcher (Descargar los PDFs)

Descargamos todos los documentos recopilados en el paso anterior.

```bash
python3 src/__main__.py -p fetcher
```

### PASO 3: Crawler (Generar el JSON)

Leemos los PDFs y generamos el archivo estructurado intermedio.

```bash
python3 src/__main__.py -p crawler
```

### PASO 4: Wrangler (Generar el CSV Final)

Limpiamos los datos y generamos el archivo final filtrado.

```bash
python3 src/__main__.py -p wrangler
```

## Logs y Resultados

* **Resultados:** El archivo final estará en `data/outputs/empresas_constitucion_limpio.csv`.
* **Logs:** Puedes consultar el historial de ejecución y posibles errores en la carpeta `data/logs/`, donde se generará un archivo diario basado en la fecha de ejecución (`pipeline_YYYYMMDD.log`).