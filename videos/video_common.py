# -*- coding: utf-8 -*-
"""
Motor común para la serie de cápsulas en video del Método de Diferencias Finitas:
- Co-conducción dinámica con dos voces neuronales expresivas (Gonzalo + Salomé) y prosodia por rol.
- Validación automática de pronunciación pausada de subíndices ("sub... í", "sub... cero", etc.).
- Generación de fondo musical ambiental suave estilo 3Blue1Brown (pad armónico cálido en estéreo a -31 dBFS).
- Compilación rápida de ecuaciones vectoriales mediante Typst -> SVG.
- Ensamblaje exacto de audio + video en MP4 H.264 + AAC 192 kbps (1080p60).
"""

import asyncio
import json
import math
import os
import re
import shutil
import subprocess
import wave
from pathlib import Path
import numpy as np

# Voces neuronales latinoamericanas expresivas (narrador principal + co-presentadora interactiva)
DEFAULT_VOICE = "es-CO-GonzaloNeural"
COHOST_VOICE = "es-CO-SalomeNeural"

PROSODY_PRESETS = {
    "hook":     {"rate": "+5%", "pitch": "+2Hz", "pad_after": 0.42},
    "funfact":  {"rate": "+5%", "pitch": "+3Hz", "pad_after": 0.46},
    "explain":  {"rate": "+3%", "pitch": "+0Hz", "pad_after": 0.38},
    "math":     {"rate": "-2%", "pitch": "-1Hz", "pad_after": 0.42},
    "endpoint": {"rate": "+4%", "pitch": "+2Hz", "pad_after": 0.55},
}


def validate_subscript_pronunciation(capsule_name: str, segments: list):
    """
    Verifica que ningún guion contenga 'sub i', 'sub 0', 'sub n', etc. sin los puntos suspensivos 'sub... '
    que obligan al motor TTS a articular una micro-pausa limpia antes del subíndice.
    """
    bad_pattern = re.compile(r"\bsub\s+(?!\.\.\.)[a-záéíóúñ0-9]\b", re.IGNORECASE)
    for seg in segments:
        m = bad_pattern.search(seg["narration"])
        if m:
            raise ValueError(
                f"[{capsule_name} / {seg['id']}] Subíndice sin pausa detectado: '{m.group(0)}'. "
                f"Usa 'sub... í', 'sub... cero', etc."
            )


async def download_segments_tts(segments: list, audio_dir: Path, voice: str = DEFAULT_VOICE, sem: asyncio.Semaphore | None = None, force: bool = False):
    """Descarga con concurrencia controlada y escritura atómica los archivos MP3 aplicando prosodia dinámica."""
    import edge_tts

    if sem is None:
        sem = asyncio.Semaphore(2)

    audio_dir.mkdir(parents=True, exist_ok=True)

    async def _one(seg):
        style = seg.get("style", "explain")
        preset = PROSODY_PRESETS.get(style, PROSODY_PRESETS["explain"])
        seg_voice = seg.get("voice", voice)
        speaker = "Salomé" if seg_voice == COHOST_VOICE else "Gonzalo"
        mp3_path = audio_dir / f"{seg['id']}.mp3"
        tmp_path = audio_dir / f"{seg['id']}.part.mp3"

        if not force and mp3_path.exists() and mp3_path.stat().st_size > 20000:
            print(f"  [TTS {speaker:7s} | cache   ] {mp3_path.name} ({mp3_path.stat().st_size:,} B)", flush=True)
            return

        async with sem:
            last_err = None
            for attempt in range(4):
                try:
                    if tmp_path.exists():
                        tmp_path.unlink()
                    comm = edge_tts.Communicate(
                        seg["narration"],
                        seg_voice,
                        rate=preset["rate"],
                        pitch=preset["pitch"],
                    )
                    await comm.save(str(tmp_path))
                    if tmp_path.exists() and tmp_path.stat().st_size > 20000:
                        tmp_path.replace(mp3_path)
                        print(f"  [TTS {speaker:7s} | {style:8s}] {mp3_path.name} ({mp3_path.stat().st_size:,} B)", flush=True)
                        return
                except Exception as exc:
                    last_err = exc
                    await asyncio.sleep(0.9 * (attempt + 1))
            raise RuntimeError(f"Fallo TTS en {seg['id']} tras reintentos: {last_err}")

    await asyncio.gather(*(_one(s) for s in segments))


