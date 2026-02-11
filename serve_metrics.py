#!/usr/bin/env python3
"""
Lance un serveur HTTP local pour afficher le rapport de métriques de code
et ouvre le rapport dans le navigateur par défaut.

À lancer depuis la racine du projet (après avoir généré le rapport) :

  python run_metrics.py
  python serve_metrics.py

Si tools/code_metrics_report/ n'existe pas, le script indique comment générer le rapport.
"""
import webbrowser
from pathlib import Path

from http.server import HTTPServer, SimpleHTTPRequestHandler


def main():
    root = Path(__file__).resolve().parent
    report_dir = root / "tools" / "code_metrics_report"
    index_html = report_dir / "index.html"

    if not index_html.exists():
        print("Rapport de métriques introuvable. Générez-le d'abord avec :")
        print()
        print("  python run_metrics.py")
        print()
        print("Puis relancez : python serve_metrics.py")
        return 1

    port = 8766
    host = "127.0.0.1"
    url = f"http://{host}:{port}/"

    class QuietHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            kwargs["directory"] = str(report_dir)
            super().__init__(*args, **kwargs)

        def log_message(self, format, *args):
            pass  # Réduire le bruit dans la console

    server = HTTPServer((host, port), QuietHandler)

    print(f"Rapport de métriques : {url}")
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
