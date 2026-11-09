"""
Generador del archivo Excel recreando exactamente el video:
"Simulando difusión de calor en EXCEL!!!" (Termofluidos TV - https://www.youtube.com/watch?v=NdxW6B0N9Wg)

Características incluidas:
1. Hoja 1 ("Caso 1 (0 y 100 C)"):
   - Placa cuadrada de 100 mm x 100 mm con paso dx = dy = 5 mm (21 x 21 nodos).
   - Coordenadas X (0 a 100 mm) en C9:W9 y coordenadas Y (0 a 100 mm) en B10:B30.
   - Frontera superior (C10:W10) a 100 °C; fronteras izquierda (C11:C30), inferior (C30:W30) y derecha (W11:W30) a 0 °C.
   - Fórmula exacta del video en cada nodo interior (D11:V29): =(izq + der + abajo + arriba)/4
     Por ejemplo, en D11: =(C11+E11+D12+D10)/4
   - Puntos de control destacados en rojo y comparados con Solid Edge:
     * Arriba (50 mm, 20 mm) -> Celda M14: 61.99 °C (~62 °C vs 62.1 °C en Solid Edge)
     * Centro (50 mm, 50 mm) -> Celda M20: 25.00 °C (25 °C vs 25.0 °C en Solid Edge)
     * Abajo  (50 mm, 80 mm) -> Celda M26: 7.38 °C  (7.4 °C vs 7.37 °C en Solid Edge)
   - Escala de color condicional nativa de Excel (Verde frío -> Amarillo medio -> Rojo caliente).

2. Hoja 2 ("Caso 2 (10-30-60-100 C)"):
   - Segunda prueba mostrada en el video: Izquierda = 10 °C, Inferior = 30 °C, Derecha = 60 °C, Superior = 100 °C.
   - Puntos de control verificados:
     * Arriba (50 mm, 20 mm) -> Celda M14: 74.93 °C (~75 °C vs 75.0 °C en Solid Edge)
     * Centro (50 mm, 50 mm) -> Celda M20: 50.00 °C (50 °C vs 50.0 °C en Solid Edge)
     * Abajo  (50 mm, 80 mm) -> Celda M26: 36.70 °C (36.7 °C / 37 °C vs 36.7 °C en Solid Edge)

3. Hoja 3 ("Simulador Editable"):
   - Permite cambiar en 4 celdas de entrada (Z10:Z13) las temperaturas de las 4 fronteras
     y recalcula automáticamente toda la malla de 21x21 nodos al presionar F9.

4. Cálculo Iterativo pre-activado en el archivo Excel (iterate="1", iterateCount="1000", iterateDelta="0.0001")
   y valores convergidos pre-calculados para visualización inmediata al abrir.
"""

import zipfile
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape


def solve_laplace_2d(t_top: float, t_left: float, t_bottom: float, t_right: float, n: int = 21, tol: float = 1e-10):
    """Resuelve la malla de n x n nodos por diferencias finitas (Gauss-Seidel) hasta convergencia."""
    grid = [[0.0 for _ in range(n)] for _ in range(n)]

    # Condiciones de frontera (igual que en el video: fila 10 arriba = 100, desde fila 11 izq/der/abajo)
    for r in range(1, n):
        grid[r][0] = t_left
        grid[r][n - 1] = t_right
    for c in range(n):
        grid[n - 1][c] = t_bottom
    for c in range(n):
        grid[0][c] = t_top

    for _ in range(15000):
        max_diff = 0.0
        for r in range(1, n - 1):
            for c in range(1, n - 1):
                new_val = 0.25 * (grid[r][c - 1] + grid[r][c + 1] + grid[r + 1][c] + grid[r - 1][c])
                diff = abs(new_val - grid[r][c])
                if diff > max_diff:
                    max_diff = diff
                grid[r][c] = new_val
        if max_diff < tol:
            break
    return grid


