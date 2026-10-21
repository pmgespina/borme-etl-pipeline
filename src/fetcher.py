# Importamos las librerías necesarias:
# http_client: sesión HTTP propia con timeout y reintentos (ver http_client.py).
# time: sirve para controlar el tiempo.
# os: para navegar por las carpetas del ordenador.
import time
import os
import logging

from http_client import crear_sesion, TIMEOUT

# Los mensajes van al logger configurado en __main__.py: consola y fichero de log
logger = logging.getLogger(__name__)

# Una sola sesión reutiliza la conexión y aplica timeout y reintentos a todas las descargas
SESION = crear_sesion()

def leer_urls(ruta_fichero):
    """
    Lee el archivo de texto y devuelve una lista de URLs limpias.
    Comprueba si el archivo existe antes de intentar leerlo.
    """
    if not os.path.exists(ruta_fichero):
        logger.error(f"Error: No se encuentra el archivo '{ruta_fichero}'. Ejecuta el spider primero.")
        return []

    with open(ruta_fichero, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def descargar_archivos(urls, output_dir):
    """
    Recorre la lista de URLs y descarga cada archivo PDF en la carpeta de salida.
    Devuelve el número de descargas que han fallado.
    """
    # Creamos el directorio si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Directorio '{output_dir}' creado.")

    total = len(urls)
    errores = 0
    logger.info(f"Iniciando descarga de {total} documentos...")

    for i, url in enumerate(urls, start=1):
        # Extraemos el nombre que le pondremos al fichero de la propia URL (lo último tras el /)
        nombre_fichero = url.split("/")[-1]
        ruta_destino = os.path.join(output_dir, nombre_fichero)

        # Si el PDF ya está descargado lo saltamos: reejecutar el fetcher solo baja lo que falta
        if os.path.exists(ruta_destino):
            logger.info(f"[{i}/{total}] Ya existe, se omite: {nombre_fichero}")
            continue

        logger.info(f"[{i}/{total}] Descargando: {nombre_fichero}")

        try:
            response = SESION.get(url, timeout=TIMEOUT)
            time.sleep(1) # Respeto al servidor

            if response.status_code == 200:
                # Escribimos primero en un fichero temporal y lo renombramos al terminar.
                # Si la ejecución se corta a mitad, no queda un PDF incompleto con el nombre
                # final que la siguiente ejecución daría por bueno y saltaría.
                ruta_temporal = ruta_destino + ".part"
                with open(ruta_temporal, "wb") as f:
                    f.write(response.content)
                os.replace(ruta_temporal, ruta_destino)
            else:
                errores += 1
                logger.error(f"Error {response.status_code} al descargar {url}")

        except Exception as e:
            errores += 1
            logger.error(f"Excepción durante la descarga de {url}: {e}")

    if errores:
        logger.warning(f"{errores} de {total} descargas han fallado.")
    return errores

# Función puente para llamarlo desde __main__.py
def run_fetcher(archivo_urls, directorio_salida):
    """
    Coordina la lectura de URLs y su descarga.
    Utiliza leer_urls() para validar que el fichero existe.
    Devuelve el número de errores (0 si todo fue bien).
    """
    if not os.path.exists(archivo_urls):
        logger.error(f"No se encuentra el archivo '{archivo_urls}'. Ejecuta el spider primero.")
        return 1

    lista_urls = leer_urls(archivo_urls)
    if not lista_urls:
        logger.warning("El archivo de URLs está vacío: no hay nada que descargar.")
        return 0

    return descargar_archivos(lista_urls, directorio_salida)