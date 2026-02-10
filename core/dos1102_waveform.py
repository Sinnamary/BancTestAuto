"""
Parsing des données forme d'onde DOS1102 (réponse :WAV:DATA:ALL?).
Réutilisable sans UI (affichage courbe, export, analyse).
"""
import re
from typing import Union


def parse_ascii_waveform(data: Union[str, bytes]) -> list[float] | None:
    """
    Extrait une liste de nombres depuis la réponse ASCII (virgules, espaces, retours à la ligne).
    Si data est bytes, tente un decode UTF-8.
    Retourne None si données binaires non décodables ou aucune valeur trouvée.
    """
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8", errors="strict")
        except Exception:
            return None
    else:
        text = data
    parts = re.split(r"[\s,;]+", text.strip())
    values: list[float] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            values.append(float(p))
        except ValueError:
            continue
    return values if values else None


def waveform_display_summary(data: Union[str, bytes]) -> str:
    """
    Résumé pour affichage : texte brut ou "<binaire N octets>".
    """
    if isinstance(data, bytes):
        return f"<binaire {len(data)} octets>"
    return data if data else "—"
