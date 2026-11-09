# -*- coding: utf-8 -*-
"""
Cápsula 4 de 4: Electrostática 2D — Laplace vs. Poisson (±ρ), Campo Eléctrico y Puente al MEF
Salida: 04_electrostatica_poisson_y_campo_e.mp4
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

CAPSULE_NUM = 4
CAPSULE_SLUG = "c04_poisson_electro"
WORK_DIR = BASE_DIR / "_build_series" / CAPSULE_SLUG
OUTPUT_MP4 = BASE_DIR / "04_electrostatica_poisson_y_campo_e.mp4"
SCENE_CLASS = "Capsula04ElectrostaticaScene"

SEGMENTS = [
    {
        "id": "s1_feynman_analogia",
        "voice": COHOST_VOICE,
        "style": "funfact",
        "subtitle": "Dato curioso (Richard Feynman): 'Las mismas ecuaciones tienen las mismas soluciones' → Calor (∇²T=0) ≡ Voltaje sin carga (∇²V=0).",
        "narration": (
            "El premio Nobel Richard Feynman solía repetir una frase genial: "
            "las mismas ecuaciones tienen exactamente las mismas soluciones. "
            "Si tomamos una región eléctrica vacía, sin cargas internas, el voltaje obedece la misma ecuación de Laplace que vimos en calor. "
            "¡Cambias grados Celsius por voltios y el mapa numérico resulta idéntico!"
        ),
    },
    {
        "id": "s2_poisson_fuentes",
        "voice": DEFAULT_VOICE,
        "style": "math",
        "subtitle": "Ecuación de Poisson (∇²V = −ρ/ε₀): cada nodo promedia a sus 4 vecinos más un término fuente local ρ.",
        "narration": (
            "Todo cambia cuando colocamos cargas libres dentro del dominio. "
            "Aquí entra la ecuación de Poisson: nabla cuadrado de ve es igual a menos ro entre épsilon sub... cero. "
            "Al despejar ve sub... í coma jota, cada nodo sigue promediando a sus cuatro vecinos, "
            "pero ahora suma un empuje extra proporcional a la carga local ro."
        ),
    },
    {
        "id": "s3_picos_y_valles",
        "voice": DEFAULT_VOICE,
        "style": "explain",
        "subtitle": "+ρ arrastra a los vecinos creando un pico rojo (+V); −ρ hunde la malla creando un valle azul (−V).",
        "narration": (
            "Mira cómo se propaga su efecto: aunque inyectamos la carga positiva en un solo nodo, "
            "al promediar iterativamente arrastra hacia arriba a sus vecinos, levantando una montaña roja de voltaje positivo. "
            "Al mismo tiempo, la carga negativa hunde una depresión azul de voltaje negativo, "
            "rompiendo la llanura plana de Laplace."
        ),
    },
    {
        "id": "s4_campo_electrico",
        "voice": COHOST_VOICE,
        "style": "explain",
        "subtitle": "Campo Eléctrico E = −∇V: apunta siempre 'cuesta abajo' en el voltaje (sale de +ρ y entra en −ρ).",
        "narration": (
            "Y una vez conocido el voltaje en cada nodo, aplicamos diferencias centrales una vez más "
            "para obtener las flechas del campo eléctrico: e igual a menos el gradiente de ve. "
            "El signo menos significa que el campo apunta siempre cuesta abajo en el potencial: "
            "naciendo de las montañas rojas positivas y cayendo hacia los valles azules negativos."
        ),
    },
    {
        "id": "s5_puente_mef",
        "voice": DEFAULT_VOICE,
        "style": "explain",
        "subtitle": "Límite geométrico del MDF: en bordes curvos aparece el 'efecto escalera' → motivación del Método de Elementos Finitos (MEF).",
        "narration": (
            "Con esto dominamos las diferencias finitas, pero observa su talón de Aquiles: "
            "¿qué pasa si la pieza real tiene bordes curvos o agujeros circulares? "
            "Una cuadrícula rígida sufre el llamado efecto escalera en la frontera. "
            "Superar esa barrera geométrica usando triángulos adaptables es precisamente la misión del Método de Elementos Finitos."
        ),
    },
    {
        "id": "s6_endpoint_final",
        "voice": COHOST_VOICE,
        "style": "endpoint",
        "subtitle": "Gran Endpoint de la Serie: Derivadas → Mallas y Vigas → Calor (Laplace) → Electrostática (Poisson) → Listos para MEF.",
        "narration": (
            "¡Y así llegamos al gran endpoint de nuestra serie! "
            "Partimos de una simple pendiente entre tres puntos, discretizamos vigas en una dimensión, "
            "relajamos placas térmicas con Laplace, simulamos cargas y campos eléctricos con Poisson, "
            "y descubrimos por qué las geometrías curvas nos impulsan hacia el Método de Elementos Finitos. "
            "¡Nos vemos en el siguiente módulo!"
        ),
    },
]

FORMULAS = {
    "eq_iso":      '#set text(fill: rgb("#fde047"), size: 22pt, weight: "bold")\n$ nabla^2 T = 0 quad <==> quad nabla^2 V = 0 quad (rho = 0) $',
    "eq_poisson":  '#set text(fill: rgb("#f87171"), size: 25pt, weight: "bold")\n$ nabla^2 V = - rho / epsilon_0 $',
    "eq_v_upd":    '#set text(fill: rgb("#e2e8f0"), size: 20pt)\n$ V_(i,j) = (V_N + V_S + V_E + V_O + (h^2 rho_(i,j)) / epsilon_0) / 4 $',
    "eq_efield":   '#set text(fill: rgb("#38bdf8"), size: 22pt, weight: "bold")\n$ arrow(E) = - nabla V = ( - (partial V)/(partial x) , - (partial V)/(partial y) ) $',
}


def volt_to_hex(v: float, vmax: float = 1.0) -> str:
    """Paleta divergente electrostática: −V azul intenso -> 0 pizarra oscura -> +V rojo intenso."""
    u = max(-1.0, min(1.0, v / (vmax + 1e-9)))
    if u >= 0:
        r = int(round(18 + u * (220 - 18)))
        g = int(round(27 + u * (38 - 27)))
        b = int(round(46 + u * (38 - 46)))
    else:
        a = -u
        r = int(round(18 + a * (29 - 18)))
        g = int(round(27 + a * (78 - 27)))
        b = int(round(46 + a * (216 - 46)))
    return f"#{r:02x}{g:02x}{b:02x}"


def solve_dipole_poisson(n: int = 9, sweeps: int = 80):
    """Resuelve ∇²V = -ρ/ε en malla n×n con bordes a 0 V, +ρ en (2, 2) y −ρ en (6, 6)."""
    V = np.zeros((n, n), dtype=float)
    src = np.zeros((n, n), dtype=float)
    src[2, 2] = +4.0
    src[n - 3, n - 3] = -4.0
    for _ in range(sweeps):
        for r in range(1, n - 1):
            for c in range(1, n - 1):
                V[r, c] = 0.25 * (V[r - 1, c] + V[r + 1, c] + V[r, c - 1] + V[r, c + 1] + src[r, c])
    # Campo eléctrico E = -grad(V) en coordenadas de pantalla (x derecha = col+, y arriba = fila-)
    Ex = np.zeros_like(V)
    Ey = np.zeros_like(V)
    for r in range(1, n - 1):
        for c in range(1, n - 1):
            Ex[r, c] = -(V[r, c + 1] - V[r, c - 1]) * 0.5
            Ey[r, c] = -(V[r - 1, c] - V[r + 1, c]) * 0.5
    return V, Ex, Ey


class Capsula04ElectrostaticaScene(Scene):
    def construct(self):
        setup_chalkboard(self)
        svg_dir = WORK_DIR / "svg"
        timings = json.loads((WORK_DIR / "timings.json").read_text(encoding="utf-8"))

        header = build_header(
            "4. Electrostática 2D: Poisson (±ρ), Campo E y Puente al MEF",
            "Cápsula 4 de 4",
            accent="#c084fc",
        )
        hud = SubtitleHud(self)
        self.add(header)

        # ================= ESCENA 1: ISOMORFISMO DE FEYNMAN (CALOR ≡ VOLTAJE SIN CARGAS) =================
        d1 = timings[0]["duration"]
        hud.show(timings[0])

        def mini_laplace_box(center_pos, title_str, top_unit):
            # Mini placa 4x4 ilustrativa de Laplace
            vals = [
                [100, 100, 100, 100],
                [0,   43,  43,  0],
                [0,   14,  14,  0],
                [0,   0,   0,   0],
            ]
            sz = 0.50
            cells = VGroup()
            for r in range(4):
                for c in range(4):
                    v = vals[r][c] / 100.0
                    col = f"#{int(18+202*v):02x}{int(35+30*(1-abs(2*v-1))):02x}{int(130*(1-v)+38*v):02x}"
                    sq = RoundedRectangle(corner_radius=0.05, width=sz - 0.04, height=sz - 0.04, fill_color=col, fill_opacity=0.95, stroke_color="#cbd5e1", stroke_width=1.2)
                    sq.move_to(center_pos + np.array([(c - 1.5) * sz, (1.5 - r) * sz, 0.0]))
                    cells.add(sq)
            t_lbl = Text(title_str, font="Segoe UI", font_size=16, weight=BOLD, color="#f8fafc").next_to(cells, UP, buff=0.14)
            u_lbl = Text(top_unit, font="Consolas", font_size=14, color="#fde047").next_to(cells, DOWN, buff=0.12)
            return VGroup(cells, t_lbl, u_lbl)

        box_heat = mini_laplace_box(np.array([-4.65, 0.45, 0.0]), "Placa de Calor", "Borde sup: 100 °C")
        box_volt = mini_laplace_box(np.array([-1.65, 0.45, 0.0]), "Voltaje (ρ = 0)", "Electrodo: 100 V")
        iso_sym = Text("≡", font="Segoe UI", font_size=40, weight=BOLD, color="#fde047").move_to(np.array([-3.15, 0.45, 0.0]))
        eq_iso = SVGMobject(str(svg_dir / "eq_iso.svg")).scale_to_fit_width(5.15).move_to(np.array([-3.15, -1.65, 0.0]))

        ff_feynman = build_funfact_card(
            "DATO CURIOSO • RICHARD FEYNMAN",
            "Isomorfismo físico-matemático",
            [
                "\"Las mismas ecuaciones tienen las mismas",
                "soluciones.\" Sin cargas libres (ρ = 0),",
                "el potencial eléctrico V se distribuye",
                "exactamente igual que la temperatura T.",
            ],
            width=5.45,
            accent="#fbbf24",
        ).move_to(np.array([3.50, 0.15, 0.0]))

        t_used = 0.0
        self.play(FadeIn(box_heat), FadeIn(iso_sym), FadeIn(box_volt), run_time=1.8)
        self.play(Write(eq_iso), FadeIn(ff_feynman, shift=LEFT * 0.25), run_time=1.8)
        t_used += 3.6
        if d1 > t_used + 0.6:
            self.wait(d1 - t_used - 0.6)
        self.play(FadeOut(VGroup(box_heat, iso_sym, box_volt, eq_iso, ff_feynman)), run_time=0.6)

        # ================= ESCENA 2: ECUACIÓN DE POISSON E INYECCIÓN DE ±ρ =================
        d2 = timings[1]["duration"]
        hud.show(timings[1])

        N_grid = 9
        V_dip, Ex_dip, Ey_dip = solve_dipole_poisson(N_grid, sweeps=90)
        vmax = float(np.max(np.abs(V_dip)))

        grid_center = np.array([-3.30, 0.08, 0.0])
        csz = 0.56

        def make_electro_grid(V_mat: np.ndarray):
            grp = VGroup()
            for r in range(N_grid):
                for c in range(N_grid):
                    pos = grid_center + np.array([(c - (N_grid - 1) / 2.0) * csz, ((N_grid - 1) / 2.0 - r) * csz, 0.0])
                    sq = Square(
                        side_length=csz - 0.03,
                        fill_color=volt_to_hex(V_mat[r, c], vmax),
                        fill_opacity=0.96,
                        stroke_color="#334155",
                        stroke_width=1.0,
                    ).move_to(pos)
                    grp.add(sq)
            return grp

        flat_grid = make_electro_grid(np.zeros_like(V_dip))
        pos_plus = grid_center + np.array([(2 - 4) * csz, (4 - 2) * csz, 0.0])
        pos_minus = grid_center + np.array([(6 - 4) * csz, (4 - 6) * csz, 0.0])

        charge_plus = VGroup(
            Circle(radius=0.22, fill_color="#dc2626", fill_opacity=1.0, stroke_color="#fef08a", stroke_width=2.5),
            Text("+ρ", font="Segoe UI", font_size=15, weight=BOLD, color="#ffffff"),
        ).move_to(pos_plus).set_z_index(10)
        charge_plus[1].move_to(charge_plus[0].get_center())

        charge_minus = VGroup(
            Circle(radius=0.22, fill_color="#1d4ed8", fill_opacity=1.0, stroke_color="#bae6fd", stroke_width=2.5),
            Text("−ρ", font="Segoe UI", font_size=15, weight=BOLD, color="#ffffff"),
        ).move_to(pos_minus).set_z_index(10)
        charge_minus[1].move_to(charge_minus[0].get_center())

        grid_caption = Text("Fronteras conectadas a tierra (0 V)", font="Segoe UI", font_size=15, color="#94a3b8").next_to(flat_grid, DOWN, buff=0.14)

        right_panel = RoundedRectangle(
            corner_radius=0.16, width=5.65, height=5.20,
            fill_color="#0f172a", fill_opacity=0.88,
            stroke_color="#1e3a8a", stroke_width=2.0,
        ).move_to(np.array([3.45, 0.08, 0.0]))

        eq_poisson = SVGMobject(str(svg_dir / "eq_poisson.svg")).scale_to_fit_height(0.68).move_to(right_panel.get_top() + DOWN * 0.85)
        eq_v_upd = SVGMobject(str(svg_dir / "eq_v_upd.svg")).scale_to_fit_width(5.10).move_to(right_panel.get_top() + DOWN * 2.05)
        upd_box = SurroundingRectangle(eq_v_upd, color="#f87171", buff=0.12, corner_radius=0.09, stroke_width=2.0)

        t_used = 0.0
        self.play(FadeIn(flat_grid), FadeIn(grid_caption), FadeIn(right_panel), run_time=1.4)
        self.play(Write(eq_poisson), FadeIn(charge_plus, scale=1.5), FadeIn(charge_minus, scale=1.5), run_time=1.8)
        self.play(Write(eq_v_upd), Create(upd_box), run_time=1.8)
        t_used += 5.0
        if d2 > t_used:
            self.wait(d2 - t_used)

        # ================= ESCENA 3: PROPAGACIÓN EN MONTAÑA ROJA (+V) Y VALLE AZUL (−V) =================
        d3 = timings[2]["duration"]
        hud.show(timings[2])

        dipole_grid = make_electro_grid(V_dip)

        # Perfil 1D diagonal mostrando pico +V y valle -V dentro de la mitad inferior del panel derecho
        prof_axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-1.2, 1.2, 1],
            x_length=4.55,
            y_length=1.85,
            axis_config={"color": "#64748b", "stroke_width": 1.8, "include_ticks": False, "include_tip": False},
        ).move_to(right_panel.get_bottom() + UP * 1.35)
        prof_zero = DashedLine(prof_axes.c2p(-3, 0), prof_axes.c2p(3, 0), color="#475569", stroke_width=1.6)
        prof_curve = prof_axes.plot(
            lambda x: 0.98 * math.exp(-((x + 1.25) ** 2) / 0.65) - 0.98 * math.exp(-((x - 1.25) ** 2) / 0.65),
            x_range=[-2.9, 2.9],
            color="#c084fc",
            stroke_width=3.8,
        )
        lbl_peak = Text("Pico +V (+ρ)", font="Segoe UI", font_size=14, weight=BOLD, color="#fca5a5").next_to(prof_axes.c2p(-1.25, 0.98), UP, buff=0.06)
        lbl_valley = Text("Valle −V (−ρ)", font="Segoe UI", font_size=14, weight=BOLD, color="#93c5fd").next_to(prof_axes.c2p(1.25, -0.98), DOWN, buff=0.06)

        t_used = 0.0
        self.play(Transform(flat_grid, dipole_grid), run_time=2.2)
        self.play(Create(prof_axes), Create(prof_zero), Create(prof_curve), FadeIn(lbl_peak), FadeIn(lbl_valley), run_time=2.2)
        t_used += 4.4
        if d3 > t_used:
            self.wait(d3 - t_used)

        # ================= ESCENA 4: VECTOR CAMPO ELÉCTRICO E = -grad(V) =================
        d4 = timings[3]["duration"]
        hud.show(timings[3])

        e_arrows = VGroup()
        for r in range(1, N_grid - 1):
            for c in range(1, N_grid - 1):
                if (r == 2 and c == 2) or (r == 6 and c == 6):
                    continue
                ex, ey = Ex_dip[r, c], Ey_dip[r, c]
                mag = math.hypot(ex, ey)
                if mag < 1e-3:
                    continue
                ux, uy = ex / mag, ey / mag
                length = min(0.42, 0.16 + 0.34 * (mag / (vmax * 0.65)))
                pos = grid_center + np.array([(c - 4) * csz, (4 - r) * csz, 0.0])
                vec = np.array([ux * length, uy * length, 0.0])
                arr = Arrow(
                    pos - 0.5 * vec,
                    pos + 0.5 * vec,
                    buff=0.0,
                    stroke_width=2.8,
                    color="#fde047",
                    max_tip_length_to_length_ratio=0.35,
                )
                e_arrows.add(arr)

        eq_efield = SVGMobject(str(svg_dir / "eq_efield.svg")).scale_to_fit_width(4.85).move_to(right_panel.get_bottom() + UP * 1.45)
        ef_box = SurroundingRectangle(eq_efield, color="#38bdf8", buff=0.14, corner_radius=0.10, stroke_width=2.2)
        ef_note = Text("Las flechas bajan del pico rojo (+V) al valle azul (−V)", font="Segoe UI", font_size=15, color="#fde68a").next_to(ef_box, DOWN, buff=0.18)

        t_used = 0.0
        self.play(
            FadeOut(VGroup(prof_axes, prof_zero, prof_curve, lbl_peak, lbl_valley)),
            Write(eq_efield), Create(ef_box), FadeIn(ef_note),
            LaggedStart(*[GrowArrow(a) for a in e_arrows], lag_ratio=0.02),
            run_time=2.8,
        )
        self.bring_to_front(charge_plus, charge_minus)
        t_used += 2.8
        if d4 > t_used + 0.6:
            self.wait(d4 - t_used - 0.6)

        self.play(
            FadeOut(VGroup(flat_grid, charge_plus, charge_minus, grid_caption, e_arrows, right_panel, eq_poisson, eq_v_upd, upd_box, eq_efield, ef_box, ef_note)),
            run_time=0.6,
        )

        # ================= ESCENA 5: LÍMITE GEOMÉTRICO DEL MDF Y PUENTE AL MEF =================
        d5 = timings[4]["duration"]
        hud.show(timings[4])

        # Izquierda: Círculo aproximado por cuadrícula escalonada MDF
        c_left = np.array([-3.25, 0.18, 0.0])
        true_circle_l = Circle(radius=1.75, color="#94a3b8", stroke_width=2.2).move_to(c_left)
        stair_cells = VGroup()
        gs = 0.42
        for ix in range(-4, 5):
            for iy in range(-4, 5):
                if ix * ix * gs * gs + iy * iy * gs * gs <= 1.72 * 1.72:
                    sq = Square(side_length=gs, fill_color="#7c2d12", fill_opacity=0.62, stroke_color="#fb923c", stroke_width=1.6)
                    sq.move_to(c_left + np.array([ix * gs, iy * gs, 0.0]))
                    stair_cells.add(sq)
        lbl_mdf_lim = Text("Malla Rectangular MDF: 'Efecto escalera'", font="Segoe UI", font_size=18, weight=BOLD, color="#fdba74").next_to(true_circle_l, DOWN, buff=0.28)

        # Derecha: Malla triangular no estructurada MEF adaptada al círculo
        c_right = np.array([3.25, 0.18, 0.0])
        true_circle_r = Circle(radius=1.75, color="#34d399", stroke_width=3.0).move_to(c_right)
        n_outer = 12
        n_inner = 6
        pts_o = [c_right + np.array([1.75 * math.cos(2 * math.pi * k / n_outer), 1.75 * math.sin(2 * math.pi * k / n_outer), 0.0]) for k in range(n_outer)]
        pts_i = [c_right + np.array([0.88 * math.cos(2 * math.pi * k / n_inner + 0.25), 0.88 * math.sin(2 * math.pi * k / n_inner + 0.25), 0.0]) for k in range(n_inner)]

        fem_edges = VGroup()
        # Triángulos interiores al centro
        for k in range(n_inner):
            fem_edges.add(Polygon(c_right, pts_i[k], pts_i[(k + 1) % n_inner], fill_color="#064e3b", fill_opacity=0.55, stroke_color="#34d399", stroke_width=1.8))
        # Anillo exterior de triángulos
        for k in range(n_outer):
            p1 = pts_o[k]
            p2 = pts_o[(k + 1) % n_outer]
            pi1 = pts_i[(k // 2) % n_inner]
            fem_edges.add(Polygon(p1, p2, pi1, fill_color="#065f46", fill_opacity=0.50, stroke_color="#34d399", stroke_width=1.8))
            if k % 2 == 1:
                pi2 = pts_i[((k // 2) + 1) % n_inner]
                fem_edges.add(Polygon(p2, pi2, pi1, fill_color="#047857", fill_opacity=0.48, stroke_color="#34d399", stroke_width=1.8))

        fem_nodes = VGroup(*[Dot(p, radius=0.055, color="#a7f3d0") for p in ([c_right] + pts_i + pts_o)])
        lbl_mef_ok = Text("Malla Triangular MEF: Frontera curva exacta", font="Segoe UI", font_size=18, weight=BOLD, color="#6ee7b7").next_to(true_circle_r, DOWN, buff=0.28)
        vs_arrow = Arrow(np.array([-0.95, 0.18, 0.0]), np.array([0.95, 0.18, 0.0]), color="#38bdf8", stroke_width=4.0)

        t_used = 0.0
        self.play(Create(true_circle_l), FadeIn(stair_cells), FadeIn(lbl_mdf_lim), run_time=1.8)
        self.play(GrowArrow(vs_arrow), Create(fem_edges), Create(true_circle_r), FadeIn(fem_nodes), FadeIn(lbl_mef_ok), run_time=2.2)
        t_used += 4.0
        if d5 > t_used + 0.6:
            self.wait(d5 - t_used - 0.6)

        self.play(FadeOut(VGroup(true_circle_l, stair_cells, lbl_mdf_lim, vs_arrow, fem_edges, true_circle_r, fem_nodes, lbl_mef_ok)), run_time=0.6)

        # ================= ESCENA 6: GRAN ENDPOINT FINAL DE LA SERIE =================
        d6 = timings[5]["duration"]
        hud.show(timings[5])

        ep_card = build_endpoint_card(
            capsule_num=4,
            capsule_title="Síntesis del Módulo de Diferencias Finitas y Puente al MEF",
            takeaways=[
                "Sin cargas (ρ = 0), el potencial V obedece Laplace igual que una placa térmica estacionaria.",
                "Con Poisson (∇²V = −ρ/ε₀), +ρ crea montañas (+V), −ρ crea valles (−V) y E = −∇V baja entre ellos.",
                "Las fronteras curvas revelan el 'efecto escalera' del MDF y motivan los triángulos del MEF.",
            ],
            next_kicker="SERIE COMPLETADA (4 DE 4)  →  SIGUIENTE FRONTERA: MÉTODO DE ELEMENTOS FINITOS",
            next_description="Ya dominas la intuición discreta, mallas, condiciones de Dirichlet y sistemas nodales. ¡Bienvenido al MEF!",
            accent="#c084fc",
        )
        self.play(FadeIn(ep_card, shift=UP * 0.20), run_time=1.4)
        if d6 > 1.4:
            self.wait(d6 - 1.4)
