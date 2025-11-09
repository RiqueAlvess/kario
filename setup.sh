#!/bin/bash

# Script de configuração inicial do projeto Kario
# Este script configura o ambiente e banco de dados

set -e  # Sai se houver erro

echo "=========================================="
echo "  Configuração Inicial - Kario"
echo "=========================================="
echo ""

# Verifica se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    echo "✓ Ambiente virtual criado"
else
    echo "✓ Ambiente virtual já existe"
fi

echo ""
echo "Ativando ambiente virtual..."
source venv/bin/activate

echo ""
echo "Instalando dependências..."
pip install -r requirements.txt -q
echo "✓ Dependências instaladas"

echo ""
echo "Executando migrações do banco de dados..."
python manage.py migrate
echo "✓ Banco de dados configurado"

echo ""
echo "Populando templates de inspeção..."
python manage.py populate_inspection
echo "✓ Templates de inspeção criados"

echo ""
echo "=========================================="
echo "  Configuração concluída com sucesso!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo ""
echo "1. Criar superusuário (opcional):"
echo "   source venv/bin/activate"
echo "   python manage.py createsuperuser"
echo ""
echo "2. Executar o servidor:"
echo "   ./run_dev.sh    (desenvolvimento)"
echo "   ./run_server.sh (produção)"
echo ""
