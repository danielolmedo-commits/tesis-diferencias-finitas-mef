# Contexto y Rol
Actúa como un ingeniero de software experto en simulación y métodos numéricos. Vamos a implementar la base del Método del Elemento Finito (FEM) en 1D para resolver la ecuación de Poisson (Transferencia de Calor).

Por favor, genera un código estructurado, modular y con comentarios explicativos en [INSERTA TU LENGUAJE, ej. Python/C++] para los siguientes hitos de nuestro curso:

## 1. Discretización del Dominio (Mallado Regular)
- Crea una clase o función `Mesh1D`.
- Debe recibir la longitud total del dominio (`L`) y el número de elementos deseados (`ne`).
- Genera y retorna un arreglo de coordenadas de nodos equiespaciados.
- Calcula y almacena la longitud constante de cada elemento (`le = L / ne`).

## 2. Generación de la Tabla de Conectividad
- Crea un método que genere una matriz o lista de listas.
- Cada fila debe representar un "elemento" de la malla.
- Las dos columnas representarán la numeración global correspondiente a los nodos locales 1 y 2.
- Emplea el patrón consecutivo de conectividad para 1D: `[ [1, 2], [2, 3], [3, 4], ... ]`.

## 3. Localización e Interpolación
- Diseña una función `interpolate_temperature(T1, T2, x_local, le)` que calcule el valor de la temperatura aproximada en el interior de un elemento aislado.
- Utiliza las funciones de forma (shape functions) lineales para 1D en función de la coordenada local `x_local`.

## 4. Pruebas y Visualización
- Crea una rutina `main` que construya una malla de prueba de 5 elementos y despliegue en consola la Tabla de Conectividad resultante.
- Muestra una prueba de interpolación dentro de uno de los elementos pasando valores arbitrarios de temperatura para los nodos $T_1$ y $T_2$.