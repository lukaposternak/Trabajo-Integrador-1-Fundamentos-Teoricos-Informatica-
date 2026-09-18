#!/bin/bash

echo "=== Configurando entorno para el TP de Autómatas ==="

# 1. Detectar el sistema operativo e instalar dependencias del sistema
if [ -f /etc/fedora-release ]; then
    echo "Distribución Fedora detectada. Instalando Graphviz y Tkinter..."
    sudo dnf install -y graphviz python3-tkinter python3-pillow-tk python3-pip
elif [ -f /etc/lsb-release ]; then
    echo "Distribución Ubuntu/Debian detectada. Instalando Graphviz y Tkinter..."
    sudo apt-get update
    sudo apt-get install -y graphviz python3-tk python3-pil.imagetk python3-pip
else
    echo "Por favor, asegúrate de tener instalados 'graphviz' y 'tkinter' en tu sistema."
fi

# 2. Instalar dependencias de Python a nivel de usuario local
echo "Instalando dependencias de Python (Pillow, Graphviz)..."
pip3 install --user -r requirements.txt

echo "=== Instalación completada ==="
echo "Iniciando la aplicación..."

# 3. Ejecutar el programa
python3 app_automata.py