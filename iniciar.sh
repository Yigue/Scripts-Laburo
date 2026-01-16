#!/bin/bash
# Script de inicio rápido para el Asistente de Soporte Andreani

# Obtener directorio actual
BASE_DIR="/home/korg/Scripts-Laburo"

echo "------------------------------------------------"
echo "🚀 Seleccione la aplicación que desea ejecutar:"
echo "------------------------------------------------"
echo "1) Asistente IT-Ops (Nueva CLI con Ansible)"
echo "2) Herramienta de Soporte (CLI Clásica)"
echo "------------------------------------------------"
read -p "Opción [1-2]: " OPCION

case $OPCION in
    1)
        echo "Lanzando Asistente IT-Ops (Ansible)..."
        cd "$BASE_DIR/automation/ansible"
        source venv/bin/activate
        python app.py
        ;;
    2)
        echo "Lanzando Herramienta de Soporte (Clásica)..."
        cd "$BASE_DIR"
        source venv/bin/activate
        python automation/App/main.py
        ;;
    *)
        echo "Opción inválida."
        ;;
esac
