# -*- coding: utf-8 -*-
"""
Componentes visuales reutilizables en Manim para las 4 cápsulas del Método de Diferencias Finitas.
Garantiza zonas seguras sin traslapes:
  - Cabecera superior: y en [3.16, 3.85]
  - Escenario principal seguro: x en [-6.55, 6.55], y en [-2.98, 3.00]
  - Barra inferior de subtítulos con indicador de locutor: y en [-3.86, -3.20]
"""

from manim import *
import numpy as np

BG_COLOR = "#090d16"
PANEL_BG = "#0f172a"


def setup_chalkboard(scene: Scene):
    """Inicializa el fondo oscuro y la cuadrícula sutil estilo 3Blue1Brown."""
    scene.camera.background_color = BG_COLOR
    bg_plane = NumberPlane(
        x_range=[-8, 8, 1],
        y_range=[-5, 5, 1],
        background_line_style={
            "stroke_color": "#1e293b",
            "stroke_width": 1.0,
            "stroke_opacity": 0.34,
        },
        axis_config={"stroke_opacity": 0},
    )
    scene.add(bg_plane)
    return bg_plane


def build_header(title_str: str, capsule_label: str, accent: str = "#3b82f6") -> VGroup:
    """Construye la cabecera estilo Khan Academy + píldora de serie a la derecha sin colisión."""
    pill_txt = Text(capsule_label, font="Segoe UI", font_size=15, weight=BOLD, color="#e2e8f0")
    pill_bg = RoundedRectangle(
        corner_radius=0.15,
        width=pill_txt.width + 0.42,
        height=0.38,
        fill_color="#1e293b",
        fill_opacity=0.95,
        stroke_color=accent,
        stroke_width=1.8,
    )
    pill = VGroup(pill_bg, pill_txt)
    pill_txt.move_to(pill_bg.get_center())
    pill.move_to(np.array([6.55 - pill.width / 2.0, 3.52, 0.0]))

    header_txt = Text(
        title_str,
        font="Segoe UI",
        font_size=23,
        weight=BOLD,
        color="#f8fafc",
    )
    max_title_w = (6.55 - pill.width - 0.45) - (-6.55)
    if header_txt.width > max_title_w:
        header_txt.scale_to_fit_width(max_title_w)
    header_txt.move_to(np.array([-6.55 + header_txt.width / 2.0, 3.52, 0.0]))

    underline = Line(
        np.array([-6.58, 3.16, 0.0]),
        np.array([6.58, 3.16, 0.0]),
        color=accent,
        stroke_width=2.4,
    )
    return VGroup(header_txt, pill, underline)


class SubtitleHud:
    """Barra inferior fija con etiqueta dinámica de locutor (Gonzalo / Salomé) y subtítulo auto-ajustado."""

    def __init__(self, scene: Scene):
        self.scene = scene
        self.box = RoundedRectangle(
            corner_radius=0.12,
            width=13.16,
            height=0.64,
            fill_color="#0f172a",
            fill_opacity=0.94,
            stroke_color="#334155",
            stroke_width=1.5,
        ).move_to(np.array([0.0, -3.54, 0.0]))
        self.scene.add(self.box)
        self.current_group = None

    def show(self, timing_entry: dict):
        if self.current_group is not None:
            self.scene.remove(self.current_group)

        speaker = timing_entry.get("speaker", "Gonzalo")
        style = timing_entry.get("style", "explain")
        txt = timing_entry.get("subtitle", "")

        if speaker == "Salomé":
            if style == "funfact":
                sp_fill, sp_stroke, sp_col = "#451a03", "#fbbf24", "#fde68a"
            elif style == "endpoint":
                sp_fill, sp_stroke, sp_col = "#064e3b", "#34d399", "#a7f3d0"
            else:
                sp_fill, sp_stroke, sp_col = "#3b0764", "#c084fc", "#e9d5ff"
        else:
            sp_fill, sp_stroke, sp_col = "#082f49", "#38bdf8", "#bae6fd"

        badge_bg = RoundedRectangle(
            corner_radius=0.09,
            width=1.32,
            height=0.42,
            fill_color=sp_fill,
            fill_opacity=0.95,
            stroke_color=sp_stroke,
            stroke_width=1.6,
        ).move_to(self.box.get_left() + RIGHT * 0.80)
        badge_txt = Text(speaker, font="Segoe UI", font_size=15, weight=BOLD, color=sp_col)
        badge_txt.move_to(badge_bg.get_center())

        sub_txt = Text(txt, font="Segoe UI", font_size=18, color="#f1f5f9")
        max_w = 11.25
        if sub_txt.width > max_w:
            sub_txt.scale_to_fit_width(max_w)
        text_center_x = (badge_bg.get_right()[0] + 0.22 + self.box.get_right()[0] - 0.20) / 2.0
        sub_txt.move_to(np.array([text_center_x, self.box.get_center()[1], 0.0]))

        self.current_group = VGroup(badge_bg, badge_txt, sub_txt)
        self.scene.add(self.current_group)


