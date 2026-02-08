#!/usr/bin/env python3
"""
Lance un serveur HTTP local pour afficher le rapport de couverture htmlcov
et ouvre le rapport dans le navigateur par défaut.

À lancer depuis la racine du projet (après avoir généré le rapport) :

  pytest --cov=config --cov=core --cov-report=html
  python serve_htmlcov.py

Si htmlcov/ n'existe pas, le script indique comment générer le rapport.
"""
import webbrowser
from pathlib import Path

from http.server import HTTPServer, SimpleHTTPRequestHandler


def main():
    root = Path(__file__).resolve().parent
    htmlcov_dir = root / "htmlcov"
    index_html = htmlcov_dir / "index.html"

    if not index_html.exists():
        print("Rapport htmlcov introuvable. Générez-le d'abord avec :")
        print()
        print("  pytest --cov=config --cov=core --cov-report=term-missing --cov-report=html")
        print()
        print("Puis relancez : python serve_htmlcov.py")
        return 1

    port = 8765
    host = "127.0.0.1"
    url = f"http://{host}:{port}/"

    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            kwargs["directory"] = str(htmlcov_dir)
            super().__init__(*args, **kwargs)

        def log_message(self, format, *args):
            pass  # Réduire le bruit dans la console

    server = HTTPServer((host, port), QuietHandler)

    print(f"Rapport de couverture : {url}")
    print("Ouverture dans le navigateur... (Ctrl+C pour arrêter le serveur)")
    print()

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    exit(main())
