# VideoBoost · Contexto para Claude Code

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
