"""Sistema de licencias de PixelBooster — claves firmadas, verificación offline.

Modelo "Topaz": la app se instala en la máquina del cliente y se activa una vez
con una clave de licencia. No hay servidor: las claves van firmadas con Ed25519
y la app las verifica localmente con la clave pública embebida. Sin internet,
sin cuentas, coherente con la filosofía 100% local.

USO DEL VENDEDOR (tú), desde la carpeta del proyecto:

  python licencias.py init
      Crea tu par de claves. Escribe `clave_privada.pem` (SECRETA: guárdala
      fuera del repo, con copia de seguridad; quien la tenga puede emitir
      licencias) y embebe la pública en `licencia_publica.py`. A partir de ahí
      la app pide licencia. Sin este paso, la app corre libre (modo desarrollo).

  python licencias.py generar --cliente "correo@cliente.com"
      Emite una clave de licencia para ese cliente. Se la envías y listo.

  python licencias.py verificar VB1-...
      Comprueba una clave (diagnóstico).

USO DEL CLIENTE: pega la clave en la pantalla de activación de la app
(una sola vez; queda guardada en `licencia.json`).

Honestidad sobre el modelo: sin servidor no hay revocación — una clave emitida
vale para siempre y puede compartirse. Es el mismo equilibrio de muchas apps
indie; si algún día necesitas revocación, se añade un servidorcito de licencias
sin cambiar el formato de clave.
"""

import base64
import json
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PRIVADA = RAIZ / "clave_privada.pem"
PUBLICA_PY = RAIZ / "licencia_publica.py"
ACTIVACION = RAIZ / "licencia.json"
PREFIJO = "VB1-"


# ------------------------------------------------------------- runtime (app)

def _clave_publica():
    """Clave pública embebida, o None si no se ha configurado (modo dev)."""
    try:
        from licencia_publica import CLAVE_PUBLICA
        return CLAVE_PUBLICA or None
    except ImportError:
        return None


def requiere_licencia() -> bool:
    return _clave_publica() is not None


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verificar(clave: str):
    """Valida una clave de licencia. Devuelve el payload (dict) o lanza ValueError."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    pub_hex = _clave_publica()
    if pub_hex is None:
        raise ValueError("La app no tiene clave pública configurada (modo desarrollo).")
    clave = clave.strip()
    if not clave.startswith(PREFIJO) or "." not in clave:
        raise ValueError("Formato de clave no válido.")
    cuerpo, firma = clave[len(PREFIJO):].split(".", 1)
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex)).verify(
            _b64d(firma), _b64d(cuerpo))
    except (InvalidSignature, Exception) as e:
        raise ValueError("La clave no es válida.") from e
    return json.loads(_b64d(cuerpo))


def activa() -> dict | None:
    """Payload de la licencia activada en esta máquina, o None."""
    if not requiere_licencia():
        return {"cliente": "desarrollo"}
    try:
        return verificar(json.loads(ACTIVACION.read_text())["clave"])
    except Exception:
        return None


def activar(clave: str) -> dict:
    """Valida y guarda la clave en esta máquina. Devuelve el payload."""
    datos = verificar(clave)
    ACTIVACION.write_text(json.dumps({"clave": clave.strip()}, indent=1))
    return datos


# ------------------------------------------------------------- CLI (vendedor)

def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _cmd_init():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    if PRIVADA.exists():
        print(f"⚠️  Ya existe {PRIVADA.name}; no se sobreescribe (bórrala a mano si "
              "de verdad quieres regenerar — las licencias emitidas dejarían de valer).")
        return
    priv = Ed25519PrivateKey.generate()
    PRIVADA.write_bytes(priv.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    pub_hex = priv.public_key().public_bytes_raw().hex()
    PUBLICA_PY.write_text(
        '"""Clave pública de licencias (generada por licencias.py init).\n\n'
        'Si CLAVE_PUBLICA tiene valor, la app exige licencia. Déjala vacía ("")\n'
        'para volver al modo desarrollo (sin licencia)."""\n\n'
        f'CLAVE_PUBLICA = "{pub_hex}"\n')
    print(f"✅ Par de claves creado.\n"
          f"   SECRETA  → {PRIVADA.name}  (¡guárdala fuera del repo y haz backup!)\n"
          f"   pública  → {PUBLICA_PY.name}  (se versiona; activa el modo licencia)\n"
          f"   Emite claves con: python licencias.py generar --cliente \"correo\"")


def _cmd_generar(cliente: str):
    from cryptography.hazmat.primitives import serialization
    if not PRIVADA.exists():
        print("❌ No existe clave_privada.pem. Corre primero: python licencias.py init")
        sys.exit(1)
    priv = serialization.load_pem_private_key(PRIVADA.read_bytes(), password=None)
    payload = json.dumps({"cliente": cliente, "emitida": date.today().isoformat()},
                         separators=(",", ":")).encode()
    clave = PREFIJO + _b64e(payload) + "." + _b64e(priv.sign(payload))
    print(f"✅ Licencia para {cliente}:\n\n{clave}\n")


def _cmd_verificar(clave: str):
    try:
        datos = verificar(clave)
        print(f"✅ Válida · cliente: {datos['cliente']} · emitida: {datos['emitida']}")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["init"]:
        _cmd_init()
    elif args[:1] == ["generar"] and "--cliente" in args:
        _cmd_generar(args[args.index("--cliente") + 1])
    elif args[:1] == ["verificar"] and len(args) > 1:
        _cmd_verificar(args[1])
    else:
        print(__doc__)