def build_funfact_card(kicker: str, title: str, lines: list[str], width: float = 5.45, accent: str = "#fbbf24") -> VGroup:
    """Crea una tarjeta visual atractiva para Datos Curiosos / Contexto Histórico."""
    k_txt = Text(kicker, font="Segoe UI", font_size=15, weight=BOLD, color=accent)
    t_txt = Text(title, font="Segoe UI", font_size=21, weight=BOLD, color="#f8fafc")
    if t_txt.width > width - 0.55:
        t_txt.scale_to_fit_width(width - 0.55)

    body_items = []
    for ln in lines:
        bt = Text(ln, font="Segoe UI", font_size=16, color="#cbd5e1")
        if bt.width > width - 0.55:
            bt.scale_to_fit_width(width - 0.55)
        body_items.append(bt)
    body_grp = VGroup(*body_items).arrange(DOWN, aligned_edge=LEFT, buff=0.12)

    inner = VGroup(k_txt, t_txt, body_grp).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    card_bg = RoundedRectangle(
        corner_radius=0.16,
        width=width,
        height=inner.height + 0.52,
        fill_color="#17130a" if accent == "#fbbf24" else "#0f172a",
        fill_opacity=0.92,
        stroke_color=accent,
        stroke_width=2.2,
    )
    inner.move_to(card_bg.get_center())
    return VGroup(card_bg, inner)


def build_endpoint_card(
    capsule_num: int,
    capsule_title: str,
    takeaways: list[str],
    next_kicker: str,
    next_description: str,
    accent: str = "#10b981",
) -> VGroup:
    """
    Construye la pantalla final de cierre ('Endpoint') para que cada cápsula tenga una conclusión
    explícita, estructurada y conectada con el siguiente tema de la serie.
    """
    outer = RoundedRectangle(
        corner_radius=0.20,
        width=12.40,
        height=5.55,
        fill_color="#0b1322",
        fill_opacity=0.96,
        stroke_color=accent,
        stroke_width=2.6,
    ).move_to(np.array([0.0, 0.04, 0.0]))

    badge_txt = Text(
        f"ENDPOINT • LO QUE LOGRAMOS EN LA CÁPSULA {capsule_num}",
        font="Segoe UI",
        font_size=16,
        weight=BOLD,
        color="#052e16" if accent == "#10b981" else "#0f172a",
    )
    badge_bg = RoundedRectangle(
        corner_radius=0.10,
        width=badge_txt.width + 0.45,
        height=0.38,
        fill_color=accent,
        fill_opacity=1.0,
        stroke_width=0,
    )
    badge_txt.move_to(badge_bg.get_center())
    badge = VGroup(badge_bg, badge_txt)
    badge.move_to(outer.get_top() + DOWN * 0.44 + LEFT * (outer.width / 2.0 - badge.width / 2.0 - 0.45))

    title = Text(capsule_title, font="Segoe UI", font_size=24, weight=BOLD, color="#f8fafc")
    if title.width > 11.4:
        title.scale_to_fit_width(11.4)
    title.next_to(badge, DOWN, aligned_edge=LEFT, buff=0.20)

    rows = []
    for idx, item in enumerate(takeaways, start=1):
        num_circle = Circle(radius=0.19, fill_color="#1e293b", fill_opacity=1.0, stroke_color=accent, stroke_width=2.0)
        num_lbl = Text(str(idx), font="Segoe UI", font_size=16, weight=BOLD, color=accent).move_to(num_circle.get_center())
        bullet = VGroup(num_circle, num_lbl)

        row_txt = Text(item, font="Segoe UI", font_size=18, color="#e2e8f0")
        if row_txt.width > 10.6:
            row_txt.scale_to_fit_width(10.6)
        row_grp = VGroup(bullet, row_txt).arrange(RIGHT, buff=0.22)
        rows.append(row_grp)

    rows_vgroup = VGroup(*rows).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
    rows_vgroup.next_to(title, DOWN, aligned_edge=LEFT, buff=0.30)

    next_box = RoundedRectangle(
        corner_radius=0.14,
        width=11.55,
        height=1.08,
        fill_color="#111c33",
        fill_opacity=0.98,
        stroke_color="#38bdf8",
        stroke_width=2.0,
    ).move_to(outer.get_bottom() + UP * 0.74)

    nk = Text(next_kicker, font="Segoe UI", font_size=15, weight=BOLD, color="#38bdf8")
    nd = Text(next_description, font="Segoe UI", font_size=18, color="#f8fafc")
    if nd.width > 10.9:
        nd.scale_to_fit_width(10.9)
    n_inner = VGroup(nk, nd).arrange(DOWN, aligned_edge=LEFT, buff=0.10)
    n_inner.move_to(next_box.get_center()).align_to(next_box.get_left() + RIGHT * 0.30, LEFT)

    return VGroup(outer, badge, title, rows_vgroup, VGroup(next_box, n_inner))