def synthesize_ambient_pad(duration_sec: float, out_wav: Path, sample_rate: int = 44100):
    """
    Genera un colchón armónico ambiental muy suave y cálido (estilo 3Blue1Brown / documental científico)
    para acompañar la voz sin distraer (~ -31 dBFS).
    Progresión lenta de 4 acordes suaves: Cmaj9 -> Am9 -> Fmaj7 -> G6/9
    """
    n_samples = int(math.ceil(duration_sec * sample_rate))
    t = np.linspace(0.0, duration_sec, n_samples, endpoint=False, dtype=np.float64)

    chords = [
        [130.81, 196.00, 246.94, 293.66, 329.63],  # Cmaj9 (C3, G3, B3, D4, E4)
        [110.00, 164.81, 220.00, 246.94, 261.63],  # Am9   (A2, E3, A3, B3, C4)
        [87.31,  174.61, 220.00, 261.63, 329.63],  # Fmaj7 (F2, F3, A3, C4, E4)
        [98.00,  196.00, 220.00, 246.94, 293.66],  # G6/9  (G2, G3, A3, B3, D4)
    ]
    chord_len = 8.0

    left = np.zeros(n_samples, dtype=np.float64)
    right = np.zeros(n_samples, dtype=np.float64)

    n_blocks = int(math.ceil(duration_sec / chord_len)) + 1
    for b in range(n_blocks):
        freqs = chords[b % len(chords)]
        center_t = (b + 0.5) * chord_len
        dist = np.abs(t - center_t) / chord_len
        mask = dist < 1.0
        if not np.any(mask):
            continue
        tm = t[mask]
        win = 0.5 * (1.0 + np.cos(np.pi * dist[mask]))

        sig_l = np.zeros_like(tm)
        sig_r = np.zeros_like(tm)
        for idx, f in enumerate(freqs):
            amp = 1.0 / (1.0 + 0.45 * idx)
            lfo_l = 1.0 + 0.12 * np.sin(2.0 * np.pi * (0.11 + 0.03 * idx) * tm)
            lfo_r = 1.0 + 0.12 * np.cos(2.0 * np.pi * (0.13 + 0.02 * idx) * tm)
            sig_l += amp * lfo_l * np.sin(2.0 * np.pi * (f * 0.9992) * tm)
            sig_r += amp * lfo_r * np.sin(2.0 * np.pi * (f * 1.0008) * tm)

        left[mask] += win * sig_l
        right[mask] += win * sig_r

    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    gain = 0.026 / peak
    left *= gain
    right *= gain

    fi = min(int(1.4 * sample_rate), n_samples // 4)
    fo = min(int(2.0 * sample_rate), n_samples // 4)
    if fi > 0:
        ramp_in = np.linspace(0.0, 1.0, fi)
        left[:fi] *= ramp_in
        right[:fi] *= ramp_in
    if fo > 0:
        ramp_out = np.linspace(1.0, 0.0, fo)
        left[-fo:] *= ramp_out
        right[-fo:] *= ramp_out

    stereo = np.empty((n_samples, 2), dtype=np.int16)
    stereo[:, 0] = np.clip(left * 32767.0, -32767, 32767).astype(np.int16)
    stereo[:, 1] = np.clip(right * 32767.0, -32767, 32767).astype(np.int16)

    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(stereo.tobytes())


def build_master_audio_and_timings(segments: list, audio_dir: Path, timings_json: Path, ffmpeg_exe: str) -> Path:
    """
    Convierte los MP3 a WAV con pausas naturales, mide la duración exacta de cada bloque,
    concatena la voz y mezcla por debajo el pad ambiental suave.
    """
    timings = []
    for seg in segments:
        style = seg.get("style", "explain")
        seg_voice = seg.get("voice", DEFAULT_VOICE)
        speaker = "Salomé" if seg_voice == COHOST_VOICE else "Gonzalo"
        pad_after = PROSODY_PRESETS.get(style, PROSODY_PRESETS["explain"])["pad_after"]
        mp3_path = audio_dir / f"{seg['id']}.mp3"
        if not mp3_path.exists():
            raise FileNotFoundError(f"No existe {mp3_path}; ejecuta la descarga TTS primero.")
        wav_path = audio_dir / f"{seg['id']}.wav"

        subprocess.run(
            [
                ffmpeg_exe, "-y", "-i", str(mp3_path),
                "-af", f"apad=pad_dur={pad_after}",
                "-ar", "44100", "-ac", "2", str(wav_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        probe = subprocess.run(
            [ffmpeg_exe, "-i", str(wav_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", probe.stderr)
        if not m:
            raise RuntimeError(f"Error al medir duración de {wav_path}: {probe.stderr}")
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        timings.append({
            "id": seg["id"],
            "speaker": speaker,
            "style": style,
            "subtitle": seg["subtitle"],
            "wav": str(wav_path),
            "duration": round(dur, 3),
        })
        print(f"  [Timing] {seg['id']:22s} ({speaker:7s}) -> {dur:6.2f} s")

    concat_txt = audio_dir / "concat.txt"
    concat_txt.write_text(
        "\n".join(f"file '{Path(t['wav']).name}'" for t in timings),
        encoding="utf-8",
    )
    voice_wav = audio_dir / "voice_concat.wav"
    subprocess.run(
        [
            ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt), "-c", "copy", str(voice_wav),
        ],
        cwd=str(audio_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    total_dur = sum(t["duration"] for t in timings) + 0.5
    pad_wav = audio_dir / "ambient_pad.wav"
    synthesize_ambient_pad(total_dur, pad_wav)

    master_wav = audio_dir / "master_mix.wav"
    subprocess.run(
        [
            ffmpeg_exe, "-y",
            "-i", str(voice_wav),
            "-i", str(pad_wav),
            "-filter_complex", "[0:a]volume=1.08[v];[1:a]volume=1.0[p];[v][p]amix=inputs=2:duration=first:dropout_transition=0,alimiter=limit=0.95[out]",
            "-map", "[out]",
            "-ar", "44100", "-ac", "2",
            str(master_wav),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    timings_json.write_text(json.dumps(timings, indent=2, ensure_ascii=False), encoding="utf-8")
    return master_wav


def compile_typst_formulas(formulas: dict, svg_dir: Path):
    """Compila un diccionario {nombre: codigo_typst} a archivos SVG vectoriales."""
    import typst

    svg_dir.mkdir(parents=True, exist_ok=True)
    preamble = "#set page(width: auto, height: auto, margin: 3pt, fill: none)\n"
    for name, body in formulas.items():
        typ_path = svg_dir / f"{name}.typ"
        svg_path = svg_dir / f"{name}.svg"
        typ_path.write_text(preamble + body + "\n", encoding="utf-8")
        typst.compile(str(typ_path), output=str(svg_path), format="svg")


def render_manim_and_mux(
    scene_py: Path,
    scene_class: str,
    master_wav: Path,
    output_mp4: Path,
    work_dir: Path,
    ffmpeg_exe: str,
    preview: bool = False,
):
    """Ejecuta Manim y ensambla el MP4 final con audio AAC y faststart."""
    media_dir = work_dir / "manim_media"
    if media_dir.exists():
        shutil.rmtree(media_dir)

    q_flags = ["-ql", "--fps", "15"] if preview else ["-qh", "--fps", "60"]
    env = os.environ.copy()
    env["PATH"] = str(Path(ffmpeg_exe).parent) + os.pathsep + env.get("PATH", "")

    subprocess.run(
        [
            os.path.abspath(os.sys.executable), "-m", "manim", "render",
            *q_flags,
            "--media_dir", str(media_dir),
            "-o", "raw_video.mp4",
            str(scene_py),
            scene_class,
        ],
        env=env,
        check=True,
    )

    candidates = list(media_dir.rglob("raw_video.mp4"))
    if not candidates:
        raise FileNotFoundError(f"No se generó raw_video.mp4 en {media_dir}")
    raw_mp4 = candidates[0]

    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg_exe, "-y",
            "-i", str(raw_mp4),
            "-i", str(master_wav),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            str(output_mp4),
        ],
        check=True,
    )
    shutil.rmtree(media_dir, ignore_errors=True)
    print(f"  [MP4 LISTO] {output_mp4} ({output_mp4.stat().st_size / (1024*1024):.2f} MB)")
