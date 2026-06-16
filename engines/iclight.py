"""IC-Light v1 (lllyasviel, Apache-2.0) — RE-ILUMINACIÓN (relighting) de imágenes
por difusión sobre Stable Diffusion 1.5. Recorta el sujeto (foreground), y vuelve
a iluminarlo de forma coherente según un prompt y una dirección de luz
(izquierda/derecha/arriba/abajo), manteniendo la identidad del sujeto.

El repo NO trae CLI de inferencia: solo `gradio_demo.py` (modelo condicionado por
texto + foreground, pesos `iclight_sd15_fc.safetensors`). Igual que EMA-VFI/FlashVSR,
escribimos un pequeño script `_vb_relight.py` dentro del repo clonado que replica su
función `process_relight()`: carga el UNet de IC-Light sobre el SD1.5
`stablediffusionapi/realistic-vision-v51`, quita el fondo con BriaRMBG-1.4, y corre
la difusión low-res + highres-fix. Devuelve la imagen re-iluminada.

Base SD1.5 + pesos IC-Light se auto-descargan de HuggingFace en el primer uso.
Vive en `.venv-iclight`. Pesado (difusión SD1.5) → SOLO NVIDIA en la práctica; el
CLI admite CPU pero es impráctico. NO PROBADO EN GPU REAL desde aquí: verificar en
la 4080 (firma de process_relight, nombres de pesos y dependencia BriaRMBG).

⚠️ Licencia: el código de IC-Light es Apache-2.0 (apto comercial), PERO el quita-fondo
por defecto BriaRMBG-1.4 es de uso NO comercial. Para vender hay que sustituirlo por
una alternativa comercial (p. ej. BiRefNet) — ver incertidumbres del SPEC.
"""

import shutil
import tempfile
from pathlib import Path

from engines import SALIDAS, VENDOR, correr, python_venv

ICLIGHT_DIR = VENDOR / "IC-Light"

# Direcciones de luz expuestas (BGSource del demo oficial). La etiqueta visible
# se traduce en la UI; aquí van los valores EXACTOS que espera el enum del repo.
DIRECCIONES = {
    "izquierda": "Left Light",
    "derecha": "Right Light",
    "arriba": "Top Light",
    "abajo": "Bottom Light",
    "ninguna": "None",
}

