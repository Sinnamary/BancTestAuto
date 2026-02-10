"""
Outil en ligne de commande pour discuter directement avec l'oscilloscope
HANMATEK DOS1102 via l'interface USB (PyUSB).

Exemples d'utilisation (à lancer depuis la racine du projet) :

    python -m tools.dos1102_cli --idn
    python -m tools.dos1102_cli --ask ":MEAS?"
    python -m tools.dos1102_cli --write ":CH1:COUP GND"
    python -m tools.dos1102_cli --waveform
    python -m tools.dos1102_cli --repl
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from core.dos1102_usb_connection import Dos1102UsbConnection
from core.dos1102_protocol import Dos1102Protocol


# Valeurs par défaut observées dans les logs (voir app_*.log)
DEFAULT_VENDOR_ID = 0x5345
DEFAULT_PRODUCT_ID = 0x1234


def _parse_hex_or_int(value: str) -> int:
    """Parse un entier, en acceptant la notation hexadécimale (ex. 0x5345)."""
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Valeur entière/hexadécimale invalide: {value!r}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Outil de test en ligne de commande pour l'oscilloscope HANMATEK DOS1102\n"
            "via l'interface USB (PyUSB + libusb).\n\n"
            "Quelques exemples d'utilisation :\n"
            "  python -m tools.dos1102_cli --idn\n"
            "  python -m tools.dos1102_cli --ask \":MEAS?\"\n"
            "  python -m tools.dos1102_cli --write \":CH1:COUP GND\"\n"
            "  python -m tools.dos1102_cli --waveform\n"
            "  python -m tools.dos1102_cli --repl\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--vendor",
        type=_parse_hex_or_int,
        default=DEFAULT_VENDOR_ID,
        help="ID vendeur USB (hex ou décimal), ex. 0x5345.",
    )
    parser.add_argument(
        "--product",
        type=_parse_hex_or_int,
        default=DEFAULT_PRODUCT_ID,
        help="ID produit USB (hex ou décimal), ex. 0x1234.",
    )
    parser.add_argument(
        "--read-timeout-ms",
        type=int,
        default=5000,
        help="Timeout de lecture USB en millisecondes (par défaut: 5000).",
    )
    parser.add_argument(
        "--write-timeout-ms",
        type=int,
        default=2000,
        help="Timeout d'écriture USB en millisecondes (par défaut: 2000).",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--idn",
        action="store_true",
        help="Envoie *IDN? et affiche la réponse.",
    )
    group.add_argument(
        "--ask",
        metavar="CMD",
        help="Envoie une commande SCPI et lit la réponse (ex. \":MEAS?\").",
    )
    group.add_argument(
        "--write",
        dest="write_cmd",
        metavar="CMD",
        help="Envoie une commande SCPI sans attendre de réponse.",
    )
    group.add_argument(
        "--waveform",
        action="store_true",
        help="Envoie :WAV:DATA:ALL? et affiche un résumé de la réponse.",
    )
    group.add_argument(
        "--repl",
        action="store_true",
        help="Lance un mode interactif (boucle de saisie).",
    )

    return parser


def open_connection(
    vendor_id: int,
    product_id: int,
    read_timeout_ms: int,
    write_timeout_ms: int,
) -> Dos1102UsbConnection:
    conn = Dos1102UsbConnection(
        id_vendor=vendor_id,
        id_product=product_id,
        read_timeout_ms=read_timeout_ms,
        write_timeout_ms=write_timeout_ms,
    )
    conn.open()
    return conn


def cmd_idn(proto: Dos1102Protocol) -> int:
    print("TX: *IDN?")
    try:
        reply = proto.idn()
    except Exception as exc:  # pragma: no cover - outil manuel
        print(f"ERREUR lors de *IDN?: {exc}", file=sys.stderr)
        return 1
    if reply:
        print(f"RX: {reply!r}")
    else:
        print("RX: (aucune donnée reçue)")
    return 0


def cmd_ask(proto: Dos1102Protocol, command: str) -> int:
    cmd = command.strip()
    print(f"TX: {cmd!r}")
    try:
        reply = proto.ask(cmd)
    except Exception as exc:  # pragma: no cover - outil manuel
        print(f"ERREUR lors de la commande {cmd!r}: {exc}", file=sys.stderr)
        return 1
    if reply:
        print(f"RX: {reply!r}")
    else:
        print("RX: (aucune donnée reçue)")
    return 0


def cmd_write(proto: Dos1102Protocol, command: str) -> int:
    cmd = command.strip()
    print(f"TX (write): {cmd!r}")
    try:
        proto.write(cmd)
    except Exception as exc:  # pragma: no cover - outil manuel
        print(f"ERREUR lors de l'envoi {cmd!r}: {exc}", file=sys.stderr)
        return 1
    print("OK (commande envoyée)")
    return 0


def cmd_waveform(proto: Dos1102Protocol) -> int:
    print("TX: :WAV:DATA:ALL?")
    try:
        data = proto.waveform_data_raw()
    except Exception as exc:  # pragma: no cover - outil manuel
        print(f"ERREUR lors de :WAV:DATA:ALL?: {exc}", file=sys.stderr)
        return 1

    if isinstance(data, bytes):
        size = len(data)
        preview = data[:32]
        print(f"RX: bloc binaire ({size} octets)")
        print(f"    Aperçu (32 octets max): {preview!r}")
    else:
        text = str(data)
        print(f"RX (texte): {text!r}")
    return 0


def run_repl(proto: Dos1102Protocol) -> int:
    print(
        "Mode interactif DOS1102.\n"
        "  - Les lignes terminées par '?' sont envoyées avec lecture de réponse (ask).\n"
        "  - Les autres lignes sont envoyées sans lecture (write).\n"
        "  - Commandes spéciales : 'waveform' pour :WAV:DATA:ALL?, 'exit' ou Ctrl+C pour quitter.\n"
    )
    while True:  # pragma: no cover - outil manuel
        try:
            line = input("dos1102> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        cmd = line.strip()
        if not cmd:
            continue
        if cmd.lower() in {"exit", "quit"}:
            return 0
        if cmd.lower() == "waveform":
            rc = cmd_waveform(proto)
            if rc != 0:
                return rc
            continue

        try:
            if cmd.endswith("?"):
                rc = cmd_ask(proto, cmd)
            else:
                rc = cmd_write(proto, cmd)
        except KeyboardInterrupt:
            print("\n(interruption utilisateur)")
            continue

        if rc != 0:
            # On continue malgré les erreurs pour faciliter le debug interactif.
            print(f"(commande terminée avec code {rc})")
    # unreachable


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        conn = open_connection(
            vendor_id=args.vendor,
            product_id=args.product,
            read_timeout_ms=args.read_timeout_ms,
            write_timeout_ms=args.write_timeout_ms,
        )
    except Exception as exc:  # pragma: no cover - outil manuel
        print(
            f"Impossible d'ouvrir le périphérique USB {args.vendor:04x}:{args.product:04x}: {exc}",
            file=sys.stderr,
        )
        return 1

    proto = Dos1102Protocol(conn)  # type: ignore[arg-type]

    try:
        if args.idn:
            return cmd_idn(proto)
        if args.ask:
            return cmd_ask(proto, args.ask)
        if args.write_cmd:
            return cmd_write(proto, args.write_cmd)
        if args.waveform:
            return cmd_waveform(proto)
        # Par défaut, on lance le REPL pour faciliter le debug.
        return run_repl(proto)
    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover - outil manuel
    raise SystemExit(main())

