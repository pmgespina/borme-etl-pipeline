# Importamos las librerías necesarias:
# requests: es como un navegador web para Python.
# time: sirve para controlar el tiempo.
# os: para navegar por las carpetas del ordenador.
import requests
import time
import os

# CONFIGURACIÓN INICIAL
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

def leer_urls(ruta_fichero):
    """
    Lee el archivo de texto y devuelve una lista de URLs limpias.
    Comprueba si el archivo existe antes de intentar leerlo.
    """
    if not os.path.exists(ruta_fichero):
        print(f"Error: No se encuentra el archivo '{ruta_fichero}'. Ejecuta el spider primero.")
        return []

    with open(ruta_fichero, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def descargar_archivos(urls, output_dir):
    """
    Recorre la lista de URLs y descarga cada archivo PDF en la carpeta de salida.
    """
    # Creamos el directorio si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Directorio '{output_dir}' creado.")

    total = len(urls)
    print(f"Iniciando descarga de {total} documentos...")

    for i, url in enumerate(urls, start=1):
        # Extraemos el nombre que le pondremos al fichero de la propia URL (lo último tras el /)
        nombre_fichero = url.split("/")[-1]
        ruta_destino = os.path.join(output_dir, nombre_fichero)

        print(f"[{i}/{total}] Descargando: {nombre_fichero}")

        try:
            response = requests.get(url, headers=HEADERS)
            time.sleep(1) # Respeto al servidor
            
            if response.status_code == 200:
                with open(ruta_destino, "wb") as f:
                    f.write(response.content)
            else:
                print(f"Error {response.status_code} al descargar.")

        except Exception as e:
            print(f"Excepción durante la descarga: {e}")

# Función puente para llamarlo desde __main__.py
def run_fetcher(archivo_urls, directorio_salida):
    """
    Coordina la lectura de URLs y su descarga.
    Utiliza leer_urls() para validar que el fichero existe.
    """
    # Usamos tu función original para leer y validar
    lista_urls = leer_urls(archivo_urls)
    
    if lista_urls:
        # Si hay URLs, procedemos a descargar
        descargar_archivos(lista_urls, directorio_salida)