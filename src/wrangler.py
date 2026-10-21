# Importamos las librerías necesarias:
# os: para navegar por las carpetas del ordenador y gestionar rutas de archivos.
# json: para leer los datos crudos que extrajimos del PDF.
# csv: para guardar los datos finales en un archivo estructurado (tipo Excel).
# re: para "expresiones regulares", útiles para limpiar texto y buscar patrones complejos.
import os
import json
import csv
import re

import logging

# Los mensajes van al logger configurado en __main__.py: consola y fichero de log
logger = logging.getLogger(__name__)

# Configuración de rutas
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_PATH = os.path.join(PROJECT_ROOT, "assets", "mappings.json")

def cargar_mappings():
    """
    Carga el diccionario de 'traducciones' desde el archivo JSON externo.
    Nos sirve para normalizar datos, por ejemplo:
    - Transformar "S.L." -> "sociedad limitada"
    - Identificar que el código "28" -> "madrid"
    """
    if not os.path.exists(ASSETS_PATH):
        raise FileNotFoundError(f"No se encontró el archivo de mappings en {ASSETS_PATH}")
    with open(ASSETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def limpiar_texto_basico(texto):
    """
    Limpieza higiénica básica.
    A veces, al extraer del PDF, las palabras vienen con 'basura' pegada alrededor.
    Ejemplo: '"DIAMANTE",' -> Queremos que quede limpio: 'DIAMANTE'
    """
    if not texto:
        return ""
    # .strip() elimina los caracteres que le indiquemos del principio y del final.
    return texto.strip(" \"'.,/")

def limpiar_capital(capital_str):
    """
    Transforma el texto del dinero en un número matemático (float).
    Entrada: "3.000,00 Euros"
    Salida: 3000.0
    Si el dato falta o no se puede interpretar devuelve None (celda vacía en el CSV).
    """
    if not capital_str:
        return None
    try:
        # 1. Quitamos la palabra "euros" y espacios.
        limpio = capital_str.lower().replace("euros", "").strip()
        # 2. Adaptamos el formato español (3.000,00) al formato inglés de Python (3000.00)
        #    - Quitamos el punto de los miles.
        #    - Cambiamos la coma decimal por un punto.
        limpio = limpio.replace(".", "").replace(",", ".")
        return float(limpio)
    except ValueError:
        return None

def formatear_fecha(fecha_str):
    """
    Normaliza la fecha al formato que pide el enunciado: DD-MM-YYYY.
    Entrada: "13.11.23." (con punto final sucio y año corto)
    Salida: "13-11-2023"
    """
    if not fecha_str:
        return ""
    try:
        # Quitamos espacios y el punto final que a veces se cuela del PDF
        fecha_limpia = fecha_str.strip().rstrip(".") 
        
        # Dividimos por el punto separador
        parts = fecha_limpia.split(".")
        
        if len(parts) == 3:
            dia, mes, anio = parts
            # Si el año tiene 2 dígitos (23), le añadimos el siglo (2023)
            if len(anio) == 2:
                anio = "20" + anio
            return f"{dia}-{mes}-{anio}"
            
        return fecha_limpia 
    except Exception:
        # Si algo falla, devolvemos la fecha original para no perder el dato
        return fecha_str

def parsear_domicilio(domicilio_str, mappings):
    """
    Descompone una dirección compleja en: Tipo, Nombre, Número y Ciudad.
    """
    parsed = {
        "TipoDeVia": "",
        "NombreDeVia": "",
        "Numero": "",
        "Ciudad": "",
        "DomicilioCompleto": domicilio_str if domicilio_str else ""
    }
    
    if not domicilio_str:
        return parsed

    # 1. EXTRAER LA CIUDAD (Entre paréntesis al final)
    ciudad_match = re.search(r'\((.*?)\)[\.\s]*$', domicilio_str)
    
    if ciudad_match:
        parsed["Ciudad"] = ciudad_match.group(1).lower()
        domicilio_sin_ciudad = domicilio_str[:ciudad_match.start()].strip()
    else:
        domicilio_sin_ciudad = domicilio_str
        
    domicilio_sin_ciudad = domicilio_sin_ciudad.rstrip("., ")

    # 2. ELIMINAR CÓDIGO POSTAL (Seguridad)
    cp_match = re.search(r'\b(\d{5})\b\s*$', domicilio_sin_ciudad)
    if cp_match:
        domicilio_sin_cp = domicilio_sin_ciudad[:cp_match.start()].strip()
    else:
        domicilio_sin_cp = domicilio_sin_ciudad
    
    domicilio_sin_cp = domicilio_sin_cp.rstrip("., ")

    # 3. SEPARAR TIPO DE VÍA
    parts = domicilio_sin_cp.split(" ", 1)
    if len(parts) > 0:
        tipo_raw = parts[0].upper().replace(".", "")
        tipo_normalizado = mappings["vias"].get(tipo_raw, "calle")
        if tipo_raw in mappings["vias"]:
             tipo_normalizado = mappings["vias"][tipo_raw]
        parsed["TipoDeVia"] = tipo_normalizado

    if len(parts) > 1:
        resto_texto = parts[1]
        
        # 4. EXTRAER NÚMERO DE CALLE (Sistema de Prioridades)
        numero_encontrado = ""
        nombre_calle_sucio = resto_texto
        
        # A) Etiqueta explícita ("Nº 12")
        match_num_label = re.search(r'(?:Nº|N\.|NUM\.|N[ÚU]MERO)\s*(\d+)', resto_texto, re.IGNORECASE)
        
        # B) Separación por coma ("Calle X, 10")
        # Solo vale si lo que sigue a la coma es un número de portal, no un piso:
        # en "Avda. X 25, 3º B" el "3º" es la planta y el número real es el 25.
        parts_comma = resto_texto.rsplit(",", 1)
        match_comma = None
        if len(parts_comma) > 1:
            match_comma = re.match(r'(\d+)\b(?!\s*[ºª])', parts_comma[1].strip())
        
        # C) Marcadores de vivienda ("Esc", "Piso", "2º")
        match_marker = re.search(
            r'\b(\d+)\s*(?:[\.,-]?\s*)?(?:ESC|PISO|PTA|PUERTA|BJ|BAJO|BL|BLOQUE|EDIF|NAVE|PORTAL|\d+[ºª])', 
            resto_texto, 
            re.IGNORECASE
        )

        # D) Separadores especiales ("-", "/")
        match_special = re.search(r'\b(\d+)\s*(?:[-–/ºª])', resto_texto)

        # E) Dos números al final ("Francisco Silvela 110 2")
        # Si acaba en "Numero Espacio Numero", cogemos el PRIMERO.
        match_two_nums = re.search(r'\b(\d+)\s+\d+\s*$', resto_texto)

        # --- SELECCIÓN ---
        
        if match_num_label:
            numero_encontrado = match_num_label.group(1)
            nombre_calle_sucio = resto_texto[:match_num_label.start()]
            
        elif match_comma:
            numero_encontrado = match_comma.group(1)
            nombre_calle_sucio = parts_comma[0]
        
        elif match_marker: 
            numero_encontrado = match_marker.group(1)
            nombre_calle_sucio = resto_texto[:match_marker.start()]

        elif match_special: 
            numero_encontrado = match_special.group(1)
            nombre_calle_sucio = resto_texto[:match_special.start()]

        # Aplicamos la nueva estrategia E
        elif match_two_nums:
            numero_encontrado = match_two_nums.group(1)
            nombre_calle_sucio = resto_texto[:match_two_nums.start()]

        # F) FALLBACK: El último recurso (coger el último número)
        if not numero_encontrado:
            match_last_num = re.search(r'(\d+)[^\d]*$', resto_texto)
            if match_last_num:
                numero_encontrado = match_last_num.group(1)
                nombre_calle_sucio = resto_texto[:match_last_num.start()]

        parsed["Numero"] = numero_encontrado
        parsed["NombreDeVia"] = limpiar_texto_basico(nombre_calle_sucio).lower()

    return parsed

def obtener_provincia(filename, mappings):
    """
    Obtiene la provincia no del texto, sino del nombre del archivo PDF.
    Ej: "BORME-A-2023-225-28.pdf" -> El código 28 corresponde a Madrid.
    """
    if not filename:
        return "desconocida"
    try:
        base = filename.replace(".pdf", "")
        parts = base.split("-")
        codigo = parts[-1]  # El último elemento es el código
        return mappings["provincias"].get(codigo, "desconocida")
    except Exception:
        return "desconocida"

def detectar_tipo_sociedad(nombre, mappings):
    """
    Deduce si es S.L. o S.A. buscando estas siglas dentro del nombre de la empresa.
    """
    nombre_upper = nombre.upper()
    for key, valor in mappings["sociedades"].items():
        # Buscamos " S.L" al final o " S.L " en medio
        if nombre_upper.endswith(f" {key}") or f" {key} " in nombre_upper:
            return valor
    return "sociedad limitada" # Valor por defecto más común

def run_wrangler(input_json, output_csv):
    """
    Orquesta todo el proceso de lectura, limpieza y escritura.
    """
    logger.info("Iniciando Wrangler...")
    logger.info(f"Leyendo datos de: {input_json}")
    
    mappings = cargar_mappings()
    
    try:
        with open(input_json, "r", encoding="utf-8") as f:
            data_cruda = json.load(f)
    except FileNotFoundError:
        logger.error("Error: No se encontró el archivo de entrada JSON.")
        return 1

    empresas_procesadas = []

    # Recorremos cada empresa del JSON
    for empresa in data_cruda:
        
        # FILTRO: Solo nos interesan las Constituciones (se especifica en el enunciado
        # que son empresas constituidas)
        if empresa.get("Acto legal") != "Constitución":
            continue

        nueva_fila = {}
        
        # 1. Copiamos y deducimos datos básicos
        nueva_fila["Nombre"] = empresa.get("Nombre", "")
        nueva_fila["TipoDeSociedad"] = detectar_tipo_sociedad(nueva_fila["Nombre"], mappings)
        
        # 2. Limpiamos Fecha y Capital
        nueva_fila["ComienzoDeOperaciones"] = formatear_fecha(empresa.get("Comienzo de operaciones", ""))
        nueva_fila["CapitalSocial"] = limpiar_capital(empresa.get("Capital", ""))
        
        # 3. Procesamos el Domicilio (La parte compleja)
        domicilio_raw = empresa.get("Domicilio", "")
        datos_domicilio = parsear_domicilio(domicilio_raw, mappings)
        
        # Asignamos los datos desglosados
        # [:-1] elimina el punto final que suele quedar en el domicilio completo original
        nueva_fila["DomicilioCompleto"] = datos_domicilio["DomicilioCompleto"][:-1] if datos_domicilio["DomicilioCompleto"].endswith(".") else datos_domicilio["DomicilioCompleto"]
        nueva_fila["TipoDeVia"] = datos_domicilio["TipoDeVia"]
        nueva_fila["NombreDeVia"] = datos_domicilio["NombreDeVia"]
        nueva_fila["Numero"] = datos_domicilio["Numero"]
        nueva_fila["Ciudad"] = datos_domicilio["Ciudad"]
        
        # 4. Obtenemos provincia del nombre del archivo
        filename = empresa.get("metadata_source_file", "")
        nueva_fila["Provincia"] = obtener_provincia(filename, mappings)

        empresas_procesadas.append(nueva_fila)

    # Definimos las columnas del CSV final (ordenadas según enunciado)
    columnas = [
        'Nombre', 'TipoDeSociedad', 'ComienzoDeOperaciones', 'CapitalSocial',
        'DomicilioCompleto', 'TipoDeVia', 'NombreDeVia', 'Numero', 'Ciudad', 'Provincia'
    ]
    
    # Escribimos el archivo CSV
    try:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columnas)
            writer.writeheader() # Escribe la fila de títulos
            writer.writerows(empresas_procesadas) # Escribe los datos
            
        logger.info(f"Limpieza completada. {len(empresas_procesadas)} empresas guardadas en: {output_csv}")
        return 0
        
    except Exception as e:
        logger.error(f"Error escribiendo el CSV: {e}")
        return 1