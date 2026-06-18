# PixelBooster · Contexto para Claude Code

App Gradio (español/inglés/francés) para mejorar videos e imágenes con IA, 100% local.
Dos plataformas objetivo del dueño: **Mac con chip M** (uso principal) y **PC con
RTX 4080**. Lee PROPUESTA.md para el razonamiento del stack.

## Arquitectura

- `hardware.py` detecta CUDA/MPS/Vulkan y asigna nivel (1 Compatible / 2 Pro / 3 Máximo)
  y el modelo SeedVR2 recomendado. Cacheado con lru_cache.
- `engines/*` son **generadores**: ceden líneas de log y devuelven (return) la ruta de
  salida. `engines.correr()` ejecuta subprocesos transmitiendo stdout en vivo.
- `app.py` usa `@gr.render(inputs=idioma)`: la UI completa se reconstruye al cambiar
  de idioma. Los motores se identifican por ids estables ("seedvr2", "rife"…) y las
  etiquetas salen de `i18n.t()`.
- Venvs separados para evitar choques de dependencias: `.venv` (app+SeedVR2),
  `.venv-faithdiff`, `.venv-instantir`, `.venv-caras` (CodeFormer),
  `.venv-color` (DDColor), `.venv-flashvsr`. `engines/faithdiff.py`,
  `instantir.py`, `faces.py`, `color.py` y `flashvsr.py` invocan el python del venv
  correspondiente por subprocess.
- HYPIR y SUPIR se retiraron (licencia no comercial). Reemplazos libres: FaithDiff
  (MIT, recomendado) e InstantIR (Apache 2.0). No reincorporarlos sin permiso.

## Puntos frágiles / NO probados en GPU real

Esta base se escribió sin GPU disponible. Al estrenarla en la máquina real, verificar
en este orden:

1. **SeedVR2 CLI**: los flags usados en `engines/seedvr2.py` salen del README de
   numz/ComfyUI-SeedVR2_VideoUpscaler (resolution, dit_model, batch_size 4n+1,
   blocks_to_swap, vae_*_tiled, color_correction, attention_mode). Si el repo cambió,
   correr `python vendor/seedvr2/inference_cli.py --help` y ajustar.
   - En Mac: NO pasar `--blocks_to_swap` (el CLI lo rechaza/ignora con memoria unificada).
   - fp8 solo en CUDA; en MPS usar fp16 o GGUF.
2. **FlashVSR** (`engines/flashvsr.py`): los entrypoints `_ENTRYPOINTS` son candidatos,
   el repo reorganiza scripts entre versiones. Verificar nombre real y sus argumentos
   tras clonar. Pesos por Git LFS según su README. Solo CUDA.
3. **CodeFormer** (`engines/faces.py`): `inference_codeformer.py -w <fidelidad>
   --input_path --output_path --upscale N --face_upsample --bg_upsampler realesrgan`.
   El resultado final queda en `output_path/final_results/`. basicsr va en modo
   `develop` (lo hace el instalador). En Mac auto-detecta MPS; si una versión vieja
   fuerza CUDA, parchear o probar CPU. Pesos auto-descargados a la primera.
4. **InstantIR** (`engines/instantir.py`): `infer.py --sdxl_path --vision_encoder_path
   --instantir_path --test_path --out_path --num_inference_steps --cfg`. Necesita SDXL
   + DINOv2-large + pesos InstantX/InstantIR (los baja el instalador a models/). Solo
   CUDA. La salida conserva el nombre del archivo de entrada en out_path. Apache 2.0.
5. **DDColor** (`engines/color.py`): `scripts/infer.py --model_path --model_size large
   --input --output --input_size 512`. Pesos de HF piddnad/ddcolor_modelscope
   (pytorch_model.pt) a models/DDColor/. El script oficial usa cuda o **cpu** (no MPS):
   en Mac va lento pero funciona. Apache 2.0.
6. **FaithDiff** (`engines/faithdiff.py`): motor de imagen **recomendado por defecto**
   (licencia MIT, supera a SUPIR en su paper). Usamos `test_wo_llava.py --img_dir
   --json_dir --save_dir --upscale --guidance_scale --num_inference_steps [--use_fp8]`
   para **evitar LLaVA-13B**: el caption se arma de un prompt opcional dentro de un JSON
   `{stem}.json` con clave `caption`, y el script descarta sus 3 primeras palabras (por
   eso prefijamos "the image shows "). Las rutas de pesos NO son flags: van en
   `CKPT_PTH.py` (SDXL_PATH/FAITHDIFF_PATH/VAE_FP16_PATH), que el engine **regenera en
   cada ejecución** apuntando a models/FaithDiff/. Instalador baja jychen9811/FaithDiff
   + SG161222/RealVisXL_V4.0 + madebyollin/sdxl-vae-fp16-fix. Verificar en GPU real que
   RealVisXL se carga en formato diffusers y el nombre del .bin. Solo CUDA.
