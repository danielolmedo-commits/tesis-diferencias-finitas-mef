# -*- coding: utf-8 -*-
"""
Cápsula 3 de 4: Difusión de Calor 2D — Ecuación de Laplace y Relajación Iterativa
Salida: 03_difusion_calor_laplace_2d.mp4
"""

import json
import math
import sys
from pathlib import Path
import numpy as np
from manim import *

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from video_common import DEFAULT_VOICE, COHOST_VOICE
from scene_helpers import setup_chalkboard, build_header, SubtitleHud, build_funfact_card, build_endpoint_card

CAPSULE_NUM = 3
CAPSULE_SLUG = "c03_calor_laplace"
WORK_DIR = BASE_DIR / "_build_series" / CAPSULE_SLUG
OUTPUT_MP4 = BASE_DIR / "03_difusion_calor_laplace_2d.mp4"
SCENE_CLASS = "Capsula03CalorLaplaceScene"

SEGMENTS = [
    {
        "id": "s1_regla_promedio",
        "voice": DEFAULT_VOICE,
        "style": "hook",
        "subtitle": "Ecuación de Laplace (∇²T = 0): en equilibrio sin fuentes, cada nodo es el promedio exacto de sus 4 vecinos.",
        "narration": (
            "Imagina una placa metálica cuyo borde superior arde a cien grados Celsius "
            "mientras los otros tres lados se mantienen a cero grados en hielo. "
            "En estado estacionario y sin fuentes internas rige la ecuación de Laplace: nabla cuadrado de te igual a cero. "
            "Al despejar te sub... í coma jota en nuestra molécula en cruz, surge una regla bellísima: "
            "cada nodo es simplemente el promedio exacto de sus cuatro vecinos."
        ),
    },
    {
        "id": "s2_principio_maximo",
        "voice": COHOST_VOICE,
        "style": "funfact",
        "subtitle": "Dato curioso: El Principio del Máximo impide picos internos; Gauss relajaba redes a mano en el siglo XIX.",
        "narration": (
            "¡Eso es democracia térmica pura! De hecho, esta regla encierra un famoso teorema físico: "
            "el Principio del Máximo de Laplace. Como ningún promedio puede superar al mayor de sus vecinos "
            "ni caer debajo del menor, es imposible que surja un punto más caliente o más frío en el interior que en los bordes. "
            "Carl Friedrich Gauss ya aplicaba esta relajación a mano en el siglo diecinueve para ajustar redes geodésicas."
        ),
    },
    {
        "id": "s3_gauss_seidel",
        "voice": DEFAULT_VOICE,
        "style": "explain",
        "subtitle": "Barrido Gauss-Seidel: cada nodo usa al instante los valores recién actualizados de sus vecinos.",
        "narration": (
            "Veamos la primera pasada en cámara lenta. El nodo superior izquierdo mira al borde norte de cien grados "
            "y a tres vecinos en cero: su promedio sube de inmediato a veinticinco grados. "
            "Con Gauss-Seidel, el nodo vecino aprovecha al instante ese veinticinco recién calculado "
            "y salta a treinta y uno punto tres grados, acelerando la difusión."
        ),
    },
    {
        "id": "s4_convergencia",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Iteración tras iteración el error máximo cae bajo ε y el centro converge exactamente a 25.0 °C.",
        "narration": (
            "Al repetir este barrido sobre toda la malla, el mapa térmico se suaviza como una onda cálida "
            "que desciende desde el borde superior. "
            "En cada iteración medimos cuánto cambió el nodo más rebelde: cuando ese residuo cae por debajo de la tolerancia épsilon, "
            "la placa alcanza su equilibrio exacto, con veinticinco grados justo en el centro."
        ),
    },
    {
        "id": "s5_endpoint",
        "voice": COHOST_VOICE,
        "style": "endpoint",
        "subtitle": "Endpoint Cápsula 3: Equilibrio de Laplace resuelto → Siguiente: Electrostática, cargas ±ρ (Poisson) y Campo E.",
        "narration": (
            "Llegamos al endpoint de la cápsula tres: comprobamos que la ecuación de Laplace convierte el equilibrio térmico "
            "en un promedio iterativo suave gobernado por las fronteras. "
            "Pero ¿qué ocurre si inyectamos cargas puntuales positivas y negativas dentro de la malla? "
            "¡Descubrámoslo en la cápsula final con la ecuación de Poisson y el campo eléctrico!"
        ),
    },
]

