# PixelBooster · Propuesta v2 — Lo mejor de lo mejor (junio 2026)

> Reemplaza el plan de la sesión anterior ("Mejorador de Video con IA Local").
> Objetivo: calidad **nivel Topaz o superior**, 100% local y gratis, para video **e imágenes**.

-----

## Por qué el plan anterior ya no es el techo

El plan original tenía dos capas: motores Vulkan (Real-ESRGAN, Real-CUGAN, waifu2x, RIFE)
y un "Modo Estudio" con BasicVSR++/RealBasicVSR sobre mmagic. Tres problemas hoy:

1. **BasicVSR++ y RealBasicVSR son de 2021-2022.** Eran lo más cercano a Topaz en su momento,
   pero la generación actual de restauradores de video por difusión los supera con claridad.
2. **mmagic está prácticamente abandonado** — era justo el punto más frágil del plan
   (choques de versiones mmcv/mmengine/torch) y ya no se justifica sufrirlo.
3. La pieza que faltaba ("consistencia temporal nativa") hoy viene **de serie** en los
   motores nuevos, con licencias permisivas y soporte activo de la comunidad.

-----

## Los motores nuevos (todos chinos, todos open source)

### 🥇 SeedVR2 — ByteDance Seed · el "Topaz killer"

- **Qué es:** restaurador/upscaler de video por difusión en **un solo paso** (no 25-50 pasos),
  entrenado específicamente en secuencias de video → consistencia temporal nativa, sin parpadeo.
- **Calidad:** iguala o supera a Topaz Video AI en video real degradado; reconstruye detalle
  donde Real-ESRGAN solo "afila". También restaura **imágenes** (frame único).
- **Licencia:** Apache 2.0 (uso comercial permitido).
- **Hardware (con la integración de numz para ComfyUI, v2.5+):**
  - **RTX 4080 (16 GB):** modelo 7B en FP8 cómodo, FP16 con BlockSwap. Calidad máxima.
  - **8-12 GB:** 7B en GGUF Q4 + BlockSwap (≈95% de la calidad, mitad de VRAM).
  - **6 GB (GTX 1660):** 3B GGUF Q4 + BlockSwap + tiling — *funciona pero muy lento*;
    para la 1660 conviene mantener el fallback Vulkan (ver arquitectura).
- **Cómo se usa:** nodos de ComfyUI **o CLI standalone** (`inference_cli.py`) para batch —
  no obliga a usar la interfaz de ComfyUI, se puede llamar desde nuestra app Gradio.
- Repo: https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler
  (modelo original: ByteDance-Seed/SeedVR2)

### 🥈 FlashVSR — Shanghai AI Lab / OpenImagingLab · velocidad

- **Qué es:** super-resolución de video por difusión en **streaming casi tiempo real**
  (CVPR 2026). ~17 fps a 768×1408 en una A100; en una 4080 sigue siendo el motor
  rápido de la casa. Hasta ~12× más rápido que otros VSR de difusión de un paso.
- **Para qué:** cuando hay que procesar horas de material y SeedVR2 7B es demasiado lento.
  Compromiso calidad/velocidad excelente.
- Repo: https://github.com/OpenImagingLab/FlashVSR (v1.1, nov 2025)

### 🥉 Para imágenes: HYPIR y SUPIR — XPixel Group

| Motor | Perfil | Velocidad | VRAM |
|-------|--------|-----------|------|
| **HYPIR** (SIGGRAPH 2025) | Restauración SOTA, control por prompt de texto y riqueza de textura | **1 solo paso** — decenas de veces más rápido que DiffBIR/SUPIR | Corre hasta en una T4 gratis de Colab |
| **SUPIR** | Máximo detalle "alucinado" (nivel piel/poros). El que destronó a Magnific y Topaz Photo | 25-35 pasos, lento | Pesado (SDXL de base), ideal 4080 |