7. **Binarios Vulkan**: URLs fijadas a releases conocidos (Real-ESRGAN v0.2.5.0,
   nihui 20220728/20221029). RIFE usa el modelo `rife-v4.6` incluido en el zip; el
   código toma el `rife-v4*` más alto que encuentre.
8. **Grano analógico** (`engines/grano.py`): 100% FFmpeg/CPU, sin venv. Placa
   `color=gray` + `noise` gaussiano (sin flag `u`) a baja resolución, reescalada
   bicúbica y `blend=overlay` (da la respuesta de luminancia del film). Verificado
   con ffmpeg 7 real: grano temporal en video, audio `-c:a copy`, σ en medios
   tonos 2-3× la de sombras/luces. Único motor probado end-to-end sin GPU.
9. **gr.render** requiere gradio ≥4.40. Al cambiar idioma se pierde el estado de los
   componentes (video subido, etc.) — esperado, elegir idioma primero.
10. **DiffBIR** (`engines/diffbir.py`, Apache-2.0): CLI `inference.py --task
    {sr,face,face_background,denoise} --input --output --upscale --version v2.1
    --captioner none --device cuda --precision fp16`. Pesos auto de HuggingFace.
    Verificar en GPU que `--captioner none` existe en la versión clonada.
11. **PMRF** (`engines/pmrf.py`, MIT): CLI `inference.py --ckpt_path
    ohayonguy/PMRF_blind_face_image_restoration --ckpt_path_is_huggingface
    --lq_data_path --output_dir --num_flow_steps 25`. SOLO caras alineadas (una
    cara); para fotos generales no aplica sin un paso de alineación previo.
12. **OSDFace** (`engines/osdface.py`): ⚠️ SIN LICENCIA → solo pruebas, no venta.
    `infer.py --input_image <dir> --output_dir <dir> --pretrained_model_name_or_path
    stabilityai/stable-diffusion-2-1-base --img_encoder_weight <ckpt>/associate_2.ckpt
    --ckpt_path <ckpt> --merge_lora`. Pesos en Google Drive (gdown; el instalador
    pide OSDFACE_GDRIVE o colocarlos a mano en models/OSDFace/).
13. **FlashVSR** (`engines/flashvsr.py`, Apache-2.0): los scripts
    `examples/WanVSR/infer_flashvsr_v1.1_*.py` NO usan argparse (traen `inputs=[...]`
    y `RESULT_ROOT` hardcodeados); el engine genera una copia parcheada con el video
    del usuario. Verificar en GPU que esos nombres de variable no cambiaron.
14. **DiffBIR/PMRF/OSDFace/FlashVSR son de difusión SD → solo NVIDIA en la
    práctica.** Escritos sin GPU disponible; verificar flags en la RTX 4080 al
    estrenarlos (igual que SeedVR2 en su momento).
15. **Motores de imagen pesados (Restormer/Retinexformer/DreamClear/HAT)**:
    deblur/lluvia/ruido (MIT), poca luz (MIT), restauración real (Apache), SR nítida
    (Apache). Solo NVIDIA salvo donde se indique; instaladores aislados, pesos por
    release/HF/gdride. NO probados en GPU: verificar comandos en la 4080.
16. **Motores de slow-mo / interpolación de frames** (sección "Motor" del tab Video,
    usan el factor `mult`; reensamblan a los fps ORIGINALES = cámara lenta real):
    - **Practical-RIFE** (`engines/practical_rife.py`, MIT, Mac+NVIDIA): CLI
      `inference_video.py --multi=N --video=… --fps=<orig>`; modelo en `train_log/`
      (Google Drive → PRIFE_GDRIVE o manual). Verificar nombre/ubicación del mp4 de
      salida y soporte MPS.
    - **FILM** (`engines/film.py`, Apache-2.0, NVIDIA/TensorFlow): `eval.interpolator_cli
      --pattern <dir> --model_path …/film_net/Style/saved_model --times_to_interpolate
      K --output_video`, K=log2(mult). ⛔ **DIFERIDO (2026-06-17)**: el engine espera un
      **SavedModel de TF**, pero el peso público es un **TorchScript `.pt`** que NO casa
      con el loader; correrlo exige reescribir el engine a TF o el loader a Torch. La
      interpolación ya la cubren Practical-RIFE (corre en Mac) y EMA-VFI. `disponible()=False`.
    - **EMA-VFI** (`engines/ema_vfi.py`, Apache-2.0, NVIDIA): SIN CLI de video → el
      engine escribe `_vb_batch.py` en el repo que recorre pares con
      `Model.multi_inference(... time_list=[...])`. Verificar API del modelo, ckpt
      (Google Drive → EMAVFI_GDRIVE) y que `.cuda()` no rompa.
