# TP Integrador 1: Conversión y Minimización de Autómatas

Aplicación gráfica desarrollada en Python que convierte un Autómata Finito No Determinista (AFND) en un Autómata Finito Determinista (AFD) utilizando el **algoritmo de Construcción de Subconjuntos**, y luego lo minimiza utilizando el **Método de Moore**.

El programa genera automáticamente un registro (log) paso a paso con tablas de trazabilidad y renderiza los diagramas visuales (grafos) de los autómatas resultantes.

## Requisitos Previos

Para ejecutar este programa, tu sistema debe tener instalados:
1. **Python 3.x**
2. **Tkinter** (Librería nativa de Python para interfaces gráficas).
3. **Graphviz** (Motor de renderizado de grafos a nivel de sistema operativo).

## Instrucciones de Instalación y Ejecución

### Opción A: Instalación rápida en Linux (Fedora / Ubuntu / Debian)
Si clonaste este repositorio o descargaste el `.zip` en un entorno Linux, simplemente abre tu terminal en la carpeta del proyecto y ejecuta el script de configuración:

```bash
chmod +x setup.sh
./setup.sh