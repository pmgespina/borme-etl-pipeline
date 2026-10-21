import crawler

CONSTITUCION = (
    "123456 - J.M. CONSULTORES S.L. Constitución. Comienzo de operaciones: 1.09.23. "
    "Objeto social: Consultoría de empresas. Domicilio: Avda. de la Constitución 25, 3º B "
    "(Sevilla). Capital: 3.000,00 Euros. Declaración de unipersonalidad."
)


def test_nombre_con_puntos_no_se_trunca():
    # Regresión: antes el nombre se cortaba en el primer punto y quedaba "J"
    empresa = crawler.procesar_texto(CONSTITUCION)
    assert empresa is not None
    assert empresa["Nombre"] == "J.M. CONSULTORES S.L"
    assert empresa["Id"] == "123456"


def test_campos_de_constitucion():
    empresa = crawler.procesar_texto(CONSTITUCION)
    assert empresa is not None
    assert empresa["Acto legal"] == "Constitución"
    # Los delimitadores encadenados evitan que "1.09.23" o "Avda." corten el campo
    assert empresa["Comienzo de operaciones"].startswith("1.09.23")
    assert empresa["Objeto social"].startswith("Consultoría de empresas")
    assert empresa["Domicilio"].startswith("Avda. de la Constitución 25, 3º B")
    assert empresa["Capital"] == "3.000,00 Euros"


def test_extincion_voluntaria():
    empresa = crawler.procesar_texto("654321 - TALLER SUR SL. Extinción. Voluntaria.")
    assert empresa is not None
    assert empresa["Nombre"] == "TALLER SUR SL"
    assert empresa["Acto legal"] == "Extinción"
    assert empresa["Disolución"] == "Voluntaria"


def test_otros_actos_se_ignoran():
    assert crawler.procesar_texto("111111 - ACME SL. Nombramientos. Adm. Unico: PEREZ JUAN.") is None


def test_bloque_sin_id_numerico_se_ignora():
    assert crawler.procesar_texto("TEXTO DE CABECERA - Sección Primera. Constitución.") is None