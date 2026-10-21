import pytest

import wrangler


@pytest.fixture(scope="module")
def mappings():
    return wrangler.cargar_mappings()

# Comprobamos que los mappings se cargan correctamente desde el repo y no desde una ruta local.
def test_mappings_se_cargan_desde_el_repo(mappings):
    assert mappings["provincias"]["28"] == "madrid"
    assert mappings["vias"]

# (domicilio, tipo de vía, nombre de vía, número, ciudad)
DOMICILIOS = [
    ("Calle Mayor, 10 (Madrid).", "calle", "mayor", "10", "madrid"),
    ("Avda. de la Constitución 25, 3º B (Sevilla).", "avenida", "de la constitución", "25", "sevilla"),
    ("Calle Alcalá 100, 31º (Madrid).", "calle", "alcalá", "100", "madrid"),
    ("Calle Sol, 10, 2º (Madrid).", "calle", "sol", "10", "madrid"),
    ("C/ Francisco Silvela 110 2 (Madrid).", "calle", "francisco silvela", "110", "madrid"),
    ("Calle 12 de Octubre 5 (Madrid).", "calle", "12 de octubre", "5", "madrid"),
    ("Calle Luna, 7 bajo (Cádiz).", "calle", "luna", "7", "cádiz"),
    ("Paseo de la Castellana Nº 200 (Madrid).", "paseo", "de la castellana", "200", "madrid"),
    ("Plaza España S/N (Toledo).", "plaza", "españa s/n", "", "toledo"),
]

@pytest.mark.parametrize("domicilio, tipo, nombre, numero, ciudad", DOMICILIOS)
def test_parsear_domicilio(mappings, domicilio, tipo, nombre, numero, ciudad):
    resultado = wrangler.parsear_domicilio(domicilio, mappings)
    assert resultado["TipoDeVia"] == tipo
    assert resultado["NombreDeVia"] == nombre
    assert resultado["Numero"] == numero
    assert resultado["Ciudad"] == ciudad

def test_parsear_domicilio_vacio(mappings):
    assert wrangler.parsear_domicilio("", mappings)["Numero"] == ""

@pytest.mark.parametrize("entrada, esperado", [
    ("3.000,00 Euros", 3000.0),
    ("1.250.000,50 Euros", 1250000.5),
    ("", None),
    (None, None),
    ("sin cifra Euros", None),
])
def test_limpiar_capital(entrada, esperado):
    assert wrangler.limpiar_capital(entrada) == esperado

@pytest.mark.parametrize("entrada, esperado", [
    ("13.11.23.", "13-11-2023"),
    ("01.09.2025", "01-09-2025"),
    ("", ""),
])
def test_formatear_fecha(entrada, esperado):
    assert wrangler.formatear_fecha(entrada) == esperado

@pytest.mark.parametrize("fichero, esperado", [
    ("BORME-A-2023-225-28.pdf", "madrid"),
    ("BORME-A-2023-225-29.pdf", "málaga"),
    ("BORME-A-2023-225-99.pdf", "desconocida"),
    ("", "desconocida"),
])
def test_obtener_provincia(mappings, fichero, esperado):
    assert wrangler.obtener_provincia(fichero, mappings) == esperado

@pytest.mark.parametrize("nombre, esperado", [
    ("RESTAURANTE PEPE SL", "sociedad limitada"),
    ("J.M. CONSULTORES S.L", "sociedad limitada"),
    ("INVERSIONES NORTE SA", "sociedad anónima"),
    ("TALLER SUR SLU", "sociedad limitada unipersonal"),
])
def test_detectar_tipo_sociedad(mappings, nombre, esperado):
    assert wrangler.detectar_tipo_sociedad(nombre, mappings) == esperado