17. **RIESGO LEGAL — SANEADO (2026-06-16)**: **CodeFormer** (S-Lab NO comercial) y
    **OSDFace** (sin LICENSE) ahora se EXCLUYEN del build que se vende por defecto
    (`app.INCLUIR_NO_COMERCIAL`, flag `VB_NO_COMERCIAL=1` los reactiva para uso
    personal). Reemplazo de caras en el build comercial: **RestoreFormer++** (Apache)
    + **PMRF** (MIT) + DiffBIR-face. **FaithDiff: confirmado MIT vía gh api** (el repo
    jychen9811/FaithDiff TIENE LICENSE MIT) → es comercial-OK, se mantiene como motor
    recomendado (la duda del barrido era infundada).
18. **Motores del ROADMAP integrados (2026-06-15, construidos con workflow multi-
    agente; NO probados en GPU salvo matting → verificar en la 4080).** Todos
    licencia comercial. Imagen (tab Imágenes): NAFNet, SCUNet, FBCNN, FFTformer
    (NVIDIA), DehazeFormer, HVI-CIDNet, DarkIR, InSPyReNet+BiRefNet (matting, ✅ Mac/
    MPS), RestoreFormer++ (caras), DSRNet (reflejos), ShadowFormer (sombras), IC-Light
    (relighting por prompt, NVIDIA). Video: DUT (estabilización IA, NVIDIA; ⚠️ confirmar
    licencia comercial con el autor — el README dice research-only aunque el LICENSE es
    MIT). Cada motor: `engines/<id>.py` + `install/extras_<id>.sh` (venv propio, pesos
    por release/HF/gdrive con patrón `<ID>_GDRIVE`). Incertidumbres de cada uno en el
    spec del workflow; varios repos no traen CLI con argparse y el engine escribe un
    script `_vb_*.py` parcheado (FBCNN, EMA-VFI, IC-Light, etc.). **IOPaint+LaMa**
    (borrar objetos) YA está en el selector de Imágenes (id `iopaint_lama`): usa un
    `gr.ImageEditor` como lienzo de máscara y el handler `hacer_borrar`; cuando el
    motor seleccionado es `iopaint_lama`, `procesar` enruta al lienzo en vez de a la
    imagen normal. Probado en Mac.
    Filtros FFmpeg nuevos (LGPL, probados en Mac): `filtros.desentrelazar` ahora usa
    **bwdif**, y `filtros.limpiar` (deblock+deband) = "Quitar artefactos de compresión".
    Ver `ROADMAP-MEJORAS.md` para lo que falta.
19. **Visor de LUTs (tab Video / "Looks de película", 2026-06-16/17)**: el botón
    "Ver el frame con todos los LUTs" genera miniaturas grandes (720px de origen) de
    TODOS los LUTs sobre un frame y abre una **hoja de contraste HTML autónoma en
    pestaña nueva** (`_html_galeria_luts`, grid `minmax(520px,1fr)` → ~3 columnas
    grandes). En modo video hay **frame-picker** ("Segundo del frame": slider +
    miniatura) para elegir sobre qué fotograma comparar; `luts.extract_frame_at_sec`
    y `vista_previa_todos_luts(..., progress_cb)`. El acordeón se renombró a "Mis
    LUTs" + botón "Abrir carpeta de LUTs". También se añadió **Historial** (columna
    central del tab Video: cada video renderizado se apila para recuperarlo).
    ⚠️ **Gradio hot-reload re-ejecuta app.py pero NO reinyecta el `css=` global**:
    los cambios en `ui_theme.CSS` exigen **reiniciar el servidor entero** (matar +
    relanzar); el CSS embebido en HTML generado en runtime (como esa hoja de LUTs) sí
    se actualiza al recargar. Reiniciar mata las sesiones de pestañas abiertas →
    recargar la pestaña (Cmd+R) tras un reinicio. Fix de la caja de subida:
    `.vb-upload button.boundedheight{min-height:128px}` en `ui_theme.py`.
