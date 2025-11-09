#!/bin/bash

# Script alternativo usando Django runserver (mais simples para desenvolvimento)
# Permite acesso via IP local (ex: pelo celular na mesma rede)

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Obter IP local
IP=$(hostname -I | awk '{print $1}')

echo "========================================"
echo "Iniciando servidor Django (runserver)"
echo "========================================"
echo ""
echo "Acesse pelo navegador:"
echo "  - Local: http://127.0.0.1:8000"
echo "  - Rede local: http://$IP:8000"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo "========================================"
echo ""

# Rodar Django runserver
# 0.0.0.0:8000 permite acesso de qualquer IP na rede
python manage.py runserver 0.0.0.0:8000
