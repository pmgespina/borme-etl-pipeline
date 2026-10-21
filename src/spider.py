# Importamos las librerías necesarias:
# BeautifulSoup (de la librería bs4): es un "analizador" de páginas web.
# time: sirve para controlar el tiempo.
# os: para navegar por las carpetas del ordenador.
from bs4 import BeautifulSoup
import time
import os
import logging

# http_client: sesión HTTP propia con timeout y reintentos (ver http_client.py).
from http_client import crear_sesion, TIMEOUT

# Los mensajes van al logger configurado en __main__.py: consola y fichero de log
logger = logging.getLogger(__name__)

# Una sola sesión reutiliza la conexión y aplica timeout y reintentos a todas las peticiones
SESION = crear_sesion()

def html(url):
    """
    Descarga el código HTML de una URL dada.
    Devuelve un objeto BeautifulSoup, o None si ese día no hay BORME publicado.
    Los errores reales se propagan para que run_spider los cuente en lugar de ocultarlos.
    """
    logger.info(f"Descargando: {url}")
    response = SESION.get(url, timeout=TIMEOUT)
    time.sleep(1) # Pausa de cortesía
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')

def extraer_urls(soup):
    """
    Busca en el HTML todos los enlaces que acaben en .pdf
    y contengan 'borme' en su ruta.
    """
    urls = []
    # Buscamos todos los tags <a> (enlaces)
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Filtramos: que sea PDF y que sea del BORME
        if href.endswith('.pdf') and 'borme' in href.lower():
            # A veces los enlaces son relativos (/borme/...), hay que ponerles el dominio
            if href.startswith('/'):
                href = f"https://www.boe.es{href}"
            urls.append(href)
    return urls

def guardar_fichero(urls, fichero_salida):
    """
    Guarda la lista de URLs en un archivo de texto.
    Devuelve True si todo fue bien y False si hubo un error.
    """
    try:
        # Aseguramos que el directorio exista
        os.makedirs(os.path.dirname(fichero_salida), exist_ok=True)

        # Leemos las URLs ya guardadas para no duplicarlas. Así el spider es idempotente:
        # repetir un día (o todo el mes) no añade líneas repetidas ni obliga a borrar el fichero.
        existentes = set() # Más eficiente que recorrer una lista
        if os.path.exists(fichero_salida):
            with open(fichero_salida, "r", encoding="utf-8") as f:
                existentes = {line.strip() for line in f if line.strip()}

        # dict.fromkeys elimina duplicados dentro del propio día manteniendo el orden
        nuevas = [url for url in dict.fromkeys(urls) if url not in existentes]

        # Vamos añadiendo las URLs nuevas al final del fichero de texto
        with open(fichero_salida, "a", encoding="utf-8") as f:
            for url in nuevas:
                f.write(url + "\n")
        logger.info(f"Éxito: {len(nuevas)} URLs nuevas guardadas en '{fichero_salida}' "
                    f"({len(urls) - len(nuevas)} ya existían).")
        return True
    except Exception as e:
        logger.error(f"Error al guardar el archivo: {e}")
        return False

# Función puente para llamarlo desde __main__.py
def run_spider(fecha, archivo_salida):
    """
    Función encargada de coordinar el proceso para una fecha específica.
    Recibe la fecha y el lugar donde guardar los resultados.
    Devuelve el número de errores (0 si todo fue bien) para que __main__.py
    pueda terminar con un código de salida distinto de cero si algo falló.
    """
    logger.info(f"Procesando fecha: {fecha}")
    
    # Parseamos la fecha dividiendo el string según los digitos esperados
    anio = fecha[:4]
    mes = fecha[4:6]
    dia = fecha[6:8]
    
    # Construimos la URL del sumario
    url_boe = f"https://www.boe.es/borme/dias/{anio}/{mes}/{dia}/"

    # Obtener el HTML parseado
    try:
        soup = html(url_boe)
    except Exception as e:
        logger.error(f"Error descargando {url_boe}: {e}")
        return 1
    
    if soup is None:
        logger.warning(f"No hay BORME publicado el día {fecha} (festivo o fin de semana).")
        return 0

    # Extraer las URLs específicas de cada PDF
    urls_dia = extraer_urls(soup)
    
    if not urls_dia:
        logger.warning(f"No se encontraron URLs de PDFs para el día {fecha}.")
        return 0

    # Guardamos las URLs encontradas en el fichero de salida
    return 0 if guardar_fichero(urls_dia, archivo_salida) else 1