Regla práctica: **HYPIR por defecto** (rápido, fiel, controlable), **SUPIR** para la foto
especial donde quieres el máximo absoluto de detalle.

- https://github.com/XPixelGroup/HYPIR
- https://github.com/Fanghua-Yu/SUPIR

### Fluidez: RIFE sigue siendo el rey práctico

Para interpolación de frames (30→60/120 fps) RIFE 4.x sigue siendo la mejor relación
calidad/velocidad/compatibilidad. Se mantiene del plan anterior, vía ncnn-Vulkan.

-----

## Arquitectura propuesta: 3 niveles según hardware

```
videoboost/
├── app.py                 # Gradio en español, detecta hardware y muestra el nivel disponible
├── engines/
│   ├── vulkan.py          # Nivel 1: Real-ESRGAN / Real-CUGAN / RIFE (ncnn-Vulkan)
│   ├── seedvr2.py         # Nivel 2-3: wrapper del CLI de SeedVR2 (GGUF→FP8→FP16 según VRAM)
│   ├── flashvsr.py        # Nivel 3: modo rápido para lotes grandes (4080+)
│   └── images.py          # HYPIR (default) + SUPIR (máxima calidad) para fotos
├── install/               # Instaladores por nivel (el 1 no necesita CUDA)
└── bin/                   # Binarios Vulkan (no versionados)
```

| Nivel | Hardware | Motores | Qué obtiene el usuario |
|-------|----------|---------|------------------------|
| **1 · Compatible** | Cualquier GPU (GTX 1660, AMD, Intel, Mac) | Real-ESRGAN, Real-CUGAN, RIFE (Vulkan) | Lo del plan original — sólido, universal |
| **2 · Pro** | NVIDIA 8-12 GB | SeedVR2 GGUF Q4 + BlockSwap, HYPIR | **Nivel Topaz real**, en GPUs medias |
| **3 · Máximo** | RTX 4080 (16 GB+) | SeedVR2 7B FP8/FP16, FlashVSR, SUPIR | **Supera a Topaz** en video degradado |

La app detecta VRAM y CUDA al arrancar y habilita el nivel máximo posible,
degradando limpiamente al nivel 1 en cualquier máquina (igual filosofía que antes,
pero ahora el techo es mucho más alto).

### Qué cambia respecto al plan anterior

| Antes | Ahora | Por qué |
|-------|-------|---------|
| BasicVSR++ / RealBasicVSR + mmagic | **SeedVR2** | Mejor calidad, un solo paso, Apache 2.0, comunidad activa, sin el infierno de mmcv |
| Solo video | **Video + imágenes** (HYPIR/SUPIR) | Era parte del objetivo y el plan viejo no lo cubría |
| — | **FlashVSR** como modo rápido | Procesar material largo sin esperar días |
| GTX 1660 = Vulkan | Igual (Vulkan) | SeedVR2 3B en 6 GB existe pero es impracticablemente lento; honestidad técnica |

-----

## El nuevo "combo Topaz casero" (nivel 3, RTX 4080)

```bash
# 1. Restaurar + escalar con consistencia temporal (SeedVR2 7B)
python -m engines.seedvr2 video.mp4 --modelo 7b-fp8 --resolucion 2160

# 2. Interpolar a 60 fps (RIFE)
python -m engines.vulkan video_seedvr2.mp4 --motor rife --mult 2
```

A diferencia del combo anterior, el paso 1 ya incluye la consistencia temporal
que era "lo único que no replicábamos". Ya no falta nada frente a Topaz.

-----

## Puntos frágiles (honestidad técnica, actualizada)

1. **SeedVR2 necesita NVIDIA + CUDA** para ser práctico. La 1660 se queda en nivel 1.
2. **VRAM en 4K:** subir a 2160p con el 7B puede requerir tiling/BlockSwap incluso en 16 GB.
3. **FlashVSR** prioriza velocidad; para el material más valioso usar siempre SeedVR2.
4. **SUPIR "alucina" detalle:** espectacular en fotos, pero por eso mismo no es para
   material documental/forense donde la fidelidad importa más que la belleza.