20. **Cableados 5 de 6 motores de Google Drive/HF (2026-06-17, commit `e7e002b`)**, todos
    `disponible()=True` y verificados en la M1 Max: **Practical-RIFE** (MPS+NVIDIA),
    **ShadowFormer** (`models/ShadowFormer/ISTD_model_best.pth`), **DSRNet**
    (`models/DSRNet/dsrnet_l_epoch18.pt`), **DehazeFormer** (variante por defecto a
    **"indoor"**/RESIDE-IN, el único peso con descarga verificada). **FILM** se difirió
    (ver nota 16). **Retinexformer reescrito** para correr en Mac y arreglar su
    instalación rota en py3.12: NO se instala el `basicsr` de pip (carece de la
    arquitectura RetinexFormer **y** rompe por `torchvision.transforms.functional_tensor`,
    eliminado en torchvision≥0.17); en su lugar se registra el **basicsr REESTRUCTURADO
    embebido** del repo con un `basicsr/__init__.py` mínimo + un `.pth` en site-packages
    (sustituye al `setup.py develop`, que falla con el build editable en py3.12 — mismo
    patrón que el fix de CodeFormer en la nota 6 pero el script vive en `Enhancement/`,
    un subdirectorio, por eso hace falta el `.pth` y no basta el `cwd`). El engine inyecta
    un `_vb_infer.py` device-agnóstico (cuda/mps/cpu) y fuerza `opt['num_gpu']=0` para
    evitar el `.cuda()` interno de `model_to_device` del repo (su `test_from_dataset.py`
    está clavado a CUDA). Verificado E2E por MPS. Caveat: Transformer pesado, lento en
    Mac; la poca luz también la dan HVI-CIDNet/DarkIR.
21. **Practical-RIFE arreglado (2026-06-17)** — Gio reportó 4 motores Mac "no funcionan
    bien"; tras reproducir, SOLO Practical-RIFE estaba roto (MetalFX, SeedVR2 y SeedVR2-MLX
    dan salida correcta al invocarlos directo; SeedVR2 por MPS es CORRECTO pero MUY lento,
    ~0.04 fps → impráctico en video, usar **SeedVR2-MLX**). Dos bugs encadenados en
    `engines/practical_rife.py` + el repo vendorizado:
    (a) pasábamos `--fps={fps:.5f}` (p.ej. `24.00000`) pero `inference_video.py` declara
    `--fps` como `type=int` → `invalid int value`. Fix: `--fps={round(fps)}` (para slow-mo
    basta fijar fps≈original para que los frames extra estiren la duración).
    (b) `inference_video.py` lee los frames con **scikit-video (`sk-video`)**, sin
    mantenimiento y ROTO con NumPy moderno (usa `np.float`, eliminado en ≥1.24, y el modo
    binario de `np.fromstring`, eliminado en ≥1.22). Parchear `sk-video` era whack-a-mole
    (3 incompatibilidades) → en su lugar **eliminamos la dependencia**: sustituimos
    `skvideo.io.vreader` por un lector **OpenCV** (`cv2` ya estaba importado) que entrega
    RGB HWC uint8, idéntico. El parche lo aplica `install/extras_practical_rife.sh` tras el
    `git clone` (idempotente, busca `_vb_vreader`), porque `vendor/` está en `.gitignore`.
    Verificado E2E por MPS: 24→47 frames a 24 fps (x2 slow-mo) en ~5 s.

## Licencias de venta (licencias.py)

Modelo C "Topaz": claves Ed25519 verificadas offline. Si `licencia_publica.py`
define CLAVE_PUBLICA, la app exige activación (pantalla en app.py antes de los
tabs); sin ese archivo corre libre (modo dev). `clave_privada.pem` y
`licencia.json` están gitignored — la privada JAMÁS se versiona. CLI: init /
generar --cliente / verificar. Sin revocación (decisión consciente, documentada).

## Reglas de memoria

- SeedVR2 batch_size sigue la regla **4n+1** (1, 5, 9, 13, 21, 33). Más batch = mejor
  consistencia temporal y más VRAM.
- 4080 (16 GB): 7B fp8, batch 13, sin swap. 8-12 GB: GGUF Q4/Q8 + blocks_to_swap.
- Mac: la "VRAM" es la RAM unificada; con 48 GB+ cabe el 7B fp16.

## Licencias

Todos los motores incluidos permiten uso comercial. FaithDiff: **MIT**. SeedVR2,
FlashVSR, InstantIR y DDColor: **Apache 2.0**. Vulkan (Real-ESRGAN, etc.): BSD/MIT.
CodeFormer: NTU S-Lab (revisar para comercial). HYPIR y SUPIR se **retiraron** por
ser de uso no comercial; no reincorporarlos a nada que se venda.
