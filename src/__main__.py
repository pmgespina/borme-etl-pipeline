import argparse
import os
import sys
import logging
from datetime import datetime

# Importación de módulos del proyecto
try:
    import spider
    import fetcher
    import crawler
    import wrangler
except ImportError as e:
    print(f"Error importando módulos: {e}")
    sys.exit(1)

# Definimos las rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# Archivos por defecto
DEFAULT_URLS = os.path.join(OUTPUTS_DIR, "urls_borme.txt")
DEFAULT_PDFS = os.path.join(OUTPUTS_DIR, "pdfs_borme")
DEFAULT_JSON = os.path.join(OUTPUTS_DIR, "empresas_borme.json")
DEFAULT_CSV = os.path.join(OUTPUTS_DIR, "empresas_constitucion_limpio.csv")

# Configuración de loggings
def configurar_logs():
    """
    Configura el sistema para guardar mensajes en un archivo y mostrarlos por consola.
    Devuelve la ruta del archivo de log generado.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # Nombre del archivo con fecha: log_20231221.log
    nombre_log = f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    ruta_log = os.path.join(LOGS_DIR, nombre_log)

    # Configuración básica
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ruta_log, encoding='utf-8'), # Guardar en archivo
            logging.StreamHandler(sys.stdout)               # Mostrar en consola
        ]
    )
    return ruta_log

def main():
    # Iniciamos los logs y obtenemos la ruta
    ruta_log = configurar_logs()
    
    print(f"SISTEMA DE LOGS INICIADO EN: {ruta_log}")
    
    parser = argparse.ArgumentParser(description='Borme Data Pipeline')

    parser.add_argument(
        '-p', '--phase',
        required=True,
        choices=['spider', 'fetcher', 'crawler', 'wrangler'],
        help='Fase a ejecutar.'
    )
    parser.add_argument('-d', '--day', help='Fecha para el spider (YYYYMMDD).')
    parser.add_argument('-fp', '--filepath', help='Ruta de archivo específica.')
    parser.add_argument('-dp', '--directorypath', help='Ruta de directorio específica.')

    args = parser.parse_args()
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    logging.info(f"INICIO DE EJECUCIÓN: FASE {args.phase.upper()}")

    # Aquí definimos la lógica de las fases del proyecto.
    # Cada fase devuelve su número de errores. Terminamos con código de salida 1 si hubo
    # alguno: así un bucle de bash, cron o un orquestador (Airflow...) detecta el fallo,
    # en lugar de recibir un 0 y dar por buena una ejecución que no lo fue.

    try:
        if args.phase == 'spider':
            if not args.day:
                logging.error("Falta el argumento fecha (-d).")
                return 1
            logging.info(f"Lanzando Spider para el día {args.day}")
            errores = spider.run_spider(args.day, DEFAULT_URLS)

        elif args.phase == 'fetcher':
            logging.info("Lanzando Fetcher...")
            errores = fetcher.run_fetcher(DEFAULT_URLS, DEFAULT_PDFS)

        elif args.phase == 'crawler':
            input_path = args.directorypath or args.filepath or DEFAULT_PDFS
            if not os.path.exists(input_path):
                logging.error(f"No existe la ruta: {input_path}")
                return 1
            logging.info(f"Lanzando Crawler sobre: {input_path}")
            errores = crawler.run_crawler(input_path, DEFAULT_JSON)

        elif args.phase == 'wrangler':
            input_file = args.filepath or DEFAULT_JSON
            if not os.path.exists(input_file):
                logging.error(f"No existe el archivo JSON: {input_file}")
                return 1
            logging.info(f"Lanzando Wrangler sobre: {input_file}")
            errores = wrangler.run_wrangler(input_file, DEFAULT_CSV)

    except Exception as e:
        logging.critical(f"ERROR CRÍTICO DURANTE LA EJECUCIÓN: {e}", exc_info=True)
        return 1

    if errores:
        logging.error(f"FIN DE {args.phase.upper()} CON {errores} ERRORES (revisa el log)")
        return 1

    logging.info(f"FIN DE EJECUCIÓN CORRECTA DE {args.phase.upper()}")
    return 0

if __name__ == '__main__':
    sys.exit(main())