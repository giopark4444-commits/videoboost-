# 🚀 VideoBoost

Mejora la calidad de **videos e imágenes** con IA, **100% local** — sin nube, sin
suscripciones, sin subir nada a internet. Calidad nivel **Topaz Video AI** (o superior
en video degradado) gracias a la generación actual de motores open source.

*App for AI video & image enhancement, fully local, Topaz-level quality. UI available
in English, Spanish and French.* · *Application d'amélioration vidéo/image par IA,
100 % locale, qualité niveau Topaz. Interface en français, anglais et espagnol.*

-----

## Plataformas

| Plataforma | Nivel máximo | Motores |
|---|---|---|
| **Mac con chip M** (M1–M4, ideal Max/Pro con 32 GB+) | Pro | SeedVR2 (Metal/MPS), HYPIR, motores Vulkan |
| **PC con NVIDIA 16 GB+** (ej. RTX 4080) | Máximo | SeedVR2 7B, FlashVSR, HYPIR, SUPIR, Vulkan |
| **PC con NVIDIA 8–12 GB** | Pro | SeedVR2 (GGUF), HYPIR, Vulkan |
| **Cualquier otra GPU** (GTX 1660, AMD, Intel) | Compatible | Real-ESRGAN, Real-CUGAN, waifu2x, RIFE |

La app detecta tu hardware al arrancar y solo muestra lo que puede funcionar.

## Instalación

**Mac (chip M):**
```bash
bash install/instalar_mac.sh     # ffmpeg + PyTorch (Metal) + SeedVR2 + Vulkan
./iniciar.sh
```

**Windows + NVIDIA:** doble clic en `install\INSTALAR_NVIDIA.bat`, luego `INICIAR.bat`.

**Linux + NVIDIA:**
```bash
bash install/instalar_nvidia.sh && ./iniciar.sh
```

**Extras opcionales** (después de la base):
- Motores de imágenes: `install/extras_imagenes.sh` (añade `--supir` para SUPIR) /
  `install\EXTRAS_IMAGENES.bat`
- Restauración de caras (CodeFormer): `install/extras_caras.sh` / `install\EXTRAS_CARAS.bat`
- Colorización (DDColor): `install/extras_color.sh` / `install\EXTRAS_COLOR.bat`
- InstantIR (imágenes, solo NVIDIA): `install/extras_instantir.sh` / `install\EXTRAS_INSTANTIR.bat`
- FlashVSR (modo rápido, solo NVIDIA): `install/extras_flashvsr.sh` / `.bat`

## Los motores

### Video

| Motor | Qué hace | Hardware |
|---|---|---|
| **SeedVR2** (ByteDance) | Restauración por difusión en 1 paso con consistencia temporal nativa. **El nivel Topaz.** | NVIDIA 8 GB+ o Mac M |
| **FlashVSR** (Shanghai AI Lab) | Super-resolución casi en tiempo real. Para horas de material. Experimental. | Solo NVIDIA |
| **Real-ESRGAN** | El todoterreno clásico para video real. | Cualquier GPU |
| **Real-CUGAN / waifu2x** | Anime (con ruido / limpio). | Cualquier GPU |
| **RIFE** | Multiplica los fps (30→60/120). | Cualquier GPU |

### Imágenes

| Motor | Qué hace | Hardware |
|---|---|---|
| **HYPIR** (XPixel, SIGGRAPH 2025) | Restauración SOTA en 1 paso, controlable con prompt. | NVIDIA o Mac M |
| **SUPIR** (XPixel) | Máximo detalle reconstruido (nivel poros de piel). Lento. | Ideal NVIDIA 16 GB+ |
| **InstantIR** (instantX) | Restauración instantánea, calidad ≥ SUPIR, **licencia Apache 2.0** (comercial). | Solo NVIDIA |
| **CodeFormer** | Restauración de **caras** (ojos, dientes, piel). El "face model" tipo HitPaw. | NVIDIA o Mac M |
| **DDColor** | **Colorizar** fotos en blanco y negro. El "colorize model" tipo HitPaw. | NVIDIA (Mac: CPU) |
| **SeedVR2** | El motor de video sobre una imagen suelta. | NVIDIA 8 GB+ o Mac M |
| **Real-ESRGAN** | Escalado instantáneo. | Cualquier GPU |

### ¿Y los de pago (Topaz, Magnific, HitPaw)?

Son productos cerrados, pero la técnica detrás es conocida — y aquí la tienes gratis:

| Producto de pago | Lo que hace por dentro | Tu equivalente en VideoBoost |
|---|---|---|
| **HitPaw** | GANs clásicos: upscale, caras, interpolación, colorizado | Vulkan + **CodeFormer** + **DDColor** + RIFE |
| **Magnific AI** | Difusión Stable Diffusion por mosaicos (tile) | **SUPIR / HYPIR** |
| **Topaz Video AI** | Modelos propios de video con consistencia temporal | **SeedVR2** (igual o mejor) |

**El combo «Topaz completo»:** primero SeedVR2 (restaura + escala con consistencia
temporal), luego RIFE sobre el resultado (más fps). Resolución **y** fluidez.

## Licencias

- SeedVR2, FlashVSR e **InstantIR**: **Apache 2.0** (sin restricción de uso).
- Real-ESRGAN, Real-CUGAN, waifu2x, RIFE, GFPGAN: BSD/MIT/Apache.
- **HYPIR, SUPIR y CodeFormer: solo uso no comercial** sin permiso escrito de sus
  autores (HYPIR/SUPIR: jinjin.gu@suppixel.ai; CodeFormer: NTU S-Lab License).
  Para uso personal no hay restricción.

## Problemas frecuentes

- **Memoria insuficiente con SeedVR2:** baja la resolución objetivo, usa un modelo
  GGUF más pequeño o reduce los frames por lote (regla 4n+1: 1, 5, 9, 13…).
- **Mac: «no se puede abrir» un binario Vulkan:** el instalador quita la cuarentena,
  pero si pasa: `xattr -dr com.apple.quarantine bin/`.
- **La primera ejecución de SeedVR2 tarda:** está descargando el modelo (varios GB)
  a `models/SEEDVR2/`. Solo pasa una vez.
- **GTX 1660 u otra GPU de 6 GB:** quédate con los motores Vulkan; SeedVR2 ahí es
  impracticablemente lento.

## Estructura

```
videoboost/
├── app.py                  # Interfaz Gradio multilingüe (es/en/fr)
├── i18n.py                 # Traducciones
├── hardware.py             # Detección CUDA / MPS / Vulkan y niveles
├── engines/
│   ├── vulkan.py           # Real-ESRGAN, Real-CUGAN, waifu2x, RIFE (ncnn-Vulkan)
│   ├── seedvr2.py          # SeedVR2 vía CLI standalone (CUDA y MPS)
│   ├── flashvsr.py         # FlashVSR (experimental, NVIDIA)
│   ├── images.py           # HYPIR y SUPIR (venvs propios)
│   ├── instantir.py        # InstantIR — restauración de imágenes (NVIDIA, venv propio)
│   ├── faces.py            # CodeFormer — restauración de caras (venv propio)
│   ├── color.py            # DDColor — colorización B/N → color (venv propio)
│   └── ffmpeg_utils.py     # Extraer/reensamblar frames, info de video
├── install/                # Instaladores por plataforma + descarga de binarios
├── bin/, vendor/, models/  # Descargados por los instaladores (no versionados)
└── salidas/                # Resultados
```

Ver [PROPUESTA.md](PROPUESTA.md) para el razonamiento técnico completo del stack.
