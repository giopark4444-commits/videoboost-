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
    "descargar": {"es": "Descargar resultado", "en": "Download result",
                  "fr": "Télécharger le résultat"},
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
    "aviso_8k_insuf": {
        "es": " ⚠️ 8K requiere ≥16 GB VRAM — puede fallar en tu equipo",
        "en": " ⚠️ 8K requires ≥16 GB VRAM — may fail on your hardware",
        "fr": " ⚠️ La 8K nécessite ≥16 Go VRAM — peut échouer sur votre matériel"},
    "obj_8k": {
        "es": "🎯 Objetivo **4320p** (8K)",
        "en": "🎯 Target **4320p** (8K)",
        "fr": "🎯 Cible **4320p** (8K)"},
    "hw_suficiente": {
        "es": "hardware suficiente",
        "en": "sufficient hardware",
        "fr": "matériel suffisant"},
    "combo": {
        "es": "💡 **Combo «Topaz completo»:** primero SeedVR2 (o Real-ESRGAN), luego RIFE sobre el resultado.",
        "en": "💡 **“Full Topaz” combo:** SeedVR2 (or Real-ESRGAN) first, then RIFE on the result.",
        "fr": "💡 **Combo « Topaz complet » :** d'abord SeedVR2 (ou Real-ESRGAN), puis RIFE sur le résultat."},

    # ---- nombres de motores (video) ----
    "m_seedvr2": {
        "es": "SeedVR2 — restauración IA (recomendado)",
        "en": "SeedVR2 — AI restoration (recommended)",
        "fr": "SeedVR2 — restauration IA (recommandé)"},
    "m_seedvr2_mlx": {
        "es": "SeedVR2 (MLX) — IA nativa Apple Silicon",
        "en": "SeedVR2 (MLX) — native Apple Silicon AI",
        "fr": "SeedVR2 (MLX) — IA native Apple Silicon"},
    "i_seedvr2_mlx": {
        "es": "SeedVR2 (MLX) — IA nativa Apple Silicon",
        "en": "SeedVR2 (MLX) — native Apple Silicon AI",
        "fr": "SeedVR2 (MLX) — IA native Apple Silicon"},
    "n_seedvr2_mlx": {
        "es": "El motor **SeedVR2 corriendo en MLX** (el framework de Apple), nativo de "
              "Apple Silicon: misma restauración por difusión que SeedVR2 pero mucho más "
              "rápida en Mac que la versión PyTorch/MPS. **Es por frame** (sin consistencia "
              "temporal nativa) → en video puede haber leve parpadeo; usamos semilla fija para "
              "reducirlo. MIT. La primera vez descarga los pesos (varios GB).",
        "en": "**SeedVR2 running on MLX** (Apple's framework), native to Apple Silicon: same "
              "diffusion restoration as SeedVR2 but far faster on Mac than the PyTorch/MPS "
              "build. **Per-frame** (no native temporal consistency) → video may flicker "
              "slightly; we use a fixed seed to reduce it. MIT. First run downloads the weights "
              "(several GB).",
        "fr": "**SeedVR2 sur MLX** (le framework d'Apple), natif Apple Silicon : même "
              "restauration par diffusion que SeedVR2 mais bien plus rapide sur Mac que la "
              "version PyTorch/MPS. **Image par image** (sans cohérence temporelle native) → "
              "léger scintillement possible en vidéo ; graine fixe pour l'atténuer. MIT. "
              "Premier lancement : téléchargement des poids (plusieurs Go)."},
    "m_metalfx": {
        "es": "MetalFX — escalado rápido (Apple Silicon)",
        "en": "MetalFX — fast upscale (Apple Silicon)",
        "fr": "MetalFX — upscale rapide (Apple Silicon)"},
    "n_metalfx": {
        "es": "Escalado de video **nativo de Apple Silicon** con MetalFX (la tecnología de "
              "Apple para juegos). Muy rápido (casi en tiempo real) y consciente de bordes, "
              "pero **NO inventa detalle nuevo** como la IA (SeedVR2/Real-ESRGAN): reconstruye "
              "y afila lo que ya hay. Ideal para escalar material decente en segundos o para "
              "previsualizar. Solo Mac con chip M (macOS 13+).",
        "en": "**Native Apple Silicon** video upscaling with MetalFX (Apple's gaming tech). "
              "Very fast (near real-time) and edge-aware, but **does NOT synthesize new detail** "
              "like AI (SeedVR2/Real-ESRGAN): it reconstructs and sharpens what's there. Great "
              "for scaling decent footage in seconds or for previewing. Apple Silicon Mac only "
              "(macOS 13+).",
        "fr": "Upscaling vidéo **natif Apple Silicon** avec MetalFX (la techno de jeu d'Apple). "
              "Très rapide (quasi temps réel) et sensible aux contours, mais **n'invente PAS de "
              "détail** comme l'IA : il reconstruit et affine l'existant. Idéal pour agrandir un "
              "métrage correct en quelques secondes ou prévisualiser. Mac Apple Silicon (macOS 13+)."},
    "i_realesrgan_mlx": {
        "es": "Real-ESRGAN x4 (MLX) — rápido, nativo Apple",
        "en": "Real-ESRGAN x4 (MLX) — fast, native Apple",
        "fr": "Real-ESRGAN x4 (MLX) — rapide, natif Apple"},
    "n_realesrgan_mlx": {
        "es": "El clásico Real-ESRGAN x4 corriendo en **MLX nativo de Apple Silicon**: escalado "
              "GAN rápido y determinista, escala **fija x4**. Misma familia que el Real-ESRGAN "
              "Vulkan pero por MLX. Tier ligero que complementa a SeedVR2 (difusión, más lento "
              "pero con más detalle). Licencia BSD-3 (uso comercial OK).",
        "en": "Classic Real-ESRGAN x4 running on **native Apple Silicon MLX**: fast, "
              "deterministic GAN upscaling, **fixed x4**. Same family as the Vulkan Real-ESRGAN "
              "but via MLX. Lightweight tier that complements SeedVR2 (diffusion, slower but "
              "more detail). BSD-3 license (commercial use OK).",
        "fr": "Le classique Real-ESRGAN x4 sur **MLX natif Apple Silicon** : upscaling GAN "
              "rapide et déterministe, **x4 fixe**. Même famille que le Real-ESRGAN Vulkan mais "
              "via MLX. Tier léger qui complète SeedVR2 (diffusion, plus lent mais plus de "
              "détail). Licence BSD-3 (usage commercial OK)."},
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
    "i_faithdiff": {
        "es": "FaithDiff — restauración fiel (recomendado, NVIDIA)",
        "en": "FaithDiff — faithful restoration (recommended, NVIDIA)",
        "fr": "FaithDiff — restauration fidèle (recommandé, NVIDIA)"},
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
    "i_diffbir": {
        "es": "DiffBIR — caras + escena (NVIDIA)",
        "en": "DiffBIR — faces + scene (NVIDIA)",
        "fr": "DiffBIR — visages + scène (NVIDIA)"},
    "i_pmrf": {
        "es": "PMRF — caras muy naturales (NVIDIA)",
        "en": "PMRF — very natural faces (NVIDIA)",
        "fr": "PMRF — visages très naturels (NVIDIA)"},
    "i_osdface": {
        "es": "OSDFace — caras ⚠️ sin licencia (pruebas)",
        "en": "OSDFace — faces ⚠️ unlicensed (testing)",
        "fr": "OSDFace — visages ⚠️ sans licence (test)"},
    "n_diffbir": {
        "es": "Restauración ciega por difusión con prior de Stable Diffusion (Apache-2.0). "
              "Reconstruye detalle muy orgánico en **caras y escena completa**; ideal para "
              "fotos y película degradada (cine). Usa la tarea `face_background`. Solo NVIDIA "
              "en la práctica. Los pesos se descargan de HuggingFace la primera vez.",
        "en": "Blind diffusion restoration with a Stable Diffusion prior (Apache-2.0). Rebuilds "
              "very organic detail in **faces and full scenes**; great for degraded photos and "
              "film. Uses the `face_background` task. NVIDIA in practice. Weights download from "
              "HuggingFace on first run.",
        "fr": "Restauration aveugle par diffusion avec prior Stable Diffusion (Apache-2.0). "
              "Reconstruit un détail très organique sur **visages et scène complète** ; idéal "
              "pour photos et films dégradés. Tâche `face_background`. NVIDIA en pratique. Poids "
              "téléchargés depuis HuggingFace au premier lancement."},
    "n_pmrf": {
        "es": "Posterior-Mean Rectified Flow (MIT) — caras **muy naturales y orgánicas** (top "
              "en NTIRE 2025). Está entrenado para **caras cuadradas y alineadas** (una cara); "
              "para fotos generales usa DiffBIR o CodeFormer. Solo NVIDIA. Modelo desde "
              "HuggingFace en el primer uso.",
        "en": "Posterior-Mean Rectified Flow (MIT) — **very natural, organic faces** (top at "
              "NTIRE 2025). Trained for **square aligned faces** (one face); for general photos "
              "use DiffBIR or CodeFormer. NVIDIA only. Model from HuggingFace on first run.",
        "fr": "Posterior-Mean Rectified Flow (MIT) — **visages très naturels** (top NTIRE 2025). "
              "Entraîné pour **visages carrés alignés** (un visage) ; pour photos générales, "
              "DiffBIR ou CodeFormer. NVIDIA uniquement. Modèle depuis HuggingFace au 1er usage."},
    "n_osdface": {
        "es": "Difusión de 1 paso (CVPR 2025): textura de cara muy orgánica (pestañas, cejas, "
              "pelo, piel); base del ganador del reto NTIRE 2026. ⚠️ **Sin licencia en el repo "
              "→ solo pruebas / uso personal, NO para una versión que vendas** (haría falta "
              "permiso de los autores). Solo NVIDIA.",
        "en": "One-step diffusion (CVPR 2025): very organic face texture (lashes, brows, hair, "
              "skin); base of the NTIRE 2026 challenge winner. ⚠️ **No license in the repo → "
              "testing / personal use only, NOT for a version you sell** (needs the authors' "
              "permission). NVIDIA only.",
        "fr": "Diffusion en 1 étape (CVPR 2025) : texture de visage très organique (cils, "
              "sourcils, cheveux, peau) ; base du gagnant du défi NTIRE 2026. ⚠️ **Sans licence "
              "dans le dépôt → usage test / personnel seulement, PAS pour une version vendue** "
              "(permission des auteurs requise). NVIDIA uniquement."},

    # ---- apariencia / tema ----
    "ap_titulo": {"es": "🎨 Apariencia", "en": "🎨 Appearance", "fr": "🎨 Apparence"},
    "ap_modo": {"es": "Tema", "en": "Theme", "fr": "Thème"},
    "ap_claro": {"es": "Claro", "en": "Light", "fr": "Clair"},
    "ap_oscuro": {"es": "Oscuro", "en": "Dark", "fr": "Sombre"},
    "ap_custom": {"es": "Personalizado", "en": "Custom", "fr": "Personnalisé"},
    "ap_acento": {"es": "Color de acento", "en": "Accent color", "fr": "Couleur d'accent"},
    "ap_fondo": {"es": "Color de fondo", "en": "Background color", "fr": "Couleur de fond"},
    "ap_reset": {"es": "Restablecer", "en": "Reset", "fr": "Réinitialiser"},

    # ---- activación de licencia ----
    "lic_titulo": {
        "es": "Activar VideoBoost", "en": "Activate VideoBoost",
        "fr": "Activer VideoBoost"},
    "lic_texto": {
        "es": "Pega tu clave de licencia para activar la app en esta máquina. "
              "Solo hace falta una vez y no necesita internet.",
        "en": "Paste your license key to activate the app on this machine. "
              "One time only, no internet needed.",
        "fr": "Collez votre clé de licence pour activer l'application sur cette "
              "machine. Une seule fois, sans internet."},
    "lic_clave": {
        "es": "Clave de licencia (VB1-…)", "en": "License key (VB1-…)",
        "fr": "Clé de licence (VB1-…)"},
    "lic_boton": {"es": "Activar", "en": "Activate", "fr": "Activer"},
    "lic_error": {
        "es": "❌ La clave no es válida. Revisa que esté copiada completa.",
        "en": "❌ Invalid key. Make sure it was copied in full.",
        "fr": "❌ Clé non valide. Vérifiez qu'elle est copiée en entier."},
    "lic_activada": {
        "es": "Licencia de", "en": "Licensed to", "fr": "Licence de"},

    # ---- grano analógico ----
    "m_grano": {
        "es": "Grano de película — efecto analógico",
        "en": "Film grain — analog effect",
        "fr": "Grain de pellicule — effet analogique"},
    "n_grano": {
        "es": "Emulación **orgánica** de grano de film (nada de ruido digital): placa "
              "gaussiana con estructura, mezclada en overlay — el grano respira en los "
              "medios tonos y desaparece en negros y blancos puros, como la película real. "
              "En video el grano es temporal (cambia cada frame). Ajusta los parámetros "
              "a tu gusto. CPU/FFmpeg: funciona en cualquier máquina.",
        "en": "**Organic** film grain emulation (no digital noise): a structured gaussian "
              "plate blended in overlay — grain breathes in the midtones and vanishes in "
              "pure blacks and whites, like real film stock. In video the grain is temporal "
              "(changes every frame). Tune the parameters freely. CPU/FFmpeg: runs anywhere.",
        "fr": "Émulation **organique** du grain argentique (aucun bruit numérique) : plaque "
              "gaussienne structurée fusionnée en overlay — le grain respire dans les tons "
              "moyens et disparaît dans les noirs et blancs purs, comme la vraie pellicule. "
              "En vidéo le grain est temporel (change à chaque image). Paramètres réglables. "
              "CPU/FFmpeg : fonctionne partout."},
    "g_preset": {
        "es": "Tipo de película", "en": "Film stock", "fr": "Type de pellicule"},
    "g_fino": {
        "es": "Profesional fina (tipo Portra/Ektar)",
        "en": "Fine professional (Portra/Ektar-like)",
        "fr": "Professionnelle fine (façon Portra/Ektar)"},
    "g_clasico": {
        "es": "35mm clásica (tipo Kodak Gold)",
        "en": "Classic 35mm (Kodak Gold-like)",
        "fr": "35mm classique (façon Kodak Gold)"},
    "g_alta_iso": {
        "es": "Alta sensibilidad (tipo Portra 800/CineStill)",
        "en": "High speed (Portra 800/CineStill-like)",
        "fr": "Haute sensibilité (façon Portra 800/CineStill)"},
    "g_super8": {
        "es": "Super 8 / casera (grano grueso)",
        "en": "Super 8 / home movie (coarse grain)",
        "fr": "Super 8 / amateur (gros grain)"},
    "g_bn_plata": {
        "es": "B/N de plata (tipo Tri-X/HP5)",
        "en": "Silver B&W (Tri-X/HP5-like)",
        "fr": "N&B argentique (façon Tri-X/HP5)"},
    "g_intensidad": {
        "es": "Intensidad del grano", "en": "Grain intensity", "fr": "Intensité du grain"},
    "g_tamano": {
        "es": "Tamaño del grano (1 fino → 4 grueso)",
        "en": "Grain size (1 fine → 4 coarse)",
        "fr": "Taille du grain (1 fin → 4 gros)"},
    "g_color": {
        "es": "Grano de color (apagado = plata monocromo)",
        "en": "Color grain (off = monochrome silver)",
        "fr": "Grain couleur (désactivé = argent monochrome)"},

    # ---- revelado de color (LUTs + ajustes estilo Lumetri) ----
    "m_lut": {
        "es": "Revelado de color — LUTs y ajustes",
        "en": "Color grading — LUTs & adjustments",
        "fr": "Étalonnage — LUTs et réglages"},
    "n_lut": {
        "es": "Panel de revelado estilo Lumetri: hasta **3 LUTs apilados** (20 carretes "
              "icónicos como .cube generados localmente, cada capa con su mezcla) más "
              "corrección básica: exposición, temperatura, tinte, contraste, saturación, "
              "vibranza, sombras, altas luces, nitidez y viñeta. Los looks están inspirados "
              "en el carácter documentado de cada película. Remata con el motor de grano. "
              "CPU/FFmpeg: funciona en cualquier máquina.",
        "en": "Lumetri-style grading panel: up to **3 stacked LUTs** (20 iconic film "
              "stocks as locally generated .cube, each layer with its own mix) plus basic "
              "correction: exposure, temperature, tint, contrast, saturation, vibrance, "
              "shadows, highlights, sharpen and vignette. Looks are inspired by each "
              "stock's documented character. Finish with the grain engine. CPU/FFmpeg.",
        "fr": "Panneau d'étalonnage façon Lumetri : jusqu'à **3 LUTs empilés** (20 "
              "pellicules iconiques en .cube générés localement, chaque couche avec son "
              "mélange) plus correction de base : exposition, température, teinte, "
              "contraste, saturation, vibrance, ombres, hautes lumières, netteté et "
              "vignettage. Looks inspirés du caractère documenté de chaque pellicule. "
              "Finissez avec le moteur de grain. CPU/FFmpeg."},
    "l_ninguno": {"es": "— Ninguno —", "en": "— None —", "fr": "— Aucun —"},
    "l_mezcla": {"es": "Mezcla", "en": "Mix", "fr": "Mélange"},
    "l_sec_looks": {
        "es": "Looks de película (hasta 3 capas)",
        "en": "Film looks (up to 3 layers)",
        "fr": "Looks pellicule (jusqu'à 3 couches)"},
    "l_sec_basica": {
        "es": "Corrección básica", "en": "Basic correction", "fr": "Correction de base"},
    "l_sec_detalle": {
        "es": "Detalle y viñeta", "en": "Detail & vignette", "fr": "Détail et vignettage"},
    "l_exposicion": {
        "es": "Exposición (EV)", "en": "Exposure (EV)", "fr": "Exposition (EV)"},
    "l_temperatura": {
        "es": "Temperatura de color (K)", "en": "Color temperature (K)",
        "fr": "Température de couleur (K)"},
    "l_tinte": {
        "es": "Tinte (verde ← → magenta)", "en": "Tint (green ← → magenta)",
        "fr": "Teinte (vert ← → magenta)"},
    "l_contraste": {"es": "Contraste", "en": "Contrast", "fr": "Contraste"},
    "l_saturacion": {"es": "Saturación", "en": "Saturation", "fr": "Saturation"},
    "l_vibranza": {
        "es": "Vibranza (satura protegiendo pieles)",
        "en": "Vibrance (saturates while protecting skin)",
        "fr": "Vibrance (sature en protégeant les peaux)"},
    "l_sombras": {"es": "Sombras", "en": "Shadows", "fr": "Ombres"},
    "l_altas": {"es": "Altas luces", "en": "Highlights", "fr": "Hautes lumières"},
    "l_blancos": {"es": "Blancos", "en": "Whites", "fr": "Blancs"},
    "l_negros": {"es": "Negros", "en": "Blacks", "fr": "Noirs"},
    "l_sec_creativo": {"es": "Creativo", "en": "Creative", "fr": "Créatif"},
    "l_matiz": {
        "es": "Matiz / Hue (rotación, °)", "en": "Hue (rotation, °)",
        "fr": "Teinte / Hue (rotation, °)"},
    "l_desvaido": {
        "es": "Película desvaída (faded film)", "en": "Faded film",
        "fr": "Pellicule délavée (faded film)"},
    "l_tinte_sombras": {
        "es": "Tinte de sombras (frío ← → cálido)",
        "en": "Shadow tint (cool ← → warm)",
        "fr": "Teinte des ombres (froid ← → chaud)"},
    "l_tinte_altas": {
        "es": "Tinte de altas luces (frío ← → cálido)",
        "en": "Highlight tint (cool ← → warm)",
        "fr": "Teinte des hautes lumières (froid ← → chaud)"},
    "l_nitidez": {"es": "Nitidez", "en": "Sharpen", "fr": "Netteté"},
    "l_claridad": {
        "es": "Claridad (contraste local)", "en": "Clarity (local contrast)",
        "fr": "Clarté (contraste local)"},
    "l_ruido_red": {
        "es": "Reducción de ruido", "en": "Noise reduction", "fr": "Réduction du bruit"},
    "l_vineta": {"es": "Viñeta", "en": "Vignette", "fr": "Vignettage"},

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
    "n_faithdiff": {
        "es": "Restauración fiel por difusión (CVPR 2025). En su paper supera a SUPIR y es "
              "~4× más rápido; pensado para fotos y películas antiguas. Acepta un prompt "
              "opcional. **Licencia MIT — uso comercial libre.** Solo NVIDIA.",
        "en": "Faithful diffusion restoration (CVPR 2025). Beats SUPIR in its paper and is "
              "~4× faster; aimed at old photos and films. Takes an optional prompt. "
              "**MIT license — free for commercial use.** NVIDIA only.",
        "fr": "Restauration fidèle par diffusion (CVPR 2025). Surpasse SUPIR dans son article "
              "et ~4× plus rapide ; pensé pour photos et films anciens. Prompt facultatif. "
              "**Licence MIT — usage commercial libre.** NVIDIA uniquement."},
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

    # ---- nuevos motores de filtro ----
    "m_desentrelazar": {
        "es": "Desentrelazar — yadif (FFmpeg)",
        "en": "Deinterlace — yadif (FFmpeg)",
        "fr": "Désentrelacer — yadif (FFmpeg)"},
    "m_denoise": {
        "es": "Reducir ruido — hqdn3d (FFmpeg)",
        "en": "Denoise — hqdn3d (FFmpeg)",
        "fr": "Débruiter — hqdn3d (FFmpeg)"},
    "m_estabilizar": {
        "es": "Estabilizar — vidstab (FFmpeg)",
        "en": "Stabilize — vidstab (FFmpeg)",
        "fr": "Stabiliser — vidstab (FFmpeg)"},
    "n_desentrelazar": {
        "es": "Elimina el entrelazado clásico de material de TV/cámara de vídeo usando "
              "yadif (Yet Another DeInterlacing Filter). Sin GPU, funciona en cualquier "
              "máquina. Rápido.",
        "en": "Removes classic interlacing from TV/video-camera footage using yadif "
              "(Yet Another DeInterlacing Filter). No GPU needed, runs anywhere. Fast.",
        "fr": "Supprime l'entrelacement classique des vidéos TV/caméscope avec yadif "
              "(Yet Another DeInterlacing Filter). Sans GPU, fonctionne partout. Rapide."},
    "n_denoise": {
        "es": "Reduce el ruido de video con el filtro hqdn3d de FFmpeg. Controla "
              "la fuerza en luminancia y crominancia por separado. Sin GPU.",
        "en": "Reduces video noise with FFmpeg's hqdn3d filter. Control luminance and "
              "chrominance strength separately. No GPU needed.",
        "fr": "Réduit le bruit vidéo avec le filtre hqdn3d de FFmpeg. Contrôlez "
              "séparément la force en luminance et chrominance. Sans GPU."},
    "n_estabilizar": {
        "es": "Estabilización de cámara en 2 pasadas con libvidstab. El zoom oculta "
              "los bordes negros. Requiere FFmpeg compilado con --enable-libvidstab. "
              "Sin GPU.",
        "en": "2-pass camera stabilization with libvidstab. Zoom hides black borders. "
              "Requires FFmpeg compiled with --enable-libvidstab. No GPU needed.",
        "fr": "Stabilisation caméra en 2 passes avec libvidstab. Le zoom masque les "
              "bords noirs. Nécessite FFmpeg compilé avec --enable-libvidstab. Sans GPU."},
    # denoise sliders
    "den_luma": {
        "es": "Fuerza luma (0–10)", "en": "Luma strength (0–10)",
        "fr": "Force luma (0–10)"},
    "den_chroma": {
        "es": "Fuerza chroma (0–10)", "en": "Chroma strength (0–10)",
        "fr": "Force chroma (0–10)"},
    # stabilize sliders
    "est_suavidad": {
        "es": "Suavidad (1–30)", "en": "Smoothing (1–30)",
        "fr": "Lissage (1–30)"},
    "est_zoom": {
        "es": "Zoom de entrada (0.0–1.0)", "en": "Input zoom (0.0–1.0)",
        "fr": "Zoom d'entrée (0.0–1.0)"},
    # ---- formato de salida ----
    "formato_salida_v": {
        "es": "Formato de salida de video", "en": "Video output format",
        "fr": "Format de sortie vidéo"},
    "formato_salida_i": {
        "es": "Formato de salida de imagen", "en": "Image output format",
        "fr": "Format de sortie de l'image"},
    # ---- cancelar ----
    "cancelar": {"es": "Cancelar", "en": "Cancel", "fr": "Annuler"},
    "cancelado": {"es": "⛔ Cancelado", "en": "⛔ Cancelled", "fr": "⛔ Annulé"},
    # ---- comparador de video ----
    "comparador_video": {
        "es": "Comparador antes/después (frame)", "en": "Before/after comparator (frame)",
        "fr": "Comparateur avant/après (image)"},
    "comparador_fs": {
        "es": "Pantalla completa", "en": "Fullscreen", "fr": "Plein écran"},
    # ---- comparador por el frame del propio video ----
    "cmp_scrub_ayuda": {
        "es": "Mueve la barra del video de arriba y **pausa en el frame que quieras**; "
              "luego pulsa «📸 Comparar este frame» (entrada vs resultado) o «👁 Vista "
              "previa» (cómo quedaría el filtro en ese frame).",
        "en": "Scrub the video bar above and **pause on the frame you want**; then press "
              "“📸 Compare this frame” (input vs result) or “👁 Preview” (how the filter "
              "would look on that frame).",
        "fr": "Déplacez la barre de la vidéo ci-dessus et **mettez en pause sur l'image "
              "voulue** ; puis « 📸 Comparer cette image » (entrée vs résultat) ou « 👁 "
              "Aperçu » (rendu du filtre sur cette image)."},
    "cmp_este_frame": {
        "es": "📸 Comparar este frame", "en": "📸 Compare this frame",
        "fr": "📸 Comparer cette image"},
    "cmp_sin_resultado": {
        "es": "⚠️ Primero mejora el video; luego mueve la barra y compara cualquier frame.",
        "en": "⚠️ Enhance the video first; then scrub and compare any frame.",
        "fr": "⚠️ Améliorez d'abord la vidéo ; ensuite déplacez la barre et comparez n'importe quelle image."},
    # ---- comparador avanzado: elegir frame por línea de tiempo + hasta 4 ----
    "cmp_avanzado": {
        "es": "🔬 Comparar otros frames (línea de tiempo)",
        "en": "🔬 Compare other frames (timeline)",
        "fr": "🔬 Comparer d'autres images (chronologie)"},
    "cmp_posicion": {
        "es": "Momento del video", "en": "Point in the video",
        "fr": "Moment de la vidéo"},
    "cmp_ayuda": {
        "es": "Mueve la barra al momento que quieras y pulsa «Añadir»: puedes fijar "
              "hasta 4 frames para compararlos antes/después a la vez.",
        "en": "Move the bar to any moment and press “Add”: you can pin up to 4 "
              "frames to compare before/after at once.",
        "fr": "Déplacez la barre au moment voulu et appuyez sur « Ajouter » : vous "
              "pouvez épingler jusqu'à 4 images à comparer avant/après."},
    "cmp_anadir": {
        "es": "➕ Añadir este frame", "en": "➕ Add this frame",
        "fr": "➕ Ajouter cette image"},
    "cmp_limpiar": {
        "es": "🗑️ Limpiar", "en": "🗑️ Clear", "fr": "🗑️ Effacer"},
    "cmp_sin_video": {
        "es": "⚠️ Primero mejora un video; luego podrás comparar sus frames.",
        "en": "⚠️ Enhance a video first; then you can compare its frames.",
        "fr": "⚠️ Améliorez d'abord une vidéo ; vous pourrez ensuite comparer ses images."},
    "cmp_lleno": {
        "es": "Ya hay 4 frames fijados — pulsa «Limpiar» para empezar de nuevo.",
        "en": "4 frames already pinned — press “Clear” to start over.",
        "fr": "4 images déjà épinglées — appuyez sur « Effacer » pour recommencer."},
    "cmp_frame_en": {
        "es": "Frame al", "en": "Frame at", "fr": "Image à"},
    # ---- presets de revelado ----
    "preset_seccion": {
        "es": "💾 Presets (guardar/cargar este look)",
        "en": "💾 Presets (save/load this look)",
        "fr": "💾 Préréglages (enregistrer/charger ce look)"},
    "preset_nombre": {
        "es": "Nombre del preset", "en": "Preset name", "fr": "Nom du préréglage"},
    "preset_guardar": {
        "es": "Guardar preset", "en": "Save preset", "fr": "Enregistrer le préréglage"},
    "preset_cargar": {
        "es": "Cargar preset guardado", "en": "Load saved preset",
        "fr": "Charger un préréglage"},
    "preset_guardado": {
        "es": "✅ Preset guardado", "en": "✅ Preset saved", "fr": "✅ Préréglage enregistré"},
    "preset_sin_nombre": {
        "es": "⚠️ Escribe un nombre para el preset", "en": "⚠️ Enter a preset name",
        "fr": "⚠️ Entrez un nom pour le préréglage"},
    # ---- galería ----
    "tab_galeria": {"es": "Galería", "en": "Gallery", "fr": "Galerie"},
    "galeria_imagenes": {
        "es": "Imágenes guardadas", "en": "Saved images", "fr": "Images enregistrées"},
    "galeria_videos": {
        "es": "Videos guardados", "en": "Saved videos", "fr": "Vidéos enregistrées"},
    "galeria_refrescar": {
        "es": "Refrescar", "en": "Refresh", "fr": "Actualiser"},
    "galeria_limpiar": {
        "es": "Limpiar todo", "en": "Clear all", "fr": "Tout supprimer"},
    "galeria_confirmar_aviso": {
        "es": "⚠️ Esto borra **todos** los archivos de salidas/. No se puede deshacer.",
        "en": "⚠️ This deletes **all** files in salidas/. This cannot be undone.",
        "fr": "⚠️ Ceci supprime **tous** les fichiers de salidas/. Irréversible."},
    "galeria_confirmar": {
        "es": "Sí, borrar todo", "en": "Yes, delete all", "fr": "Oui, tout supprimer"},
    "galeria_vacia": {
        "es": "_No hay archivos en salidas/_", "en": "_No files in salidas/_",
        "fr": "_Aucun fichier dans salidas/_"},
    # ---- lote (batch) ----
    "tab_lote": {"es": "Lote", "en": "Batch", "fr": "Lot"},
    "lote_archivos": {
        "es": "Archivos a procesar", "en": "Files to process",
        "fr": "Fichiers à traiter"},
    "lote_motor": {"es": "Motor", "en": "Engine", "fr": "Moteur"},
    "lote_escala": {"es": "Escala", "en": "Scale", "fr": "Échelle"},
    "lote_resolucion": {
        "es": "Resolución objetivo", "en": "Target resolution",
        "fr": "Résolution cible"},
    "lote_procesar": {
        "es": "Procesar lote", "en": "Process batch", "fr": "Traiter le lot"},
    "lote_progreso": {
        "es": "Progreso del lote", "en": "Batch progress", "fr": "Progression du lot"},
    "lote_archivo_n": {
        "es": "Archivo {n}/{total}: {nombre}", "en": "File {n}/{total}: {nombre}",
        "fr": "Fichier {n}/{total} : {nombre}"},
    # ---- estado de modelos ----
    "s_modelos": {
        "es": "Estado de modelos", "en": "Model status", "fr": "État des modèles"},
    "s_pesos_ok": {"es": "✅ pesos encontrados", "en": "✅ weights found",
                   "fr": "✅ poids trouvés"},
    "s_pesos_no": {"es": "❌ pesos no encontrados", "en": "❌ weights not found",
                   "fr": "❌ poids introuvables"},
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
    # ---- secciones del estado de motores (pestaña Sistema) ----
    "s_listos": {
        "es": "Motores listos en tu equipo",
        "en": "Engines ready on your machine",
        "fr": "Moteurs prêts sur votre machine"},
    "s_instalables": {
        "es": "Extras opcionales — se instalan con un comando",
        "en": "Optional extras — install with one command",
        "fr": "Extras optionnels — à installer en une commande"},
    "s_no_aplican": {
        "es": "No disponibles en tu equipo (no es un error)",
        "en": "Not available on your machine (not an error)",
        "fr": "Indisponibles sur votre machine (ce n'est pas une erreur)"},
    "s_requiere_nvidia": {
        "es": "requiere GPU NVIDIA",
        "en": "requires an NVIDIA GPU",
        "fr": "nécessite un GPU NVIDIA"},
    "s_instalar_intro": {
        "es": "En Terminal, dentro de la carpeta de la app, ejecuta:",
        "en": "In Terminal, inside the app folder, run:",
        "fr": "Dans le Terminal, dans le dossier de l'app, lancez :"},
    "s_nada_listo": {
        "es": "_Aún no hay motores instalados — corre el instalador de tu plataforma._",
        "en": "_No engines installed yet — run your platform's installer._",
        "fr": "_Aucun moteur installé — lancez l'installateur de votre plateforme._"},

    # ---- aviso: no hay motor de mejora por IA instalado ----
    "sin_mejorador_v": {
        "es": "⚠️ **No hay ningún motor de mejora por IA instalado.** Los motores de "
              "abajo solo aplican color, grano o limpieza — **no suben la resolución ni "
              "reconstruyen detalle**. Para mejora real (SeedVR2, nivel Topaz), instálalo:",
        "en": "⚠️ **No AI enhancement engine is installed.** The engines below only apply "
              "color, grain or cleanup — **they do not increase resolution or rebuild "
              "detail**. For real enhancement (SeedVR2, Topaz-level), install it:",
        "fr": "⚠️ **Aucun moteur d'amélioration par IA n'est installé.** Les moteurs "
              "ci-dessous n'appliquent que couleur, grain ou nettoyage — **ils n'augmentent "
              "pas la résolution**. Pour une vraie amélioration (SeedVR2, niveau Topaz), "
              "installez-le :"},
    "sin_mejorador_i": {
        "es": "⚠️ **No hay ningún motor de mejora por IA instalado.** Los motores de "
              "abajo solo aplican color o grano — **no suben la resolución ni reconstruyen "
              "detalle**. Para mejora real de imagen, instala los motores:",
        "en": "⚠️ **No AI enhancement engine is installed.** The engines below only apply "
              "color or grain — **they do not increase resolution or rebuild detail**. For "
              "real image enhancement, install the engines:",
        "fr": "⚠️ **Aucun moteur d'amélioration par IA n'est installé.** Les moteurs "
              "ci-dessous n'appliquent que couleur ou grain. Pour une vraie amélioration "
              "d'image, installez les moteurs :"},
    "como_instalar_mac": {
        "es": "En Terminal, dentro de la carpeta de la app: `bash install/instalar_mac.sh` "
              "(descarga SeedVR2, varios GB). Luego reinicia VideoBoost.",
        "en": "In Terminal, inside the app folder: `bash install/instalar_mac.sh` "
              "(downloads SeedVR2, several GB). Then restart VideoBoost.",
        "fr": "Dans le Terminal, dans le dossier de l'app : `bash install/instalar_mac.sh` "
              "(télécharge SeedVR2, plusieurs Go). Puis relancez VideoBoost."},
    "como_instalar_nvidia": {
        "es": "En la terminal, dentro de la carpeta de la app: `bash install/instalar_nvidia.sh` "
              "(o `install\\INSTALAR_NVIDIA.bat` en Windows). Luego reinicia VideoBoost.",
        "en": "In the terminal, inside the app folder: `bash install/instalar_nvidia.sh` "
              "(or `install\\INSTALAR_NVIDIA.bat` on Windows). Then restart VideoBoost.",
        "fr": "Dans le terminal, dans le dossier de l'app : `bash install/instalar_nvidia.sh` "
              "(ou `install\\INSTALAR_NVIDIA.bat` sous Windows). Puis relancez VideoBoost."},

    # ---- vista previa de motor + resolución ----
    "vp_motor": {"es": "Motor", "en": "Engine", "fr": "Moteur"},
    "vp_no_resol": {
        "es": "no cambia la resolución (solo color/limpieza)",
        "en": "does not change resolution (color/cleanup only)",
        "fr": "ne change pas la résolution (couleur/nettoyage seulement)"},
    "vp_sube_a": {"es": "sube a", "en": "upscales to", "fr": "passe à"},

    # ---- formato / descarga de video ----
    "formato_nota": {
        "es": "ProRes y H.265 son para exportar/editar — **no se previsualizan en el "
              "navegador** (el reproductor saldría en blanco). La vista previa siempre usa "
              "H.264; descarga el formato elegido con el botón de abajo.",
        "en": "ProRes and H.265 are for export/editing — **they don't preview in the "
              "browser** (the player would show blank). The preview always uses H.264; "
              "download your chosen format with the button below.",
        "fr": "ProRes et H.265 servent à l'export/montage — **pas d'aperçu dans le "
              "navigateur** (le lecteur resterait blanc). L'aperçu utilise toujours H.264 ; "
              "téléchargez le format choisi avec le bouton ci-dessous."},
    "descargar_v": {
        "es": "Descargar video", "en": "Download video", "fr": "Télécharger la vidéo"},
    # ---- filtros de post-proceso (columna derecha) ----
    "filtros_titulo": {
        "es": "🎨 Filtros y ajustes", "en": "🎨 Filters & adjustments",
        "fr": "🎨 Filtres et réglages"},
    "filtros_intro": {
        "es": "Se aplican AL RESULTADO ya mejorado (o al video original), antes de "
              "descargar. Puedes encadenar varios. Mira la vista previa antes de aplicar.",
        "en": "Applied to the ENHANCED result (or the original video), before downloading. "
              "You can chain several. Check the preview before applying.",
        "fr": "Appliqués au RÉSULTAT amélioré (ou à la vidéo d'origine), avant le "
              "téléchargement. Vous pouvez en enchaîner plusieurs. Voyez l'aperçu avant."},
    "filtros_picker": {
        "es": "Filtro", "en": "Filter", "fr": "Filtre"},
    "filtros_preview": {
        "es": "Vista previa (un frame)", "en": "Preview (one frame)",
        "fr": "Aperçu (une image)"},
    "filtros_ver_preview": {
        "es": "👁 Vista previa", "en": "👁 Preview", "fr": "👁 Aperçu"},
    "filtros_aplicar": {
        "es": "Aplicar filtro al video mejorado",
        "en": "Apply filter to the enhanced video",
        "fr": "Appliquer le filtre à la vidéo améliorée"},
    "filtros_aplicar_nota": {
        "es": "Se aplica al video de **«Resultado»** (el ya mejorado). Si aún no has "
              "mejorado nada, se aplica al video de entrada.",
        "en": "Applies to the **“Result”** video (the enhanced one). If you haven't "
              "enhanced yet, it applies to the input video.",
        "fr": "S'applique à la vidéo **« Résultat »** (l'améliorée). Si vous n'avez rien "
              "amélioré, elle s'applique à la vidéo d'entrée."},
    "filtros_sin_base": {
        "es": "⚠️ Primero mejora un video (o sube uno); el filtro se aplica sobre ese resultado.",
        "en": "⚠️ Enhance a video first (or upload one); the filter applies to that result.",
        "fr": "⚠️ Améliorez d'abord une vidéo (ou téléversez-en une) ; le filtre s'applique au résultat."},
    "preview_temporal": {
        "es": "Este filtro es temporal (necesita movimiento entre frames): no tiene vista "
              "previa de un solo frame. Aplícalo y mira el resultado.",
        "en": "This filter is temporal (needs motion across frames): no single-frame preview. "
              "Apply it and check the result.",
        "fr": "Ce filtre est temporel (mouvement entre images) : pas d'aperçu d'une seule "
              "image. Appliquez-le et regardez le résultat."},

    # ---- aviso SeedVR2 lento en Mac ----
    "n_seedvr2_mac_lento": {
        "es": "⚠️ **En Mac (MPS) SeedVR2 es MUY lento** — minutos por cada segundo "
              "de video; un clip de varios segundos puede tardar horas y parecer "
              "«atascado» (no lo está, está procesando). Para uso normal usa "
              "**Real-ESRGAN**; deja SeedVR2 para clips muy cortos.",
        "en": "⚠️ **On Mac (MPS), SeedVR2 is VERY slow** — minutes per second of "
              "video; a few-second clip can take hours and look “stuck” (it isn't, "
              "it's processing). For everyday use pick **Real-ESRGAN**; keep SeedVR2 "
              "for very short clips.",
        "fr": "⚠️ **Sur Mac (MPS), SeedVR2 est TRÈS lent** — des minutes par seconde "
              "de vidéo ; un clip de quelques secondes peut prendre des heures et "
              "sembler « bloqué » (il ne l'est pas). Pour un usage courant, choisissez "
              "**Real-ESRGAN** ; réservez SeedVR2 aux clips très courts."},

    # ---- mantenimiento de motores (pestaña Sistema) ----
    "mant_titulo": {
        "es": "Mantenimiento de motores", "en": "Engine maintenance",
        "fr": "Maintenance des moteurs"},
    "mant_intro": {
        "es": "Re-descarga un motor si se corrompió, o comprueba si hay una versión más nueva.",
        "en": "Re-download an engine if it got corrupted, or check for a newer version.",
        "fr": "Re-téléchargez un moteur s'il est corrompu, ou vérifiez s'il existe une version plus récente."},
    "mant_redescargar": {
        "es": "🔄 Re-descargar", "en": "🔄 Re-download", "fr": "🔄 Re-télécharger"},
    "mant_comprobar": {
        "es": "🔍 Comprobar versión", "en": "🔍 Check version", "fr": "🔍 Vérifier la version"},
    "mant_log": {
        "es": "Mantenimiento", "en": "Maintenance", "fr": "Maintenance"},
    "mant_abrir": {
        "es": "📁 Abrir carpeta", "en": "📁 Open folder", "fr": "📁 Ouvrir le dossier"},
    "mant_ubic": {
        "es": "Se guarda en", "en": "Stored at", "fr": "Enregistré dans"},
    "mant_no_descargado": {
        "es": "(aún no descargado)", "en": "(not downloaded yet)",
        "fr": "(pas encore téléchargé)"},
}


def t(clave: str, lang: str = "es") -> str:
    entrada = T.get(clave, {})
    return entrada.get(lang) or entrada.get("es") or clave