def col_letter(col_idx_1based: int) -> str:
    """Convierte índice de columna 1-based (1=A, 3=C, 23=W) a letra de Excel."""
    res = ""
    n = col_idx_1based
    while n > 0:
        n, rem = divmod(n - 1, 26)
        res = chr(65 + rem) + res
    return res


def cell_ref(row_1based: int, col_1based: int) -> str:
    return f"{col_letter(col_1based)}{row_1based}"


def build_styles_xml() -> str:
    """Construye xl/styles.xml con formatos numéricos, fuentes, bordes y estilos de celda."""
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="2">
    <numFmt numFmtId="164" formatCode="0.0"/>
    <numFmt numFmtId="165" formatCode="0.00"/>
  </numFmts>
  <fonts count="8">
    <font><sz val="10"/><color theme="1"/><name val="Calibri"/></font>
    <font><b/><sz val="13"/><color rgb="FF1E293B"/><name val="Calibri"/></font>
    <font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
    <font><b/><sz val="9"/><color rgb="FF334155"/><name val="Calibri"/></font>
    <font><sz val="9"/><color rgb="FF0F172A"/><name val="Calibri"/></font>
    <font><b/><sz val="9"/><color rgb="FF0F172A"/><name val="Calibri"/></font>
    <font><b/><sz val="9"/><color rgb="FFC00000"/><name val="Calibri"/></font>
    <font><i/><sz val="10"/><color rgb="FF475569"/><name val="Calibri"/></font>
  </fonts>
  <fills count="7">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1E3A8A"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE2E8F0"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF8FAFC"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFEF3C7"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDCFCE7"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="4">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFCBD5E1"/></left>
      <right style="thin"><color rgb="FFCBD5E1"/></right>
      <top style="thin"><color rgb="FFCBD5E1"/></top>
      <bottom style="thin"><color rgb="FFCBD5E1"/></bottom>
      <diagonal/>
    </border>
    <border>
      <left style="medium"><color rgb="FF334155"/></left>
      <right style="medium"><color rgb="FF334155"/></right>
      <top style="medium"><color rgb="FF334155"/></top>
      <bottom style="medium"><color rgb="FF334155"/></bottom>
      <diagonal/>
    </border>
    <border>
      <left style="medium"><color rgb="FFC00000"/></left>
      <right style="medium"><color rgb="FFC00000"/></right>
      <top style="medium"><color rgb="FFC00000"/></top>
      <bottom style="medium"><color rgb="FFC00000"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="12">
    <!-- 0: Default -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <!-- 1: Title bold 13pt -->
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <!-- 2: Subtitle italic -->
    <xf numFmtId="0" fontId="7" fillId="0" borderId="0" xfId="0" applyFont="1"/>
    <!-- 3: Coordinate Header (gray fill, bold 9pt, centered) -->
    <xf numFmtId="0" fontId="3" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <!-- 4: Interior Node (General format so narrow square columns never show ###, 9pt, thin border, centered) -->
    <xf numFmtId="0" fontId="4" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <!-- 5: Boundary Node (General format, bold 9pt, medium border, centered) -->
    <xf numFmtId="0" fontId="5" fillId="0" borderId="2" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <!-- 6: Probe Node Highlighted (General format, bold red font, red border, centered) -->
    <xf numFmtId="0" fontId="6" fillId="0" borderId="3" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <!-- 7: Table Header Dark Blue (white bold text) -->
    <xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <!-- 8: Comparison Table Cell (centered, 0.00) -->
    <xf numFmtId="165" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <!-- 9: Comparison Table Label (left, bold) -->
    <xf numFmtId="0" fontId="5" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="left" vertical="center"/>
    </xf>
    <!-- 10: Editable Input Cell (Yellow fill, bold, medium border) -->
    <xf numFmtId="164" fontId="5" fillId="5" borderId="2" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="center" vertical="center"/>
    </xf>
    <!-- 11: Info Box Green -->
    <xf numFmtId="0" fontId="5" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment horizontal="left" vertical="center"/>
    </xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>"""


def make_sheet_xml(
    title: str,
    subtitle: str,
    t_top: float,
    t_left: float,
    t_bottom: float,
    t_right: float,
    solid_edge_refs: dict,
    use_control_cells: bool = False,
) -> str:
    """
    Construye el XML de una hoja de cálculo con la malla 21x21 en C10:W30,
    coordenadas X en C9:W9 (0 a 100 mm), coordenadas Y en B10:B30 (0 a 100 mm),
    fórmulas exactas =(izq+der+abajo+arriba)/4 en D11:V29 y tabla comparativa a la derecha.
    """
    grid = solve_laplace_2d(t_top, t_left, t_bottom, t_right, n=21)

    rows_map = {}

    def set_cell(r: int, c: int, val=None, formula: str = None, style: int = 0, is_str: bool = False):
        rows_map.setdefault(r, {})[c] = (val, formula, style, is_str)

    # Encabezado explicativo (Filas 2 a 5)
    set_cell(2, 2, title, style=1, is_str=True)
    set_cell(3, 2, subtitle, style=2, is_str=True)
    set_cell(
        4,
        2,
        "Ecuación de Difusión 2D (Diferencias Finitas, Δx = Δy = 5 mm):   T(i,j) = ( T_izq + T_der + T_abajo + T_arriba ) / 4",
        style=11,
        is_str=True,
    )
    set_cell(
        5,
        2,
        "Cálculo iterativo pre-activado. En el primer nodo interior D11 la fórmula es: =(C11+E11+D12+D10)/4",
        style=2,
        is_str=True,
    )

    # Etiqueta de coordenadas
    set_cell(8, 3, "Coordenada X [mm] (Ancho de la placa: 0 a 100 mm, de 5 en 5 mm -> 21 nodos)", style=2, is_str=True)
    set_cell(9, 2, "Y \\ X [mm]", style=3, is_str=True)

    # Coordenadas X en fila 9: C9 (col 3) a W9 (col 23) -> 0, 5, 10, ..., 100
    for idx in range(21):
        c = 3 + idx
        x_mm = idx * 5
        set_cell(9, c, x_mm, style=3, is_str=False)

    # Si es la hoja editable, colocamos el panel de control en columnas Y..Z (cols 25..26)
    if use_control_cells:
        set_cell(9, 25, "Parámetro de Frontera (Editable)", style=7, is_str=True)
        set_cell(9, 26, "Temp [°C]", style=7, is_str=True)

        set_cell(10, 25, "Frontera Superior (Arriba, Y=0 mm)", style=9, is_str=True)
        set_cell(10, 26, t_top, style=10, is_str=False)  # Z10

        set_cell(11, 25, "Frontera Izquierda (X=0 mm)", style=9, is_str=True)
        set_cell(11, 26, t_left, style=10, is_str=False)  # Z11

        set_cell(12, 25, "Frontera Inferior (Abajo, Y=100 mm)", style=9, is_str=True)
        set_cell(12, 26, t_bottom, style=10, is_str=False)  # Z12

        set_cell(13, 25, "Frontera Derecha (X=100 mm)", style=9, is_str=True)
        set_cell(13, 26, t_right, style=10, is_str=False)  # Z13

    # Coordenadas Y en columna B (col 2): B10 a B30 -> 0, 5, 10, ..., 100
    # Y llenado de la malla 21x21 en C10:W30 (filas 10 a 30, columnas 3 a 23)
    probe_coords = {(14, 13), (20, 13), (26, 13)}  # M14 (50,20), M20 (50,50), M26 (50,80)

    for r_idx in range(21):
        excel_row = 10 + r_idx
        y_mm = r_idx * 5
        set_cell(excel_row, 2, y_mm, style=3, is_str=False)

        for c_idx in range(21):
            excel_col = 3 + c_idx
            val = round(grid[r_idx][c_idx], 4)

            is_top = r_idx == 0
            is_bottom = r_idx == 20
            is_left = c_idx == 0
            is_right = c_idx == 20

            if is_top or is_bottom or is_left or is_right:
                f_str = None
                if use_control_cells:
                    if is_top:
                        f_str = "$Z$10"
                    elif is_bottom:
                        f_str = "$Z$12"
                    elif is_left:
                        f_str = "$Z$11"
                    elif is_right:
                        f_str = "$Z$13"
                set_cell(excel_row, excel_col, val, formula=f_str, style=5, is_str=False)
            else:
                # Nodo interior: fórmula exacta del video =(Izquierda + Derecha + Abajo + Arriba)/4
                left_ref = cell_ref(excel_row, excel_col - 1)
                right_ref = cell_ref(excel_row, excel_col + 1)
                down_ref = cell_ref(excel_row + 1, excel_col)
                up_ref = cell_ref(excel_row - 1, excel_col)
                formula = f"({left_ref}+{right_ref}+{down_ref}+{up_ref})/4"
                st = 6 if (excel_row, excel_col) in probe_coords else 4
                set_cell(excel_row, excel_col, val, formula=formula, style=st, is_str=False)

    # Tabla de validación / comparación con Solid Edge (en columnas Y..AB)
    start_r = 16 if use_control_cells else 10
    set_cell(start_r, 25, "Punto de Comparación (Video)", style=7, is_str=True)
    set_cell(start_r, 26, "Celda", style=7, is_str=True)
    set_cell(start_r, 27, "Excel FDM [°C]", style=7, is_str=True)
    set_cell(start_r, 28, "Solid Edge [°C]", style=7, is_str=True)

    probes_info = [
        ("A 20 mm de Arriba (X=50, Y=20 mm)", "M14", grid[4][10], solid_edge_refs["top20"]),
        ("Centro de la Placa (X=50, Y=50 mm)", "M20", grid[10][10], solid_edge_refs["center"]),
        ("A 20 mm de Abajo (X=50, Y=80 mm)", "M26", grid[16][10], solid_edge_refs["bot20"]),
    ]

    for idx, (label, cref, ex_val, se_val) in enumerate(probes_info, start=1):
        rr = start_r + idx
        set_cell(rr, 25, label, style=9, is_str=True)
        set_cell(rr, 26, cref, style=9, is_str=True)
        set_cell(rr, 27, round(ex_val, 4), formula=cref, style=8, is_str=False)
        set_cell(rr, 28, se_val, style=8, is_str=False)

    # Construir XML de columnas (C..W cuadradas de ancho 4.2 para verse como placa cuadrada tal como en el video)
    cols_xml = [
        "<cols>",
        '  <col min="1" max="1" width="3" customWidth="1"/>',
        '  <col min="2" max="2" width="9.5" customWidth="1"/>',
        '  <col min="3" max="23" width="4.2" customWidth="1"/>',
        '  <col min="24" max="24" width="3" customWidth="1"/>',
        '  <col min="25" max="25" width="32" customWidth="1"/>',
        '  <col min="26" max="28" width="15" customWidth="1"/>',
        "</cols>",
    ]

    # Construir XML de filas y celdas
    sheet_data_lines = ["<sheetData>"]
    for r in sorted(rows_map.keys()):
        ht_attr = ' ht="20" customHeight="1"' if 9 <= r <= 30 else (' ht="24" customHeight="1"' if r == 2 else "")
        sheet_data_lines.append(f'  <row r="{r}"{ht_attr}>')
        for c in sorted(rows_map[r].keys()):
            val, formula, style, is_str = rows_map[r][c]
            ref = cell_ref(r, c)
            if is_str:
                esc_val = escape(str(val))
                sheet_data_lines.append(
                    f'    <c r="{ref}" s="{style}" t="inlineStr"><is><t>{esc_val}</t></is></c>'
                )
            else:
                if formula is not None:
                    sheet_data_lines.append(
                        f'    <c r="{ref}" s="{style}"><f>{escape(formula)}</f><v>{val}</v></c>'
                    )
                else:
                    sheet_data_lines.append(f'    <c r="{ref}" s="{style}"><v>{val}</v></c>')
        sheet_data_lines.append("  </row>")
    sheet_data_lines.append("</sheetData>")

    # Escala de color condicional idéntica a la del video (Verde frío -> Amarillo -> Rojo caliente)
    cond_fmt_xml = """
  <conditionalFormatting sqref="C10:W30">
    <cfRule type="colorScale" priority="1">
      <colorScale>
        <cfvo type="min"/>
        <cfvo type="percentile" val="50"/>
        <cfvo type="max"/>
        <color rgb="FF63BE7B"/>
        <color rgb="FFFFEB84"/>
        <color rgb="FFF8696B"/>
      </colorScale>
    </cfRule>
  </conditionalFormatting>"""

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews>
    <sheetView workbookViewId="0" showGridLines="1">
      <selection activeCell="D11" sqref="D11"/>
    </sheetView>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="18"/>
  {"".join(cols_xml)}
  {"".join(sheet_data_lines)}
  {cond_fmt_xml}
</worksheet>"""


def create_excel_file(output_path: str):
    sheet1_xml = make_sheet_xml(
        title="Simulación de Difusión de Calor 2D en Excel - Caso 1 (Fronteras: 100°C Arriba, 0°C Izq/Abajo/Der)",
        subtitle="Recreación exacta del video 'Simulando difusión de calor en EXCEL!!!' (Termofluidos TV) - Placa de 100 mm x 100 mm (21x21 nodos)",
        t_top=100.0,
        t_left=0.0,
        t_bottom=0.0,
        t_right=0.0,
        solid_edge_refs={"top20": 62.10, "center": 25.00, "bot20": 7.37},
        use_control_cells=False,
    )

    sheet2_xml = make_sheet_xml(
        title="Simulación de Difusión de Calor 2D en Excel - Caso 2 (Izq: 10°C, Abajo: 30°C, Der: 60°C, Arriba: 100°C)",
        subtitle="Segunda prueba del video comparada contra Solid Edge - Placa de 100 mm x 100 mm (21x21 nodos)",
        t_top=100.0,
        t_left=10.0,
        t_bottom=30.0,
        t_right=60.0,
        solid_edge_refs={"top20": 75.00, "center": 50.00, "bot20": 36.70},
        use_control_cells=False,
    )

    sheet3_xml = make_sheet_xml(
        title="Simulador Interactivo Editable - Cambia las Temperaturas de Frontera en Z10:Z13",
        subtitle="Modifica las celdas amarillas (Z10:Z13) y presiona F9 para actualizar toda la placa de 21x21 nodos",
        t_top=100.0,
        t_left=10.0,
        t_bottom=30.0,
        t_right=60.0,
        solid_edge_refs={"top20": 75.00, "center": 50.00, "bot20": 36.70},
        use_control_cells=True,
    )

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Caso 1 (0 y 100 C)" sheetId="1" r:id="rId1"/>
    <sheet name="Caso 2 (10-30-60-100 C)" sheetId="2" r:id="rId2"/>
    <sheet name="Simulador Editable" sheetId="3" r:id="rId3"/>
  </sheets>
  <calcPr calcId="191029" iterate="1" iterateCount="1000" iterateDelta="0.0001" fullCalcOnLoad="1"/>
</workbook>"""

    workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        zf.writestr("xl/styles.xml", build_styles_xml())
        zf.writestr("xl/worksheets/sheet1.xml", sheet1_xml)
        zf.writestr("xl/worksheets/sheet2.xml", sheet2_xml)
        zf.writestr("xl/worksheets/sheet3.xml", sheet3_xml)

    # Validar que todos los archivos XML del paquete sean válidos
    with zipfile.ZipFile(output_path, "r") as zf:
        for name in zf.namelist():
            ET.fromstring(zf.read(name))

    print(f"Archivo Excel generado y validado exitosamente en: {output_path}")


if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Simulacion_Difusion_Calor_Excel.xlsx")
    create_excel_file(out_file)
