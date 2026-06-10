"""Traducciones de la interfaz: español, inglés y francés.

Uso: t("clave", lang). Si falta una clave o idioma, cae a español.
"""

import locale

IDIOMAS = [("Español", "es"), ("English", "en"), ("Français", "fr")]


def idioma_por_defecto() -> str:
    try:
        code = (locale.getlocale()[0] or "")[:2].lower()
        if code in ("es", "en", "fr"):
            return code
    except Exception:
        pass
    return "es"


T = {
    # ---- generales ----
    "titulo": {
        "es": "VideoBoost", "en": "VideoBoost", "fr": "VideoBoost"},
    "subtitulo": {
        "es": "Mejora de video e imagen con IA · 100% local",
        "en": "AI video & image enhancement · 100% local",
        "fr": "Amélioration vidéo et image par IA · 100% local"},
    "idioma": {
        "es": "Idioma", "en": "Language", "fr": "Langue"},
    "tab_video": {"es": "Video", "en": "Video", "fr": "Vidéo"},
    "tab_imagenes": {"es": "Imágenes", "en": "Images", "fr": "Images"},
    "tab_sistema": {"es": "Sistema", "en": "System", "fr": "Système"},
    "nivel": {"es": "Nivel", "en": "Tier", "fr": "Niveau"},
    "nivel_3": {"es": "Máximo", "en": "Maximum", "fr": "Maximum"},
    "nivel_2": {"es": "Pro", "en": "Pro", "fr": "Pro"},
    "nivel_1": {"es": "Compatible", "en": "Compatible", "fr": "Compatible"},
    "gpu_generica": {
        "es": "GPU genérica (solo motores Vulkan)",
        "en": "Generic GPU (Vulkan engines only)",
        "fr": "GPU générique (moteurs Vulkan uniquement)"},
    "mem_unificada": {
        "es": "GB de memoria unificada (Metal/MPS)",
        "en": "GB unified memory (Metal/MPS)",
        "fr": "Go de mémoire unifiée (Metal/MPS)"},

    # ---- controles de video ----
    "video_entrada": {"es": "Video de entrada", "en": "Input video", "fr": "Vidéo d'entrée"},
    "motor": {"es": "Motor", "en": "Engine", "fr": "Moteur"},
    "escala": {"es": "Escala", "en": "Scale", "fr": "Échelle"},
    "ruido": {"es": "Reducción de ruido", "en": "Denoise level", "fr": "Réduction du bruit"},
    "mult_fps": {"es": "Multiplicador de fps", "en": "FPS multiplier", "fr": "Multiplicateur de fps"},
    "resolucion_obj": {
        "es": "Resolución objetivo (lado corto)",
        "en": "Target resolution (short side)",
        "fr": "Résolution cible (côté court)"},
    "modelo_auto": {
        "es": "Modelo (auto-recomendado para tu hardware)",
        "en": "Model (auto-recommended for your hardware)",
        "fr": "Modèle (auto-recommandé pour votre matériel)"},
    "batch": {
        "es": "Frames por lote (más = mejor consistencia, más memoria)",
        "en": "Frames per batch (more = better consistency, more memory)",
        "fr": "Images par lot (plus = meilleure cohérence, plus de mémoire)"},
    "boton_video": {"es": "Mejorar video", "en": "Enhance video", "fr": "Améliorer la vidéo"},
    "progreso": {"es": "Progreso", "en": "Progress", "fr": "Progression"},
    "resultado": {"es": "Resultado", "en": "Result", "fr": "Résultat"},
    "antes": {"es": "Antes", "en": "Before", "fr": "Avant"},
    "despues": {"es": "Después", "en": "After", "fr": "Après"},
    "arrastra_comparar": {
        "es": "Arrastra para comparar · el archivo se guardó en salidas/",
        "en": "Drag to compare · file saved to salidas/",
        "fr": "Glissez pour comparer · fichier enregistré dans salidas/"},

    # ---- controles de imagen ----
    "imagen_entrada": {"es": "Imagen de entrada", "en": "Input image", "fr": "Image d'entrée"},
    "prompt": {
        "es": "Prompt opcional (guía la restauración)",
        "en": "Optional prompt (guides the restoration)",
        "fr": "Prompt facultatif (guide la restauration)"},
    "prompt_ej": {
        "es": "ej.: retrato nítido, piel detallada",
        "en": "e.g.: sharp portrait, detailed skin",
        "fr": "ex. : portrait net, peau détaillée"},
    "boton_imagen": {"es": "Mejorar imagen", "en": "Enhance image", "fr": "Améliorer l'image"},

    # ---- mensajes ----
    "sube_video": {"es": "⚠️ Sube un video primero.", "en": "⚠️ Upload a video first.",
                   "fr": "⚠️ Téléversez d'abord une vidéo."},
    "sube_imagen": {"es": "⚠️ Sube una imagen primero.", "en": "⚠️ Upload an image first.",
                    "fr": "⚠️ Téléversez d'abord une image."},
    "listo": {"es": "✅ Listo", "en": "✅ Done", "fr": "✅ Terminé"},
    "error": {"es": "❌ Error", "en": "❌ Error", "fr": "❌ Erreur"},
    "se_mantiene": {"es": "se mantiene", "en": "unchanged", "fr": "inchangée"},
    "supera_4k": {"es": " ⚠️ supera 4K — será lento", "en": " ⚠️ above 4K — will be slow",
                  "fr": " ⚠️ dépasse la 4K — ce sera lent"},
    "combo": {
        "es": "💡 **Combo «Topaz completo»:** primero SeedVR2 (o Real-ESRGAN), luego RIFE sobre el resultado.",
        "en": "💡 **“Full Topaz” combo:** SeedVR2 (or Real-ESRGAN) first, then RIFE on the result.",
        "fr": "💡 **Combo « Topaz complet » :** d'abord SeedVR2 (ou Real-ESRGAN), puis RIFE sur le résultat."},

    # ---- nombres de motores (video) ----
    "m_seedvr2": {
        "es": "SeedVR2 — restauración IA (recomendado)",
        "en": "SeedVR2 — AI restoration (recommended)",
        "fr": "SeedVR2 — restauration IA (recommandé)"},
    "m_realesrgan": {
        "es": "Real-ESRGAN — video real (Vulkan)",
        "en": "Real-ESRGAN — real-world video (Vulkan)",
        "fr": "Real-ESRGAN — vidéo réelle (Vulkan)"},
    "m_realcugan": {
        "es": "Real-CUGAN — anime con ruido (Vulkan)",
        "en": "Real-CUGAN — noisy anime (Vulkan)",
        "fr": "Real-CUGAN — anime bruité (Vulkan)"},
    "m_waifu2x": {
        "es": "waifu2x — anime limpio (Vulkan)",
        "en": "waifu2x — clean anime (Vulkan)",
        "fr": "waifu2x — anime propre (Vulkan)"},
    "m_rife": {
        "es": "RIFE — más fps, interpolación (Vulkan)",
        "en": "RIFE — more fps, interpolation (Vulkan)",
        "fr": "RIFE — plus de fps, interpolation (Vulkan)"},
    "m_flashvsr": {
        "es": "FlashVSR — modo rápido (experimental, NVIDIA)",
        "en": "FlashVSR — fast mode (experimental, NVIDIA)",
        "fr": "FlashVSR — mode rapide (expérimental, NVIDIA)"},

    # ---- nombres de motores (imagen) ----
    "i_hypir": {
        "es": "HYPIR — restauración SOTA (recomendado)",
        "en": "HYPIR — SOTA restoration (recommended)",
        "fr": "HYPIR — restauration SOTA (recommandé)"},
    "i_supir": {
        "es": "SUPIR — máximo detalle (lento)",
        "en": "SUPIR — maximum detail (slow)",
        "fr": "SUPIR — détail maximal (lent)"},
    "i_seedvr2": {"es": "SeedVR2 — imagen", "en": "SeedVR2 — image", "fr": "SeedVR2 — image"},
    "i_realesrgan": {
        "es": "Real-ESRGAN — rápido (Vulkan)",
        "en": "Real-ESRGAN — fast (Vulkan)",
        "fr": "Real-ESRGAN — rapide (Vulkan)"},
    "i_codeformer": {
        "es": "CodeFormer — restaurar caras",
        "en": "CodeFormer — face restoration",
        "fr": "CodeFormer — restauration des visages"},
    "i_instantir": {
        "es": "InstantIR — restauración instantánea (NVIDIA)",
        "en": "InstantIR — instant restoration (NVIDIA)",
        "fr": "InstantIR — restauration instantanée (NVIDIA)"},
    "i_ddcolor": {
        "es": "DDColor — colorizar (B/N → color)",
        "en": "DDColor — colorize (B&W → color)",
        "fr": "DDColor — coloriser (N&B → couleur)"},

    # ---- control de fidelidad de caras ----
    "fidelidad": {
        "es": "Fidelidad (0 = más nítido, 1 = más fiel al original)",
        "en": "Fidelity (0 = sharper, 1 = truer to original)",
        "fr": "Fidélité (0 = plus net, 1 = plus fidèle à l'original)"},

    # ---- notas por motor ----
    "n_seedvr2": {
        "es": "Difusión en 1 paso con **consistencia temporal nativa** (cero parpadeo). "
              "Reconstruye detalle real en video degradado. Nivel Topaz. La primera vez "
              "descarga el modelo (varios GB).",
        "en": "One-step diffusion with **native temporal consistency** (zero flicker). "
              "Rebuilds real detail in degraded footage. Topaz-level. First run downloads "
              "the model (several GB).",
        "fr": "Diffusion en 1 étape avec **cohérence temporelle native** (zéro scintillement). "
              "Reconstruit le détail réel des vidéos dégradées. Niveau Topaz. Le premier "
              "lancement télécharge le modèle (plusieurs Go)."},
    "n_realesrgan": {
        "es": "El todoterreno clásico para video real: eventos, caras, texturas. Rápido y "
              "funciona en cualquier GPU.",
        "en": "The classic all-rounder for real-world video: events, faces, textures. Fast "
              "and runs on any GPU.",
        "fr": "Le tout-terrain classique pour la vidéo réelle : événements, visages, textures. "
              "Rapide et fonctionne sur n'importe quel GPU."},
    "n_realcugan": {
        "es": "Para anime con ruido o compresión. Rescata material degradado.",
        "en": "For anime with noise or compression. Rescues degraded material.",
        "fr": "Pour l'anime avec bruit ou compression. Sauve les sources dégradées."},
    "n_waifu2x": {
        "es": "Para anime limpio. Suave y fiel al original.",
        "en": "For clean anime. Smooth and faithful to the original.",
        "fr": "Pour l'anime propre. Doux et fidèle à l'original."},
    "n_rife": {
        "es": "Multiplica los fps (30→60/120) interpolando frames. **No cambia la resolución** "
              "— combínalo después de escalar para el efecto «Topaz completo».",
        "en": "Multiplies fps (30→60/120) by interpolating frames. **Does not change resolution** "
              "— run it after upscaling for the “full Topaz” effect.",
        "fr": "Multiplie les fps (30→60/120) en interpolant des images. **Ne change pas la "
              "résolution** — à lancer après l'upscale pour l'effet « Topaz complet »."},
    "n_flashvsr": {
        "es": "Super-resolución casi en tiempo real (CVPR 2026). Para horas de material. "
              "Experimental: si falla, usa SeedVR2.",
        "en": "Near real-time super-resolution (CVPR 2026). For hours of footage. "
              "Experimental: if it fails, use SeedVR2.",
        "fr": "Super-résolution quasi temps réel (CVPR 2026). Pour des heures de rushes. "
              "Expérimental : en cas d'échec, utilisez SeedVR2."},
    "n_hypir": {
        "es": "Restauración en 1 paso (SIGGRAPH 2025). Acepta un prompt opcional que guía "
              "la textura. *Licencia: solo uso no comercial.*",
        "en": "One-step restoration (SIGGRAPH 2025). Takes an optional prompt to guide "
              "texture. *License: non-commercial use only.*",
        "fr": "Restauration en 1 étape (SIGGRAPH 2025). Accepte un prompt facultatif qui "
              "guide la texture. *Licence : usage non commercial uniquement.*"},
    "n_supir": {
        "es": "Reconstruye detalle a nivel de poros de piel. 25-35 pasos de difusión: lento "
              "y pesado (ideal en la 4080). *Licencia: solo uso no comercial.*",
        "en": "Rebuilds detail down to skin pores. 25-35 diffusion steps: slow and heavy "
              "(ideal on the 4080). *License: non-commercial use only.*",
        "fr": "Reconstruit le détail jusqu'aux pores de la peau. 25-35 étapes de diffusion : "
              "lent et lourd (idéal sur la 4080). *Licence : usage non commercial uniquement.*"},
    "n_seedvr2_img": {
        "es": "El mismo motor de video aplicado a una imagen suelta. Muy buen equilibrio.",
        "en": "The video engine applied to a single image. Great balance.",
        "fr": "Le moteur vidéo appliqué à une image seule. Très bon équilibre."},
    "n_realesrgan_img": {
        "es": "Escalado clásico instantáneo. Para cuando la velocidad importa más.",
        "en": "Instant classic upscaling. For when speed matters most.",
        "fr": "Upscaling classique instantané. Quand la vitesse prime."},
    "n_codeformer": {
        "es": "Entrenado solo en rostros: recupera ojos, dientes y piel donde los "
              "upscalers generales fallan. La pieza «face model» tipo HitPaw. La "
              "fidelidad ajusta nitidez vs. parecido al original. *Uso no comercial.*",
        "en": "Trained only on faces: recovers eyes, teeth and skin where general "
              "upscalers fail. The HitPaw-style “face model”. Fidelity trades sharpness "
              "for resemblance to the original. *Non-commercial use.*",
        "fr": "Entraîné uniquement sur les visages : récupère yeux, dents et peau là où "
              "les upscalers généraux échouent. Le « face model » façon HitPaw. La "
              "fidélité arbitre netteté vs. ressemblance. *Usage non commercial.*"},
    "n_instantir": {
        "es": "Restauración por difusión con referencia generativa. Calidad a la par o "
              "superior a SUPIR pero más rápida, y con **licencia Apache 2.0** (uso "
              "comercial libre). Solo NVIDIA. Acepta prompt opcional.",
        "en": "Diffusion restoration with a generative reference. Quality on par with or "
              "above SUPIR but faster, and **Apache 2.0 licensed** (commercial use OK). "
              "NVIDIA only. Takes an optional prompt.",
        "fr": "Restauration par diffusion avec référence générative. Qualité égale ou "
              "supérieure à SUPIR mais plus rapide, et **licence Apache 2.0** (usage "
              "commercial libre). NVIDIA uniquement. Accepte un prompt facultatif."},
    "n_ddcolor": {
        "es": "Da color a fotos en blanco y negro (ICCV 2023). Más nuevo y mejor que "
              "DeOldify: colores ricos y coherentes. El «colorize model» tipo HitPaw. "
              "Apache 2.0. En Mac corre en CPU (más lento).",
        "en": "Adds color to black-and-white photos (ICCV 2023). Newer and better than "
              "DeOldify: rich, coherent colors. The HitPaw-style “colorize model”. "
              "Apache 2.0. On Mac it runs on CPU (slower).",
        "fr": "Met en couleur les photos en noir et blanc (ICCV 2023). Plus récent et "
              "meilleur que DeOldify : couleurs riches et cohérentes. Le « colorize "
              "model » façon HitPaw. Apache 2.0. Sur Mac, tourne sur CPU (plus lent)."},

    # ---- pestaña sistema ----
    "s_sistema": {"es": "Sistema", "en": "System", "fr": "Système"},
    "s_instalados": {"es": "✅ instalados", "en": "✅ installed", "fr": "✅ installés"},
    "s_corre_inst": {"es": "❌ corre el instalador", "en": "❌ run the installer",
                     "fr": "❌ lancez l'installateur"},
    "s_listo_modelo": {"es": "✅ listo · modelo recomendado:", "en": "✅ ready · recommended model:",
                       "fr": "✅ prêt · modèle recommandé :"},
    "s_no_instalado": {"es": "❌ no instalado", "en": "❌ not installed", "fr": "❌ non installé"},
    "s_opcional": {"es": "❌ opcional", "en": "❌ optional", "fr": "❌ facultatif"},
    "s_opcional_nvidia": {"es": "❌ opcional, solo NVIDIA", "en": "❌ optional, NVIDIA only",
                          "fr": "❌ facultatif, NVIDIA uniquement"},
    "s_sin_gpu": {"es": "sin acelerador detectado", "en": "no accelerator detected",
                  "fr": "aucun accélérateur détecté"},
}


def t(clave: str, lang: str = "es") -> str:
    entrada = T.get(clave, {})
    return entrada.get(lang) or entrada.get("es") or clave
