#!/usr/bin/env python3
"""
Met à jour le numéro de version et la date dans core/version.py.

Usage :
  python bump_version.py patch   → 1.0.0 → 1.0.1 (correctif)
  python bump_version.py minor   → 1.0.1 → 1.1.0 (nouvelle fonctionnalité)
  python bump_version.py major   → 1.1.0 → 2.0.0 (changement majeur)

La date __version_date__ est mise à jour avec la date du jour.
"""
import re
import sys
from datetime import date
from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parent / "core" / "version.py"
VERSION_PATTERN = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
DATE_PATTERN = re.compile(r'^__version_date__\s*=\s*.*$', re.MULTILINE)


def parse_version(s: str) -> tuple[int, int, int]:
    """Parse '1.2.3' → (1, 2, 3)."""
    parts = s.strip().split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return major, minor, patch


def bump(version: str, kind: str) -> str:
    """Incrémente la version selon kind (patch, minor, major)."""
    major, minor, patch = parse_version(version)
    if kind == "patch":
        patch += 1
    elif kind == "minor":
        minor += 1
        patch = 0
    elif kind == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Kind attendu: patch, minor ou major (reçu: {kind!r})")
    return f"{major}.{minor}.{patch}"


def main():
    if len(sys.argv) != 2 or sys.argv[1].lower() not in ("patch", "minor", "major"):
        print("Usage: python bump_version.py patch|minor|major")
        print("")
        print("Exemples (depuis la racine du projet) :")
        print("  python bump_version.py patch   # 1.0.0 -> 1.0.1 (correctif)")
        print("  python bump_version.py minor   # 1.0.1 -> 1.1.0 (nouvelle fonctionnalite)")
        print("  python bump_version.py major   # 1.1.0 -> 2.0.0 (changement majeur)")
        sys.exit(1)
    kind = sys.argv[1].lower()

    if not VERSION_FILE.exists():
        print(f"Fichier introuvable: {VERSION_FILE}")
        sys.exit(1)

    text = VERSION_FILE.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(text)
    if not match:
        print("Impossible de trouver __version__ dans core/version.py")
        sys.exit(1)

    old_ver = match.group(1)
    new_ver = bump(old_ver, kind)
    today = date.today().isoformat()

    # Remplacer __version__ = "x.y.z" par la nouvelle version
    new_text = VERSION_PATTERN.sub(f'__version__ = "{new_ver}"', text, count=1)
    # Remplacer __version_date__ = ... par la date du jour
    new_text = DATE_PATTERN.sub(f'__version_date__ = "{today}"', new_text, count=1)

    VERSION_FILE.write_text(new_text, encoding="utf-8")
    print(f"Version {old_ver} -> {new_ver}, date -> {today}")


if __name__ == "__main__":
    main()
