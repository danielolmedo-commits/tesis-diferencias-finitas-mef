# -*- coding: utf-8 -*-
"""
Cápsula 2 de 4: Discretización, Fronteras de Dirichlet, Viga 1D y Molécula Computacional 2D
Salida: 02_malla_molecula_y_viga.mp4
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

CAPSULE_NUM = 2
CAPSULE_SLUG = "c02_malla_viga"
WORK_DIR = BASE_DIR / "_build_series" / CAPSULE_SLUG
OUTPUT_MP4 = BASE_DIR / "02_malla_molecula_y_viga.mp4"
SCENE_CLASS = "Capsula02MallaVigaScene"

SEGMENTS = [
    {
        "id": "s1_malla_1d",
        "voice": DEFAULT_VOICE,
        "style": "hook",
        "subtitle": "Discretización 1D: partimos un dominio continuo [0, L] en N intervalos iguales de paso h = L / N.",
        "narration": (
            "En la cápsula anterior descubrimos cómo calcular derivadas con tres puntos vecinos. "
            "Pero en ingeniería tenemos estructuras continuas completas, como una barra o un puente de longitud ele. "
            "El primer paso del método es discretizar: partir el dominio en ene intervalos iguales de tamaño hache, "
            "creando una fila ordenada de nodos."
        ),
    },
    {
        "id": "s2_dirichlet_funfact",
        "voice": COHOST_VOICE,
        "style": "funfact",
        "subtitle": "Dato curioso (Dirichlet, 1850): Sin fijar los bordes existen infinitas soluciones; las fronteras anclan el interior.",
        "narration": (
            "Y aquí entra un dato histórico clave: en mil ochocientos cincuenta, el matemático alemán Lejeune Dirichlet "
            "demostró que sin fijar los bordes, una ecuación diferencial tiene infinitas soluciones flotando en el aire. "
            "Las condiciones de frontera de Dirichlet, en los extremos ye sub... cero y ye sub... ene, "
            "son como los clavos que sujetan la cuerda de una guitarra: anclan de forma única todo el interior."
        ),
    },
    {
        "id": "s3_viga_1d",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Viga de Euler-Bernoulli: yᵢ₋₁ − 2yᵢ + yᵢ₊₁ = h² M(xᵢ)/(EI) forma una matriz tridiagonal exacta.",
        "narration": (
            "Veámoslo en acción sobre una viga biapoyada bajo carga distribuida. "
            "En cada nodo interior equis sub... í, aplicamos nuestra plantilla uno, menos dos, uno "
            "para igualar la curvatura con el momento flector dividido entre la rigidez e í. "
            "Eso ensambla un sistema tridiagonal que revela al instante cuánto se dobla cada punto del puente."
        ),
    },
    {
        "id": "s4_molecula_2d",
        "voice": COHOST_VOICE,
        "style": "explain",
        "subtitle": "Al pasar a 2D, cada nodo interior (i, j) conversa con 4 vecinos: Norte, Sur, Este y Oeste.",
        "narration": (
            "¿Y qué pasa cuando saltamos de una línea a una placa en dos dimensiones? "
            "Ahora cada nodo interior í coma jota ya no tiene dos vecinos, ¡sino cuatro: norte, sur, este y oeste! "
            "Al sumar la segunda derivada en equis más la segunda derivada en ye, "
            "nace la célebre molécula computacional en cruz de cinco puntos."
        ),
    },
    {
        "id": "s5_simetria_cruz",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "En malla cuadrada (Δx = Δy = h), el Laplaciano discreto asigna −4 al centro y +1 a cada vecino.",
        "narration": (
            "Si los pasos delta equis y delta ye son distintos, una razón geométrica erre pondera cada dirección. "
            "Pero cuando usamos una malla cuadrada uniforme, la molécula adquiere una simetría perfecta: "
            "peso menos cuatro en el nodo central y más uno en cada uno de sus cuatro vecinos cardinales."
        ),
    },
    {
        "id": "s6_endpoint",
        "voice": COHOST_VOICE,
        "style": "endpoint",
        "subtitle": "Endpoint Cápsula 2: Malla, Dirichlet, Viga 1D y Molécula 2D listos → Siguiente: Difusión de Calor 2D.",
        "narration": (
            "Cerramos el endpoint de la cápsula dos: aprendimos a discretizar dominios en mallas, "
            "anclar sus bordes con condiciones de Dirichlet, calcular la deflexión de una viga "
            "y construir la molécula en cruz de cinco puntos. "
            "En la cápsula tres calentaremos un borde a cien grados Celsius para ver cómo el calor se difunde solo por toda una placa."
        ),
    },
]

FORMULAS = {
    "eq_step_h":   '#set text(fill: rgb("#38bdf8"), size: 24pt, weight: "bold")\n$ h = Delta x = L / N $',
    "eq_beam":     '#set text(fill: rgb("#fbbf24"), size: 22pt)\n$ y_(i-1) - 2 y_i + y_(i+1) = (h^2 M(x_i)) / (E I) $',
    "eq_lap_gen":  '#set text(fill: rgb("#e2e8f0"), size: 20pt)\n$ u_(i+1,j) + u_(i-1,j) + r u_(i,j+1) + r u_(i,j-1) - 2(1+r) u_(i,j) $',
    "eq_lap_sq":   '#set text(fill: rgb("#34d399"), size: 23pt, weight: "bold")\n$ nabla^2 u_(i,j) approx (u_N + u_S + u_E + u_O - 4 u_(i,j)) / h^2 $',
    "lbl_y0":      '#set text(fill: rgb("#f87171"), size: 21pt, weight: "bold")\n$ y_0 = 0 $',
    "lbl_yn":      '#set text(fill: rgb("#f87171"), size: 21pt, weight: "bold")\n$ y_N = 0 $',
}


class Capsula02MallaVigaScene(Scene):
    def construct(self):
        setup_chalkboard(self)
        svg_dir = WORK_DIR / "svg"
        timings = json.loads((WORK_DIR / "timings.json").read_text(encoding="utf-8"))

        header = build_header(
            "2. Discretización, Fronteras de Dirichlet y Molécula 2D",
            "Cápsula 2 de 4",
            accent="#f59e0b",
        )
        hud = SubtitleHud(self)
        self.add(header)

        # ================= ESCENA 1: DISCRETIZACIÓN 1D =================
        d1 = timings[0]["duration"]
        hud.show(timings[0])

        bar_left = np.array([-5.60, 1.35, 0.0])
        bar_right = np.array([1.20, 1.35, 0.0])
        cont_bar = RoundedRectangle(
            corner_radius=0.06, width=6.80, height=0.34,
            fill_color="#334155", fill_opacity=0.95,
            stroke_color="#94a3b8", stroke_width=2.0,
        ).move_to(0.5 * (bar_left + bar_right))
        cont_lbl = Text("Dominio continuo [0, L]", font="Segoe UI", font_size=19, color="#cbd5e1").next_to(cont_bar, UP, buff=0.22)

        N = 6
        xs_1d = [bar_left[0] + k * (6.80 / N) for k in range(N + 1)]
        mesh_line = Line(bar_left, bar_right, color="#64748b", stroke_width=4.0)

        nodes_1d = VGroup()
        node_lbls = VGroup()
        for k, xv in enumerate(xs_1d):
            pt = np.array([xv, 1.35, 0.0])
            if k == 0 or k == N:
                nd = Square(side_length=0.24, fill_color="#ef4444", fill_opacity=1.0, stroke_color="#fecaca", stroke_width=2.0).move_to(pt)
            else:
                nd = Circle(radius=0.12, fill_color="#38bdf8", fill_opacity=1.0, stroke_color="#e0f2fe", stroke_width=2.0).move_to(pt)
            nodes_1d.add(nd)
            nl = Text(f"x{k}", font="Consolas", font_size=16, color="#fca5a5" if (k == 0 or k == N) else "#bae6fd").next_to(nd, DOWN, buff=0.16)
            node_lbls.add(nl)

        brace_h = BraceBetweenPoints(np.array([xs_1d[2], 1.60, 0]), np.array([xs_1d[3], 1.60, 0]), direction=UP, color="#38bdf8")
        eq_step = SVGMobject(str(svg_dir / "eq_step_h.svg")).scale_to_fit_height(0.58).move_to(np.array([4.30, 1.35, 0.0]))
        step_box = SurroundingRectangle(eq_step, color="#38bdf8", buff=0.18, corner_radius=0.10, stroke_width=2.0)

        legend_red = VGroup(
            Square(side_length=0.20, fill_color="#ef4444", fill_opacity=1.0, stroke_color="#fecaca", stroke_width=1.5),
            Text("Frontera Dirichlet (conocida)", font="Segoe UI", font_size=17, color="#fca5a5"),
        ).arrange(RIGHT, buff=0.14)
        legend_blue = VGroup(
            Circle(radius=0.10, fill_color="#38bdf8", fill_opacity=1.0, stroke_color="#e0f2fe", stroke_width=1.5),
            Text("Nodos interiores (incógnitas)", font="Segoe UI", font_size=17, color="#bae6fd"),
        ).arrange(RIGHT, buff=0.14)
        legend_grp = VGroup(legend_red, legend_blue).arrange(RIGHT, buff=0.55).move_to(np.array([-2.20, 0.32, 0.0]))

        t_used = 0.0
        self.play(FadeIn(cont_bar), FadeIn(cont_lbl), run_time=1.3)
        self.play(
            ReplacementTransform(cont_bar, mesh_line),
            FadeOut(cont_lbl),
            LaggedStart(*[FadeIn(n, scale=1.4) for n in nodes_1d], lag_ratio=0.08),
            LaggedStart(*[FadeIn(l) for l in node_lbls], lag_ratio=0.08),
            run_time=2.0,
        )
        self.play(FadeIn(brace_h), Write(eq_step), Create(step_box), FadeIn(legend_grp), run_time=1.8)
        t_used += 5.1
        if d1 > t_used:
            self.wait(d1 - t_used)

        # ================= ESCENA 2: FUN FACT DE DIRICHLET (1850) =================
        d2 = timings[1]["duration"]
        hud.show(timings[1])

        # Curvas flotantes sin fronteras vs. curva anclada abajo a la izquierda
        ghost_curves = VGroup(*[
            FunctionGraph(
                lambda x, shift_y=sy: shift_y - 0.55 * math.sin(math.pi * (x + 5.95) / 6.50),
                x_range=[-5.95, 0.55],
                color="#64748b",
                stroke_opacity=0.55,
                stroke_width=2.5,
            )
            for sy in [-0.75, -1.35, -1.95]
        ])
        anchored_curve = FunctionGraph(
            lambda x: -1.35 - 0.72 * math.sin(math.pi * (x + 5.95) / 6.50),
            x_range=[-5.95, 0.55],
            color="#34d399",
            stroke_width=4.0,
        )
        pin_l = Dot(np.array([-5.95, -1.35, 0.0]), radius=0.11, color="#ef4444")
        pin_r = Dot(np.array([0.55, -1.35, 0.0]), radius=0.11, color="#ef4444")
        lbl_y0 = SVGMobject(str(svg_dir / "lbl_y0.svg")).scale_to_fit_height(0.30).next_to(pin_l, UP, buff=0.12)
        lbl_yn = SVGMobject(str(svg_dir / "lbl_yn.svg")).scale_to_fit_height(0.30).next_to(pin_r, UP, buff=0.12)

        ff_dirichlet = build_funfact_card(
            "DATO CURIOSO • LEJEUNE DIRICHLET (1850)",
            "Los clavos que anclan la solución",
            [
                "Sin valores en los bordes, una ecuación",
                "diferencial admite infinitas curvas paralelas",
                "(diferentes constantes de integración).",
                "Fijar y₀ e y_N elimina toda ambigüedad.",
            ],
            width=4.95,
            accent="#fbbf24",
        ).move_to(np.array([4.05, -0.95, 0.0]))

        t_used = 0.0
        self.play(Create(ghost_curves), FadeIn(ff_dirichlet, shift=LEFT * 0.25), run_time=1.8)
        self.play(
            FadeIn(pin_l, scale=1.5), FadeIn(pin_r, scale=1.5),
            FadeIn(lbl_y0), FadeIn(lbl_yn),
            ReplacementTransform(ghost_curves, anchored_curve),
            run_time=2.0,
        )
        t_used += 3.8
        if d2 > t_used + 0.6:
            self.wait(d2 - t_used - 0.6)

        self.play(
            FadeOut(VGroup(mesh_line, nodes_1d, node_lbls, brace_h, eq_step, step_box, legend_grp, anchored_curve, pin_l, pin_r, lbl_y0, lbl_yn, ff_dirichlet)),
            run_time=0.6,
        )

        # ================= ESCENA 3: VIGA DE EULER-BERNOULLI 1D =================
        d3 = timings[2]["duration"]
        hud.show(timings[2])

        beam_y = 1.25
        bx0, bx1 = -5.85, 0.55
        b_len = bx1 - bx0
        beam_xs = [bx0 + k * (b_len / N) for k in range(N + 1)]

        # Apoyos triangulares de la viga
        sup_l = RegularPolygon(n=3, color="#ef4444", fill_color="#7f1d1d", fill_opacity=0.9).scale(0.24)
        sup_l.move_to(np.array([bx0, beam_y - 0.24, 0.0]))
        sup_r = RegularPolygon(n=3, color="#ef4444", fill_color="#7f1d1d", fill_opacity=0.9).scale(0.24)
        sup_r.move_to(np.array([bx1, beam_y - 0.24, 0.0]))

        # Flechas de carga uniforme q
        load_arrows = VGroup(*[
            Arrow(
                np.array([xv, beam_y + 0.95, 0.0]),
                np.array([xv, beam_y + 0.16, 0.0]),
                buff=0.0, stroke_width=2.8, color="#fbbf24", max_tip_length_to_length_ratio=0.28,
            )
            for xv in np.linspace(bx0 + 0.35, bx1 - 0.35, 9)
        ])
        load_top = Line(np.array([bx0 + 0.35, beam_y + 0.95, 0.0]), np.array([bx1 - 0.35, beam_y + 0.95, 0.0]), color="#fbbf24", stroke_width=2.4)
        load_lbl = Text("Carga uniforme distribuida q", font="Segoe UI", font_size=17, color="#fde68a").next_to(load_top, UP, buff=0.12)

        defl_tracker = ValueTracker(0.0)

        def beam_deflection(x_pos: float, amp: float) -> float:
            xi = (x_pos - bx0) / b_len
            # Perfil cuártico exacto normalizado de viga simplemente apoyada: xi - 2*xi^3 + xi^4 (máx = 5/16 en xi=0.5)
            shape = (16.0 / 5.0) * (xi - 2.0 * (xi**3) + (xi**4))
            return beam_y - amp * shape

        beam_curve = always_redraw(lambda: FunctionGraph(
            lambda x: beam_deflection(x, defl_tracker.get_value()),
            x_range=[bx0, bx1],
            color="#38bdf8",
            stroke_width=5.0,
        ))
        beam_nodes = always_redraw(lambda: VGroup(*[
            Dot(
                np.array([xv, beam_deflection(xv, defl_tracker.get_value()), 0.0]),
                radius=0.105 if (0 < k < N) else 0.115,
                color="#38bdf8" if (0 < k < N) else "#ef4444",
            )
            for k, xv in enumerate(beam_xs)
        ]))
        max_defl_lbl = always_redraw(lambda: Text(
            f"Flecha central y₃ = -{defl_tracker.get_value()*12.5:.1f} mm",
            font="Consolas", font_size=18, color="#7dd3fc",
        ).move_to(np.array([-2.65, -1.65, 0.0])))

        # Panel derecho: ecuación y matriz tridiagonal [1, -2, 1]
        right_card = RoundedRectangle(
            corner_radius=0.16, width=5.20, height=5.15,
            fill_color="#0f172a", fill_opacity=0.88,
            stroke_color="#1e3a8a", stroke_width=2.0,
        ).move_to(np.array([3.85, 0.10, 0.0]))
        eq_beam = SVGMobject(str(svg_dir / "eq_beam.svg")).scale_to_fit_width(4.65).move_to(right_card.get_top() + DOWN * 0.80)

        mat_title = Text("Matriz Tridiagonal [ 1, −2, 1 ]", font="Segoe UI", font_size=18, weight=BOLD, color="#93c5fd")
        mat_title.move_to(right_card.get_top() + DOWN * 1.75)

        mat_rows_str = [
            "[-2   1   0   0   0 ] [y₁]",
            "[ 1  -2   1   0   0 ] [y₂]",
            "[ 0   1  -2   1   0 ] [y₃]",
            "[ 0   0   1  -2   1 ] [y₄]",
            "[ 0   0   0   1  -2 ] [y₅]",
        ]
        mat_lines = VGroup(*[
            Text(s, font="Consolas", font_size=17, color="#fde047" if idx == 2 else "#cbd5e1")
            for idx, s in enumerate(mat_rows_str)
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(right_card.get_center() + DOWN * 0.65)

        self.add(beam_curve, beam_nodes, max_defl_lbl)
        t_used = 0.0
        self.play(FadeIn(sup_l), FadeIn(sup_r), Create(load_top), FadeIn(load_lbl), LaggedStart(*[GrowArrow(a) for a in load_arrows], lag_ratio=0.06), run_time=1.6)
        self.play(FadeIn(right_card), Write(eq_beam), FadeIn(mat_title), FadeIn(mat_lines), run_time=1.8)
        self.play(defl_tracker.animate.set_value(1.85), run_time=2.6, rate_func=smooth)
        t_used += 6.0
        if d3 > t_used + 0.6:
            self.wait(d3 - t_used - 0.6)

        self.remove(beam_curve, beam_nodes, max_defl_lbl)
        self.play(FadeOut(VGroup(sup_l, sup_r, load_top, load_lbl, load_arrows, right_card, eq_beam, mat_title, mat_lines)), run_time=0.6)

        # ================= ESCENA 4: MALLA 2D Y MOLÉCULA DE 5 PUNTOS =================
        d4 = timings[3]["duration"]
        hud.show(timings[3])

        grid_origin = np.array([-3.10, 0.12, 0.0])
        sp = 1.05
        grid_lines = VGroup()
        for idx in range(-2, 3):
            grid_lines.add(Line(grid_origin + np.array([idx * sp, -2 * sp, 0]), grid_origin + np.array([idx * sp, 2 * sp, 0]), color="#334155", stroke_width=2.0))
            grid_lines.add(Line(grid_origin + np.array([-2 * sp, idx * sp, 0]), grid_origin + np.array([2 * sp, idx * sp, 0]), color="#334155", stroke_width=2.0))

        grid_nodes = VGroup()
        for r_i in range(-2, 3):
            for c_i in range(-2, 3):
                pt = grid_origin + np.array([c_i * sp, r_i * sp, 0.0])
                is_border = abs(r_i) == 2 or abs(c_i) == 2
                if is_border:
                    nd = Square(side_length=0.20, fill_color="#ef4444", fill_opacity=0.95, stroke_color="#fecaca", stroke_width=1.5).move_to(pt)
                else:
                    nd = Circle(radius=0.11, fill_color="#38bdf8", fill_opacity=0.95, stroke_color="#e0f2fe", stroke_width=1.5).move_to(pt)
                grid_nodes.add(nd)

        # Brazos de la molécula computacional en el centro (0, 0)
        mol_arms = VGroup(
            Line(grid_origin, grid_origin + UP * sp, color="#fbbf24", stroke_width=6.0),
            Line(grid_origin, grid_origin + DOWN * sp, color="#fbbf24", stroke_width=6.0),
            Line(grid_origin, grid_origin + RIGHT * sp, color="#fbbf24", stroke_width=6.0),
            Line(grid_origin, grid_origin + LEFT * sp, color="#fbbf24", stroke_width=6.0),
        )

        def make_weight_node(pos, text_val, fill_c, stroke_c, radius=0.28):
            c = Circle(radius=radius, fill_color=fill_c, fill_opacity=1.0, stroke_color=stroke_c, stroke_width=2.6).move_to(pos)
            t = Text(text_val, font="Consolas", font_size=19, weight=BOLD, color="#f8fafc").move_to(pos)
            return VGroup(c, t)

        w_center = make_weight_node(grid_origin, "-4", "#b45309", "#fde047", radius=0.32)
        w_n = make_weight_node(grid_origin + UP * sp, "+1", "#065f46", "#34d399")
        w_s = make_weight_node(grid_origin + DOWN * sp, "+1", "#065f46", "#34d399")
        w_e = make_weight_node(grid_origin + RIGHT * sp, "+1", "#065f46", "#34d399")
        w_w = make_weight_node(grid_origin + LEFT * sp, "+1", "#065f46", "#34d399")

        dir_tags = VGroup(
            Text("Norte (i, j+1)", font="Segoe UI", font_size=15, color="#a7f3d0").next_to(w_n, UP, buff=0.10),
            Text("Sur (i, j-1)", font="Segoe UI", font_size=15, color="#a7f3d0").next_to(w_s, DOWN, buff=0.10),
            Text("Este", font="Segoe UI", font_size=15, color="#a7f3d0").next_to(w_e, RIGHT, buff=0.10),
            Text("Oeste", font="Segoe UI", font_size=15, color="#a7f3d0").next_to(w_w, LEFT, buff=0.10),
        )

        mol_panel = RoundedRectangle(
            corner_radius=0.16, width=5.55, height=4.85,
            fill_color="#0f172a", fill_opacity=0.88,
            stroke_color="#1e3a8a", stroke_width=2.0,
        ).move_to(np.array([3.65, 0.12, 0.0]))
        mol_title = Text("Molécula Computacional 2D", font="Segoe UI", font_size=21, weight=BOLD, color="#fde047")
        mol_title.move_to(mol_panel.get_top() + DOWN * 0.55)
        mol_sub = Text("Conecta cada nodo (i, j) con sus 4 vecinos", font="Segoe UI", font_size=16, color="#cbd5e1")
        mol_sub.next_to(mol_title, DOWN, buff=0.14)

        t_used = 0.0
        self.play(Create(grid_lines), LaggedStart(*[FadeIn(n, scale=1.2) for n in grid_nodes], lag_ratio=0.03), FadeIn(mol_panel), FadeIn(mol_title), FadeIn(mol_sub), run_time=2.0)
        self.play(Create(mol_arms), FadeIn(w_center, scale=1.3), FadeIn(w_n, scale=1.3), FadeIn(w_s, scale=1.3), FadeIn(w_e, scale=1.3), FadeIn(w_w, scale=1.3), FadeIn(dir_tags), run_time=2.0)
        t_used += 4.0
        if d4 > t_used:
            self.wait(d4 - t_used)

        # ================= ESCENA 5: ECUACIÓN GENERAL vs MALLA CUADRADA =================
        d5 = timings[4]["duration"]
        hud.show(timings[4])

        eq_gen = SVGMobject(str(svg_dir / "eq_lap_gen.svg")).scale_to_fit_width(5.05).move_to(mol_panel.get_center() + UP * 0.20)
        r_note = Text("Razón de aspecto:  r = (Δx / Δy)²", font="Consolas", font_size=16, color="#93c5fd").next_to(eq_gen, DOWN, buff=0.20)

        eq_sq = SVGMobject(str(svg_dir / "eq_lap_sq.svg")).scale_to_fit_width(4.95).move_to(mol_panel.get_bottom() + UP * 1.05)
        sq_box = SurroundingRectangle(eq_sq, color="#34d399", buff=0.12, corner_radius=0.09, stroke_width=2.2)

        t_used = 0.0
        self.play(Write(eq_gen), FadeIn(r_note), run_time=2.0)
        self.play(Write(eq_sq), Create(sq_box), Indicate(w_center, color="#fde047", scale_factor=1.15), run_time=2.2)
        t_used += 4.2
        if d5 > t_used + 0.6:
            self.wait(d5 - t_used - 0.6)

        self.play(
            FadeOut(VGroup(grid_lines, grid_nodes, mol_arms, w_center, w_n, w_s, w_e, w_w, dir_tags, mol_panel, mol_title, mol_sub, eq_gen, r_note, eq_sq, sq_box)),
            run_time=0.6,
        )

        # ================= ESCENA 6: ENDPOINT CÁPSULA 2 =================
        d6 = timings[5]["duration"]
        hud.show(timings[5])

        ep_card = build_endpoint_card(
            capsule_num=2,
            capsule_title="De los nodos aislados al sistema global en 1D y 2D",
            takeaways=[
                "Discretizar divide dominios continuos en mallas regulares con fronteras fijas de Dirichlet.",
                "En 1D, la plantilla [1, −2, 1] forma sistemas tridiagonales que resuelven vigas reales.",
                "En 2D, la Molécula en Cruz (+1, +1, −4, +1, +1) acopla cada nodo interior con sus 4 vecinos.",
            ],
            next_kicker="SIGUIENTE CÁPSULA (3 DE 4)  →  DIFUSIÓN DE CALOR 2D Y ECUACIÓN DE LAPLACE",
            next_description="¿Qué sucede al fijar un borde a 100 °C y dejar que cada nodo promedie a sus 4 vecinos iterativamente?",
            accent="#10b981",
        )
        self.play(FadeIn(ep_card, shift=UP * 0.20), run_time=1.4)
        if d6 > 1.4:
            self.wait(d6 - 1.4)
