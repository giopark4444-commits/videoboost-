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
  `.venv-imagenes` (HYPIR), `.venv-supir`, `.venv-instantir`, `.venv-caras`
  (CodeFormer), `.venv-flashvsr`. `engines/images.py`, `instantir.py`, `faces.py` y
  `flashvsr.py` invocan el python del venv correspondiente por subprocess.

## Puntos frágiles / NO probados en GPU real

Esta base se escribió sin GPU disponible. Al estrenarla en la máquina real, verificar
en este orden:

1. **SeedVR2 CLI**: los flags usados en `engines/seedvr2.py` salen del README de
   numz/ComfyUI-SeedVR2_VideoUpscaler (resolution, dit_model, batch_size 4n+1,
   blocks_to_swap, vae_*_tiled, color_correction, attention_mode). Si el repo cambió,
   correr `python vendor/seedvr2/inference_cli.py --help` y ajustar.
   - En Mac: NO pasar `--blocks_to_swap` (el CLI lo rechaza/ignora con memoria unificada).
   - fp8 solo en CUDA; en MPS usar fp16 o GGUF.
2. **HYPIR**: comando exacto copiado de su README (test.py con lora_modules
   comma-separated, model_t/coeff_t 200, lora_rank 256). `--device mps` no está
   verificado por los autores; si falla en Mac, probar `--device cpu` o parchear.
3. **FlashVSR** (`engines/flashvsr.py`): los entrypoints `_ENTRYPOINTS` son candidatos,
   el repo reorganiza scripts entre versiones. Verificar nombre real y sus argumentos
   tras clonar. Pesos por Git LFS según su README. Solo CUDA.
4. **SUPIR**: `test.py --img_dir --save_dir --SUPIR_sign Q --upscale N` según su README,
   pero los pesos (SUPIR-v0Q + SDXL + CLIPs) se configuran a mano en sus yaml de
   opciones. Es el motor más quisquilloso; está marcado como "experto" en la doc.
5. **CodeFormer** (`engines/faces.py`): `inference_codeformer.py -w <fidelidad>
   --input_path --output_path --upscale N --face_upsample --bg_upsampler realesrgan`.
   El resultado final queda en `output_path/final_results/`. basicsr va en modo
   `develop` (lo hace el instalador). En Mac auto-detecta MPS; si una versión vieja
   fuerza CUDA, parchear o probar CPU. Pesos auto-descargados a la primera.
6. **InstantIR** (`engines/instantir.py`): `infer.py --sdxl_path --vision_encoder_path
   --instantir_path --test_path --out_path --num_inference_steps --cfg`. Necesita SDXL
   + DINOv2-large + pesos InstantX/InstantIR (los baja el instalador a models/). Solo
   CUDA. La salida conserva el nombre del archivo de entrada en out_path. Apache 2.0.
7. **Binarios Vulkan**: URLs fijadas a releases conocidos (Real-ESRGAN v0.2.5.0,
   nihui 20220728/20221029). RIFE usa el modelo `rife-v4.6` incluido en el zip; el
   código toma el `rife-v4*` más alto que encuentre.
8. **gr.render** requiere gradio ≥4.40. Al cambiar idioma se pierde el estado de los
   componentes (video subido, etc.) — esperado, elegir idioma primero.

## Reglas de memoria

- SeedVR2 batch_size sigue la regla **4n+1** (1, 5, 9, 13, 21, 33). Más batch = mejor
  consistencia temporal y más VRAM.
- 4080 (16 GB): 7B fp8, batch 13, sin swap. 8-12 GB: GGUF Q4/Q8 + blocks_to_swap.
- Mac: la "VRAM" es la RAM unificada; con 48 GB+ cabe el 7B fp16.

## Licencias

SeedVR2/FlashVSR: Apache 2.0. HYPIR/SUPIR: **no comercial** (permiso:
jinjin.gu@suppixel.ai). No incorporar HYPIR/SUPIR a nada que se venda.
