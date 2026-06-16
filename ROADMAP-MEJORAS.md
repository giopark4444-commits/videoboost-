# VideoBoost — Hoja de ruta de mejoras (futuro)

> Backlog de capacidades a añadir/mejorar, salido del barrido multi-agente del
> 2026-06-15 (20 categorías de mejora de imagen/video investigadas con licencia
> verificada en GitHub). **Nada de esto está implementado todavía** — está marcado
> para revisarlo y priorizarlo más adelante.
>
> Contexto fijo: la app **se VENDE** → solo licencias comerciales (MIT/Apache/BSD/
> LGPL-como-binario). Se descarta CC-BY-NC, S-Lab, GPL viral, "academic only" y
> repos sin LICENSE. Plataformas: **Mac Apple Silicon** (MPS/MLX, sin CUDA) + **PC
> RTX 4080** (CUDA).

---

## ✅ Estado de integración (actualizado 2026-06-15)

**YA INTEGRADOS** (motor + instalador + UI + i18n + Sistema/mantenimiento; NO probados
en GPU salvo donde se indica — verificar en la 4080):

- **Imagen (tab Imágenes):** NAFNet (denoise/deblur), SCUNet (denoise ciego), FBCNN
  (artefactos JPEG), FFTformer (deblur movim., NVIDIA), DehazeFormer (neblina),
  HVI-CIDNet (poca luz premium), DarkIR (noche extrema), **InSPyReNet** y **BiRefNet**
  (quitar fondo/matting — ✅ corren en Mac/MPS), RestoreFormer++ (caras, Apache),
  DSRNet (reflejos), ShadowFormer (sombras), IC-Light (relighting por prompt, NVIDIA).
- **Video (tab Video):** FILM, Practical-RIFE, EMA-VFI (slow-mo); DUT (estabilización IA, NVIDIA).
- **Filtros FFmpeg (sección «Imagen»):** desentrelazado **bwdif** (sustituye a yadif);
  **«Quitar artefactos de compresión»** (deblock+deband). ✅ probados en Mac.
- **IOPaint+LaMa** (borrar objetos): instalable en Sistema; **falta la UI de máscara**
  (no está en el selector todavía).

**HECHO en la 2ª tanda (2026-06-16):**
- ✅ **Sanear caras legal**: CodeFormer (S-Lab) y OSDFace (sin licencia) EXCLUIDOS del
  build comercial por defecto (`VB_NO_COMERCIAL=1` los reactiva). FaithDiff confirmado
  MIT → se mantiene.
- ✅ **UI de máscara para IOPaint**: nuevo tab **«Borrar objetos»** (lienzo + LaMa).
- ✅ Filtro **emulación de película** (cine: halation+bloom+viñeta) — probado en Mac.
- ✅ Filtro **corrección de lente** (lenscorrection k1/k2) — probado en Mac.

**PENDIENTE / bloqueado:**
- **HDR / tone mapping**: ⛔ bloqueado — el FFmpeg de Homebrew no trae `zscale`/
  `libplacebo`; requiere recompilar FFmpeg con libzimg+libplacebo.
- **Igualar color** (entre tomas) y **balance de blancos auto**: necesitan input de
  referencia / cv2 → más UI (siguiente tanda).
- **DDColor MPS**: el script oficial cae a CPU en Mac; forzar MPS es arriesgado (ops no
  soportadas) → pendiente de probar con cuidado.
- **RIFE→v4.26**: cubierto en la práctica por **Practical-RIFE** (4.x) ya integrado.
- **IC-Light**: funciona con dirección de luz por defecto; falta dropdown de dirección
  (polish, NVIDIA-only).
- **OSEDiff/DRCT** (modos SR rápido/fidelidad): opcional.
- Verificar en la 4080 todos los motores GPU; confirmar licencia comercial de **DUT**
  con el autor.

---

## 0) 🚨 RIESGO LEGAL — atender antes de vender (bloqueante)

| Problema | Detalle | Acción |
|---|---|---|
| **CodeFormer embebido** | Licencia **S-Lab = NO comercial** (`engines/faces.py`) | Retirar del build comercial **o** dejarlo como plugin opt-in que descarga el usuario |
| **OSDFace embebido** | **Sin LICENSE** + base SD2.1 (`engines/osdface.py`) | Retirar / opt-in (ya marcado "solo pruebas") |
| **FaithDiff** | **Sin licencia clara** (`engines/faithdiff.py`) | Verificar licencia o aislar como opt-in |
| **Reemplazo de caras** | — | Quedarse con **PMRF** (MIT) por defecto + **RestoreFormer++** (Apache-2.0) de respaldo; DiffBIR-face (Apache) ya está |

---

## 1) Imprescindibles que faltan o están a medias

