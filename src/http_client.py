# Cliente HTTP compartido por el spider y el fetcher.
# Centraliza tres cosas:
#   1. Timeout: sin él, una conexión colgada bloquea el pipeline indefinidamente.
#   2. Reintentos con espera creciente ante errores temporales del servidor (429, 5xx).
#   3. Un User-Agent de navegador definido en un solo sitio, en lugar de duplicado.
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# User-Agent de navegador: algunos servidores rechazan o limitan clientes no reconocidos
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

# (segundos para conectar, segundos esperando la respuesta)
TIMEOUT = (10, 30)

def crear_sesion():
    """
    Devuelve una sesión de requests con reintentos automáticos.
    Reintenta hasta 3 veces con esperas de 1, 2 y 4 segundos y respeta la
    cabecera Retry-After si el servidor la envía.
    """
    reintentos = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    sesion = requests.Session()
    sesion.headers.update({"User-Agent": USER_AGENT})
    adaptador = HTTPAdapter(max_retries=reintentos)
    sesion.mount("https://", adaptador)
    sesion.mount("http://", adaptador)
    return sesion