"""
Módulo de Elemento Finito (FEM) en 1D para Transferencia de Calor (Ecuación de Poisson).

Este módulo implementa las bases del método:
1. Discretización del dominio en malla regular (Mesh1D).
2. Generación de la tabla de conectividad de elementos.
3. Funciones de forma lineales e interpolación en coordenadas locales.
4. Rutina de prueba y visualización en consola.

Autor: Asistente de Simulación y Métodos Numéricos
"""

from typing import List, Tuple


class Mesh1D:
    """
    Representa una malla unidimensional regular para el Método de Elementos Finitos.

    Atributos:
        L (float): Longitud total del dominio (L > 0).
        ne (int): Número de elementos finitos (ne >= 1).
        nn (int): Número total de nodos (nn = ne + 1).
        le (float): Longitud constante de cada elemento (le = L / ne).
        nodes (List[float]): Arreglo de coordenadas de los nodos equiespaciados.
        connectivity (List[List[int]]): Tabla de conectividad de los elementos.
        one_based (bool): Si es True, la conectividad se numera desde 1 (estándar FEM);
                          si es False, se numera desde 0 (estándar Python).
    """

    def __init__(self, L: float, ne: int, one_based: bool = True) -> None:
        """
        Inicializa y genera la malla unidimensional.

        Parámetros:
            L (float): Longitud total del dominio. Debe ser mayor a 0.
            ne (int): Número de elementos en la malla. Debe ser un entero >= 1.
            one_based (bool): Bandera para indicar si los nodos en la tabla de
                             conectividad se enumeran comenzando en 1 o en 0.
        """
        if L <= 0.0:
            raise ValueError(f"La longitud del dominio L debe ser mayor a 0. Valor recibido: {L}")
        if not isinstance(ne, int) or ne < 1:
            raise ValueError(f"El número de elementos ne debe ser un entero >= 1. Valor recibido: {ne}")

        self.L: float = float(L)
        self.ne: int = ne
        self.nn: int = ne + 1
        self.le: float = self.L / self.ne
        self.one_based: bool = one_based

        # Hito 1: Coordenadas de los nodos
        self.nodes: List[float] = self._generate_nodes()

        # Hito 2: Tabla de conectividad
        self.connectivity: List[List[int]] = self._generate_connectivity()

    def _generate_nodes(self) -> List[float]:
        """
        Genera y retorna el arreglo de coordenadas globales de los nodos equiespaciados.
        x_i = i * le, para i = 0, 1, ..., ne.
        """
        return [i * self.le for i in range(self.nn)]

    def _generate_connectivity(self) -> List[List[int]]:
        """
        Genera la matriz de conectividad elemento-nodo.
        Cada fila 'e' representa el elemento e, y las columnas contienen
        los identificadores globales de sus nodos locales 1 y 2.

        Retorna:
            List[List[int]]: Conectividad con patrón consecutivo.
                            Ej: [[1, 2], [2, 3], ...] si one_based es True.
                                [[0, 1], [1, 2], ...] si one_based es False.
        """
        offset = 1 if self.one_based else 0
        return [[e + offset, e + 1 + offset] for e in range(self.ne)]

    def get_element_coordinates(self, elem_idx: int) -> Tuple[float, float]:
        """
        Obtiene las coordenadas globales (x1, x2) del elemento especificado.

        Parámetros:
            elem_idx (int): Índice del elemento (0-indexed).

        Retorna:
            Tuple[float, float]: Coordenadas (x1, x2) de los extremos del elemento.
        """
        if not (0 <= elem_idx < self.ne):
            raise IndexError(f"Índice de elemento {elem_idx} fuera de rango [0, {self.ne - 1}].")
        x1 = self.nodes[elem_idx]
        x2 = self.nodes[elem_idx + 1]
        return x1, x2

    def __repr__(self) -> str:
        return (
            f"Mesh1D(L={self.L}, ne={self.ne}, nn={self.nn}, "
            f"le={self.le:.4f}, one_based={self.one_based})"
        )


def linear_shape_functions(x_local: float, le: float) -> Tuple[float, float]:
    """
    Calcula las funciones de forma lineales de Lagrange de 1D en un elemento
    de longitud 'le' evaluadas en la coordenada local 'x_local' (0 <= x_local <= le).

    Ecuaciones:
        N_1(x_local) = 1 - (x_local / le)
        N_2(x_local) = x_local / le

    Propiedades:
        - Partición de la unidad: N_1 + N_2 = 1
        - Delta de Kronecker en los nodos:
          En x_local = 0:  N_1 = 1, N_2 = 0
          En x_local = le: N_1 = 0, N_2 = 1

    Parámetros:
        x_local (float): Coordenada local dentro del elemento (0 <= x_local <= le).
        le (float): Longitud del elemento finito (le > 0).

    Retorna:
        Tuple[float, float]: Valores (N1, N2) de las funciones de forma.
    """
    if le <= 0.0:
        raise ValueError(f"La longitud del elemento le debe ser mayor que 0. Valor recibido: {le}")

    # Advertencia o tolerancia numérica suave para límites
    tol = 1e-12
    if x_local < -tol or x_local > le + tol:
        print(f"[Aviso] Coordenada local x_local={x_local} fuera del rango [0, {le}].")

    n1 = 1.0 - (x_local / le)
    n2 = x_local / le
    return n1, n2