FORMULAS = {
    "eq_laplace_t": '#set text(fill: rgb("#38bdf8"), size: 25pt, weight: "bold")\n$ nabla^2 T = (partial^2 T) / (partial x^2) + (partial^2 T) / (partial y^2) = 0 $',
    "eq_avg_4":     '#set text(fill: rgb("#fde047"), size: 24pt, weight: "bold")\n$ T_(i,j) = (T_N + T_S + T_E + T_O) / 4 $',
    "eq_tol":       '#set text(fill: rgb("#34d399"), size: 21pt)\n$ max |T_(i,j)^((k)) - T_(i,j)^((k-1))| < epsilon $',
}


def temp_to_hex(temp: float) -> str:
    """Mapea [0, 100] °C a una paleta térmica científica oscura -> cian -> ámbar -> rojo intenso."""
    u = max(0.0, min(1.0, temp / 100.0))
    stops = [
        (0.00, (15, 38, 78)),    # azul frío profundo
        (0.25, (14, 116, 144)),  # cian/teal templado
        (0.55, (217, 119, 6)),   # ámbar cálido
        (1.00, (220, 38, 38)),   # rojo incandescente
    ]
    for k in range(len(stops) - 1):
        u0, c0 = stops[k]
        u1, c1 = stops[k + 1]
        if u <= u1:
            t = (u - u0) / (u1 - u0 + 1e-9)
            r = int(round(c0[0] + t * (c1[0] - c0[0])))
            g = int(round(c0[1] + t * (c1[1] - c0[1])))
            b = int(round(c0[2] + t * (c1[2] - c0[2])))
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#dc2626"


def compute_gauss_seidel_history(n_sweeps: int = 20):
    """Calcula la evolución exacta de Gauss-Seidel en una placa de 5x5 nodos (borde sup = 100, otros = 0)."""
    T = np.zeros((5, 5), dtype=float)
    T[0, :] = 100.0
    T[0, 0] = 50.0
    T[0, 4] = 50.0
    history = [T.copy()]
    residuals = []
    for _ in range(n_sweeps):
        prev = T.copy()
        for r in range(1, 4):
            for c in range(1, 4):
                T[r, c] = 0.25 * (T[r - 1, c] + T[r + 1, c] + T[r, c - 1] + T[r, c + 1])
        residuals.append(float(np.max(np.abs(T - prev))))
        history.append(T.copy())
    return history, residuals


