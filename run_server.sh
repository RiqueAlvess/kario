#!/bin/bash

# Script para rodar o servidor Django com Gunicorn
# Permite acesso via IP local (ex: pelo celular na mesma rede)

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Obter IP local
IP=$(hostname -I | awk '{print $1}')

echo "========================================"
echo "Iniciando servidor Django com Gunicorn"
echo "========================================"
echo ""
echo "Acesse pelo navegador:"
echo "  - Local: http://127.0.0.1:8000"
echo "  - Rede local: http://$IP:8000"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo "========================================"
echo ""

# Rodar Gunicorn
# - bind 0.0.0.0:8000 permite acesso de qualquer IP na rede
# - workers 3 define 3 processos workers
# - reload recarrega automaticamente quando o código muda
gunicorn kario.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --reload \
    --access-logfile - \
    --error-logfile -