# Script de inferencia que vive dentro del repo (necesita sus imports: briarmbg).
# Destila gradio_demo.py: carga IC-Light (fc) sobre realistic-vision-v51, recorta el
# sujeto con BriaRMBG-1.4 e ilumina low-res + highres-fix. Un solo sujeto/imagen.
_INFER = r'''
import os, sys, math, argparse
sys.path.append('.')
import numpy as np
import torch
import safetensors.torch as sf
from PIL import Image
from torch.hub import download_url_to_file
from diffusers import (StableDiffusionPipeline, StableDiffusionImg2ImgPipeline,
                       AutoencoderKL, UNet2DConditionModel, DDIMScheduler,
                       EulerAncestralDiscreteScheduler, DPMSolverMultistepScheduler)
from diffusers.models.attention_processor import AttnProcessor2_0
from transformers import CLIPTextModel, CLIPTokenizer
from briarmbg import BriaRMBG

ap = argparse.ArgumentParser()
ap.add_argument('--input', required=True)
ap.add_argument('--output', required=True)
ap.add_argument('--prompt', default='')
ap.add_argument('--bg_source', default='None')     # None/Left Light/Right Light/Top Light/Bottom Light
ap.add_argument('--steps', type=int, default=25)
ap.add_argument('--cfg', type=float, default=2.0)
ap.add_argument('--seed', type=int, default=12345)
ap.add_argument('--width', type=int, default=512)
ap.add_argument('--height', type=int, default=640)
ap.add_argument('--highres_scale', type=float, default=1.5)
ap.add_argument('--highres_denoise', type=float, default=0.5)
ap.add_argument('--lowres_denoise', type=float, default=0.9)
a = ap.parse_args()

dev = torch.device('cuda' if torch.cuda.is_available() else (
    'mps' if getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available() else 'cpu'))
dtype = torch.float16 if dev.type == 'cuda' else torch.float32

# --- Modelos (igual que gradio_demo.py) ---
sd15_name = 'stablediffusionapi/realistic-vision-v51'
tokenizer = CLIPTokenizer.from_pretrained(sd15_name, subfolder='tokenizer')
text_encoder = CLIPTextModel.from_pretrained(sd15_name, subfolder='text_encoder')
vae = AutoencoderKL.from_pretrained(sd15_name, subfolder='vae')
unet = UNet2DConditionModel.from_pretrained(sd15_name, subfolder='unet')
rmbg = BriaRMBG.from_pretrained('briaai/RMBG-1.4')

# Pesos IC-Light (fc): foreground + texto. Se descargan de HF a ./models/.
model_path = './models/iclight_sd15_fc.safetensors'
if not os.path.exists(model_path):
    os.makedirs('./models', exist_ok=True)
    download_url_to_file(
        'https://huggingface.co/lllyasviel/ic-light/resolve/main/iclight_sd15_fc.safetensors',
        model_path)

# Ampliar el UNet de 4 a 8 canales de entrada (concat del latente del sujeto).
with torch.no_grad():
    new_conv_in = torch.nn.Conv2d(8, unet.conv_in.out_channels, unet.conv_in.kernel_size,
                                  unet.conv_in.stride, unet.conv_in.padding)
    new_conv_in.weight.zero_()
    new_conv_in.weight[:, :4, :, :].copy_(unet.conv_in.weight)
    new_conv_in.bias.copy_(unet.conv_in.bias)
    unet.conv_in = new_conv_in

unet_original_forward = unet.forward
def hooked_unet_forward(sample, timestep, encoder_hidden_states, **kwargs):
    c_concat = kwargs['cross_attention_kwargs']['concat_conds'].to(sample)
    c_concat = torch.cat([c_concat] * (sample.shape[0] // c_concat.shape[0]), dim=0)
    new_sample = torch.cat([sample, c_concat], dim=1)
    kwargs['cross_attention_kwargs'] = {}
    return unet_original_forward(new_sample, timestep, encoder_hidden_states, **kwargs)
unet.forward = hooked_unet_forward

sd_offset = sf.load_file(model_path)
sd_origin = unet.state_dict()
sd_merged = {k: sd_origin[k] + sd_offset[k] for k in sd_origin.keys()}
unet.load_state_dict(sd_merged, strict=True)
del sd_offset, sd_origin, sd_merged

text_encoder = text_encoder.to(device=dev, dtype=dtype)
vae = vae.to(device=dev, dtype=dtype)
unet = unet.to(device=dev, dtype=dtype)
rmbg = rmbg.to(device=dev, dtype=torch.float32)

unet.set_attn_processor(AttnProcessor2_0())
vae.set_attn_processor(AttnProcessor2_0())

ddim_scheduler = DDIMScheduler(num_train_timesteps=1000, beta_start=0.00085, beta_end=0.012,
                               beta_schedule='scaled_linear', clip_sample=False,
                               set_alpha_to_one=False, steps_offset=1)
euler_a_scheduler = EulerAncestralDiscreteScheduler(num_train_timesteps=1000, beta_start=0.00085,
                                                    beta_end=0.012, steps_offset=1)
dpmpp_2m_sde_karras_scheduler = DPMSolverMultistepScheduler(
    num_train_timesteps=1000, beta_start=0.00085, beta_end=0.012, algorithm_type='sde-dpmsolver++',
    use_karras_sigmas=True, steps_offset=1)

t2i_pipe = StableDiffusionPipeline(vae=vae, text_encoder=text_encoder, tokenizer=tokenizer,
                                   unet=unet, scheduler=dpmpp_2m_sde_karras_scheduler,
                                   safety_checker=None, requires_safety_checker=False,
                                   feature_extractor=None, image_encoder=None)
i2i_pipe = StableDiffusionImg2ImgPipeline(vae=vae, text_encoder=text_encoder, tokenizer=tokenizer,
                                          unet=unet, scheduler=dpmpp_2m_sde_karras_scheduler,
                                          safety_checker=None, requires_safety_checker=False,
                                          feature_extractor=None, image_encoder=None)


@torch.inference_mode()
def encode_prompt_inner(txt):
    max_length = tokenizer.model_max_length
    chunk_length = tokenizer.model_max_length - 2
    id_start = tokenizer.bos_token_id
    id_end = tokenizer.eos_token_id
    id_pad = id_end
    def pad(x, p, i):
        return x[:i] if len(x) >= i else x + [p] * (i - len(x))
    tokens = tokenizer(txt, truncation=False, add_special_tokens=False)['input_ids']
    chunks = [[id_start] + tokens[i:i + chunk_length] + [id_end]
              for i in range(0, len(tokens), chunk_length)]
    chunks = [pad(ck, id_pad, max_length) for ck in chunks]
    token_ids = torch.tensor(chunks).to(device=dev, dtype=torch.int64)
    conds = text_encoder(token_ids).last_hidden_state
    return conds


@torch.inference_mode()
def encode_prompt_pair(positive_prompt, negative_prompt):
    c = encode_prompt_inner(positive_prompt)
    uc = encode_prompt_inner(negative_prompt)
    c_len = float(len(c)); uc_len = float(len(uc))
    max_count = max(c_len, uc_len)
    c_repeat = int(math.ceil(max_count / c_len)); uc_repeat = int(math.ceil(max_count / uc_len))
    max_chunk = max(len(c), len(uc))
    c = torch.cat([c] * c_repeat, dim=0)[:max_chunk]
    uc = torch.cat([uc] * uc_repeat, dim=0)[:max_chunk]
    c = torch.cat([p[None, ...] for p in c], dim=1)
    uc = torch.cat([p[None, ...] for p in uc], dim=1)
    return c, uc


@torch.inference_mode()
def pytorch2numpy(imgs, quant=True):
    results = []
    for x in imgs:
        y = x.movedim(0, -1)
        if quant:
            y = y * 127.5 + 127.5
            y = y.detach().float().cpu().numpy().clip(0, 255).astype(np.uint8)
        else:
            y = y * 0.5 + 0.5
            y = y.detach().float().cpu().numpy().clip(0, 1).astype(np.float32)
        results.append(y)
    return results


@torch.inference_mode()
def numpy2pytorch(imgs):
    h = torch.from_numpy(np.stack(imgs, axis=0)).float() / 127.0 - 1.0
    return h.movedim(-1, 1)


def resize_and_center_crop(image, target_width, target_height):
    pil_image = Image.fromarray(image)
    ow, oh = pil_image.size
    scale = max(target_width / ow, target_height / oh)
    rw, rh = round(ow * scale), round(oh * scale)
    pil_image = pil_image.resize((rw, rh), Image.LANCZOS)
    left = (rw - target_width) / 2; top = (rh - target_height) / 2
    pil_image = pil_image.crop((left, top, left + target_width, top + target_height))
    return np.array(pil_image)


def resize_without_crop(image, target_width, target_height):
    pil_image = Image.fromarray(image)
    return np.array(pil_image.resize((target_width, target_height), Image.LANCZOS))


@torch.inference_mode()
def run_rmbg(img, sigma=0.0):
    H, W, C = img.shape
    k = (256.0 / float(H * W)) ** 0.5
    feed = resize_without_crop(img, int(64 * round(W * k / 64)), int(64 * round(H * k / 64)))
    feed = numpy2pytorch([feed]).to(device=dev, dtype=torch.float32)
    alpha = rmbg(feed)[0][0]
    alpha = torch.nn.functional.interpolate(alpha, size=(H, W), mode='bilinear')
    alpha = alpha.movedim(1, -1)[0]
    alpha = alpha.detach().float().cpu().numpy().clip(0, 1)
    result = 127 + (img.astype(np.float32) - 127 + sigma) * alpha
    return result.clip(0, 255).astype(np.uint8), alpha


@torch.inference_mode()
def process(input_fg, prompt, image_width, image_height, num_samples, seed, steps,
            a_prompt, n_prompt, cfg, highres_scale, highres_denoise, lowres_denoise, bg_source):
    from enum import Enum
    input_fg, matting = run_rmbg(input_fg)
    rng = torch.Generator(device=dev).manual_seed(int(seed))

    fg = resize_and_center_crop(input_fg, image_width, image_height)
    concat_conds = numpy2pytorch([fg]).to(device=vae.device, dtype=vae.dtype)
    concat_conds = vae.encode(concat_conds).latent_dist.mode() * vae.config.scaling_factor

    conds, unconds = encode_prompt_pair(positive_prompt=prompt + ', ' + a_prompt, negative_prompt=n_prompt)

    latents = t2i_pipe(
        prompt_embeds=conds, negative_prompt_embeds=unconds, width=image_width, height=image_height,
        num_inference_steps=steps, num_images_per_prompt=num_samples, generator=rng,
        output_type='latent', guidance_scale=cfg,
        cross_attention_kwargs={'concat_conds': concat_conds}).images.to(vae.dtype) / vae.config.scaling_factor

    pixels = vae.decode(latents).sample
    pixels = pytorch2numpy(pixels)
    pixels = [resize_without_crop(p, int(round(image_width * highres_scale / 64.0) * 64),
                                  int(round(image_height * highres_scale / 64.0) * 64)) for p in pixels]
    pixels = numpy2pytorch(pixels).to(device=vae.device, dtype=vae.dtype)
    latents = vae.encode(pixels).latent_dist.mode() * vae.config.scaling_factor
    latents = latents.to(device=unet.device, dtype=unet.dtype)

    image_height, image_width = latents.shape[2] * 8, latents.shape[3] * 8
    fg = resize_and_center_crop(input_fg, image_width, image_height)
    concat_conds = numpy2pytorch([fg]).to(device=vae.device, dtype=vae.dtype)
    concat_conds = vae.encode(concat_conds).latent_dist.mode() * vae.config.scaling_factor

    latents = i2i_pipe(
        image=latents, strength=highres_denoise, prompt_embeds=conds, negative_prompt_embeds=unconds,
        width=image_width, height=image_height, num_inference_steps=int(round(steps / highres_denoise)),
        num_images_per_prompt=num_samples, generator=rng, output_type='latent',
        guidance_scale=cfg,
        cross_attention_kwargs={'concat_conds': concat_conds}).images.to(vae.dtype) / vae.config.scaling_factor

    pixels = vae.decode(latents).sample
    return pytorch2numpy(pixels)


img = np.array(Image.open(a.input).convert('RGB'))
a_prompt = 'best quality'
n_prompt = 'lowres, bad anatomy, bad hands, cropped, worst quality'
results = process(img, a.prompt, a.width, a.height, 1, a.seed, a.steps,
                  a_prompt, n_prompt, a.cfg, a.highres_scale, a.highres_denoise,
                  a.lowres_denoise, a.bg_source)
Image.fromarray(results[0]).save(a.output)
print('OK relight ->', a.output)
'''