class Capsula03CalorLaplaceScene(Scene):
    def construct(self):
        setup_chalkboard(self)
        svg_dir = WORK_DIR / "svg"
        timings = json.loads((WORK_DIR / "timings.json").read_text(encoding="utf-8"))

        header = build_header(
            "3. Difusión de Calor 2D y Relajación Iterativa de Laplace",
            "Cápsula 3 de 4",
            accent="#ef4444",
        )
        hud = SubtitleHud(self)
        self.add(header)

        history, residuals = compute_gauss_seidel_history(20)

        # Construcción visual de la placa 5x5 a la izquierda
        plate_center = np.array([-3.25, 0.02, 0.0])
        cell_sz = 0.92

        def build_plate_mobject(T_mat: np.ndarray):
            tiles = VGroup()
            labels = VGroup()
            for r in range(5):
                for c in range(5):
                    pos = plate_center + np.array([(c - 2) * cell_sz, (2 - r) * cell_sz, 0.0])
                    is_border = (r == 0 or r == 4 or c == 0 or c == 4)
                    val = T_mat[r, c]
                    sq = RoundedRectangle(
                        corner_radius=0.07,
                        width=cell_sz - 0.06,
                        height=cell_sz - 0.06,
                        fill_color=temp_to_hex(val),
                        fill_opacity=0.96,
                        stroke_color="#f8fafc" if not is_border else "#94a3b8",
                        stroke_width=1.4 if not is_border else 2.2,
                    ).move_to(pos)
                    txt_str = f"{int(round(val))}°" if is_border else f"{val:.1f}°"
                    lbl = Text(
                        txt_str,
                        font="Consolas",
                        font_size=15 if not is_border else 16,
                        weight=BOLD if is_border else NORMAL,
                        color="#f8fafc",
                    ).move_to(pos)
                    tiles.add(sq)
                    labels.add(lbl)
            return VGroup(tiles, labels)

        # ================= ESCENA 1: LAPLACE Y REGLA DEL PROMEDIO =================
        d1 = timings[0]["duration"]
        hud.show(timings[0])

        plate_v = build_plate_mobject(history[0])
        top_tag = Text("Frontera caliente: 100 °C", font="Segoe UI", font_size=16, weight=BOLD, color="#fca5a5").next_to(plate_v, UP, buff=0.14)
        bot_tag = Text("Bordes fríos: 0 °C", font="Segoe UI", font_size=15, color="#93c5fd").next_to(plate_v, DOWN, buff=0.12)

        right_panel = RoundedRectangle(
            corner_radius=0.16, width=5.65, height=5.20,
            fill_color="#0f172a", fill_opacity=0.88,
            stroke_color="#1e3a8a", stroke_width=2.0,
        ).move_to(np.array([3.45, 0.08, 0.0]))

        eq_lap = SVGMobject(str(svg_dir / "eq_laplace_t.svg")).scale_to_fit_width(4.85).move_to(right_panel.get_top() + DOWN * 0.95)
        arrow_down = Arrow(eq_lap.get_bottom() + DOWN * 0.12, eq_lap.get_bottom() + DOWN * 0.85, buff=0.05, color="#94a3b8", stroke_width=3.0)
        eq_avg4 = SVGMobject(str(svg_dir / "eq_avg_4.svg")).scale_to_fit_width(4.75).move_to(right_panel.get_center() + DOWN * 0.45)
        avg4_box = SurroundingRectangle(eq_avg4, color="#fde047", buff=0.15, corner_radius=0.10, stroke_width=2.2)

        t_used = 0.0
        self.play(FadeIn(plate_v), FadeIn(top_tag), FadeIn(bot_tag), FadeIn(right_panel), run_time=1.6)
        self.play(Write(eq_lap), run_time=1.8)
        self.play(GrowArrow(arrow_down), Write(eq_avg4), Create(avg4_box), run_time=2.2)
        t_used += 5.6
        if d1 > t_used:
            self.wait(d1 - t_used)

        # ================= ESCENA 2: FUN FACT PRINCIPIO DEL MÁXIMO Y GAUSS =================
        d2 = timings[1]["duration"]
        hud.show(timings[1])

        ff_max = build_funfact_card(
            "DATO CURIOSO • PRINCIPIO DEL MÁXIMO",
            "Imposible crear extremos internos",
            [
                "Sin fuentes internas de calor, ningún nodo",
                "puede superar 100 °C ni bajar de 0 °C.",
                "Carl Friedrich Gauss relajaba a mano estas",
                "mallas corrigiendo primero el mayor error.",
            ],
            width=5.15,
            accent="#fbbf24",
        ).move_to(right_panel.get_bottom() + UP * 1.35)

        center_pos = plate_center
        cross_hl = VGroup(
            SurroundingRectangle(plate_v[0][12], color="#fde047", buff=0.02, stroke_width=3.2),
            SurroundingRectangle(plate_v[0][7], color="#38bdf8", buff=0.02, stroke_width=2.2),
            SurroundingRectangle(plate_v[0][17], color="#38bdf8", buff=0.02, stroke_width=2.2),
            SurroundingRectangle(plate_v[0][11], color="#38bdf8", buff=0.02, stroke_width=2.2),
            SurroundingRectangle(plate_v[0][13], color="#38bdf8", buff=0.02, stroke_width=2.2),
        )

        t_used = 0.0
        self.play(
            eq_lap.animate.scale(0.80).move_to(right_panel.get_top() + DOWN * 0.54),
            FadeOut(arrow_down),
            VGroup(eq_avg4, avg4_box).animate.scale(0.84).move_to(right_panel.get_top() + DOWN * 1.66),
            FadeIn(ff_max, shift=UP * 0.20),
            Create(cross_hl),
            run_time=2.0,
        )
        t_used += 2.0
        if d2 > t_used:
            self.wait(d2 - t_used)

        # ================= ESCENA 3: CÁMARA LENTA GAUSS-SEIDEL (PASADA 1) =================
        d3 = timings[2]["duration"]
        hud.show(timings[2])

        self.play(FadeOut(ff_max), FadeOut(cross_hl), run_time=0.5)

        # Paso 1a: nodo (1,1) -> índice 6 (fila 1, col 1): (100 + 0 + 0 + 0)/4 = 25.0
        T_step1a = history[0].copy()
        T_step1a[1, 1] = 25.0
        plate_1a = build_plate_mobject(T_step1a)
        hl_n1 = SurroundingRectangle(plate_v[0][6], color="#fde047", buff=0.03, stroke_width=3.5)
        calc_1a = Text("Nodo (1,1): (100 + 0 + 0 + 0) / 4 = 25.0°", font="Consolas", font_size=16, color="#fde047")
        calc_1a.move_to(right_panel.get_center() + DOWN * 0.55)

        # Paso 1b: nodo (1,2) -> índice 7 (fila 1, col 2): (100 + 25.0 + 0 + 0)/4 = 31.25 -> 31.2°
        T_step1b = T_step1a.copy()
        T_step1b[1, 2] = 31.25
        plate_1b = build_plate_mobject(T_step1b)
        hl_n2 = SurroundingRectangle(plate_v[0][7], color="#34d399", buff=0.03, stroke_width=3.5)
        calc_1b = Text("Nodo (1,2): (100 + 25.0 + 0 + 0) / 4 = 31.3°", font="Consolas", font_size=16, color="#34d399")
        calc_1b.next_to(calc_1a, DOWN, buff=0.26)

        gs_note = Text("¡Gauss-Seidel reutiliza el 25.0° al instante!", font="Segoe UI", font_size=16, color="#93c5fd")
        gs_note.next_to(calc_1b, DOWN, buff=0.28)

        t_used = 0.5
        self.play(Create(hl_n1), FadeIn(calc_1a), Transform(plate_v, plate_1a), run_time=1.8)
        self.wait(0.5)
        self.play(ReplacementTransform(hl_n1, hl_n2), FadeIn(calc_1b), FadeIn(gs_note), Transform(plate_v, plate_1b), run_time=2.0)
        t_used += 4.3
        if d3 > t_used:
            self.wait(d3 - t_used)

        # ================= ESCENA 4: ITERACIONES Y CURVA DE CONVERGENCIA =================
        d4 = timings[3]["duration"]
        hud.show(timings[3])

        self.play(FadeOut(hl_n2), FadeOut(calc_1a), FadeOut(calc_1b), FadeOut(gs_note), run_time=0.5)

        # Ejes de convergencia dentro del panel derecho
        conv_axes = Axes(
            x_range=[0, 18, 5],
            y_range=[-3, 2, 1],
            x_length=4.45,
            y_length=1.85,
            axis_config={"color": "#94a3b8", "stroke_width": 2.0, "include_ticks": False, "include_tip": True, "tip_width": 0.16, "tip_height": 0.16},
        ).move_to(right_panel.get_bottom() + UP * 1.82)
        conv_xlbl = Text("Iteración k", font="Segoe UI", font_size=14, color="#94a3b8").move_to(conv_axes.c2p(15.2, 0.45))
        conv_ylbl = Text("log₁₀(Error máx)", font="Segoe UI", font_size=14, color="#94a3b8").next_to(conv_axes, UP, aligned_edge=LEFT, buff=0.06)

        pts_conv = [
            conv_axes.c2p(k + 1, max(-2.9, min(1.9, math.log10(max(residuals[k], 1e-4)))))
            for k in range(18)
        ]
        conv_path = VMobject(color="#34d399", stroke_width=3.5)
        conv_path.set_points_smoothly(pts_conv)

        tol_line = DashedLine(conv_axes.c2p(0, -1.8), conv_axes.c2p(18, -1.8), color="#fbbf24", stroke_width=1.8)
        eq_tol = SVGMobject(str(svg_dir / "eq_tol.svg")).scale_to_fit_width(4.15).move_to(right_panel.get_bottom() + UP * 0.42)

        iter_badge = Text("Iteración k = 1", font="Consolas", font_size=17, weight=BOLD, color="#fde047")
        iter_badge.move_to(np.array([-3.25, -2.82, 0.0]))

        self.play(Create(conv_axes), FadeIn(conv_xlbl), FadeIn(conv_ylbl), Create(tol_line), FadeIn(eq_tol), FadeIn(iter_badge), run_time=1.3)

        sweep_steps = [1, 2, 4, 8, 18]
        t_used = 1.8
        for sw in sweep_steps:
            new_plate = build_plate_mobject(history[sw])
            new_badge = Text(f"Iteración k = {sw}", font="Consolas", font_size=17, weight=BOLD, color="#34d399" if sw == 18 else "#fde047").move_to(iter_badge.get_center())
            self.play(Transform(plate_v, new_plate), Transform(iter_badge, new_badge), run_time=0.85)
            t_used += 0.85

        self.play(Create(conv_path), Indicate(plate_v[0][12], color="#fde047", scale_factor=1.12), run_time=1.6)
        t_used += 1.6
        if d4 > t_used + 0.6:
            self.wait(d4 - t_used - 0.6)

        self.play(
            FadeOut(VGroup(plate_v, top_tag, bot_tag, iter_badge, right_panel, eq_lap, eq_avg4, avg4_box, conv_axes, conv_xlbl, conv_ylbl, conv_path, tol_line, eq_tol)),
            run_time=0.6,
        )

        # ================= ESCENA 5: ENDPOINT CÁPSULA 3 =================
        d5 = timings[4]["duration"]
        hud.show(timings[4])

        ep_card = build_endpoint_card(
            capsule_num=3,
            capsule_title="Equilibrio térmico resuelto mediante promedios locales",
            takeaways=[
                "La ecuación de Laplace (∇²T = 0) convierte cada nodo interior en el promedio de sus 4 vecinos.",
                "El Principio del Máximo garantiza suavidad total sin picos ni valles artificiales dentro de la placa.",
                "El método iterativo de Gauss-Seidel propaga las fronteras hasta converger bajo una tolerancia ε.",
            ],
            next_kicker="SIGUIENTE CÁPSULA (4 DE 4)  →  ELECTROSTÁTICA, POISSON (±ρ) Y PUENTE AL MEF",
            next_description="¿Cómo deforman las cargas puntuales (+ρ y −ρ) ese mapa plano y cómo nace el Campo Eléctrico E = −∇V?",
            accent="#10b981",
        )
        self.play(FadeIn(ep_card, shift=UP * 0.20), run_time=1.4)
        if d5 > 1.4:
            self.wait(d5 - 1.4)
