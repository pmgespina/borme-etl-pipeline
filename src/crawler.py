# Importamos las librerías necesarias:
# os: para navegar por las carpetas del ordenador.
# json: para guardar los datos finales en un archivo estructurado.
# re: para "expresiones regulares", útiles para limpiar texto.
# pypdf: la herramienta que nos permite abrir y leer archivos PDF.
import os
import json
import re
from pypdf import PdfReader

def cargar_ficheros(path):
    """
    Función encargada de buscar qué archivos vamos a procesar.
    """
    pdf_files = []
    
    # CASO A: Si la ruta es un archivo suelto y es PDF, lo añadimos a la lista.
    if os.path.isfile(path) and path.lower().endswith(".pdf"):
        pdf_files.append(path)
    
    # CASO B: Si la ruta es una carpeta, entramos y buscamos todos los PDFs que haya dentro.
    elif os.path.isdir(path):
        for file in os.listdir(path):
            if file.endswith(".pdf"):
                # Construimos la ruta completa con la librería os
                pdf_files.append(os.path.join(path, file))
    
    return pdf_files

def extraer_campo(text, keyword_start, keyword_end=None):
    """
    Esta función actúa como un "recortador" de texto.
    Le damos un texto largo y le decimos: "Corta lo que hay después de ESTO".
    """
    try:
        # 1. Buscamos dónde empieza la palabra clave (ej: "Capital:")
        start_index = text.find(keyword_start)
        
        # Si no encuentra la palabra clave, devolvemos 'None' (vacío)
        if start_index == -1:
            return None
        
        # 2. Calculamos dónde empieza realmente el valor (justo después de la palabra clave)
        content_start = start_index + len(keyword_start)
        
        # 3. Buscamos dónde termina el valor.
        # Si nos han dicho una palabra de fin específica, buscamos esa.
        if keyword_end:
            end_index = text.find(keyword_end, content_start)
            if end_index != -1:
                return text[content_start:end_index].strip()
        
        # Si no, por defecto cortamos hasta el siguiente punto "."
        end_index = text.find(".", content_start)
        if end_index != -1:
            return text[content_start:end_index].strip()
            
        # Si no hay punto, cogemos todo hasta el final del texto
        return text[content_start:].strip()
        
    except Exception:
        return None

def procesar_texto(text):
    """
    Recibe un párrafo de texto (una empresa) y decide si nos interesa.
    Solo nos interesa si es 'Constitución' o 'Extinción'.
    """
    info = {}
    
    # Limpieza: quitamos saltos de línea raros y espacios dobles para dejar el texto limpio
    text = re.sub(r'\s+', ' ', text)
    
    # 1. Extraer ID y Nombre de la empresa
    # El formato suele ser: "12345 - NOMBRE DE LA EMPRESA S.L."
    try:
        # Partimos el texto por el primer guion "-" que encontremos
        parts = text.split("-", 1)
        if len(parts) < 2:
            return None # Si no hay guion, no es el formato esperado
            
        id_empresa = parts[0].strip()
        
        # Verificamos que la parte izquierda sea un número (el ID de la empresa)
        if not id_empresa.isdigit():
            return None

        # La parte derecha es el nombre + el resto del texto
        resto_texto = parts[1].strip()
        
        # El nombre suele acabar en el primer punto "."
        nombre_end = resto_texto.find(".")
        
        if nombre_end != -1:
            nombre = resto_texto[:nombre_end].strip()
        else:
            nombre = resto_texto
            
        # Guardamos estos datos básicos
        info["Nombre"] = nombre
        info["Id"] = id_empresa
        
    except Exception:
        return None

    # 2. Detectar qué tipo de Acto Legal es el que vamos a almacenar
    
    # CASO A: Es una Constitución
    if "Constitución" in text:
        info["Acto legal"] = "Constitución"

        # MODIFICACIÓN IMPORTANTE:
        # Usamos tuplas (Inicio, Fin) para delimitar cada campo encadenándolos.
        # Esto evita que los puntos internos (ej: fechas 30.10.23 o "Avda.") corten el texto.
        campos_a_buscar = {
            # La fecha termina cuando empieza el siguiente campo (Objeto social)
            "Comienzo de operaciones": ("Comienzo de operaciones:", "Objeto social:"),
            
            # El objeto social termina cuando empieza el Domicilio
            "Objeto social": ("Objeto social:", "Domicilio:"),
            
            # El domicilio termina cuando empieza el Capital
            "Domicilio": ("Domicilio:", "Capital:"),
            
            # El Capital termina específicamente en "Euros"
            "Capital": ("Capital:", "Euros")
        }
        
        # Recorremos la lista. Si encontramos el dato, lo guardamos.
        # Si 'extraer_campo' devuelve None, NO hacemos nada (la clave no se crea en el diccionario).
        for clave_json, (etiqueta_inicio, etiqueta_fin) in campos_a_buscar.items():
            valor = extraer_campo(text, etiqueta_inicio, etiqueta_fin)
            if valor:
                # Si es Capital, le volvemos a pegar la palabra " Euros" para guardarlo TAL CUAL
                # y que el Wrangler se encargue de limpiarlo después.
                if clave_json == "Capital":
                    valor += " Euros"
                
                info[clave_json] = valor
        
        return info
        
    # CASO B: Es una Extinción
    elif "Extinción" in text:
        info["Acto legal"] = "Extinción"
        
        # Miramos si es voluntaria o por fusión
        if "Voluntaria" in text:
            info["Disolución"] = "Voluntaria"
        elif "fusión" in text.lower():
            info["Disolución"] = "Por fusión"
        
        # Intentamos sacar si hay nombramientos de liquidadores
        nombramientos = extraer_campo(text, "Nombramientos.")
        if nombramientos:
            info["Nombramientos"] = nombramientos

        return info
    
    # Si no es ni Constitución ni Extinción, devolvemos None (ignoramos la empresa y no se almacena nada)
    return None

