# Guía de instalación y prueba de PixelBooster

Paso a paso para poner PixelBooster a funcionar en tus dos máquinas:
**PC con RTX 4080 (Windows)** y **Mac M4**. Empieza por el PC: es donde
corren TODOS los motores (los de solo-CUDA — FaithDiff, InstantIR, FlashVSR —
únicamente funcionan ahí).

---

## 0. Requisitos previos (las dos máquinas)

| Requisito | Por qué |
|-----------|---------|
| **Python 3.11** | Compatibilidad con las librerías de IA (evitar 3.12+) |
| **Git** | Para clonar el repositorio |
| Conexión a internet | Las descargas iniciales de modelos son varios GB |

---

## 1. RTX 4080 (Windows)

### 1.1 Instalar una vez
- **Python 3.11** → https://www.python.org/downloads/release/python-3119/
  - ⚠️ En el instalador marca **"Add Python to PATH"**.
- **Git** → https://git-scm.com/download/win
- **Drivers NVIDIA** recientes (GeForce Game Ready o Studio, ≥ 551.x).
  - No hace falta el CUDA Toolkit completo: PyTorch trae sus propias
    librerías CUDA. Basta el driver.

### 1.2 Bajar el repositorio
Abre **PowerShell**:
```powershell
git clone https://github.com/giopark4444-commits/videoboost-
cd videoboost-
```

### 1.3 Instalar todo (un solo doble clic)
En el explorador de archivos, doble clic en:
```
INSTALAR_TODO.bat
```
Crea los venvs (`.venv`, `.venv-faithdiff`, `.venv-instantir`, `.venv-caras`,
`.venv-color`, `.venv-flashvsr`), baja los binarios Vulkan y prepara los
motores. Tarda un rato (varios GB). Si un motor falla, el instalador sigue con
el resto y lo avisa al final.

> **Si Windows bloquea el .bat** ("Windows protegió tu PC") →
> *Más información* → *Ejecutar de todas formas*.

### 1.4 Arrancar la app
Doble clic en `PixelBooster.bat` (o `python app.py` con el venv activado).
Se abre solo en el navegador.

### 1.5 Configuración recomendada (ya viene por defecto)
- SeedVR2: **7B fp8**, **batch 13**, **sin** `blocks_to_swap`.
- FaithDiff / InstantIR / FlashVSR: disponibles (solo-CUDA, aquí sí corren).
- fp8 activado.

---

## 2. Mac M4 (después del PC)

### 2.1 Instalar una vez
- **Python 3.11** → https://www.python.org/downloads/release/python-3119/
  (o `brew install python@3.11`).
- **Git** (viene con Xcode Command Line Tools: `xcode-select --install`).
- **FFmpeg completo** (recomendado para estabilización con libvidstab):
  `brew install ffmpeg`.

### 2.2 Bajar y arrancar
```bash
git clone https://github.com/giopark4444-commits/videoboost-
cd videoboost-
```
Doble clic en **`INSTALAR_TODO.command`**, luego en `PixelBooster.command`.

### 2.3 Diferencias clave del Mac (memoria unificada / MPS)
- **NO** se usa fp8 → en MPS va fp16 o GGUF.
- **NO** se pasa `--blocks_to_swap` (el CLI lo rechaza con memoria unificada).
- FaithDiff, InstantIR y FlashVSR **no corren** (son solo-CUDA).
- DDColor usa CPU en Mac (no MPS): funciona pero va lento.
- El batch de SeedVR2 depende de la RAM unificada. Con 48 GB+ cabe el 7B fp16.

---

## 3. Probar los motores (orden de prioridad)

| Motor | Cómo probarlo | Nota |
|-------|---------------|------|
| **Grano (FFmpeg)** | Tab Vídeo → motor Grano | Único 100% probado; debe ir ya |
| **Real-ESRGAN (Vulkan)** | Tab Imagen → ESRGAN | Binario ncnn, sin GPU CUDA |
| **RIFE (Vulkan)** | Tab Vídeo → RIFE | Interpolación de frames |
| **SeedVR2** | Tab Vídeo → SeedVR2 | Modelos en `models/SeedVR2/` |
| **FaithDiff** | Tab Imagen → FaithDiff | Solo CUDA; 1er uso baja ~8 GB |
| **DDColor** | Tab Imagen → DDColor | Colorización (CPU en Mac) |
| **CodeFormer** | Tab Imagen → Caras | Revisar licencia NTU S-Lab si se vende |
| **FlashVSR** | Tab Vídeo → FlashVSR | Solo CUDA; pesos por Git LFS |
| **InstantIR** | Tab Imagen → InstantIR | Solo CUDA; baja SDXL + DINOv2 + pesos |

---

## 4. Chequeos que confirman que el código encaja con tu hardware

Estos motores se escribieron **sin GPU disponible**, así que en la máquina real
hay que verificar tres cosas:

**a) SeedVR2 reconoce sus flags**
```powershell
.venv\Scripts\python vendor\seedvr2\inference_cli.py --help
```
(En Mac: `.venv/bin/python vendor/seedvr2/inference_cli.py --help`.)
Verifica que existen `--dit_model`, `--blocks_to_swap`, `--vae_*_tiled`,
`--attention_mode`, `--batch_size`, `--resolution`. Si el repo cambió, se
ajustan los flags en `engines/seedvr2.py`.

**b) FaithDiff carga RealVisXL** (solo RTX 4080)
Tab Imagen → FaithDiff con una imagen de prueba. Confirmar que RealVisXL se
carga en formato diffusers y el nombre real del `.bin`.

**c) FlashVSR encuentra su script** (solo RTX 4080)
Los entrypoints en `engines/flashvsr.py` son candidatos; el repo reorganiza
scripts entre versiones. Si falla, ajustar el nombre real del entrypoint.

---

## 5. Licencias (modo venta, opcional)

```bash
# Solo una vez: genera el par de claves Ed25519
python licencias.py init

# Generar una clave para un cliente
python licencias.py generar --cliente "correo@cliente.com"

# Verificar una clave
python licencias.py verificar VB1-...
```

- `clave_privada.pem` **JAMÁS** se sube al repositorio. Guárdala aparte.
- Panel gráfico de licencias: `python admin_licencias.py` (abre en el
  puerto 7861).
- Si existe `licencia_publica.py` con `CLAVE_PUBLICA`, la app exige activación.
  Sin ese archivo, corre en modo libre (dev).

---

## 6. Tamaños de descarga (referencia)

| Modelo | Tamaño aprox. | Motor |
|--------|---------------|-------|
| SeedVR2 7B fp8 | ~8 GB | SeedVR2 |
| RealVisXL V4.0 | ~7 GB | FaithDiff |
| FaithDiff pesos | ~2 GB | FaithDiff |
| InstantIR (SDXL + DINOv2 + pesos) | ~10 GB | InstantIR |

El instalador / primer uso de cada motor los baja automáticamente.
