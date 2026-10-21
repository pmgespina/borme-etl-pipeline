from bs4 import BeautifulSoup

import fetcher
import spider


def test_extraer_urls_solo_pdfs_del_borme_y_absolutas():
    soup = BeautifulSoup(
        '<a href="/borme/dias/2025/09/02/pdfs/BORME-A-2025-167-28.pdf">Madrid</a>'
        '<a href="https://www.boe.es/borme/otro.pdf">Absoluta</a>'
        '<a href="/boe/dias/2025/09/02/pdfs/BOE-A-1.pdf">BOE</a>'
        '<a href="/borme/dias/2025/09/02/index.html">HTML</a>',
        "html.parser",
    )
    assert spider.extraer_urls(soup) == [
        "https://www.boe.es/borme/dias/2025/09/02/pdfs/BORME-A-2025-167-28.pdf",
        "https://www.boe.es/borme/otro.pdf",
    ]


def test_spider_no_duplica_urls(tmp_path):
    fichero = tmp_path / "urls.txt"
    spider.guardar_fichero(["a", "b", "a"], str(fichero))
    spider.guardar_fichero(["b", "c"], str(fichero))
    assert fichero.read_text().split() == ["a", "b", "c"]


class _Respuesta:
    def __init__(self, status_code=200, content=b"%PDF-1.4"):
        self.status_code = status_code
        self.content = content


class _SesionFalsa:
    """Sustituye a la sesión HTTP real para no depender de la red en los tests."""

    def __init__(self, status_code=200):
        self.status_code = status_code
        self.peticiones = []

    def get(self, url, timeout):
        self.peticiones.append(url)
        return _Respuesta(self.status_code)


def test_fetcher_omite_pdfs_ya_descargados(tmp_path, monkeypatch):
    sesion = _SesionFalsa()
    monkeypatch.setattr(fetcher, "SESION", sesion)
    monkeypatch.setattr(fetcher.time, "sleep", lambda segundos: None)

    urls = ["https://x/a.pdf", "https://x/b.pdf"]
    assert fetcher.descargar_archivos(urls, str(tmp_path)) == 0
    assert fetcher.descargar_archivos(urls + ["https://x/c.pdf"], str(tmp_path)) == 0

    # Solo se descarga c.pdf la segunda vez
    assert len(sesion.peticiones) == 3
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.pdf", "b.pdf", "c.pdf"]


def test_fetcher_cuenta_descargas_fallidas(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "SESION", _SesionFalsa(status_code=500))
    monkeypatch.setattr(fetcher.time, "sleep", lambda segundos: None)

    assert fetcher.descargar_archivos(["https://x/a.pdf"], str(tmp_path)) == 1
    assert list(tmp_path.iterdir()) == []  # ni PDF ni fichero .part a medias