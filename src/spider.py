# Importamos las librerías necesarias:
# requests: es como un navegador web para Python.
# BeautifulSoup (de la librería bs4): es un "analizador" de páginas web.
# time: sirve para controlar el tiempo.
# os: para navegar por las carpetas del ordenador.
import requests
from bs4 import BeautifulSoup
import time
import os

# CONFIGURACIÓN INICIAL
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

def html(url):
    """
    Descarga el código HTML de una URL dada.
    Devuelve un objeto BeautifulSoup o None si falla.
    """
    print(f"Descargando: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        time.sleep(1) # Pausa de cortesía
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error descargando {url}: {e}")
        return None

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
    """
    try:
        # Aseguramos que el directorio exista
        os.makedirs(os.path.dirname(fichero_salida), exist_ok=True)
        
        # Vamos añadiendo las URLs de los días que queramos descargar a un fichero de texto
        with open(fichero_salida, "a", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        print(f"Éxito: Se han guardado {len(urls)} URLs en '{fichero_salida}'.")
    except Exception as e:
        print(f"Error al guardar el archivo: {e}")

# Función puente para llamarlo desde __main__.py
def run_spider(fecha, archivo_salida):
    """
    Función encargada de coordinar el proceso para una fecha específica.
    Recibe la fecha y el lugar donde guardar los resultados.
    """
    print(f"Procesando fecha: {fecha}")
    
    # Parseamos la fecha dividiendo el string según los digitos esperados
    anio = fecha[:4]
    mes = fecha[4:6]
    dia = fecha[6:8]
    
    # Construimos la URL del sumario
    url_boe = f"https://www.boe.es/borme/dias/{anio}/{mes}/{dia}/"

    # Obtener el HTML parseado
    soup = html(url_boe)
    
    if soup:
        # Extraer las URLs específicas de cada PDF
        urls_dia = extraer_urls(soup)
        
        if urls_dia:
            # Guardamos las URLs encontradas en el fichero de salida
            guardar_fichero(urls_dia, archivo_salida)
        else:
            print(f"No se encontraron URLs de PDFs para el día {fecha}.")
    else:
        print(f"No encontramos el recurso HTML para la fecha {fecha}")