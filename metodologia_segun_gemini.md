\# Guía Didáctica y Especificación Interactiva: Método de Diferencias Finitas (MDF)



\## Página 1: De la Derivada Continua a la Diferencia Finita

\### 1.1 Fundamento Geométrico (1ra Derivada)

En el medio continuo, la derivada $y'(x\_i)$ es la pendiente de la recta tangente en un punto. Al discretizar con un paso $h = \\Delta x$, aproximamos esa tangente mediante rectas secantes entre nodos vecinos:

\* \*\*Diferencia hacia adelante (Forward):\*\* $y'\_i \\approx \\frac{y\_{i+1} - y\_i}{h}$

\* \*\*Diferencia hacia atrás (Backward):\*\* $y'\_i \\approx \\frac{y\_i - y\_{i-1}}{h}$

\* \*\*Diferencia central (Promedio de ambas, menor error):\*\*

&#x20; $$y'\_i \\approx \\frac{y\_{i+1} - y\_{i-1}}{2h}$$



\### 1.2 Cambio de Pendientes (2da Derivada)

La segunda derivada mide cómo cambia la pendiente entre el tramo posterior y el anterior dividido entre el paso $h$:

$$y''\_i \\approx \\frac{\\left(\\frac{y\_{i+1} - y\_i}{h}\\right) - \\left(\\frac{y\_i - y\_{i-1}}{h}\\right)}{h} = \\frac{y\_{i+1} - 2y\_i + y\_{i-1}}{h^2}$$



\* \*\*Elemento interactivo en HTML:\*\* Gráfica de una curva con un deslizador para el tamaño de paso $h$ que muestra cómo la secante central se aproxima a la tangente real cuando $h$ disminuye.



\---



\## Página 2: Discretización del Dominio y Metodología (1D y 2D)

\### 2.1 Creación de la Malla

1\. \*\*Dominio 1D (Viga / Barra):\*\* Se divide la longitud $L$ en $N$ subintervalos de tamaño $h = L/N$, generando nodos $x\_0, x\_1, \\dots, x\_N$.

2\. \*\*Dominio 2D (Placa / Región Electrostática):\*\* Se divide el plano en una cuadrícula de coordenadas $(i, j)$ con pasos $\\Delta x$ y $\\Delta y$.



\### 2.2 De la Ecuación Diferencial a la Ecuación Algebraica

Se aplica el principio de sustitución directa en cada nodo interno:

\* \*\*En 1D (ej. Deflexión de viga $y'' = \\frac{M(x)}{EI}$):\*\*

&#x20; $$\\frac{y\_{i+1} - 2y\_i + y\_{i-1}}{h^2} = \\frac{M(x\_i)}{EI} \\implies y\_{i-1} - 2y\_i + y\_{i+1} = h^2\\frac{M(x\_i)}{EI}$$

\* \*\*En 2D (con factor de forma $r = \\frac{\\Delta x^2}{\\Delta y^2}$):\*\*

&#x20; $$(u\_{i+1,j} - 2u\_{i,j} + u\_{i-1,j}) + r(u\_{i,j+1} - 2u\_{i,j} + u\_{i,j-1}) = 0$$



\* \*\*Elemento interactivo en HTML:\*\* Cuadrícula donde al pasar el cursor sobre un nodo $(i, j)$ se ilumina la "molécula de cálculo" (el nodo central y sus vecinos en cruz) y se muestra cómo se arma su ecuación con las condiciones de frontera (Dirichlet).



\---



\## Página 3: Difusión de Calor Estacionaria en 2D ($\\nabla^2 T = 0$)

\### 3.1 Ecuación Discretizada (Malla Cuadrada $\\Delta x = \\Delta y = h$)

Partiendo de $\\frac{\\partial^2 T}{\\partial x^2} + \\frac{\\partial^2 T}{\\partial y^2} = 0$, con $r = 1$:

$$T\_{i+1,j} + T\_{i-1,j} + T\_{i,j+1} + T\_{i,j-1} - 4T\_{i,j} = 0$$

Despejando el nodo central para resolución iterativa:

$$T\_{i,j}^{(k)} = \\frac{T\_{i+1,j} + T\_{i-1,j} + T\_{i,j+1} + T\_{i,j-1}}{4}$$



\### 3.2 Criterio de Convergencia

El ciclo iterativo se detiene cuando en todos los nodos se cumple que el error $\\left| T\_{i,j}^{(k)} - T\_{i,j}^{(k-1)} \\right|$ es menor que la tolerancia $\\epsilon$.



\* \*\*Elemento interactivo en HTML:\*\* Simulador de placa con entradas para las 4 temperaturas de borde, botón de "Paso +1 (Iterar)", botón de "Converger automáticamente" y mapa de calor por colores.



\---



\## Página 4: Electrostática — Ecuaciones de Laplace y Poisson

\### 4.1 Formulación Física

A partir de la Ley de Gauss ($\\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\varepsilon}$) y $\\mathbf{E} = -\\nabla V$, se obtiene la Ecuación de Poisson para el potencial eléctrico $V$ (en Voltios):

$$\\frac{\\partial^2 V}{\\partial x^2} + \\frac{\\partial^2 V}{\\partial y^2} = -\\frac{\\rho}{\\varepsilon}$$



\### 4.2 Ecuación Maestra con Carga Espacial

Sustituyendo diferencias centrales con paso uniforme $h$ y despejando $V\_{i,j}$:

$$V\_{i,j} = \\frac{V\_{i+1,j} + V\_{i-1,j} + V\_{i,j+1} + V\_{i,j-1}}{4} + \\frac{\\rho\_{i,j} h^2}{4\\varepsilon}$$

\* Si $\\rho = 0$ (Laplace): el potencial es el promedio exacto de los 4 vecinos.

\* Si $\\rho \\neq 0$ (Poisson): la carga local suma o resta potencial respecto al promedio vecino.



\* \*\*Elemento interactivo en HTML:\*\* Malla electrostática donde el usuario puede hacer clic en cualquier nodo interno para inyectar una fuente de carga ($\\pm \\rho$) y comparar la deformación del voltaje frente al caso sin carga.

