#!/bin/bash
# Script de inicio rápido para el Asistente de Soporte Andreani

# Obtener directorio actual
BASE_DIR="/home/korg/Scripts-Laburo"

echo "Lanzando Asistente IT-Ops (Ansible)..."
cd "$BASE_DIR/automation/ansible"
source venv/bin/activate
python app.py