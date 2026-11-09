# -*- coding: utf-8 -*-
"""
Orquestador maestro de la serie de 4 cápsulas en video del Método de Diferencias Finitas:
  1. 01_derivadas_diferencias_finitas.mp4
  2. 02_malla_molecula_y_viga.mp4
  3. 03_difusion_calor_laplace_2d.mp4
  4. 04_electrostatica_poisson_y_campo_e.mp4

Modos de uso:
  python videos/build_series.py --check-offline        # Valida subíndices y compila todos los SVG de Typst (offline)
  python videos/build_series.py --tts-only             # Descarga en paralelo toda la locución neuronal (requiere red)
  python videos/build_series.py --render-only --preview # Render rápido 480p15 para auditoría visual (offline)
  python videos/build_series.py --render-only          # Render final Full HD 1080p60 de las 4 cápsulas (offline)
"""

import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from video_common import (
    validate_subscript_pronunciation,
    download_segments_tts,
    build_master_audio_and_timings,
    compile_typst_formulas,
    render_manim_and_mux,
)

import capsula_01
import capsula_02
import capsula_03
import capsula_04

ALL_CAPSULES = {
    1: (capsula_01, Path(capsula_01.__file__).resolve()),
    2: (capsula_02, Path(capsula_02.__file__).resolve()),
    3: (capsula_03, Path(capsula_03.__file__).resolve()),
    4: (capsula_04, Path(capsula_04.__file__).resolve()),
}


async def download_all_tts(selected, force: bool = False):
    sem = asyncio.Semaphore(2)
    for num in selected:
        mod, _ = ALL_CAPSULES[num]
        audio_dir = mod.WORK_DIR / "audio"
        print(f"[Cápsula {num}] Descargando {len(mod.SEGMENTS)} segmentos...", flush=True)
        await download_segments_tts(mod.SEGMENTS, audio_dir, sem=sem, force=force)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    raw_args = sys.argv[1:]
    flags = {a for a in raw_args if a.startswith("--")}
    nums = [int(a) for a in raw_args if a.isdigit() and int(a) in ALL_CAPSULES]
    selected = nums if nums else [1, 2, 3, 4]

    # 1. Validación estricta de pronunciación de subíndices en todas las cápsulas seleccionadas
    for num in selected:
        mod, _ = ALL_CAPSULES[num]
        validate_subscript_pronunciation(mod.CAPSULE_SLUG, mod.SEGMENTS)
    print(f"[OK] Pronunciación de subíndices validada en cápsulas: {selected}")

    if "--check-offline" in flags:
        for num in selected:
            mod, _ = ALL_CAPSULES[num]
            svg_dir = mod.WORK_DIR / "svg"
            compile_typst_formulas(mod.FORMULAS, svg_dir)
            print(f"[OK] Cápsula {num}: {len(mod.FORMULAS)} fórmulas Typst compiladas a SVG en {svg_dir}")
        return

    if "--tts-only" in flags:
        asyncio.run(download_all_tts(selected, force=("--force-tts" in flags)))
        print("\n[OK] Todas las pistas MP3 neuronales fueron descargadas exitosamente.", flush=True)
        return

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    preview = "--preview" in flags

    if "--render-only" not in flags:
        asyncio.run(download_all_tts(selected))

    for num in selected:
        mod, mod_path = ALL_CAPSULES[num]
        print(f"\n{'='*72}")
        print(f"PROCESANDO CÁPSULA {num}: {mod.OUTPUT_MP4.name} ({'PREVIEW 480p15' if preview else 'FINAL 1080p60'})")
        print(f"{'='*72}")
        mod.WORK_DIR.mkdir(parents=True, exist_ok=True)
        audio_dir = mod.WORK_DIR / "audio"
        svg_dir = mod.WORK_DIR / "svg"
        timings_json = mod.WORK_DIR / "timings.json"

        master_wav = build_master_audio_and_timings(mod.SEGMENTS, audio_dir, timings_json, ffmpeg_exe)
        compile_typst_formulas(mod.FORMULAS, svg_dir)

        out_target = (mod.WORK_DIR / f"preview_{mod.OUTPUT_MP4.name}") if preview else mod.OUTPUT_MP4
        render_manim_and_mux(
            scene_py=mod_path,
            scene_class=mod.SCENE_CLASS,
            master_wav=master_wav,
            output_mp4=out_target,
            work_dir=mod.WORK_DIR,
            ffmpeg_exe=ffmpeg_exe,
            preview=preview,
        )


if __name__ == "__main__":
    main()