def disponible() -> bool:
    return (ICLIGHT_DIR / "gradio_demo.py").exists()


def relight(entrada, prompt="", direccion="izquierda", pasos=25, cfg=2.0, seed=12345):
    """Generador: cede log y devuelve la ruta de la imagen re-iluminada.

    direccion: clave de DIRECCIONES (izquierda/derecha/arriba/abajo/ninguna).
    prompt: descripción de la iluminación deseada (p. ej. "sunset over sea").
    """
    if not disponible():
        raise RuntimeError(
            "IC-Light no está instalado. Corre install/extras_iclight.sh (o .bat)."
        )
    entrada = Path(entrada)
    py = python_venv(".venv-iclight", "install/extras_iclight.sh")
    bg_source = DIRECCIONES.get(direccion, "Left Light")

    tmp = Path(tempfile.mkdtemp(prefix="videoboost_iclight_"))
    salida_tmp = tmp / f"{entrada.stem}_iclight.png"
    # Escribimos el script de inferencia dentro del repo (usa imports relativos: briarmbg).
    script = ICLIGHT_DIR / "_vb_relight.py"
    script.write_text(_INFER)

    cmd = [
        py, "_vb_relight.py",
        "--input", entrada,
        "--output", salida_tmp,
        "--prompt", prompt,
        "--bg_source", bg_source,
        "--steps", int(pasos),
        "--cfg", float(cfg),
        "--seed", int(seed),
    ]
    try:
        yield f"🚀 IC-Light · relight · luz: {direccion} · pasos {pasos}"
        yield "ℹ️ La primera vez descarga SD1.5 (realistic-vision-v51), BriaRMBG-1.4 y los pesos IC-Light de HuggingFace."
        yield from correr(cmd, cwd=ICLIGHT_DIR)
        if not salida_tmp.exists():
            raise RuntimeError("IC-Light terminó pero no generó ninguna imagen.")
        salida = SALIDAS / f"{entrada.stem}_iclight.png"
        shutil.copy(salida_tmp, salida)
        return str(salida)
    finally:
        script.unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)
