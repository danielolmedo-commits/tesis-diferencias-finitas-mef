# -*- coding: utf-8 -*-
"""
Cápsula 1 de 4: De la Derivada Continua a las Diferencias Finitas (1ra y 2da Derivada)
Salida: 01_derivadas_diferencias_finitas.mp4
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

CAPSULE_NUM = 1
CAPSULE_SLUG = "c01_derivadas"
WORK_DIR = BASE_DIR / "_build_series" / CAPSULE_SLUG
OUTPUT_MP4 = BASE_DIR / "01_derivadas_diferencias_finitas.mp4"
SCENE_CLASS = "Capsula01DerivadasScene"

SEGMENTS = [
    {
        "id": "s1_hook_historia",
        "voice": COHOST_VOICE,
        "style": "funfact",
        "subtitle": "Dato curioso (1922): Lewis Fry Richardson imaginó 64,000 calculistas en un estadio prediciendo el clima con restas.",
        "narration": (
            "Imagina un estadio gigante con sesenta y cuatro mil matemáticos calculando el clima a mano al mismo tiempo. "
            "En mil novecientos veintidós, Lewis Fry Richardson propuso exactamente esa locura: dividir la atmósfera en una cuadrícula "
            "donde cada persona solo restaba datos con sus vecinos inmediatos. "
            "Sin saberlo, estaba inaugurando la era moderna de las diferencias finitas."
        ),
    },
    {
        "id": "s2_puente_continuo",
        "voice": DEFAULT_VOICE,
        "style": "explain",
        "subtitle": "En cálculo continuo h → 0 da la tangente exacta; en digital dividir 0/0 colapsa y necesitamos un paso finito h.",
        "narration": (
            "¡Así es! En el papel, la derivada en un nodo equis sub... í es la pendiente exacta de su recta tangente "
            "cuando el paso hache tiende a cero. "
            "Pero si le pides a un procesador dividir cero entre cero, el cálculo colapsa al instante. "
            "La computadora necesita apoyarse en nodos separados por un paso finito hache."
        ),
    },
    {
        "id": "s3_forward",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Diferencia hacia adelante (Forward): cateto vertical (yᵢ₊₁ − yᵢ) entre base h.",
        "narration": (
            "Si avanzamos un paso hache hacia la derecha hasta equis sub... í más uno, "
            "formamos un triángulo rectángulo de base hache y altura ye sub... í más uno, menos ye sub... í. "
            "Esa pendiente secante define la diferencia finita hacia adelante."
        ),
    },
    {
        "id": "s4_backward",
        "voice": COHOST_VOICE,
        "style": "explain",
        "subtitle": "Diferencia hacia atrás (Backward): (yᵢ − yᵢ₋₁) / h. Una secante subestima la pendiente y la otra la sobreestima.",
        "narration": (
            "Y si miramos un paso hacia atrás, hasta equis sub... í menos uno, "
            "obtenemos otra secante con altura ye sub... í, menos ye sub... í menos uno. "
            "Pero observa la curva: una secante se queda corta y la otra se pasa de inclinación. "
            "¿Cómo eliminamos ese sesgo geométrico?"
        ),
    },
    {
        "id": "s5_central",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Al promediar ambas pendientes se cancela −yᵢ + yᵢ y nace la Diferencia Central: (yᵢ₊₁ − yᵢ₋₁) / (2h).",
        "narration": (
            "¡Promediando ambas pendientes! Mira qué elegante: al sumar los numeradores, "
            "menos ye sub... í más ye sub... í se cancelan exactamente. "
            "Nos queda ye sub... í más uno, menos ye sub... í menos uno, dividido entre dos hache: "
            "la diferencia central, cuya secante resulta casi paralela a la tangente exacta."
        ),
    },
    {
        "id": "s6_convergencia_segunda",
        "voice": DEFAULT_VOICE,
        "style": "explain",
        "subtitle": "Error cuadrático O(h²) y Segunda Derivada (curvatura): pesos [ +1 , −2 , +1 ] / h².",
        "narration": (
            "Al partir el paso hache a la mitad, el error central cae cuatro veces más rápido. "
            "Y al calcular la diferencia de las diferencias, obtenemos la joya para simular la física: "
            "la segunda derivada, con sus famosos pesos uno, menos dos y uno, divididos entre hache al cuadrado."
        ),
    },
    {
        "id": "s7_endpoint",
        "voice": COHOST_VOICE,
        "style": "endpoint",
        "subtitle": "Endpoint Cápsula 1: Derivadas traducidas a álgebra nodal → Siguiente paso: Malla 1D/2D y Viga con fronteras.",
        "narration": (
            "Llegamos al endpoint de nuestra primera cápsula: "
            "ya sabemos traducir primera y segunda derivada a simples sumas y restas entre tres nodos vecinos con precisión cuadrática. "
            "En la cápsula dos conectaremos estos bloques en una malla completa con fronteras fijas "
            "para calcular la deflexión real de una viga."
        ),
    },
]

FORMULAS = {
    "eq_title": '#set text(fill: rgb("#f8fafc"), size: 24pt, weight: "bold")\n$ y\'(x_i) = lim_(h -> 0) (y(x_i + h) - y(x_i)) / h $',
    "eq_fwd":   '#set text(fill: rgb("#fbbf24"), size: 23pt)\n$ m_("Forward") = (y_(i+1) - y_i) / h $',
    "eq_bwd":   '#set text(fill: rgb("#34d399"), size: 23pt)\n$ m_("Backward") = (y_i - y_(i-1)) / h $',
    "eq_avg":   '#set text(fill: rgb("#e2e8f0"), size: 21pt)\n$ m_("Central") = (y_(i+1) - y_i + y_i - y_(i-1)) / (2 h) $',
    "eq_cen":   '#set text(fill: rgb("#c084fc"), size: 24pt)\n$ m_("Central") = (y_(i+1) - y_(i-1)) / (2 h) + O(h^2) $',
    "eq_d2":    '#set text(fill: rgb("#38bdf8"), size: 24pt, weight: "bold")\n$ y\'\'(x_i) approx (y_(i-1) - 2 y_i + y_(i+1)) / h^2 $',
    "lbl_xm1":  '#set text(fill: rgb("#cbd5e1"), size: 21pt)\n$ x_(i-1) $',
    "lbl_x0":   '#set text(fill: rgb("#f8fafc"), size: 21pt)\n$ x_i $',
    "lbl_xp1":  '#set text(fill: rgb("#cbd5e1"), size: 21pt)\n$ x_(i+1) $',
    "lbl_fx":   '#set text(fill: rgb("#38bdf8"), size: 23pt)\n$ y = f(x) $',
    "lbl_h":    '#set text(fill: rgb("#fbbf24"), size: 20pt)\n$ h $',
}


def f_curve(x: float) -> float:
    return 1.35 + 1.55 * math.sin(0.85 * x - 0.35) + 0.22 * x


def df_curve(x: float) -> float:
    return 1.55 * 0.85 * math.cos(0.85 * x - 0.35) + 0.22


class Capsula01DerivadasScene(Scene):
    def construct(self):
        setup_chalkboard(self)
        svg_dir = WORK_DIR / "svg"
        timings = json.loads((WORK_DIR / "timings.json").read_text(encoding="utf-8"))

        header = build_header(
            "1. De la Derivada Continua a las Diferencias Finitas",
            "Cápsula 1 de 4",
            accent="#3b82f6",
        )
        hud = SubtitleHud(self)
        self.add(header)

        # ================= ESCENA 1: HOOK HISTÓRICO (RICHARDSON 1922) =================
        d1 = timings[0]["duration"]
        hud.show(timings[0])

        # Ilustración geométrica izquierda: globo / anfiteatro de calculistas conectados en malla
        globe_center = np.array([-3.25, 0.15, 0.0])
        outer_ring = Circle(radius=2.15, color="#38bdf8", stroke_width=2.5, fill_color="#0b192c", fill_opacity=0.65).move_to(globe_center)
        lat_lines = VGroup(*[
            Line(
                globe_center + np.array([-math.sqrt(max(0.01, 2.15**2 - dy**2)), dy, 0]),
                globe_center + np.array([math.sqrt(max(0.01, 2.15**2 - dy**2)), dy, 0]),
                color="#1e3a8a", stroke_width=1.6,
            )
            for dy in [-1.35, -0.68, 0.0, 0.68, 1.35]
        ])
        lon_arcs = VGroup(*[
            Ellipse(width=w, height=4.30, color="#1e3a8a", stroke_width=1.6).move_to(globe_center)
            for w in [1.3, 2.7, 3.8]
        ])
        calc_dots = VGroup()
        links = VGroup()
        pts_grid = {}
        for r_i, dy in enumerate([-1.35, -0.68, 0.0, 0.68, 1.35]):
            for c_i, dx in enumerate([-1.35, -0.68, 0.0, 0.68, 1.35]):
                if dx*dx + dy*dy <= 1.95**2:
                    pt = globe_center + np.array([dx, dy, 0.0])
                    pts_grid[(r_i, c_i)] = pt
                    col = "#fbbf24" if (r_i == 2 and c_i == 2) else ("#38bdf8" if abs(r_i - 2) + abs(c_i - 2) == 1 else "#94a3b8")
                    rad = 0.095 if (r_i == 2 and c_i == 2) else 0.065
                    calc_dots.add(Dot(pt, radius=rad, color=col))

        for (r_i, c_i), pt in pts_grid.items():
            if r_i == 2 and c_i == 2:
                for nr, nc in [(1, 2), (3, 2), (2, 1), (2, 3)]:
                    if (nr, nc) in pts_grid:
                        links.add(Arrow(pt, pts_grid[(nr, nc)], buff=0.10, stroke_width=3.2, color="#fbbf24", max_tip_length_to_length_ratio=0.25))

        globe_lbl = Text("Red humana de cálculo (1922)", font="Segoe UI", font_size=17, color="#93c5fd").next_to(outer_ring, DOWN, buff=0.20)
        globe_grp = VGroup(outer_ring, lat_lines, lon_arcs, links, calc_dots, globe_lbl)

        ff_card = build_funfact_card(
            "DATO CURIOSO • HISTORIA COMPUTACIONAL",
            "El estadio de 64,000 calculistas",
            [
                "Lewis Fry Richardson (Weather Prediction, 1922)",
                "imaginó un teatro esférico gigante donde cada",
                "calculista recibía datos de sus 4 vecinos y",
                "resolvía derivadas usando solo sumas y restas.",
                "¡Exactamente la misma lógica de nuestra malla!",
            ],
            width=6.25,
            accent="#fbbf24",
        ).move_to(np.array([3.05, 0.15, 0.0]))

        t_used = 0.0
        self.play(FadeIn(outer_ring), Create(lat_lines), Create(lon_arcs), run_time=1.5)
        self.play(LaggedStart(*[FadeIn(d, scale=1.4) for d in calc_dots], lag_ratio=0.04), run_time=1.4)
        self.play(Create(links), FadeIn(globe_lbl), FadeIn(ff_card, shift=LEFT * 0.25), run_time=1.8)
        t_used += 4.7
        if d1 > t_used + 0.6:
            self.wait(d1 - t_used - 0.6)
        self.play(FadeOut(globe_grp), FadeOut(ff_card), run_time=0.6)

        # ================= ESCENA 2: PUENTE DEL CÁLCULO CONTINUO AL DIGITAL =================
        d2 = timings[1]["duration"]
        hud.show(timings[1])

        axes = Axes(
            x_range=[0, 4.2, 1],
            y_range=[0, 4.3, 1],
            x_length=6.85,
            y_length=4.05,
            axis_config={
                "color": "#cbd5e1",
                "stroke_width": 2.7,
                "include_ticks": False,
                "include_tip": True,
                "tip_width": 0.2,
                "tip_height": 0.2,
            },
        ).move_to(LEFT * 2.90 + UP * 0.34)

        curve = axes.plot(f_curve, x_range=[0.25, 3.95], color="#38bdf8", stroke_width=4.4)
        lbl_fx = SVGMobject(str(svg_dir / "lbl_fx.svg")).scale_to_fit_height(0.36)
        lbl_fx.move_to(axes.c2p(3.62, f_curve(3.62)) + UP * 0.48 + RIGHT * 0.28)

        board_panel = RoundedRectangle(
            corner_radius=0.16, width=5.40, height=5.35,
            fill_color="#0f172a", fill_opacity=0.84,
            stroke_color="#1e3a8a", stroke_width=2.0,
        ).move_to(RIGHT * 3.85 + UP * 0.08)

        x0_val = 2.05
        h_tracker = ValueTracker(0.95)
        m_exact = df_curve(x0_val)

        p_center = Dot(axes.c2p(x0_val, f_curve(x0_val)), radius=0.09, color="#f8fafc")
        tan_line = axes.plot(
            lambda x: f_curve(x0_val) + m_exact * (x - x0_val),
            x_range=[x0_val - 1.12, x0_val + 1.12],
            color="#fb7185",
            stroke_width=3.8,
        )
        tan_tag = Text("Tangente exacta", font="Segoe UI", font_size=18, color="#fb7185")
        tan_tag.next_to(axes.c2p(x0_val - 0.55, f_curve(x0_val) - 0.55 * m_exact), UP + LEFT, buff=0.10)

        dash_x0 = DashedLine(axes.c2p(x0_val, f_curve(x0_val)), axes.c2p(x0_val, 0), color="#94a3b8", stroke_width=2.1)
        lbl_x0 = SVGMobject(str(svg_dir / "lbl_x0.svg")).scale_to_fit_height(0.32).next_to(axes.c2p(x0_val, 0), DOWN, buff=0.13)

        eq_title = SVGMobject(str(svg_dir / "eq_title.svg")).scale_to_fit_width(4.70)
        eq_title.move_to(board_panel.get_top() + DOWN * 0.66)

        zero_warn_txt = Text("En digital: h = 0  →  0 / 0 (Error)", font="Consolas", font_size=17, color="#fca5a5")
        zero_warn_bg = RoundedRectangle(corner_radius=0.08, width=4.65, height=0.42, fill_color="#450a0a", fill_opacity=0.85, stroke_color="#ef4444", stroke_width=1.5)
        zero_warn = VGroup(zero_warn_bg, zero_warn_txt).move_to(board_panel.get_top() + DOWN * 1.42)
        zero_warn_txt.move_to(zero_warn_bg.get_center())

        t_used = 0.0
        self.play(FadeIn(board_panel), Create(axes), Create(curve), FadeIn(lbl_fx), run_time=1.8)
        self.play(FadeIn(p_center, scale=1.4), Create(dash_x0), FadeIn(lbl_x0), run_time=1.1)
        self.play(Create(tan_line), FadeIn(tan_tag), Write(eq_title), run_time=1.8)
        self.play(FadeIn(zero_warn, scale=1.05), run_time=0.9)
        t_used += 5.6
        if d2 > t_used:
            self.wait(d2 - t_used)

        # ================= ESCENA 3: FORWARD DIFFERENCE =================
        d3 = timings[2]["duration"]
        hud.show(timings[2])

        h0 = h_tracker.get_value()
        xp1_val = x0_val + h0
        p_right = Dot(axes.c2p(xp1_val, f_curve(xp1_val)), radius=0.085, color="#fbbf24")
        dash_xp1 = DashedLine(axes.c2p(xp1_val, f_curve(xp1_val)), axes.c2p(xp1_val, 0), color="#fbbf24", stroke_width=2.0, stroke_opacity=0.65)
        lbl_xp1 = SVGMobject(str(svg_dir / "lbl_xp1.svg")).scale_to_fit_height(0.32).next_to(axes.c2p(xp1_val, 0), DOWN, buff=0.13)

        tri_fwd_h = DashedLine(axes.c2p(x0_val, f_curve(x0_val)), axes.c2p(xp1_val, f_curve(x0_val)), color="#fbbf24", stroke_width=2.3)
        tri_fwd_v = DashedLine(axes.c2p(xp1_val, f_curve(x0_val)), axes.c2p(xp1_val, f_curve(xp1_val)), color="#fbbf24", stroke_width=2.7)
        sec_fwd = Line(axes.c2p(x0_val, f_curve(x0_val)), axes.c2p(xp1_val, f_curve(xp1_val)), color="#fbbf24", stroke_width=3.9)

        brace_h_r = BraceBetweenPoints(axes.c2p(x0_val, 0), axes.c2p(xp1_val, 0), direction=DOWN, color="#fbbf24").shift(DOWN * 0.34)
        lbl_h_r = SVGMobject(str(svg_dir / "lbl_h.svg")).scale_to_fit_height(0.24).next_to(brace_h_r, DOWN, buff=0.04)

        eq_fwd = SVGMobject(str(svg_dir / "eq_fwd.svg")).scale_to_fit_width(4.15)
        eq_fwd.move_to(board_panel.get_top() + DOWN * 1.65)

        t_used = 0.0
        self.play(FadeOut(zero_warn), FadeIn(p_right, scale=1.4), Create(dash_xp1), FadeIn(lbl_xp1), run_time=1.3)
        self.play(Create(tri_fwd_h), Create(tri_fwd_v), FadeIn(brace_h_r), FadeIn(lbl_h_r), run_time=1.5)
        self.play(Create(sec_fwd), Write(eq_fwd), run_time=1.8)
        t_used += 4.6
        if d3 > t_used:
            self.wait(d3 - t_used)

        # ================= ESCENA 4: BACKWARD DIFFERENCE =================
        d4 = timings[3]["duration"]
        hud.show(timings[3])

        xm1_val = x0_val - h0
        p_left = Dot(axes.c2p(xm1_val, f_curve(xm1_val)), radius=0.085, color="#34d399")
        dash_xm1 = DashedLine(axes.c2p(xm1_val, f_curve(xm1_val)), axes.c2p(xm1_val, 0), color="#34d399", stroke_width=2.0, stroke_opacity=0.65)
        lbl_xm1 = SVGMobject(str(svg_dir / "lbl_xm1.svg")).scale_to_fit_height(0.32).next_to(axes.c2p(xm1_val, 0), DOWN, buff=0.13)

        tri_bwd_h = DashedLine(axes.c2p(xm1_val, f_curve(xm1_val)), axes.c2p(x0_val, f_curve(xm1_val)), color="#34d399", stroke_width=2.3)
        tri_bwd_v = DashedLine(axes.c2p(x0_val, f_curve(xm1_val)), axes.c2p(x0_val, f_curve(x0_val)), color="#34d399", stroke_width=2.7)
        sec_bwd = Line(axes.c2p(xm1_val, f_curve(xm1_val)), axes.c2p(x0_val, f_curve(x0_val)), color="#34d399", stroke_width=3.9)

        brace_h_l = BraceBetweenPoints(axes.c2p(xm1_val, 0), axes.c2p(x0_val, 0), direction=DOWN, color="#34d399").shift(DOWN * 0.34)
        lbl_h_l = SVGMobject(str(svg_dir / "lbl_h.svg")).scale_to_fit_height(0.24).set_color("#34d399").next_to(brace_h_l, DOWN, buff=0.04)

        eq_bwd = SVGMobject(str(svg_dir / "eq_bwd.svg")).scale_to_fit_width(4.35)
        eq_bwd.move_to(board_panel.get_top() + DOWN * 2.65)

        t_used = 0.0
        self.play(FadeIn(p_left, scale=1.4), Create(dash_xm1), FadeIn(lbl_xm1), run_time=1.3)
        self.play(Create(tri_bwd_h), Create(tri_bwd_v), FadeIn(brace_h_l), FadeIn(lbl_h_l), run_time=1.5)
        self.play(Create(sec_bwd), Write(eq_bwd), run_time=1.8)
        t_used += 4.6
        if d4 > t_used:
            self.wait(d4 - t_used)

        # ================= ESCENA 5: DIFERENCIA CENTRAL Y CANCELACIÓN =================
        d5 = timings[4]["duration"]
        hud.show(timings[4])

        eq_avg = SVGMobject(str(svg_dir / "eq_avg.svg")).scale_to_fit_width(4.80)
        eq_avg.move_to(board_panel.get_top() + DOWN * 3.70)

        eq_cen = SVGMobject(str(svg_dir / "eq_cen.svg")).scale_to_fit_width(4.70)
        eq_cen.move_to(board_panel.get_top() + DOWN * 3.70)
        cen_box = SurroundingRectangle(eq_cen, color="#c084fc", buff=0.11, corner_radius=0.08, stroke_width=2.0)

        mc0 = (f_curve(xp1_val) - f_curve(xm1_val)) / (2.0 * h0)
        sec_central = Line(
            axes.c2p(xm1_val - 0.16, f_curve(xm1_val) - 0.16 * mc0),
            axes.c2p(xp1_val + 0.16, f_curve(xp1_val) + 0.16 * mc0),
            color="#c084fc",
            stroke_width=4.3,
        )

        cancel_center = eq_avg.get_center() + RIGHT * 0.60 + UP * 0.16
        slash1 = Line(cancel_center + LEFT * 0.42 + DOWN * 0.16, cancel_center + LEFT * 0.08 + UP * 0.16, color="#ef4444", stroke_width=3.5)
        slash2 = Line(cancel_center + RIGHT * 0.20 + DOWN * 0.16, cancel_center + RIGHT * 0.56 + UP * 0.16, color="#ef4444", stroke_width=3.5)

        t_used = 0.0
        self.play(Write(eq_avg), run_time=1.8)
        self.play(Create(slash1), Create(slash2), run_time=1.0)
        self.wait(0.6)
        self.play(
            FadeOut(slash1), FadeOut(slash2),
            ReplacementTransform(eq_avg, eq_cen),
            Create(cen_box),
            Create(sec_central),
            FadeOut(tri_fwd_h), FadeOut(tri_fwd_v), FadeOut(tri_bwd_h), FadeOut(tri_bwd_v),
            run_time=2.0,
        )
        t_used += 5.4
        if d5 > t_used:
            self.wait(d5 - t_used)

        # ================= ESCENA 6: CONVERGENCIA O(h^2) Y SEGUNDA DERIVADA =================
        d6 = timings[5]["duration"]
        hud.show(timings[5])

        self.play(
            FadeOut(brace_h_l), FadeOut(lbl_h_l), FadeOut(brace_h_r), FadeOut(lbl_h_r),
            FadeOut(lbl_xm1), FadeOut(lbl_xp1),
            run_time=0.6,
        )

        p_left.add_updater(lambda m: m.move_to(axes.c2p(x0_val - h_tracker.get_value(), f_curve(x0_val - h_tracker.get_value()))))
        p_right.add_updater(lambda m: m.move_to(axes.c2p(x0_val + h_tracker.get_value(), f_curve(x0_val + h_tracker.get_value()))))
        dash_xm1.add_updater(lambda m: m.put_start_and_end_on(
            axes.c2p(x0_val - h_tracker.get_value(), f_curve(x0_val - h_tracker.get_value())),
            axes.c2p(x0_val - h_tracker.get_value(), 0),
        ))
        dash_xp1.add_updater(lambda m: m.put_start_and_end_on(
            axes.c2p(x0_val + h_tracker.get_value(), f_curve(x0_val + h_tracker.get_value())),
            axes.c2p(x0_val + h_tracker.get_value(), 0),
        ))
        sec_fwd.add_updater(lambda m: m.put_start_and_end_on(
            axes.c2p(x0_val, f_curve(x0_val)),
            axes.c2p(x0_val + h_tracker.get_value(), f_curve(x0_val + h_tracker.get_value())),
        ))
        sec_bwd.add_updater(lambda m: m.put_start_and_end_on(
            axes.c2p(x0_val - h_tracker.get_value(), f_curve(x0_val - h_tracker.get_value())),
            axes.c2p(x0_val, f_curve(x0_val)),
        ))

        def update_central(mob):
            hv = h_tracker.get_value()
            xl, xr = x0_val - hv, x0_val + hv
            mc = (f_curve(xr) - f_curve(xl)) / (2.0 * hv)
            mob.put_start_and_end_on(
                axes.c2p(x0_val - 1.05, 0.5 * (f_curve(xl) + f_curve(xr)) - 1.05 * mc),
                axes.c2p(x0_val + 1.05, 0.5 * (f_curve(xl) + f_curve(xr)) + 1.05 * mc),
            )

        sec_central.add_updater(update_central)

        h_badge = always_redraw(lambda: Text(
            f"Paso h = {h_tracker.get_value():.2f}  |  Error Central = {abs(((f_curve(x0_val + h_tracker.get_value()) - f_curve(x0_val - h_tracker.get_value()))/(2*h_tracker.get_value())) - m_exact):.4f}",
            font="Consolas", font_size=17, color="#fde047",
        ).next_to(lbl_x0, DOWN, buff=0.20))
        self.add(h_badge)

        eq_d2 = SVGMobject(str(svg_dir / "eq_d2.svg")).scale_to_fit_width(4.70)
        eq_d2.move_to(board_panel.get_top() + DOWN * 4.78)
        d2_box = SurroundingRectangle(eq_d2, color="#38bdf8", buff=0.10, corner_radius=0.08, stroke_width=2.0)

        t_used = 0.6
        self.play(h_tracker.animate.set_value(0.16), run_time=3.6, rate_func=smooth)
        self.play(Write(eq_d2), Create(d2_box), run_time=2.0)
        t_used += 5.6
        if d6 > t_used + 0.6:
            self.wait(d6 - t_used - 0.6)

        p_left.clear_updaters()
        p_right.clear_updaters()
        dash_xm1.clear_updaters()
        dash_xp1.clear_updaters()
        sec_fwd.clear_updaters()
        sec_bwd.clear_updaters()
        sec_central.clear_updaters()
        self.remove(h_badge)

        stage_objs = VGroup(
            axes, curve, lbl_fx, board_panel, p_center, tan_line, tan_tag,
            dash_x0, lbl_x0, eq_title, p_right, dash_xp1, sec_fwd, eq_fwd,
            p_left, dash_xm1, sec_bwd, eq_bwd, eq_cen, cen_box, sec_central, eq_d2, d2_box,
        )
        self.play(FadeOut(stage_objs), run_time=0.6)

        # ================= ESCENA 7: ENDPOINT DE LA CÁPSULA 1 =================
        d7 = timings[6]["duration"]
        hud.show(timings[6])

        ep_card = build_endpoint_card(
            capsule_num=1,
            capsule_title="Tradujimos derivadas continuas en aritmética sobre nodos vecinos",
            takeaways=[
                "1ra Derivada Central: (yᵢ₊₁ − yᵢ₋₁) / (2h) cancela el sesgo lateral y logra precisión O(h²).",
                "2da Derivada (Curvatura): (yᵢ₋₁ − 2yᵢ + yᵢ₊₁) / h² usa la plantilla simétrica [ +1, −2, +1 ].",
                "Con solo sumas y restas, la computadora ya puede evaluar ecuaciones diferenciales.",
            ],
            next_kicker="SIGUIENTE CÁPSULA (2 DE 4)  →  DISCRETIZACIÓN, FRONTERAS Y VIGA 1D",
            next_description="¿Cómo ensamblamos estos nodos en una malla real con extremos fijos de Dirichlet y calculamos una viga?",
            accent="#10b981",
        )
        self.play(FadeIn(ep_card, shift=UP * 0.20), run_time=1.4)
        if d7 > 1.4:
            self.wait(d7 - 1.4)