def interpolate_temperature(T1: float, T2: float, x_local: float, le: float) -> float:
    """
    Calcula la temperatura aproximada T(x_local) en el interior de un elemento aislado
    utilizando interpolación lineal basada en las funciones de forma de FEM.

    Ecuación:
        T(x_local) = N_1(x_local) * T_1 + N_2(x_local) * T_2
                   = (1 - x_local / le) * T_1 + (x_local / le) * T_2

    Parámetros:
        T1 (float): Temperatura nodal en el nodo local 1 (x_local = 0).
        T2 (float): Temperatura nodal en el nodo local 2 (x_local = le).
        x_local (float): Coordenada local en el elemento (0 <= x_local <= le).
        le (float): Longitud del elemento finito (le > 0).

    Retorna:
        float: Temperatura aproximada T en x_local.
    """
    n1, n2 = linear_shape_functions(x_local, le)
    return n1 * T1 + n2 * T2


def print_banner(title: str) -> None:
    """Imprime un encabezado con formato estético para consola."""
    separator = "=" * 65
    print(f"\n{separator}\n  {title}\n{separator}")


def main() -> None:
    """
    Rutina principal:
    1. Construye una malla de prueba de 5 elementos.
    2. Imprime en consola los detalles de la malla y la Tabla de Conectividad.
    3. Ejecuta pruebas de interpolación con valores arbitrarios de temperatura.
    """
    print_banner("SIMULACIÓN FEM 1D - TRANSFERENCIA DE CALOR: MALLADO E INTERPOLACIÓN")

    # Parámetros del dominio
    L_domain = 1.0   # Longitud de la barra (ej. 1.0 metro)
    num_elements = 5 # Número de elementos finitos

    # ---------------------------------------------------------
    # Hito 1: Construcción de la Malla 1D
    # ---------------------------------------------------------
    mesh = Mesh1D(L=L_domain, ne=num_elements, one_based=True)

    print(f"Propiedades de la Malla:")
    print(f"  • Longitud del dominio (L)     : {mesh.L:.4f} m")
    print(f"  • Número de elementos (ne)     : {mesh.ne}")
    print(f"  • Número total de nodos (nn)   : {mesh.nn}")
    print(f"  • Longitud de elemento (le)    : {mesh.le:.4f} m")

    print("\nArreglo de Coordenadas Nodales (Globales):")
    for i, x in enumerate(mesh.nodes):
        node_id = i + 1 if mesh.one_based else i
        print(f"  Nodo {node_id:2d} -> x = {x:.4f} m")

    # ---------------------------------------------------------
    # Hito 2: Tabla de Conectividad
    # ---------------------------------------------------------
    print_banner("TABLA DE CONECTIVIDAD (ELEMENTO -> NODOS)")
    print(f"{'Elemento':^12} | {'Nodo Local 1':^14} | {'Nodo Local 2':^14} | {'Rango x [m]':^20}")
    print("-" * 68)
    for elem_idx, conn in enumerate(mesh.connectivity):
        elem_display_id = elem_idx + 1 if mesh.one_based else elem_idx
        x_start, x_end = mesh.get_element_coordinates(elem_idx)
        print(
            f"{elem_display_id:^12} | "
            f"{conn[0]:^14} | "
            f"{conn[1]:^14} | "
            f"[{x_start:.2f}, {x_end:.2f}]".center(20)
        )

    print(f"\nRepresentación en lista de listas:")
    print(f"  conectividad = {mesh.connectivity}")

    # ---------------------------------------------------------
    # Hito 3 & 4: Localización e Interpolación de Temperatura
    # ---------------------------------------------------------
    print_banner("PRUEBA DE INTERPOLACIÓN EN UN ELEMENTO")

    # Seleccionamos el Elemento 3 (índice 2)
    target_elem = 2
    x_elem_start, x_elem_end = mesh.get_element_coordinates(target_elem)
    elem_id_str = f"Elemento {target_elem + 1}"

    # Temperaturas arbitrarias asignadas a los nodos locales
    T1 = 100.0  # Temperatura en Nodo local 1 (°C)
    T2 = 40.0   # Temperatura en Nodo local 2 (°C)

    print(f"Analizando {elem_id_str}:")
    print(f"  • Coordenadas globales : x ∈ [{x_elem_start:.4f}, {x_elem_end:.4f}] m")
    print(f"  • Longitud de elemento : le = {mesh.le:.4f} m")
    print(f"  • Temperatura Nodo 1   : T1 = {T1:.2f} °C (en x_local = 0.0000 m)")
    print(f"  • Temperatura Nodo 2   : T2 = {T2:.2f} °C (en x_local = {mesh.le:.4f} m)")

    print("\nEvaluación en diferentes puntos locales del elemento:")
    print(f"{'x_local [m]':^14} | {'x_global [m]':^14} | {'N1':^10} | {'N2':^10} | {'T interpolada [°C]':^20}")
    print("-" * 76)

    # Probamos varios puntos: inicio, 25%, mitad, 75% y final del elemento
    test_fractions = [0.0, 0.25, 0.50, 0.75, 1.0]
    for frac in test_fractions:
        x_loc = frac * mesh.le
        x_glob = x_elem_start + x_loc
        n1, n2 = linear_shape_functions(x_loc, mesh.le)
        T_interp = interpolate_temperature(T1, T2, x_loc, mesh.le)
        print(
            f"{x_loc:^14.4f} | "
            f"{x_glob:^14.4f} | "
            f"{n1:^10.4f} | "
            f"{n2:^10.4f} | "
            f"{T_interp:^20.4f}"
        )

    # Verificación de valor puntual específico
    x_test_local = 0.5 * mesh.le
    T_mid = interpolate_temperature(T1, T2, x_test_local, mesh.le)
    print(f"\nResultado clave:")
    print(f"  En el punto medio del elemento (x_local = {x_test_local:.4f} m):")
    print(f"  T = {T_mid:.2f} °C (coincide exactamente con el promedio {(T1 + T2)/2:.2f} °C)")

    print_banner("FIN DE LA EJECUCIÓN")


if __name__ == "__main__":
    main()