-----

## Próximos pasos

1. Validar SeedVR2 en la 4080 con un clip corto (instalar `ComfyUI-SeedVR2_VideoUpscaler`
   y probar su CLI standalone antes de integrar nada).
2. Construir `engines/seedvr2.py` como wrapper del CLI + detección de VRAM.
3. Portar los motores Vulkan del proyecto anterior como nivel 1.
4. Añadir pestaña de imágenes con HYPIR (y SUPIR como opción "máxima calidad").
5. Integrar FlashVSR como "modo rápido" al final — es lo menos maduro de la lista.

-----

## Adiciones posteriores (junio 2026) y modelos a vigilar

Tras revisar el estado del arte más reciente:

- **FaithDiff** (CVPR 2025) — **añadido como motor de imagen recomendado por defecto**.
  Restauración fiel por difusión sobre SDXL; en su paper supera a SUPIR y es ~4× más
  rápido, pensado para fotos y películas antiguas. **Licencia MIT** (uso comercial
  libre). Solo CUDA. Evitamos LLaVA-13B usando `test_wo_llava.py` con un caption a
  partir de prompt. Repo: https://github.com/JyChen9811/FaithDiff

- **HYPIR y SUPIR — RETIRADOS.** Eran de uso **no comercial** (permiso a
  jinjin.gu@suppixel.ai). Para evitar problemas de licencia se sacaron del producto y
  se reemplazaron por **FaithDiff** (MIT) e **InstantIR** (Apache 2.0), que cubren la
  misma función con licencia libre. En Mac, la restauración por difusión queda sin
  reemplazo directo (FaithDiff/InstantIR son CUDA): allí se usa SeedVR2 (imagen).

- **InstantIR** (instantX-research) — **añadido**. Restauración de imágenes por
  difusión con referencia generativa: calidad a la par o superior a SUPIR en métricas
  (hasta +22% MANIQA), pero instantáneo (sin los 25-35 pasos de SUPIR) y con licencia
  **Apache 2.0** — el único motor de imagen del stack apto para uso comercial. Solo
  CUDA (SDXL + DINOv2), así que es exclusivo de la 4080; en Mac queda SeedVR2.
  Repo: https://github.com/instantX-research/InstantIR

- **InfVSR** — **a vigilar, aún sin código**. Es el único trabajo que afirma superar a
  SeedVR2 en video (≈5.48× más rápido con mejor calidad), reformulando VSR como
  difusión autoregresiva de un paso para inferencia en streaming. El repo marca el
  código como "TBC": es un paper, no algo usable. Cuando publiquen pesos, sería el
  candidato natural a reemplazar/complementar a SeedVR2. Paper: arXiv:2510.00948

- **CodeFormer++** — mejora marginal sobre CodeFormer en métricas perceptuales, pero
  sin integración madura. No compensa cambiar por ahora.

Conclusión: el stack de video (SeedVR2 + FlashVSR) sigue siendo lo mejor publicado;
en imágenes, InstantIR añade una opción rápida y de licencia libre para la 4080.

## Fuentes

- SeedVR2 para ComfyUI (GGUF, BlockSwap, CLI): https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler
- SeedVR2 v2.5 — 7B en GPUs de 8 GB: https://www.ainvfx.com/blog/seedvr2-v2-5-the-complete-redesign-that-makes-7b-models-run-on-8gb-gpus/
- FlashVSR (CVPR 2026): https://github.com/OpenImagingLab/FlashVSR · paper: https://arxiv.org/abs/2510.12747
- HYPIR (SIGGRAPH 2025): https://github.com/XPixelGroup/HYPIR
- SUPIR: https://github.com/Fanghua-Yu/SUPIR
- InstantIR (Apache 2.0): https://github.com/instantX-research/InstantIR
- InfVSR (paper, código pendiente): https://arxiv.org/html/2510.00948v2
