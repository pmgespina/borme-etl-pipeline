# pytest carga este fichero antes que los tests.
# Los módulos viven en src/ y se importan entre sí por su nombre (import spider...),
# así que añadimos src/ al path para poder importarlos igual desde los tests.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))