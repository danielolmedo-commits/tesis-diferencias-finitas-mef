# -*- coding: utf-8 -*-
"""
Generador de los 3 Videos de Demostración Matemática y Sustitución Paso a Paso (Fase 3):
- Con narración interactiva a dos voces (Gonzalo + Salomé), pausas naturales en subíndices ("sub... í")
  y fondo musical ambiental suave estilo 3Blue1Brown.
- Con animación algebraica dinámica ("elementos que viajan" en arcos suaves: de las tarjetas a la fracción,
  de los nodos de la malla a la ecuación, cruzando el signo '=' hacia la matriz, y de regreso a la placa).
- Con control estricto de alturas y zonas seguras para evitar cualquier traslape entre fórmulas o encabezados.

Uso:
  1) Descargar audio TTS (requiere red):
     python -u videos/build_demos_fase3.py --tts-only
  2) Compilar Typst + Renderizar Manim 1080p60 + Mezclar audio (100% local):
     python -u videos/build_demos_fase3.py --render-only
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
import numpy as np
from manim import *

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from video_common import (
    DEFAULT_VOICE,
    COHOST_VOICE,
    validate_subscript_pronunciation,
    download_segments_tts,
    build_master_audio_and_timings,
    compile_typst_formulas,
    render_manim_and_mux,
)
from scene_helpers import setup_chalkboard, build_header, SubtitleHud

WORK_ROOT = BASE_DIR / "_build_series" / "demos_fase3_v2"
SVG_DIR = WORK_ROOT / "svg"


def get_ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


# ==============================================================================
# GUIONES DE VOZ (GONZALO + SALOMÉ) CON SUBÍNDICES PAUSADOS ("sub... ")
# ==============================================================================
DEMO1_SEGMENTS = [
    {
        "id": "d1_s1_promedio",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Paso 1: Viajan los numeradores de Forward y Backward hacia el denominador común 2h.",
        "narration": (
            "Veamos en cámara lenta cómo nace la diferencia central. "
            "Tomamos el numerador de la pendiente hacia adelante: ye sub... í más uno, menos ye sub... í, "
            "y le sumamos el numerador de la pendiente hacia atrás: más ye sub... í, menos ye sub... í menos uno, "
            "todo sobre el denominador común dos hache."
        ),
    },
    {
        "id": "d1_s2_cancela",
        "voice": COHOST_VOICE,
        "style": "explain",
        "subtitle": "En el centro, −yᵢ y +yᵢ chocan y se cancelan (= 0), cerrando la fracción en (yᵢ₊₁ − yᵢ₋₁) / (2h).",
        "narration": (
            "¡Mira el centro del numerador! Menos ye sub... í y más ye sub... í son exactamente opuestos: "
            "chocan, se anulan en cero, y los extremos viajan hacia el centro para formar "
            "ye sub... í más uno, menos ye sub... í menos uno, entre dos hache."
        ),
    },
    {
        "id": "d1_s3_taylor",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Paso 2 (Serie de Taylor): Al restar término a término, se anulan tanto yᵢ como el término cuadrático (h²/2)·y''ᵢ.",
        "narration": (
            "¿Y por qué su precisión es cuadrática? Si escribimos las series de Taylor hacia adelante y hacia atrás "
            "y las restamos columna por columna, ye sub... í se cancela, las primeras derivadas se suman en dos hache por ye prima, "
            "y los términos con hache al cuadrado también se anulan por completo. "
            "Al despejar ye prima, el error que sobrevive es de orden hache al cuadrado."
        ),
    },
    {
        "id": "d1_s4_segunda",
        "voice": COHOST_VOICE,
        "style": "explain",
        "subtitle": "Paso 3 (2da Derivada): Restamos las pendientes entre h; los dos −yᵢ se fusionan en −2yᵢ formando [+1, −2, +1].",
        "narration": (
            "Finalmente, para la segunda derivada restamos la pendiente delantera menos la trasera y dividimos entre hache. "
            "Observa cómo los dos términos centrales negativos viajan juntos para fusionarse en menos dos ye sub... í. "
            "De ahí viajan directamente los famosos pesos de nuestra molécula: más uno, menos dos y más uno."
        ),
    },
]

DEMO2_SEGMENTS = [
    {
        "id": "d2_s1_plantilla",
        "voice": DEFAULT_VOICE,
        "style": "explain",
        "subtitle": "Paso 1: Posicionamos la molécula en cruz sobre el nodo (1,1) y escribimos sus 5 términos.",
        "narration": (
            "Veamos cómo se arma una fila de la matriz a partir de la malla. "
            "Al colocar la molécula en cruz sobre el nodo interno uno coma uno, "
            "sumamos sus cuatro vecinos menos cuatro veces el nodo central igual a cero."
        ),
    },
    {
        "id": "d2_s2_viajan_bordes",
        "voice": COHOST_VOICE,
        "style": "math",
        "subtitle": "Paso 2: Los valores de borde conocidos (50 a la izquierda y 0 abajo) viajan desde la malla hasta la ecuación.",
        "narration": (
            "Pero fíjate en la malla: el vecino izquierdo u sub... cero coma uno toca el borde fijo de cincuenta, "
            "y el vecino inferior u sub... uno coma cero toca el borde de cero. "
            "Esos dos números viajan directamente desde la frontera para sustituir a sus símbolos en la ecuación."
        ),
    },
    {
        "id": "d2_s3_viajan_matriz",
        "voice": DEFAULT_VOICE,
        "style": "endpoint",
        "subtitle": "Paso 3: El 50 cruza el signo '=' hacia {b}, y los coeficientes [4, −1, −1, 0] viajan a la Fila 1 de la matriz [A].",
        "narration": (
            "Ahora el cincuenta conocido salta al otro lado del signo igual, "
            "y los coeficientes de nuestras incógnitas internas, cuatro, menos uno, menos uno y cero, "
            "viajan directo a sus casillas en la primera fila de la matriz A. "
            "Al repetirlo en los cuatro nodos internos, el sistema queda listo y resuelto."
        ),
    },
]

DEMO3_SEGMENTS = [
    {
        "id": "d3_s1_sustitucion_edp",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Paso 1: Sustituimos ∂²T/∂x² (variando i) y ∂²T/∂y² (variando j) por sus diferencias finitas centrales.",
        "narration": (
            "Veamos paso a paso cómo pasamos de la ecuación diferencial de Laplace a la fórmula del promedio de los cuatro vecinos. "
            "Partimos de la segunda derivada parcial de Te respecto a equis, más la segunda derivada respecto a ye, igual a cero. "
            "Primero sustituimos la derivada en equis variando el índice í y dejando fijo jota: "
            "Te sub... í más uno coma jota, menos dos Te sub... í coma jota, más Te sub... í menos uno coma jota, entre delta equis al cuadrado. "
            "Y hacemos exactamente lo mismo en el eje vertical variando el índice jota, entre delta ye al cuadrado."
        ),
    },
    {
        "id": "d3_s2_malla_h_y_fusion",
        "voice": COHOST_VOICE,
        "style": "explain",
        "subtitle": "Paso 2: Con Δx = Δy = h multiplicamos todo por h² (se van los denominadores) y −2Tᵢ,ⱼ − 2Tᵢ,ⱼ se fusionan en −4Tᵢ,ⱼ.",
        "narration": (
            "Ahora, como nuestra malla es cuadrada, delta equis y delta ye son iguales al paso hache. "
            "Al multiplicar toda la ecuación por hache al cuadrado, ambos denominadores viajan hacia el cero de la derecha y desaparecen. "
            "Y observa los dos términos centrales negativos: menos dos Te sub... í coma jota del eje equis, "
            "y menos dos Te sub... í coma jota del eje ye, viajan al centro para fusionarse en menos cuatro Te sub... í coma jota."
        ),
    },
    {
        "id": "d3_s3_despeje_promedio",
        "voice": DEFAULT_VOICE,
        "style": "endpoint",
        "subtitle": "Paso 3: −4Tᵢ,ⱼ cruza el signo '=' como +4Tᵢ,ⱼ y el 4 baja dividiendo → Promedio exacto de los 4 vecinos.",
        "narration": (
            "Por último hacemos el despeje: el término menos cuatro Te sub... í coma jota salta al lado derecho del signo igual con signo positivo. "
            "Y ese cuatro que multiplica baja dividiendo a toda la suma. "
            "¡Así demostramos por qué la temperatura en cada nodo de la placa es exactamente la suma de sus cuatro vecinos dividida entre cuatro!"
        ),
    },
]


# ==============================================================================
# FÓRMULAS VECTORIALES TYPST (ALTURAS CONTROLADAS, SIN PARÉNTESIS GIGANTES)
# ==============================================================================
FORMULAS_ALL = {
    # Demo 1
    "d1_card_fwd": '#set text(fill: rgb("#fbbf24"), size: 22pt)\n$ m_("Forward") = frac(y_(i+1) - y_i, h) $',
    "d1_card_bwd": '#set text(fill: rgb("#38bdf8"), size: 22pt)\n$ m_("Backward") = frac(y_i - y_(i-1), h) $',
    "d1_lhs_yp": '#set text(fill: rgb("#f8fafc"), size: 25pt, weight: "bold")\n$ y\'(x_i) approx $',
    "d1_tok_yip1": '#set text(fill: rgb("#fbbf24"), size: 24pt, weight: "bold")\n$ y_(i+1) $',
    "d1_tok_myi": '#set text(fill: rgb("#f87171"), size: 24pt, weight: "bold")\n$ - y_i $',
    "d1_tok_pyi": '#set text(fill: rgb("#f87171"), size: 24pt, weight: "bold")\n$ + y_i $',
    "d1_tok_myim1": '#set text(fill: rgb("#38bdf8"), size: 24pt, weight: "bold")\n$ - y_(i-1) $',
    "d1_tok_pyim1": '#set text(fill: rgb("#38bdf8"), size: 24pt, weight: "bold")\n$ + y_(i-1) $',
    "d1_tok_m2yi": '#set text(fill: rgb("#34d399"), size: 25pt, weight: "bold")\n$ - 2 y_i $',
    "d1_den_2h": '#set text(fill: rgb("#e2e8f0"), size: 24pt, weight: "bold")\n$ 2 h $',
    "d1_den_h2": '#set text(fill: rgb("#e2e8f0"), size: 24pt, weight: "bold")\n$ h^2 $',
    "d1_cen_box": '#set text(fill: rgb("#60a5fa"), size: 25pt, weight: "bold")\n$ y\'(x_i) approx frac(y_(i+1) - y_(i-1), 2 h) $',

    # Taylor tokens por columna (sin paréntesis altos para evitar traslape vertical)
    "t_r1_lhs": '#set text(fill: rgb("#fbbf24"), size: 21pt, weight: "bold")\n$ y_(i+1) = $',
    "t_r1_c1":  '#set text(fill: rgb("#f87171"), size: 21pt)\n$ y_i $',
    "t_r1_c2":  '#set text(fill: rgb("#34d399"), size: 21pt)\n$ + h y\'_i $',
    "t_r1_c3":  '#set text(fill: rgb("#f87171"), size: 21pt)\n$ + frac(h^2, 2) y\'\'_i $',
    "t_r1_c4":  '#set text(fill: rgb("#cbd5e1"), size: 21pt)\n$ + frac(h^3, 6) y\'\'\'_i $',

    "t_r2_lhs": '#set text(fill: rgb("#38bdf8"), size: 21pt, weight: "bold")\n$ - y_(i-1) = $',
    "t_r2_c1":  '#set text(fill: rgb("#f87171"), size: 21pt)\n$ - y_i $',
    "t_r2_c2":  '#set text(fill: rgb("#34d399"), size: 21pt)\n$ + h y\'_i $',
    "t_r2_c3":  '#set text(fill: rgb("#f87171"), size: 21pt)\n$ - frac(h^2, 2) y\'\'_i $',
    "t_r2_c4":  '#set text(fill: rgb("#cbd5e1"), size: 21pt)\n$ + frac(h^3, 6) y\'\'\'_i $',

    "t_res_lhs": '#set text(fill: rgb("#f8fafc"), size: 21pt, weight: "bold")\n$ y_(i+1) - y_(i-1) = $',
    "t_res_c2":  '#set text(fill: rgb("#34d399"), size: 22pt, weight: "bold")\n$ 2 h y\'_i $',
    "t_res_c4":  '#set text(fill: rgb("#fde68a"), size: 21pt, weight: "bold")\n$ + frac(h^3, 3) y\'\'\'_i   ==>   "Error" = O(h^2) $',

    "d1_d2_top": '#set text(fill: rgb("#f8fafc"), size: 22pt)\n$ y\'\'(x_i) approx frac(m_("Forward") - m_("Backward"), h) $',
    "d1_lhs_ypp": '#set text(fill: rgb("#f8fafc"), size: 25pt, weight: "bold")\n$ y\'\'(x_i) approx $',

    # Demo 2
    "d2_tok_u21": '#set text(fill: rgb("#60a5fa"), size: 22pt, weight: "bold")\n$ u_(2,1) $',
    "d2_tok_u01": '#set text(fill: rgb("#fbbf24"), size: 22pt, weight: "bold")\n$ u_(0,1) $',
    "d2_tok_u12": '#set text(fill: rgb("#60a5fa"), size: 22pt, weight: "bold")\n$ u_(1,2) $',
    "d2_tok_u10": '#set text(fill: rgb("#fbbf24"), size: 22pt, weight: "bold")\n$ u_(1,0) $',
    "d2_tok_m4u11": '#set text(fill: rgb("#f8fafc"), size: 22pt, weight: "bold")\n$ - 4 u_(1,1) $',
    "d2_row_ready": '#set text(fill: rgb("#f8fafc"), size: 22pt, weight: "bold")\n$ 4 u_(1,1)  -  1 u_(2,1)  -  1 u_(1,2)  +  0 u_(2,2)  =  50 $',

    # Demo 3: Derivación completa desde EDP de Laplace hasta el promedio de 4 vecinos
    "d3_pde_x":   '#set text(fill: rgb("#38bdf8"), size: 25pt, weight: "bold")\n$ frac(partial^2 T, partial x^2) $',
    "d3_pde_y":   '#set text(fill: rgb("#34d399"), size: 25pt, weight: "bold")\n$ frac(partial^2 T, partial y^2) $',
    "d3_num_x":   '#set text(fill: rgb("#38bdf8"), size: 21pt, weight: "bold")\n$ T_(i+1,j) - 2 T_(i,j) + T_(i-1,j) $',
    "d3_num_y":   '#set text(fill: rgb("#34d399"), size: 21pt, weight: "bold")\n$ T_(i,j+1) - 2 T_(i,j) + T_(i,j-1) $',
    "d3_den_dx2": '#set text(fill: rgb("#38bdf8"), size: 21pt, weight: "bold")\n$ Delta x^2 $',
    "d3_den_dy2": '#set text(fill: rgb("#34d399"), size: 21pt, weight: "bold")\n$ Delta y^2 $',
    "d3_den_h2":  '#set text(fill: rgb("#fbbf24"), size: 22pt, weight: "bold")\n$ h^2 $',

    "d3_t_ip1":   '#set text(fill: rgb("#38bdf8"), size: 21pt, weight: "bold")\n$ T_(i+1,j) $',
    "d3_t_im1":   '#set text(fill: rgb("#38bdf8"), size: 21pt, weight: "bold")\n$ + T_(i-1,j) $',
    "d3_t_jp1":   '#set text(fill: rgb("#34d399"), size: 21pt, weight: "bold")\n$ + T_(i,j+1) $',
    "d3_t_jm1":   '#set text(fill: rgb("#34d399"), size: 21pt, weight: "bold")\n$ + T_(i,j-1) $',
    "d3_t_m2x":   '#set text(fill: rgb("#f87171"), size: 21pt, weight: "bold")\n$ - 2 T_(i,j) $',
    "d3_t_m2y":   '#set text(fill: rgb("#f87171"), size: 21pt, weight: "bold")\n$ - 2 T_(i,j) $',
    "d3_t_m4":    '#set text(fill: rgb("#ef4444"), size: 23pt, weight: "bold")\n$ - 4 T_(i,j) $',

    "d3_sum4_nb": '#set text(fill: rgb("#f8fafc"), size: 23pt, weight: "bold")\n$ T_(i+1,j) + T_(i-1,j) + T_(i,j+1) + T_(i,j-1) $',
    "d3_tok_4":   '#set text(fill: rgb("#fbbf24"), size: 25pt, weight: "bold")\n$ 4 $',
    "d3_tok_tij_bare": '#set text(fill: rgb("#38bdf8"), size: 25pt, weight: "bold")\n$ T_(i,j) $',
}


def load_svg(name: str, height: float | None = None, max_width: float | None = None) -> SVGMobject:
    m = SVGMobject(str(SVG_DIR / f"{name}.svg"))
    if height is not None:
        m.scale_to_fit_height(height)
    if max_width is not None and m.width > max_width:
        m.scale_to_fit_width(max_width)
    return m


def make_token_chip(label_str: str, fill_hex: str, stroke_hex: str, text_hex: str = "#ffffff", width: float = 0.92, height: float = 0.50, font_size: int = 19) -> VGroup:
    bg = RoundedRectangle(corner_radius=0.10, width=width, height=height, fill_color=fill_hex, fill_opacity=0.96, stroke_color=stroke_hex, stroke_width=2.0)
    txt = Text(label_str, font="Segoe UI", font_size=font_size, weight=BOLD, color=text_hex).move_to(bg.get_center())
    if txt.width > width - 0.16:
        txt.scale_to_fit_width(width - 0.16)
    return VGroup(bg, txt)


# ==============================================================================
# ESCENA 1: DEMOSTRACIÓN DE LA DIFERENCIA CENTRAL Y 2DA DERIVADA (CON VIAJE DE ELEMENTOS)
# ==============================================================================
class Demo01CentralSegundaScene(Scene):
    def construct(self):
        timings = json.loads((WORK_ROOT / "d1_timings.json").read_text(encoding="utf-8"))
        setup_chalkboard(self)
        header = build_header(
            "Demostración 1: Diferencia Central y 2da Derivada",
            "Pizarrón Paso a Paso • Página 1",
            accent="#3b82f6",
        )
        self.add(header)
        hud = SubtitleHud(self)

        # ---------------- SEGMENTO 1: VIAJAN LOS NUMERADORES A LA FRACCIÓN ----------------
        t1 = timings[0]["duration"]
        hud.show(timings[0])

        card_fwd = RoundedRectangle(corner_radius=0.12, width=5.0, height=1.18, fill_color="#17130a", fill_opacity=0.94, stroke_color="#fbbf24", stroke_width=2.0)
        eq_fwd = load_svg("d1_card_fwd", height=0.80, max_width=4.5).move_to(card_fwd.get_center())
        grp_fwd = VGroup(card_fwd, eq_fwd).move_to(np.array([-3.25, 2.05, 0.0]))

        card_bwd = RoundedRectangle(corner_radius=0.12, width=5.0, height=1.18, fill_color="#082f49", fill_opacity=0.94, stroke_color="#38bdf8", stroke_width=2.0)
        eq_bwd = load_svg("d1_card_bwd", height=0.80, max_width=4.5).move_to(card_bwd.get_center())
        grp_bwd = VGroup(card_bwd, eq_bwd).move_to(np.array([3.25, 2.05, 0.0]))

        # Estructura de la gran fracción central en y = -0.35
        lhs_yp = load_svg("d1_lhs_yp", height=0.52).move_to(np.array([-3.75, -0.35, 0.0]))
        frac_bar = Line(np.array([-2.55, -0.35, 0.0]), np.array([3.55, -0.35, 0.0]), color="#94a3b8", stroke_width=3.2)
        den_2h = load_svg("d1_den_2h", height=0.42).move_to(np.array([0.50, -0.82, 0.0]))

        # Tokens individuales del numerador (en y = +0.16)
        tok_yip1 = load_svg("d1_tok_yip1", height=0.44).move_to(np.array([-1.75, 0.16, 0.0]))
        tok_myi = load_svg("d1_tok_myi", height=0.44).move_to(np.array([-0.35, 0.16, 0.0]))
        tok_pyi = load_svg("d1_tok_pyi", height=0.44).move_to(np.array([0.95, 0.16, 0.0]))
        tok_myim1 = load_svg("d1_tok_myim1", height=0.44).move_to(np.array([2.55, 0.16, 0.0]))

        # Posiciones iniciales dentro de las tarjetas superiores para que "viajen" hacia la fracción
        start_fwd_1 = tok_yip1.copy().scale(0.75).move_to(grp_fwd.get_center() + UP * 0.18 + RIGHT * 0.35)
        start_fwd_2 = tok_myi.copy().scale(0.75).move_to(grp_fwd.get_center() + UP * 0.18 + RIGHT * 1.15)
        start_bwd_1 = tok_pyi.copy().scale(0.75).move_to(grp_bwd.get_center() + UP * 0.18 + RIGHT * 0.35)
        start_bwd_2 = tok_myim1.copy().scale(0.75).move_to(grp_bwd.get_center() + UP * 0.18 + RIGHT * 1.15)

        self.play(FadeIn(grp_fwd, shift=DOWN * 0.15), FadeIn(grp_bwd, shift=DOWN * 0.15), run_time=1.2)
        self.play(FadeIn(lhs_yp), Create(frac_bar), FadeIn(den_2h), run_time=1.0)
        # Viaje en arco desde la tarjeta Forward hasta el numerador
        self.play(
            TransformFromCopy(start_fwd_1, tok_yip1, path_arc=-0.45),
            TransformFromCopy(start_fwd_2, tok_myi, path_arc=-0.45),
            run_time=1.6,
        )
        # Viaje en arco desde la tarjeta Backward hasta el numerador
        self.play(
            TransformFromCopy(start_bwd_1, tok_pyi, path_arc=0.45),
            TransformFromCopy(start_bwd_2, tok_myim1, path_arc=0.45),
            run_time=1.6,
        )
        self.wait(max(0.1, t1 - 5.4))

        # ---------------- SEGMENTO 2: CHOQUE Y CANCELACIÓN DE −yᵢ + yᵢ ----------------
        t2 = timings[1]["duration"]
        hud.show(timings[1])

        hl_left = SurroundingRectangle(tok_myi, color="#ef4444", buff=0.10, corner_radius=0.08)
        hl_right = SurroundingRectangle(tok_pyi, color="#ef4444", buff=0.10, corner_radius=0.08)
        self.play(Create(hl_left), Create(hl_right), run_time=0.8)

        # Los dos términos opuestos viajan uno contra el otro al centro y explotan en "0"
        collision_pt = np.array([0.30, 0.16, 0.0])
        zero_flash = Text("0", font="Segoe UI", font_size=28, weight=BOLD, color="#ef4444").move_to(collision_pt)
        self.play(
            tok_myi.animate.move_to(collision_pt),
            tok_pyi.animate.move_to(collision_pt),
            hl_left.animate.move_to(collision_pt),
            hl_right.animate.move_to(collision_pt),
            run_time=1.1,
        )
        self.play(
            FadeOut(tok_myi, scale=0.2),
            FadeOut(tok_pyi, scale=0.2),
            FadeOut(hl_left, scale=0.2),
            FadeOut(hl_right, scale=0.2),
            FadeIn(zero_flash, scale=1.5),
            run_time=0.7,
        )
        self.play(FadeOut(zero_flash, scale=0.3), run_time=0.5)

        # Ahora los extremos y_{i+1} y -y_{i-1} viajan suavemente hacia el centro para cerrar el hueco
        new_bar = Line(np.array([-1.55, -0.35, 0.0]), np.array([2.55, -0.35, 0.0]), color="#3b82f6", stroke_width=3.6)
        final_glow = RoundedRectangle(corner_radius=0.14, width=6.7, height=1.65, fill_color="#1e3a8a", fill_opacity=0.22, stroke_color="#60a5fa", stroke_width=2.6).move_to(np.array([-0.55, -0.32, 0.0]))

        self.play(
            tok_yip1.animate.move_to(np.array([-0.45, 0.16, 0.0])),
            tok_myim1.animate.move_to(np.array([1.25, 0.16, 0.0])),
            Transform(frac_bar, new_bar),
            FadeIn(final_glow),
            run_time=1.5,
        )
        self.wait(max(0.1, t2 - 4.6))

        # Limpiar escenario antes del Paso 2
        self.play(
            FadeOut(VGroup(grp_fwd, grp_bwd, lhs_yp, frac_bar, den_2h, tok_yip1, tok_myim1, final_glow)),
            run_time=0.7,
        )

        # ---------------- SEGMENTO 3: SERIE DE TAYLOR COLUMNA POR COLUMNA SIN TRASLAPES ----------------
        t3 = timings[2]["duration"]
        hud.show(timings[2])

        tay_title = Text(
            "Paso 2: Resta de Series de Taylor columna por columna (sin traslapes)",
            font="Segoe UI", font_size=20, weight=BOLD, color="#a7f3d0"
        ).move_to(np.array([0.0, 2.52, 0.0]))

        # Coordenadas X de las 5 columnas alineadas y coordenadas Y bien separadas (y=1.45, y=0.30, y=-1.15)
        col_x = [-4.55, -2.55, -0.75, 1.55, 4.15]
        y_row1 = 1.42
        y_row2 = 0.22
        y_res = -1.15

        r1_lhs = load_svg("t_r1_lhs", height=0.40).move_to(np.array([col_x[0], y_row1, 0.0]))
        r1_c1 = load_svg("t_r1_c1", height=0.40).move_to(np.array([col_x[1], y_row1, 0.0]))
        r1_c2 = load_svg("t_r1_c2", height=0.44).move_to(np.array([col_x[2], y_row1, 0.0]))
        r1_c3 = load_svg("t_r1_c3", height=0.68).move_to(np.array([col_x[3], y_row1, 0.0]))
        r1_c4 = load_svg("t_r1_c4", height=0.68).move_to(np.array([col_x[4], y_row1, 0.0]))

        r2_lhs = load_svg("t_r2_lhs", height=0.40).move_to(np.array([col_x[0], y_row2, 0.0]))
        r2_c1 = load_svg("t_r2_c1", height=0.40).move_to(np.array([col_x[1], y_row2, 0.0]))
        r2_c2 = load_svg("t_r2_c2", height=0.44).move_to(np.array([col_x[2], y_row2, 0.0]))
        r2_c3 = load_svg("t_r2_c3", height=0.68).move_to(np.array([col_x[3], y_row2, 0.0]))
        r2_c4 = load_svg("t_r2_c4", height=0.68).move_to(np.array([col_x[4], y_row2, 0.0]))

        sub_line = Line(np.array([-5.65, -0.42, 0.0]), np.array([5.55, -0.42, 0.0]), color="#64748b", stroke_width=2.4)

        res_lhs = load_svg("t_res_lhs", height=0.42).move_to(np.array([-3.85, y_res, 0.0]))
        res_c2 = load_svg("t_res_c2", height=0.46).move_to(np.array([col_x[2], y_res, 0.0]))
        res_c4 = load_svg("t_res_c4", height=0.68, max_width=5.4).move_to(np.array([2.85, y_res, 0.0]))

        self.play(FadeIn(tay_title), FadeIn(VGroup(r1_lhs, r1_c1, r1_c2, r1_c3, r1_c4), shift=DOWN * 0.12), run_time=1.4)
        self.play(FadeIn(VGroup(r2_lhs, r2_c1, r2_c2, r2_c3, r2_c4), shift=UP * 0.12), Create(sub_line), run_time=1.4)

        # Cancelación visual de la Columna 1 (y_i - y_i = 0) y Columna 3 (h²/2 y''_i - h²/2 y''_i = 0)
        strike_c1 = Line(r2_c1.get_corner(DL), r1_c1.get_corner(UR), color="#ef4444", stroke_width=3.2)
        strike_c3 = Line(r2_c3.get_corner(DL), r1_c3.get_corner(UR), color="#ef4444", stroke_width=3.2)
        self.play(
            Create(strike_c1),
            r1_c1.animate.set_opacity(0.28),
            r2_c1.animate.set_opacity(0.28),
            run_time=1.0,
        )
        # Columna 2 viaja hacia abajo para sumar 2h y'_i
        self.play(
            FadeIn(res_lhs),
            TransformFromCopy(VGroup(r1_c2, r2_c2), res_c2),
            run_time=1.3,
        )
        # Columna 3 se cancela y Columna 4 baja como término de error O(h²)
        self.play(
            Create(strike_c3),
            r1_c3.animate.set_opacity(0.28),
            r2_c3.animate.set_opacity(0.28),
            TransformFromCopy(VGroup(r1_c4, r2_c4), res_c4),
            run_time=1.5,
        )
        self.wait(max(0.1, t3 - 6.6))

        self.play(
            FadeOut(VGroup(tay_title, r1_lhs, r1_c1, r1_c2, r1_c3, r1_c4, r2_lhs, r2_c1, r2_c2, r2_c3, r2_c4, sub_line, strike_c1, strike_c3, res_lhs, res_c2, res_c4)),
            run_time=0.7,
        )

        # ---------------- SEGMENTO 4: SEGUNDA DERIVADA Y FUSIÓN DE −yᵢ − yᵢ → −2yᵢ ----------------
        t4 = timings[3]["duration"]
        hud.show(timings[3])

        d2_top = load_svg("d1_d2_top", height=0.75).move_to(np.array([0.0, 2.15, 0.0]))
        lhs_ypp = load_svg("d1_lhs_ypp", height=0.52).move_to(np.array([-3.85, 0.35, 0.0]))
        bar_d2 = Line(np.array([-2.55, 0.35, 0.0]), np.array([3.65, 0.35, 0.0]), color="#94a3b8", stroke_width=3.2)
        den_h2 = load_svg("d1_den_h2", height=0.44).move_to(np.array([0.55, -0.15, 0.0]))

        s_yip1 = load_svg("d1_tok_yip1", height=0.44).move_to(np.array([-1.65, 0.85, 0.0]))
        s_myi1 = load_svg("d1_tok_myi", height=0.44).move_to(np.array([-0.30, 0.85, 0.0]))
        s_myi2 = load_svg("d1_tok_myi", height=0.44).move_to(np.array([1.00, 0.85, 0.0]))
        s_pyim1 = load_svg("d1_tok_pyim1", height=0.44).move_to(np.array([2.55, 0.85, 0.0]))
        s_m2yi = load_svg("d1_tok_m2yi", height=0.48).move_to(np.array([0.35, 0.85, 0.0]))

        self.play(FadeIn(d2_top), FadeIn(lhs_ypp), Create(bar_d2), FadeIn(den_h2), run_time=1.1)
        self.play(FadeIn(VGroup(s_yip1, s_myi1, s_myi2, s_pyim1), shift=DOWN * 0.15), run_time=1.1)

        # Los dos términos -y_i viajan hacia el centro y se fusionan en -2y_i
        self.play(
            ReplacementTransform(VGroup(s_myi1, s_myi2), s_m2yi),
            s_yip1.animate.move_to(np.array([-1.15, 0.85, 0.0])),
            s_pyim1.animate.move_to(np.array([1.95, 0.85, 0.0])),
            run_time=1.4,
        )

        # Abajo dibujamos la molécula 1D [ +1 , -2 , +1 ] y hacemos viajar los pesos desde la ecuación
        st_line = Line(np.array([-3.2, -1.85, 0.0]), np.array([3.2, -1.85, 0.0]), color="#38bdf8", stroke_width=4.0)
        chip_p1_l = make_token_chip("+1", "#082f49", "#38bdf8", width=1.1, height=0.56).move_to(np.array([-2.8, -1.85, 0.0]))
        chip_m2_c = make_token_chip("−2", "#064e3b", "#34d399", width=1.2, height=0.62).move_to(np.array([0.0, -1.85, 0.0]))
        chip_p1_r = make_token_chip("+1", "#082f49", "#38bdf8", width=1.1, height=0.56).move_to(np.array([2.8, -1.85, 0.0]))

        lbl_l = Text("yᵢ₋₁", font="Segoe UI", font_size=16, weight=BOLD, color="#93c5fd").next_to(chip_p1_l, DOWN, buff=0.12)
        lbl_c = Text("yᵢ (Centro)", font="Segoe UI", font_size=16, weight=BOLD, color="#6ee7b7").next_to(chip_m2_c, DOWN, buff=0.12)
        lbl_r = Text("yᵢ₊₁", font="Segoe UI", font_size=16, weight=BOLD, color="#93c5fd").next_to(chip_p1_r, DOWN, buff=0.12)

        self.play(
            Create(st_line),
            TransformFromCopy(s_pyim1, chip_p1_l, path_arc=0.35),
            TransformFromCopy(s_m2yi, chip_m2_c),
            TransformFromCopy(s_yip1, chip_p1_r, path_arc=-0.35),
            FadeIn(VGroup(lbl_l, lbl_c, lbl_r)),
            run_time=1.8,
        )
        self.wait(max(0.1, t4 - 5.4))


# ==============================================================================
# ESCENA 2: SUSTITUCIÓN DIRICHLET Y ELEMENTOS QUE VIAJAN DE LA MALLA A LA MATRIZ
# ==============================================================================
class Demo02SustitucionDirichletScene(Scene):
    def construct(self):
        timings = json.loads((WORK_ROOT / "d2_timings.json").read_text(encoding="utf-8"))
        setup_chalkboard(self)
        header = build_header(
            "Demostración 2: Sustitución Dirichlet y Matriz",
            "Pizarrón Paso a Paso • Página 2",
            accent="#f59e0b",
        )
        self.add(header)
        hud = SubtitleHud(self)

        # Panel izquierdo: Malla 4x4 con el nodo (1,1) iluminado
        mesh_card = RoundedRectangle(corner_radius=0.14, width=4.35, height=4.75, fill_color="#0f172a", fill_opacity=0.95, stroke_color="#334155", stroke_width=1.8).move_to(np.array([-4.25, 0.05, 0.0]))
        mesh_title = Text("Malla 4×4 • Nodo (1,1)", font="Segoe UI", font_size=16, weight=BOLD, color="#e2e8f0").move_to(mesh_card.get_top() + DOWN * 0.34)

        gx0, gy0 = -5.65, -1.60
        step = 0.94
        grid_lines = VGroup()
        for k in range(4):
            grid_lines.add(Line(np.array([gx0 + k * step, gy0, 0]), np.array([gx0 + k * step, gy0 + 3 * step, 0]), color="#334155", stroke_width=1.5))
            grid_lines.add(Line(np.array([gx0, gy0 + k * step, 0]), np.array([gx0 + 3 * step, gy0 + k * step, 0]), color="#334155", stroke_width=1.5))

        c11 = np.array([gx0 + 1 * step, gy0 + 1 * step, 0])
        arms = VGroup(
            Line(c11, np.array([gx0 + 2 * step, gy0 + 1 * step, 0]), color="#3b82f6", stroke_width=4.8),
            Line(c11, np.array([gx0 + 0 * step, gy0 + 1 * step, 0]), color="#f59e0b", stroke_width=4.8),
            Line(c11, np.array([gx0 + 1 * step, gy0 + 2 * step, 0]), color="#3b82f6", stroke_width=4.8),
            Line(c11, np.array([gx0 + 1 * step, gy0 + 0 * step, 0]), color="#f59e0b", stroke_width=4.8),
        )

        nodes_grp = VGroup()
        node_map = {}
        border_vals = {(1, 3): "100", (2, 3): "100", (1, 0): "0", (2, 0): "0", (0, 1): "50", (0, 2): "50", (3, 1): "20", (3, 2): "20"}
        for j in range(4):
            for i in range(4):
                pt = np.array([gx0 + i * step, gy0 + j * step, 0])
                is_corner = (i in (0, 3)) and (j in (0, 3))
                is_border = (i in (0, 3)) or (j in (0, 3))
                if is_corner:
                    c = Circle(radius=0.16, fill_color="#1e293b", fill_opacity=1, stroke_color="#475569", stroke_width=1.4).move_to(pt)
                    nodes_grp.add(c)
                elif is_border:
                    is_nb = (i == 0 and j == 1) or (i == 1 and j == 0)
                    c = Circle(radius=0.24, fill_color="#f59e0b" if is_nb else "#451a03", fill_opacity=1, stroke_color="#fbbf24", stroke_width=2.0).move_to(pt)
                    t = Text(border_vals.get((i, j), "0"), font="Segoe UI", font_size=12, weight=BOLD, color="#ffffff" if is_nb else "#fde68a").move_to(pt)
                    g = VGroup(c, t)
                    nodes_grp.add(g)
                    node_map[(i, j)] = g
                else:
                    is_act = (i == 1 and j == 1)
                    c = Circle(radius=0.26 if is_act else 0.22, fill_color="#2563eb" if is_act else "#0f172a", fill_opacity=1, stroke_color="#60a5fa", stroke_width=2.2).move_to(pt)
                    t = Text(f"{i},{j}", font="Segoe UI", font_size=11.5, weight=BOLD, color="#ffffff").move_to(pt)
                    g = VGroup(c, t)
                    nodes_grp.add(g)
                    node_map[(i, j)] = g

        mesh_all = VGroup(mesh_card, mesh_title, grid_lines, arms, nodes_grp)

        # ---------------- SEGMENTO 1: FICHAS DE LA ECUACIÓN EN LA ZONA SUPERIOR DERECHA ----------------
        t1 = timings[0]["duration"]
        hud.show(timings[0])

        eq_stage_card = RoundedRectangle(corner_radius=0.14, width=8.25, height=1.55, fill_color="#0f172a", fill_opacity=0.95, stroke_color="#38bdf8", stroke_width=2.0).move_to(np.array([2.15, 1.65, 0.0]))
        eq_stage_lbl = Text("Ecuación activa en el Nodo (1, 1):", font="Segoe UI", font_size=15, weight=BOLD, color="#93c5fd").move_to(eq_stage_card.get_top() + DOWN * 0.28 + LEFT * 2.45)

        y_eq = 1.48
        chip_u21 = make_token_chip("u₂,₁", "#1e3a8a", "#60a5fa", width=0.92, height=0.48, font_size=16).move_to(np.array([-1.25, y_eq, 0.0]))
        plus1 = Text("+", font="Segoe UI", font_size=19, weight=BOLD, color="#cbd5e1").move_to(np.array([-0.62, y_eq, 0.0]))
        chip_u01 = make_token_chip("u₀,₁", "#451a03", "#fbbf24", width=0.92, height=0.48, font_size=16).move_to(np.array([0.00, y_eq, 0.0]))
        plus2 = Text("+", font="Segoe UI", font_size=19, weight=BOLD, color="#cbd5e1").move_to(np.array([0.62, y_eq, 0.0]))
        chip_u12 = make_token_chip("u₁,₂", "#1e3a8a", "#60a5fa", width=0.92, height=0.48, font_size=16).move_to(np.array([1.25, y_eq, 0.0]))
        plus3 = Text("+", font="Segoe UI", font_size=19, weight=BOLD, color="#cbd5e1").move_to(np.array([1.88, y_eq, 0.0]))
        chip_u10 = make_token_chip("u₁,₀", "#451a03", "#fbbf24", width=0.92, height=0.48, font_size=16).move_to(np.array([2.50, y_eq, 0.0]))
        chip_m4u11 = make_token_chip("−4·u₁,₁", "#0f172a", "#38bdf8", width=1.22, height=0.48, font_size=16).move_to(np.array([3.82, y_eq, 0.0]))
        eq_sign = Text("=", font="Segoe UI", font_size=21, weight=BOLD, color="#f8fafc").move_to(np.array([4.72, y_eq, 0.0]))
        chip_rhs = make_token_chip("0", "#0f172a", "#64748b", width=0.78, height=0.48, font_size=16).move_to(np.array([5.35, y_eq, 0.0]))

        self.play(FadeIn(mesh_all), FadeIn(eq_stage_card), FadeIn(eq_stage_lbl), run_time=1.2)
        self.play(
            LaggedStart(
                TransformFromCopy(node_map[(2, 1)], chip_u21, path_arc=-0.25),
                FadeIn(plus1),
                TransformFromCopy(node_map[(0, 1)], chip_u01, path_arc=-0.25),
                FadeIn(plus2),
                TransformFromCopy(node_map[(1, 2)], chip_u12, path_arc=-0.25),
                FadeIn(plus3),
                TransformFromCopy(node_map[(1, 0)], chip_u10, path_arc=-0.25),
                TransformFromCopy(node_map[(1, 1)], chip_m4u11, path_arc=-0.25),
                FadeIn(eq_sign),
                FadeIn(chip_rhs),
                lag_ratio=0.12,
            ),
            run_time=2.6,
        )
        self.wait(max(0.1, t1 - 3.8))

        # ---------------- SEGMENTO 2: EL 50 Y EL 0 VIAJAN DESDE LA MALLA HASTA LA ECUACIÓN ----------------
        t2 = timings[1]["duration"]
        hud.show(timings[1])

        chip_50 = make_token_chip("50", "#b45309", "#fde68a", width=0.92, height=0.48, font_size=17).move_to(chip_u01.get_center())
        chip_0 = make_token_chip("0", "#b45309", "#fde68a", width=0.92, height=0.48, font_size=17).move_to(chip_u10.get_center())

        fly_50 = chip_50.copy().scale(0.8).move_to(node_map[(0, 1)].get_center())
        fly_0 = chip_0.copy().scale(0.8).move_to(node_map[(1, 0)].get_center())

        self.play(Indicate(node_map[(0, 1)], color="#fde68a", scale_factor=1.25), run_time=0.7)
        self.play(
            FadeOut(chip_u01, scale=0.4),
            ReplacementTransform(fly_50, chip_50, path_arc=-0.42),
            run_time=1.4,
        )
        self.play(Indicate(node_map[(1, 0)], color="#fde68a", scale_factor=1.25), run_time=0.7)
        self.play(
            FadeOut(chip_u10, scale=0.4),
            ReplacementTransform(fly_0, chip_0, path_arc=-0.42),
            run_time=1.4,
        )
        self.wait(max(0.1, t2 - 4.2))

        # ---------------- SEGMENTO 3: EL 50 SALTA EL '=' Y LOS COEFICIENTES VIAJAN A LA MATRIZ 4x4 ----------------
        t3 = timings[2]["duration"]
        hud.show(timings[2])

        # El 50 vuela en arco por encima del signo '=' hacia el lado derecho y se ordena la ecuación lineal
        chip_rhs_50 = make_token_chip("50", "#b45309", "#fde68a", width=0.88, height=0.48, font_size=17).move_to(chip_rhs.get_center())
        c_p4 = make_token_chip("+4", "#1d4ed8", "#93c5fd", width=0.68, height=0.46, font_size=16).move_to(np.array([-1.35, y_eq, 0.0]))
        t_u11 = Text("u₁,₁", font="Segoe UI", font_size=16, weight=BOLD, color="#e2e8f0").move_to(np.array([-0.68, y_eq, 0.0]))
        c_m1a = make_token_chip("−1", "#0f172a", "#60a5fa", width=0.68, height=0.46, font_size=16).move_to(np.array([0.18, y_eq, 0.0]))
        t_u21 = Text("u₂,₁", font="Segoe UI", font_size=16, weight=BOLD, color="#e2e8f0").move_to(np.array([0.85, y_eq, 0.0]))
        c_m1b = make_token_chip("−1", "#0f172a", "#60a5fa", width=0.68, height=0.46, font_size=16).move_to(np.array([1.72, y_eq, 0.0]))
        t_u12 = Text("u₁,₂", font="Segoe UI", font_size=16, weight=BOLD, color="#e2e8f0").move_to(np.array([2.38, y_eq, 0.0]))
        c_z22 = make_token_chip("0", "#0f172a", "#475569", width=0.62, height=0.46, font_size=16).move_to(np.array([3.22, y_eq, 0.0]))
        t_u22 = Text("u₂,₂", font="Segoe UI", font_size=16, weight=BOLD, color="#94a3b8").move_to(np.array([3.86, y_eq, 0.0]))

        self.play(
            FadeOut(VGroup(plus1, plus2, plus3, chip_0, chip_rhs)),
            ReplacementTransform(chip_50, chip_rhs_50, path_arc=-0.65),
            ReplacementTransform(chip_m4u11, VGroup(c_p4, t_u11)),
            ReplacementTransform(chip_u21, VGroup(c_m1a, t_u21)),
            ReplacementTransform(chip_u12, VGroup(c_m1b, t_u12)),
            FadeIn(VGroup(c_z22, t_u22)),
            run_time=1.8,
        )

        # Panel inferior derecho: Matriz 4x4 [A]{u} = {b} y solución {u}
        mat_card = RoundedRectangle(corner_radius=0.14, width=8.25, height=2.95, fill_color="#0b1322", fill_opacity=0.96, stroke_color="#10b981", stroke_width=2.0).move_to(np.array([2.15, -0.92, 0.0]))
        mat_hdr = Text("Sistema Global [A]{u} = {b}   →   Solución {u}", font="Segoe UI", font_size=15, weight=BOLD, color="#6ee7b7").move_to(mat_card.get_top() + DOWN * 0.28)

        # Coordenadas de las 4 filas y columnas dentro de mat_card
        col_xs = [-1.05, -0.15, 0.75, 1.65]  # columnas de [A]
        x_b = 2.95
        x_sol = 4.65
        row_ys = [-0.18, -0.68, -1.18, -1.68]

        row1_hl = RoundedRectangle(corner_radius=0.07, width=7.75, height=0.44, fill_color="#1e3a8a", fill_opacity=0.38, stroke_color="#60a5fa", stroke_width=1.5).move_to(np.array([2.15, row_ys[0], 0.0]))

        self.play(FadeIn(mat_card), FadeIn(mat_hdr), FadeIn(row1_hl), run_time=0.8)

        # Viajan los 4 coeficientes +4, -1, -1, 0 y el 50 desde la ecuación hasta la Fila 1 de la matriz
        m_r1_c1 = Text("4", font="Segoe UI", font_size=17, weight=BOLD, color="#60a5fa").move_to(np.array([col_xs[0], row_ys[0], 0.0]))
        m_r1_c2 = Text("−1", font="Segoe UI", font_size=17, weight=BOLD, color="#fbbf24").move_to(np.array([col_xs[1], row_ys[0], 0.0]))
        m_r1_c3 = Text("−1", font="Segoe UI", font_size=17, weight=BOLD, color="#fbbf24").move_to(np.array([col_xs[2], row_ys[0], 0.0]))
        m_r1_c4 = Text("0", font="Segoe UI", font_size=17, color="#94a3b8").move_to(np.array([col_xs[3], row_ys[0], 0.0]))
        m_r1_b = Text("=  50", font="Segoe UI", font_size=17, weight=BOLD, color="#fde68a").move_to(np.array([x_b, row_ys[0], 0.0]))

        self.play(
            TransformFromCopy(c_p4, m_r1_c1, path_arc=-0.25),
            TransformFromCopy(c_m1a, m_r1_c2, path_arc=-0.25),
            TransformFromCopy(c_m1b, m_r1_c3, path_arc=-0.25),
            TransformFromCopy(c_z22, m_r1_c4, path_arc=-0.25),
            TransformFromCopy(chip_rhs_50, m_r1_b, path_arc=-0.25),
            run_time=1.6,
        )

        # Rellenar filas 2, 3, 4 y mostrar la columna de solución u resuelta
        other_rows_data = [
            (["−1", "4", "0", "−1"], "=  20", "u₂,₁ = 35.0", 1),
            (["−1", "0", "4", "−1"], "= 150", "u₁,₂ = 67.5", 2),
            (["0", "−1", "−1", "4"], "= 120", "u₂,₂ = 60.0", 3),
        ]
        rest_mobs = VGroup()
        sol_r1 = Text("→  u₁,₁ = 42.5", font="Segoe UI", font_size=16, weight=BOLD, color="#34d399").move_to(np.array([x_sol, row_ys[0], 0.0]))
        rest_mobs.add(sol_r1)

        for vals, b_str, s_str, r_idx in other_rows_data:
            ry = row_ys[r_idx]
            for c_idx, v in enumerate(vals):
                col = "#60a5fa" if c_idx == r_idx else ("#fbbf24" if v != "0" else "#64748b")
                rest_mobs.add(Text(v, font="Segoe UI", font_size=16, weight=BOLD, color=col).move_to(np.array([col_xs[c_idx], ry, 0.0])))
            rest_mobs.add(Text(b_str, font="Segoe UI", font_size=16, weight=BOLD, color="#fde68a").move_to(np.array([x_b, ry, 0.0])))
            rest_mobs.add(Text("→  " + s_str, font="Segoe UI", font_size=16, weight=BOLD, color="#34d399").move_to(np.array([x_sol, ry, 0.0])))

        self.play(FadeIn(rest_mobs, shift=UP * 0.10), run_time=1.4)
        self.wait(max(0.1, t3 - 5.6))


# ==============================================================================
# ESCENA 3: DE LAS DERIVADAS PARCIALES DE LAPLACE AL PROMEDIO DE LOS 4 VECINOS
# ==============================================================================
class Demo03SustitucionCalorScene(Scene):
    def construct(self):
        timings = json.loads((WORK_ROOT / "d3_timings.json").read_text(encoding="utf-8"))
        setup_chalkboard(self)
        header = build_header(
            "Demostración 3: De Derivadas Parciales al Promedio de 4 Vecinos",
            "Pizarrón Paso a Paso • Página 3",
            accent="#10b981",
        )
        self.add(header)
        hud = SubtitleHud(self)

        # ---------------- SEGMENTO 1: SUSTITUCIÓN DE LAS 2 DERIVADAS PARCIALES POR DIFERENCIAS FINITAS ----------------
        t1 = timings[0]["duration"]
        hud.show(timings[0])

        s1_title = Text(
            "Paso 1: Sustituir cada derivada parcial por su Diferencia Finita Central",
            font="Segoe UI", font_size=20, weight=BOLD, color="#6ee7b7"
        ).move_to(np.array([0.0, 2.52, 0.0]))

        # Ecuación diferencial de Laplace en la parte alta (y = 1.48)
        pde_x = load_svg("d3_pde_x", height=0.92).move_to(np.array([-2.65, 1.45, 0.0]))
        pde_plus = Text("+", font="Segoe UI", font_size=26, weight=BOLD, color="#f8fafc").move_to(np.array([0.0, 1.45, 0.0]))
        pde_y = load_svg("d3_pde_y", height=0.92).move_to(np.array([2.65, 1.45, 0.0]))
        pde_eq0 = Text("=  0", font="Segoe UI", font_size=26, weight=BOLD, color="#f8fafc").move_to(np.array([4.65, 1.45, 0.0]))

        box_px = SurroundingRectangle(pde_x, color="#38bdf8", buff=0.14, corner_radius=0.10)
        box_py = SurroundingRectangle(pde_y, color="#34d399", buff=0.14, corner_radius=0.10)

        self.play(FadeIn(s1_title), FadeIn(pde_x), FadeIn(pde_plus), FadeIn(pde_y), FadeIn(pde_eq0), run_time=1.3)
        self.play(Create(box_px), Create(box_py), run_time=0.8)

        # Fracción izquierda (Eje X: varía i, fijo j) en y = -0.85
        tag_x = Text("Eje X: varía i, fijo j", font="Segoe UI", font_size=15, weight=BOLD, color="#38bdf8").move_to(np.array([-3.10, 0.12, 0.0]))
        num_x = load_svg("d3_num_x", height=0.45, max_width=4.6).move_to(np.array([-3.10, -0.48, 0.0]))
        bar_x = Line(np.array([-5.45, -0.88, 0.0]), np.array([-0.75, -0.88, 0.0]), color="#38bdf8", stroke_width=3.0)
        den_dx2 = load_svg("d3_den_dx2", height=0.42).move_to(np.array([-3.10, -1.32, 0.0]))
        frac_x_grp = VGroup(num_x, bar_x, den_dx2)

        # Fracción derecha (Eje Y: fijo i, varía j) en y = -0.85
        mid_plus = Text("+", font="Segoe UI", font_size=25, weight=BOLD, color="#f8fafc").move_to(np.array([-0.15, -0.88, 0.0]))
        tag_y = Text("Eje Y: fijo i, varía j", font="Segoe UI", font_size=15, weight=BOLD, color="#34d399").move_to(np.array([2.50, 0.12, 0.0]))
        num_y = load_svg("d3_num_y", height=0.45, max_width=4.6).move_to(np.array([2.50, -0.48, 0.0]))
        bar_y = Line(np.array([0.15, -0.88, 0.0]), np.array([4.85, -0.88, 0.0]), color="#34d399", stroke_width=3.0)
        den_dy2 = load_svg("d3_den_dy2", height=0.42).move_to(np.array([2.50, -1.32, 0.0]))
        frac_y_grp = VGroup(num_y, bar_y, den_dy2)
        rhs_eq0 = Text("=  0", font="Segoe UI", font_size=25, weight=BOLD, color="#f8fafc").move_to(np.array([5.65, -0.88, 0.0]))

        # Viaje desde ∂²T/∂x² hacia la primera fracción discreta
        self.play(
            FadeIn(tag_x),
            TransformFromCopy(pde_x, frac_x_grp, path_arc=-0.28),
            run_time=1.8,
        )
        # Viaje desde ∂²T/∂y² hacia la segunda fracción discreta
        self.play(
            FadeIn(mid_plus),
            FadeIn(tag_y),
            TransformFromCopy(pde_y, frac_y_grp, path_arc=0.28),
            FadeIn(rhs_eq0),
            run_time=1.8,
        )
        self.wait(max(0.1, t1 - 5.7))

        # ---------------- SEGMENTO 2: MALLA CUADRADA (Δx=Δy=h), SE VAN LOS h² Y FUSIÓN EN −4Tᵢ,ⱼ ----------------
        t2 = timings[1]["duration"]
        hud.show(timings[1])

        s2_title = Text(
            "Paso 2: En malla cuadrada (Δx = Δy = h) eliminamos h² y fusionamos −4Tᵢ,ⱼ",
            font="Segoe UI", font_size=20, weight=BOLD, color="#fde68a"
        ).move_to(np.array([0.0, 2.52, 0.0]))

        # Subimos las dos fracciones a y = 1.15 limpiando la EDP superior
        self.play(
            FadeOut(VGroup(s1_title, pde_x, pde_plus, pde_y, pde_eq0, box_px, box_py, tag_x, tag_y)),
            FadeIn(s2_title),
            frac_x_grp.animate.shift(UP * 2.00),
            mid_plus.animate.shift(UP * 2.00),
            frac_y_grp.animate.shift(UP * 2.00),
            rhs_eq0.animate.shift(UP * 2.00),
            run_time=1.2,
        )

        # Δx² y Δy² se transforman en h²
        den_h2_l = load_svg("d3_den_h2", height=0.42).move_to(den_dx2.get_center())
        den_h2_r = load_svg("d3_den_h2", height=0.42).move_to(den_dy2.get_center())
        self.play(
            ReplacementTransform(den_dx2, den_h2_l),
            ReplacementTransform(den_dy2, den_h2_r),
            run_time=1.1,
        )

        # Multiplicamos por h²: ambos denominadores h² viajan en arco hacia el "= 0" de la derecha y desaparecen
        target_zero_pt = np.array([5.85, 1.52, 0.0])
        self.play(
            den_h2_l.animate(path_arc=-0.35).move_to(target_zero_pt).scale(0.2),
            den_h2_r.animate(path_arc=-0.25).move_to(target_zero_pt).scale(0.2),
            FadeOut(bar_x),
            FadeOut(bar_y),
            mid_plus.animate.move_to(np.array([-0.15, 1.52, 0.0])),
            rhs_eq0.animate.move_to(np.array([5.65, 1.52, 0.0])),
            run_time=1.5,
        )
        self.remove(den_h2_l, den_h2_r)

        # Ahora separamos los 6 términos en y = -0.10 para ver cómo los dos -2T_{i,j} viajan y se fusionan en -4T_{i,j}
        y_sep = -0.10
        tk_ip1 = load_svg("d3_t_ip1", height=0.42, max_width=1.55).move_to(np.array([-5.20, y_sep, 0.0]))
        tk_m2x = load_svg("d3_t_m2x", height=0.42, max_width=1.55).move_to(np.array([-3.40, y_sep, 0.0]))
        tk_im1 = load_svg("d3_t_im1", height=0.42, max_width=1.65).move_to(np.array([-1.50, y_sep, 0.0]))
        tk_jp1 = load_svg("d3_t_jp1", height=0.42, max_width=1.65).move_to(np.array([0.45, y_sep, 0.0]))
        tk_m2y = load_svg("d3_t_m2y", height=0.42, max_width=1.55).move_to(np.array([2.35, y_sep, 0.0]))
        tk_jm1 = load_svg("d3_t_jm1", height=0.42, max_width=1.65).move_to(np.array([4.20, y_sep, 0.0]))
        tk_eq0 = Text("=  0", font="Segoe UI", font_size=23, weight=BOLD, color="#f8fafc").move_to(np.array([5.80, y_sep, 0.0]))

        self.play(
            TransformFromCopy(num_x, VGroup(tk_ip1, tk_m2x, tk_im1)),
            TransformFromCopy(num_y, VGroup(tk_jp1, tk_m2y, tk_jm1)),
            FadeIn(tk_eq0),
            run_time=1.4,
        )

        # Resaltamos los dos -2T_{i,j} en rojo y los hacemos viajar juntos para fusionarse en -4T_{i,j} en y = -1.55
        hl_m2x = SurroundingRectangle(tk_m2x, color="#ef4444", buff=0.08, corner_radius=0.08)
        hl_m2y = SurroundingRectangle(tk_m2y, color="#ef4444", buff=0.08, corner_radius=0.08)
        self.play(Create(hl_m2x), Create(hl_m2y), run_time=0.6)

        y_comb = -1.55
        sum4_nb = load_svg("d3_sum4_nb", height=0.46, max_width=7.4).move_to(np.array([-1.65, y_comb, 0.0]))
        tok_m4 = load_svg("d3_t_m4", height=0.48).move_to(np.array([3.05, y_comb, 0.0]))
        comb_eq0 = Text("=  0", font="Segoe UI", font_size=24, weight=BOLD, color="#f8fafc").move_to(np.array([4.85, y_comb, 0.0]))

        self.play(
            ReplacementTransform(VGroup(tk_ip1, tk_im1, tk_jp1, tk_jm1), sum4_nb),
            ReplacementTransform(VGroup(tk_m2x, tk_m2y, hl_m2x, hl_m2y), tok_m4),
            ReplacementTransform(tk_eq0, comb_eq0),
            run_time=1.6,
        )
        self.wait(max(0.1, t2 - 7.4))

        # ---------------- SEGMENTO 3: DESPEJE FINAL HASTA EL PROMEDIO DE LOS 4 VECINOS ----------------
        t3 = timings[2]["duration"]
        hud.show(timings[2])

        s3_title = Text(
            "Paso 3: Despejamos Tᵢ,ⱼ → ¡Cada nodo es el promedio de sus 4 vecinos!",
            font="Segoe UI", font_size=20, weight=BOLD, color="#34d399"
        ).move_to(np.array([0.0, 2.52, 0.0]))

        # Subimos la ecuación de 5 puntos a y = 1.45 y limpiamos lo anterior
        self.play(
            FadeOut(VGroup(s2_title, num_x, mid_plus, num_y, rhs_eq0)),
            FadeIn(s3_title),
            sum4_nb.animate.move_to(np.array([-1.65, 1.45, 0.0])),
            tok_m4.animate.move_to(np.array([3.05, 1.45, 0.0])),
            comb_eq0.animate.move_to(np.array([4.85, 1.45, 0.0])),
            run_time=1.1,
        )

        # -4 T_{i,j} salta por encima del signo '=' y se separa en [ 4 ] · [ T_{i,j} ] positivo
        eq_mid = Text("=", font="Segoe UI", font_size=26, weight=BOLD, color="#f8fafc").move_to(np.array([2.55, 1.45, 0.0]))
        tok_4 = load_svg("d3_tok_4", height=0.46).move_to(np.array([3.55, 1.45, 0.0]))
        tok_tij = load_svg("d3_tok_tij_bare", height=0.50).move_to(np.array([4.55, 1.45, 0.0]))

        self.play(
            ReplacementTransform(comb_eq0, eq_mid),
            ReplacementTransform(tok_m4, VGroup(tok_4, tok_tij), path_arc=-0.60),
            run_time=1.6,
        )

        # Ahora construimos la gran fórmula final en y = -0.65 (con borde brillante y relleno translúcido 0.14 debajo)
        final_frame = RoundedRectangle(
            corner_radius=0.16, width=10.8, height=2.25,
            fill_color="#064e3b", fill_opacity=0.16, stroke_color="#10b981", stroke_width=2.8
        ).move_to(np.array([0.0, -0.75, 0.0]))
        self.play(FadeIn(final_frame), run_time=0.5)

        final_lhs = load_svg("d3_tok_tij_bare", height=0.58).move_to(np.array([-4.05, -0.55, 0.0]))
        final_eq = Text("=", font="Segoe UI", font_size=27, weight=BOLD, color="#f8fafc").move_to(np.array([-3.05, -0.55, 0.0]))
        final_bar = Line(np.array([-2.35, -0.55, 0.0]), np.array([4.65, -0.55, 0.0]), color="#34d399", stroke_width=3.6)
        final_num = load_svg("d3_sum4_nb", height=0.48, max_width=6.8).move_to(np.array([1.15, -0.05, 0.0]))
        final_den = load_svg("d3_tok_4", height=0.48).move_to(np.array([1.15, -1.08, 0.0]))

        lbl_neighbors = Text(
            "( Vecino Derecha  +  Vecino Izquierda  +  Vecino Arriba  +  Vecino Abajo )  ÷  4",
            font="Segoe UI", font_size=15.5, weight=BOLD, color="#a7f3d0"
        ).move_to(np.array([0.35, -1.62, 0.0]))

        # El 4 que multiplica viaja en arco hacia abajo para colocarse en el denominador
        self.play(
            TransformFromCopy(tok_tij, final_lhs, path_arc=0.25),
            FadeIn(final_eq),
            Create(final_bar),
            TransformFromCopy(sum4_nb, final_num),
            TransformFromCopy(tok_4, final_den, path_arc=-0.55),
            run_time=1.9,
        )
        self.play(FadeIn(lbl_neighbors, shift=UP * 0.10), run_time=0.9)
        self.wait(max(0.1, t3 - 6.0))


# ==============================================================================
# ORQUESTADOR PRINCIPAL (--tts-only y --render-only)
# ==============================================================================
DEMOS_SPEC = [
    {
        "slug": "d1",
        "segments": DEMO1_SEGMENTS,
        "scene_class": "Demo01CentralSegundaScene",
        "output_mp4": BASE_DIR / "demo_01_central_y_segunda_derivada.mp4",
    },
    {
        "slug": "d2",
        "segments": DEMO2_SEGMENTS,
        "scene_class": "Demo02SustitucionDirichletScene",
        "output_mp4": BASE_DIR / "demo_02_sustitucion_molecula_dirichlet.mp4",
    },
    {
        "slug": "d3",
        "segments": DEMO3_SEGMENTS,
        "scene_class": "Demo03SustitucionCalorScene",
        "output_mp4": BASE_DIR / "demo_03_sustitucion_gauss_seidel_calor.mp4",
    },
]


async def run_all_tts(force: bool = False, only_slug: str | None = None):
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(1)
    for spec in DEMOS_SPEC:
        if only_slug and spec["slug"] != only_slug:
            continue
        validate_subscript_pronunciation(spec["slug"], spec["segments"])
        audio_dir = WORK_ROOT / f"audio_{spec['slug']}"
        print(f"\n=== Descargando TTS para {spec['slug']} ===", flush=True)
        await download_segments_tts(spec["segments"], audio_dir, sem=sem, force=force)


def run_all_renders(preview: bool = False, only_slug: str | None = None):
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    print("\n=== Compilando fórmulas Typst -> SVG ===", flush=True)
    compile_typst_formulas(FORMULAS_ALL, SVG_DIR)
    ffmpeg_exe = get_ffmpeg_exe()

    for spec in DEMOS_SPEC:
        slug = spec["slug"]
        if only_slug and slug != only_slug:
            continue
        audio_dir = WORK_ROOT / f"audio_{slug}"
        timings_json = WORK_ROOT / f"{slug}_timings.json"
        print(f"\n=== Ensamblando audio maestro y tiempos para {slug} ===", flush=True)
        master_wav = build_master_audio_and_timings(spec["segments"], audio_dir, timings_json, ffmpeg_exe)

        print(f"\n=== Renderizando Manim 1080p60 + Audio para {spec['output_mp4'].name} ===", flush=True)
        render_manim_and_mux(
            scene_py=Path(__file__).resolve(),
            scene_class=spec["scene_class"],
            master_wav=master_wav,
            output_mp4=spec["output_mp4"],
            work_dir=WORK_ROOT / f"work_{slug}",
            ffmpeg_exe=ffmpeg_exe,
            preview=preview,
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tts-only", action="store_true")
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--force-tts", action="store_true")
    parser.add_argument("--demo", type=str, default=None, help="d1, d2 o d3")
    args = parser.parse_args()

    if args.tts_only:
        asyncio.run(run_all_tts(force=args.force_tts, only_slug=args.demo))
    elif args.render_only:
        run_all_renders(preview=args.preview, only_slug=args.demo)
    else:
        asyncio.run(run_all_tts(force=args.force_tts, only_slug=args.demo))
        run_all_renders(preview=args.preview, only_slug=args.demo)


if __name__ == "__main__":
    main()