| Capacidad | Estado | Mejor pick comercial | Licencia | Plataforma | Dif. |
|---|---|---|---|---|---|
| **Quitar artefactos de compresión** (blocking H.264/JPEG, banding) | ❌ no | **FBCNN** (slider de calidad) + FFmpeg `spp/pp7 + deband`; **PromptCIR** (ganador NTIRE'24) modo máx. en RTX | Apache-2.0 / LGPL / Apache-2.0 | ambas | baja |
| **Denoise por GPU de más calidad** | ⚠️ parcial (Restormer img + hqdn3d CPU) | **NAFNet** (40.30 dB SIDD, supera a Restormer y más rápido) + **SCUNet** (denoise ciego) | MIT / Apache-2.0 | ambas | media |

> Nitidez, deblur, super-resolución y low-light ya están cubiertos a nivel
> imprescindible (ver §4).

---

## 2) ⬆️ Actualizables: lo que hoy es CPU/FFmpeg → upgrade GPU de más calidad

| Categoría | Hoy | Upgrade | Licencia | Plataforma | Métrica/nota |
|---|---|---|---|---|---|
| **Denoise** | Restormer + hqdn3d | **NAFNet** + **SCUNet** ciego | MIT / Apache-2.0 | ambas | NAFNet 40.30 dB SIDD |
| **Deblur movimiento** | Restormer (solo NVIDIA) | **FFTformer** (34.21 dB GoPro) + **NAFNet** ligero (ruta MPS) | MIT / MIT | ambas | conservar Restormer para defocus 1-img |
| **Desentrelazado** | solo `yadif` (el más básico) | **bwdif** (nuevo default) + **estdif**; IA: **DDD/Disney Deep Deinterlacing** | LGPL / LGPL / MIT | ambas | bwdif ya está en el FFmpeg empaquetado |
| **Estabilización** | vidstab + deshake (2D, CPU) | **DUT** (DUTCode, IA por malla) ambas; **GaVS** (3D full-frame SIGGRAPH'25) solo RTX | MIT / MIT | DUT ambas · GaVS nvidia | GaVS necesita CUDA + gaussian splatting |
| **Colorización** | DDColor pero **corre en CPU en Mac** (lento) + solo imagen | forzar **device=mps/cuda** + **re-DDColor** (gana MPS + color de VÍDEO) | Apache-2.0 | ambas | quick win enorme |
| **Interpolación frames** | RIFE 4.6 (Vulkan) + FILM/Practical-RIFE/EMA-VFI ya añadidos | actualizar binario Vulkan a **rife-v4.26** (mismo `.exe`, mejor calidad gratis) | MIT | ambas | trivial |
| **Super-resolución** | Real-ESRGAN/SeedVR2/HAT/DiffBIR | **OSEDiff** (difusión 1-paso, rápida) + **DRCT-L** (fidelidad/PSNR sin inventar) | Apache-2.0 / MIT | ambas | modos rápido/fidelidad |
| **Low-light** | Retinexformer (ya SOTA) | **HVI-CIDNet** (ganador NTIRE'25, mejor en LOLv2) + **DarkIR** (luz+ruido+desenfoque en 1 pasada, "noche extrema") | MIT / MIT | ambas | HVI-CIDNet 28.14 dB LOLv1 |
| **Emulación de película** | grano + LUTs + viñeta | pasada FFmpeg propia de **halation + bloom + viñeteado óptico cos⁴**; opcional `spectral_film_lut` (LUTs por datasheet) | propio / MIT | ambas | |

---

## 3) ✨ Capacidades NUEVAS muy vendibles (no existen hoy)

| Capacidad | Pick principal | Alternativa/notas | Licencia | Plataforma | Dif. |
|---|---|---|---|---|---|
| **Quitar fondo / matting** (tipo Topaz/Photoshop) | **InSPyReNet / transparent-background** (pip de 1 línea) | **BiRefNet** HR-matting (calidad) | MIT | ambas | baja |
| **Quitar neblina/calima (dehazing)** | **DehazeFormer** (>40 dB SOTS-indoor) | **gUNet** (modo rápido) | MIT / MIT | ambas | media |
| **HDR / mapeo tonal** | **FFmpeg libplacebo** BT.2390 (HDR→SDR, ya en el binario) | **HDRTVDM** (MPL-2.0, SDR→HDR, 37.09 dB) + **GMNet** (gain-map iPhone, MIT) | LGPL / MPL-2.0 / MIT | ambas | baja (FFmpeg) |
| **Relighting / reiluminación** | **IC-Light v1** (SD1.5) | requiere **BiRefNet** para máscara (no RMBG, que es NC) | Apache-2.0 | ambas | alta |
| **Borrar objetos / quitar con máscara** | **SAM 2** + **LaMa** vía **IOPaint** (solo motor LaMa) | todo Apache; evitar ProPainter (S-Lab) | Apache-2.0 | ambas | alta |
| **Igualar color entre tomas** | **color_transfer** (Reinhard) + `skimage` | WCT2 (MIT) solo NVIDIA; evitar color-matcher (GPL) | MIT | ambas | baja |
| **Corrección de lente** (distorsión/aberración/de-vignette) | FFmpeg **`lenscorrection`** (k1/k2, ya está) | **OpenCV** (undistort + canal R/B) auto; **GeoCalib** estima sin EXIF; **NO** usar lensfun de FFmpeg (exige `--enable-gpl`) | LGPL / Apache | ambas | media |
| **Balance de blancos automático** | **Shades-of-Gray** + `cv2.xphoto LearningBasedWB` | **FC4** (FC4-pytorch, MIT) | MIT / Apache | ambas | media |
| **Quitar reflejos / sombras** | **DSRNet** (reflejos) + **ShadowFormer** (sombras) | — | Apache-2.0 / MIT | ambas | alta |

---

## 4) ✅ Ya bien cubierto (no tocar, salvo modos opcionales)

- **Super-resolución de imagen**: Real-ESRGAN + SeedVR2 (Apache) + HAT + DiffBIR + InstantIR. Solo faltan modos rápido/fidelidad (OSEDiff/DRCT-L).
- **Nitidez / detalle**: sliders FFmpeg + Restormer deblur (MIT).
- **Deblur**: Restormer (motion + defocus). Mejora opcional: FFTformer/NAFNet.
- **Low-light**: Retinexformer (MIT, SOTA real). Mejora: HVI-CIDNet/DarkIR.
- **Colorización B/N→color**: DDColor (Apache) — el mejor automático con licencia limpia; solo **acelerar** (device).
- **Interpolación / slow-mo**: RIFE (Vulkan) + FILM/Practical-RIFE/EMA-VFI ya integrados.
- **Grano analógico**: 5 presets, temporal en vídeo.
- **Lluvia (derain)**: ya cubierta por Restormer.

---

## 5) 🏆 Orden sugerido para empezar (impacto × calidad × facilidad)

1. **Sanear caras** (riesgo legal) → PMRF default + RestoreFormer++ · *media · bloqueante*
2. **Acelerar DDColor** (device=mps/cuda + re-DDColor) · *trivial · quick win*
3. **Actualizar RIFE** a v4.26 (mismo binario Vulkan) · *trivial*
4. **Desentrelazado** bwdif (nuevo default) + estdif · *trivial, cero riesgo*
5. **Artefactos de compresión** FBCNN + FFmpeg deband · *baja*
6. **Denoise GPU** NAFNet + SCUNet · *media*
7. **Quitar fondo / matting** InSPyReNet/BiRefNet · *baja, feature vendible*
8. **Low-light premium** HVI-CIDNet + DarkIR · *media*

Siguiente tanda (más esfuerzo): dehazing, HDR/tonemap, relighting, borrar objetos,
igualar color, corrección de lente, auto white balance, quitar reflejos/sombras.

---

## 6) ⛔ Descartado por licencia (NO usar en el build que se vende)

- **Caras**: CodeFormer (S-Lab NC — hoy embebido, retirar), OSDFace (sin LICENSE), GFPGAN/GPEN (NC/académico).
- **Super-res**: SUPIR (NC). FaithDiff (sin LICENSE clara → verificar/aislar).
- **Denoise/deblur vídeo**: RVRT, VRT (CC-BY-NC); AdaRevD, LoFormer (academic). *FFTformer del repo `kkkls` SÍ es MIT — usar ese.*
- **Low-light**: LightenDiffusion (sin LICENSE).
- **Dehazing**: PromptIR (academic), MB-TaylorFormer V1 / C2PNet (sin LICENSE), RIDCP (CC-BY-NC).
- **HDR**: HDCFM (GPL-3.0 viral).
- **Desentrelazado**: vs_deepdeinterlace / DfConvEkSA (sin LICENSE), NNEDI3 / QTGMC / znedi3 (GPLv2 viral) — más calidad pero no vendibles.
- **Estabilización**: NNDVS, FuSta (sin LICENSE), DIFRINT (academic), **Gyroflow** (GPLv3 — solo como CLI externa separada, nunca enlazado; además exige metadatos de giroscopio).
- **Matting**: RMBG-2.0/1.4 (CC-BY-NC), RVM (GPL-3.0).
- **Relighting**: IC-Light **v2/Flux** (NC), RelightVid (CC-BY-NC). *Solo IC-Light **v1** es Apache.*
- **Inpainting/removal**: ProPainter (S-Lab), DiffuEraser (depende de pesos ProPainter NC), MAT/FcF (CC-BY-NC). MiniMax-Remover: sin LICENSE → confirmar.
- **Color match**: color-matcher, ColorMatch/KJNodes (GPL-3.0), FastPhotoStyle/PhotoWCT (CC-BY-NC-SA).
- **Auto WB**: Deep White-Balance, mixedillWB, Interactive_WB, CCMNet (research/CC-BY-NC).
- **Colorización vídeo**: ColorMNet (CC-BY-NC-SA), Control-Color (S-Lab).

---

## Archivos relevantes para cuando se implemente

`engines/faces.py` · `engines/osdface.py` · `engines/pmrf.py` (caras) ·
`engines/color.py` (DDColor en CPU) · `engines/vulkan.py` (RIFE 4.6) ·
`engines/filtros.py` (yadif/vidstab/hqdn3d) · `engines/restormer.py` ·
`engines/faithdiff.py` (licencia a verificar). Patrón de motor nuevo: copiar
`engines/diffbir.py` + `install/extras_diffbir.sh` (venv propio, `disponible()`,
generador con `correr`, marcador `.venv-*/.ok`).
