"""Panel de administración de licencias VideoBoost — uso exclusivo del vendedor.

Genera y verifica claves de licencia Ed25519 firmadas offline.
Requiere que `clave_privada.pem` exista en la carpeta del proyecto
(créala con `python licencias.py init` si aún no existe).

Uso:
    python admin_licencias.py

La app abre en http://localhost:7861 (puerto distinto al de la app principal).
"""

import json
from datetime import date
from pathlib import Path

import gradio as gr

RAIZ = Path(__file__).resolve().parent
PRIVADA = RAIZ / "clave_privada.pem"
PREFIJO = "VB1-"


def _b64e(b: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    import base64
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _generar_clave(cliente: str) -> str:
    """Genera una clave de licencia firmada con la clave privada local."""
    if not cliente or not cliente.strip():
        return "⚠️ Escribe el nombre o correo del cliente."
    if not PRIVADA.exists():
        return (f"❌ No se encontró `{PRIVADA.name}`.\n\n"
                "Crea el par de claves primero:\n```\npython licencias.py init\n```")
    try:
        from cryptography.hazmat.primitives import serialization
        priv = serialization.load_pem_private_key(PRIVADA.read_bytes(), password=None)
        payload = json.dumps(
            {"cliente": cliente.strip(), "emitida": date.today().isoformat()},
            separators=(",", ":"),
        ).encode()
        clave = PREFIJO + _b64e(payload) + "." + _b64e(priv.sign(payload))
        return clave
    except ImportError:
        return "❌ Instala `cryptography`: `pip install cryptography`"
    except Exception as e:
        return f"❌ Error al generar: {e}"


def _verificar_clave(clave: str) -> str:
    """Verifica una clave de licencia usando la clave pública embebida."""
    if not clave or not clave.strip():
        return "⚠️ Pega una clave para verificar."
    try:
        from licencias import verificar
        datos = verificar(clave.strip())
        return (f"✅ **Válida**\n\n"
                f"- **Cliente:** {datos.get('cliente', '?')}\n"
                f"- **Emitida:** {datos.get('emitida', '?')}")
    except ImportError:
        return "❌ No se pudo importar `licencias.py`."
    except ValueError as e:
        return f"❌ **No válida:** {e}"
    except Exception as e:
        return f"❌ Error: {e}"


def _verificar_raw(clave: str) -> str:
    """Verifica sin necesitar licencia_publica.py (usa la privada para decodificar)."""
    if not clave or not clave.strip():
        return "⚠️ Pega una clave para verificar."
    clave = clave.strip()
    if not clave.startswith(PREFIJO) or "." not in clave:
        return "❌ Formato de clave no válido (debe empezar por VB1-)."
    try:
        cuerpo, _ = clave[len(PREFIJO):].split(".", 1)
        datos = json.loads(_b64d(cuerpo))
        # Si hay clave pública configurada, usamos verificar() completo
        try:
            from licencias import verificar
            datos = verificar(clave)
            return (f"✅ **Firma verificada**\n\n"
                    f"- **Cliente:** {datos.get('cliente', '?')}\n"
                    f"- **Emitida:** {datos.get('emitida', '?')}")
        except ValueError as e:
            return f"❌ **Firma inválida:** {e}"
        except ImportError:
            pass
        # Sin clave pública, solo mostramos el payload (sin verificar firma)
        return (f"ℹ️ **Payload** (firma no verificada — configura `licencia_publica.py`)\n\n"
                f"- **Cliente:** {datos.get('cliente', '?')}\n"
                f"- **Emitida:** {datos.get('emitida', '?')}")
    except Exception as e:
        return f"❌ Error al decodificar: {e}"


CSS = """
.admin-title { font-size: 1.4em; font-weight: 700; margin-bottom: 0.3em; }
.admin-note { color: #888; font-size: 0.88em; margin-top: 0.5em; }
"""

with gr.Blocks(title="VideoBoost — Admin Licencias", css=CSS) as admin:
    gr.HTML('<div class="admin-title">🔑 VideoBoost — Panel de licencias</div>'
            '<div class="admin-note">Solo para uso del vendedor. '
            'No compartas esta herramienta.</div>')

    with gr.Tab("Generar clave"):
        gr.Markdown(
            "Introduce el nombre o correo del cliente y pulsa **Generar**. "
            "La clave generada es válida permanentemente y funciona offline. "
            "Envíasela al cliente para que la pegue en la pantalla de activación."
        )
        gen_cliente = gr.Textbox(
            label="Cliente (nombre o correo)",
            placeholder="ej.: juan@empresa.com",
        )
        gen_btn = gr.Button("Generar clave", variant="primary")
        gen_out = gr.Textbox(
            label="Clave generada (copia y envía al cliente)",
            lines=3,
            interactive=False,
            show_copy_button=True,
        )
        gen_btn.click(_generar_clave, gen_cliente, gen_out)

    with gr.Tab("Verificar clave"):
        gr.Markdown(
            "Pega una clave `VB1-…` para comprobar su validez y ver a qué "
            "cliente pertenece. Útil para soporte o diagnóstico."
        )
        ver_in = gr.Textbox(
            label="Clave de licencia (VB1-…)",
            lines=3,
            placeholder="VB1-...",
        )
        ver_btn = gr.Button("Verificar", variant="primary")
        ver_out = gr.Markdown()
        ver_btn.click(_verificar_raw, ver_in, ver_out)

    with gr.Tab("Info"):
        def _info():
            privada_ok = PRIVADA.exists()
            try:
                from licencia_publica import CLAVE_PUBLICA
                publica_ok = bool(CLAVE_PUBLICA)
            except ImportError:
                publica_ok = False

            lineas = [
                f"- **`clave_privada.pem`:** {'✅ presente' if privada_ok else '❌ no encontrada'}",
                f"- **`licencia_publica.py`:** {'✅ configurada' if publica_ok else '⚠️ no configurada (modo dev)'}",
                "",
                "### Comandos útiles",
                "```",
                "# Crear par de claves (solo una vez)",
                "python licencias.py init",
                "",
                "# Generar clave por CLI",
                'python licencias.py generar --cliente "correo@cliente.com"',
                "",
                "# Verificar clave por CLI",
                "python licencias.py verificar VB1-...",
                "```",
            ]
            return "\n".join(lineas)

        gr.Markdown(_info())


if __name__ == "__main__":
    admin.launch(server_port=7861, inbrowser=True)