def parsear_pdf(pdf_path):
    """
    Función principal de lectura. Abre el PDF y separa el texto gigante
    en pequeños bloques, uno por cada empresa.
    """
    if PdfReader is None:
        return []
    
    nombre_archivo = os.path.basename(pdf_path)

    print(f"Parseando archivo: {nombre_archivo}")
    empresas = []

    try:
        # Abrimos el PDF con la librería
        reader = PdfReader(pdf_path)
        full_text = ""
        
        # pypdf no lee todo de golpe, hay que ir página por página
        for page in reader.pages:
            texto_pagina = page.extract_text()
            if texto_pagina:
                # Añadimos un salto de línea al final de cada página para que no se peguen las palabras
                full_text += texto_pagina + "\n" 
        
        if not full_text:
            print("Aviso: No se extrajo texto del PDF")
            return []

        # Dividimos todo el texto gigante en líneas individuales
        lines = full_text.split('\n')
        
        current_block = [] # Aquí iremos acumulando las líneas de UNA empresa
        
        # A continuación se presenta la lógica de separación de empresas
        for line in lines:
            line = line.strip()
            if not line:
                continue # Saltamos líneas vacías

            # Analizamos la primera palabra de la línea
            parts = line.split("-")
            first_word = parts[0].strip()
            
            # CRITERIO: Una nueva empresa empieza si la línea arranca con un NÚMERO largo (su ID)
            # Ejemplo: "12345 - RESTAURANTE PEPE SL" -> Empieza por número -> Nueva empresa
            if first_word.isdigit() and len(first_word) > 3:
                
                # Si ya teníamos una empresa guardada en 'current_block', la procesamos antes de empezar la nueva
                if current_block:
                    full_paragraph = " ".join(current_block) # Unimos las líneas en un solo párrafo
                    empresa_data = procesar_texto(full_paragraph) # Extraemos los datos
                    if empresa_data:
                        empresa_data["metadata_source_file"] = nombre_archivo
                        empresas.append(empresa_data) # Si era válida, la guardamos
                
                # Empezamos el bloque de la nueva empresa
                current_block = [line]
            else:
                # Si no empieza por número, es una línea de continuación de la empresa actual
                current_block.append(line)
        
        # No podemos olvidar procesar el último bloque que se queda colgado al acabar el bucle
        if current_block:
            full_paragraph = " ".join(current_block)
            empresa_data = procesar_texto(full_paragraph)
            if empresa_data:
                # MODIFICACIÓN: Guardamos el nombre del archivo también aquí
                empresa_data["metadata_source_file"] = nombre_archivo
                empresas.append(empresa_data)

    except Exception as e:
        print(f"Error procesando el PDF {pdf_path}: {e}")

    return empresas

def run_crawler(input_path, output_file):
    """
    Función que coordina todo el proceso: busca archivos, los lee uno a uno y guarda el resultado final.
    """
    print(f"Iniciando Crawler con PyPDF sobre: {input_path}")
    
    # 1. Obtenemos la lista de archivos a leer
    files = cargar_ficheros(input_path)
    all_data = []
    
    print(f"Se han encontrado {len(files)} archivos PDF.")
    
    # 2. Bucle principal: Procesamos cada archivo PDF
    for pdf_file in files:
        data = parsear_pdf(pdf_file) # Esto nos devuelve una lista de empresas de ese PDF
        if data:
            all_data.extend(data) # Las añadimos a la lista general
            
    # 3. Guardado final en JSON
    try:
        # Nos aseguramos de que la carpeta de destino exista, si no, la crea
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Abrimos el fichero en modo escritura ('w') y guardamos los datos
        with open(output_file, "w", encoding="utf-8") as f:
            # ensure_ascii=False permite guardar tildes y ñ correctamente
            # indent=4 hace que el JSON se vea bonito y legible
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        
        print(f"\nDatos guardados correctamente en {output_file}")
        print(f"Total empresas procesadas: {len(all_data)}")
        
    except Exception as e:
        print(f"Error guardando el JSON: {e}")

if __name__ == "__main__":
    # Test input: Ruta donde están tus PDFs (o un PDF suelto)
    test_input = "/Users/pablomoreno/Desktop/ADQUISICION/clase10/practicafinal/data/outputs/pdfs_borme/"
    
    # Test output: Ruta donde quieres que aparezca el archivo JSON con los resultados
    test_output = "/Users/pablomoreno/Desktop/ADQUISICION/clase10/practicafinal/data/outputs/empresas_borme.json"

    run_crawler(test_input, test_output)