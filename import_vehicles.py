#!/usr/bin/env python

"""

Script para importar veículos de CSV para o sistema Kario

Uso: python import_vehicles.py vehicles.csv

"""

 

import os

import sys

import django

import csv

import re

 

# Setup Django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kario.settings')

django.setup()

 

from garage.models import Vehicle, InspectionTemplate, VehicleInspection

from django.contrib.auth.models import User

 

 

def clean_value(value):

    """Limpar e converter valores"""

    if not value or value.strip() == '':

        return None

 

    value = value.strip()

 

    # Remover vírgulas de números

    if ',' in value and any(char.isdigit() for char in value):

        value = value.replace(',', '')

 

    # Remover $ de valores monetários

    if value.startswith('$'):

        value = value.replace('$', '').replace('.', '')

 

    return value

 

 

def clean_miles(miles_str):

    """Limpar valor de milhas"""

    if not miles_str:

        return 0

 

    miles_str = clean_value(miles_str)

    if not miles_str:

        return 0

 

    # Remover ? e outros caracteres não numéricos exceto ponto

    miles_str = re.sub(r'[^\d.]', '', miles_str)

 

    try:

        return int(float(miles_str))

    except (ValueError, TypeError):

        return 0

 

 

def clean_value_price(value_str):

    """Limpar valor de preço"""

    if not value_str:

        return 0

 

    value_str = clean_value(value_str)

    if not value_str:

        return 0

 

    # Remover tudo exceto dígitos e ponto

    value_str = re.sub(r'[^\d.]', '', value_str)

 

    try:

        return float(value_str)

    except (ValueError, TypeError):

        return 0

 

 

def determine_car_type(make, model):

    """Determinar tipo do carro baseado na marca e modelo"""

    model_upper = model.upper() if model else ''

    make_upper = make.upper() if make else ''

 

    # SUVs

    if any(x in model_upper for x in ['ROGUE', 'ECOSPORT', 'FORESTER', 'SPORTAGE',

                                       'EDGE', 'EXPLORER', 'COMPASS', 'CX-9', 'X-5', 'XTERRA']):

        return 'SUV'

 

    # Pickups

    if any(x in model_upper for x in ['SILVERADO', 'RAM']):

        return 'PICKUP'

 

    # Vans

    if any(x in model_upper for x in ['CARAVAN']):

        return 'VAN'

 

    # Coupes

    if 'COUPE' in model_upper or 'TC' in model_upper or 'CHALLENGER' in model_upper or 'CHARGER' in model_upper:

        return 'COUPE'

 

    # Hatchback/Wagon

    if any(x in model_upper for x in ['WAGON', 'SOUL', 'SPARK', 'FIESTA', 'MIRAGE', 'IMPREZA']):

        return 'HATCHBACK'

 

    # Sedan por padrão

    return 'SEDAN'

 

 

def import_vehicles_from_csv(csv_file_path):

    """Importar veículos do CSV"""

 

    # Pegar ou criar usuário admin

    try:

        user = User.objects.filter(is_staff=True).first()

        if not user:

            user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')

            print("✓ Usuário admin criado (username: admin, password: admin123)")

    except Exception as e:

        print(f"⚠ Erro ao criar usuário: {e}")

        user = None

 

    # Ler CSV

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:

        reader = csv.reader(csvfile)

 

        # Pular primeiras 2 linhas (headers)

        next(reader)  # Header principal

        next(reader)  # Sub-header

 

        imported = 0

        skipped = 0

        errors = []

 

        for row_num, row in enumerate(reader, start=3):

            try:

                # Verificar se tem dados suficientes

                if len(row) < 17:

                    skipped += 1

                    continue

 

                # Extrair dados

                status_col = row[1] if len(row) > 1 else ''

                vin = clean_value(row[2]) if len(row) > 2 else None

                year = clean_value(row[3]) if len(row) > 3 else None

                make = clean_value(row[4]) if len(row) > 4 else None

                model = clean_value(row[5]) if len(row) > 5 else None

                engine = clean_value(row[9]) if len(row) > 9 else ''

                transmission = clean_value(row[10]) if len(row) > 10 else ''

                train = clean_value(row[11]) if len(row) > 11 else ''

                color = clean_value(row[12]) if len(row) > 12 else None

                miles = clean_miles(row[13]) if len(row) > 13 else 0

                mpg = clean_value(row[14]) if len(row) > 14 else ''

                clean_title = clean_value(row[15]) if len(row) > 15 else 'NO'

                value = clean_value_price(row[16]) if len(row) > 16 else 0

 

                # Validar dados mínimos

                if not year or not make or not model:

                    skipped += 1

                    continue

 

                # Converter year para inteiro

                try:

                    year = int(year)

                except (ValueError, TypeError):

                    errors.append(f"Linha {row_num}: Ano inválido '{year}'")

                    skipped += 1

                    continue

 

                # Determinar status do título

                title_status = 'LIMPO' if clean_title and clean_title.upper() == 'YES' else 'NAO_LIMPO'

 

                # Determinar status do veículo

                if status_col.upper() == 'E':

                    vehicle_status = 'DISPONIVEL'

                elif status_col.upper() == 'SE':

                    vehicle_status = 'DISPONIVEL'

                else:

                    vehicle_status = 'FALTA_INSPECAO'

 

                # Determinar tipo do carro

                car_type = determine_car_type(make, model)

 

                # Criar veículo

                vehicle = Vehicle.objects.create(

                    year=year,

                    make=make,

                    model=model,

                    trim='',

                    vin=vin or '',

                    engine=engine or '',

                    transmission=transmission or '',

                    train=train or '',

                    car_type=car_type,

                    exterior_color=color or '',

                    interior_color='',

                    miles=miles,

                    mpg=mpg or '',

                    title_status=title_status,

                    title_problem_description='' if title_status == 'LIMPO' else 'Verificar documentação',

                    value=value,

                    general_notes=f'Importado do CSV - Status original: {status_col}',

                    status=vehicle_status,

                    updated_by=user

                )

 

                # Criar fichas de inspeção

                for template in InspectionTemplate.objects.all():

                    VehicleInspection.objects.create(

                        vehicle=vehicle,

                        template=template

                    )

 

                imported += 1

                print(f"✓ {year} {make} {model} (VIN: {vin or 'N/A'}) - ${value}")

 

            except Exception as e:

                errors.append(f"Linha {row_num}: {str(e)}")

                skipped += 1

 

    # Relatório final

    print("\n" + "="*60)

    print("IMPORTAÇÃO CONCLUÍDA")

    print("="*60)

    print(f"✓ Veículos importados: {imported}")

    print(f"⊘ Linhas puladas: {skipped}")

 

    if errors:

        print(f"\n⚠ Erros encontrados ({len(errors)}):")

        for error in errors[:10]:  # Mostrar apenas os primeiros 10 erros

            print(f"  - {error}")

        if len(errors) > 10:

            print(f"  ... e mais {len(errors) - 10} erros")

 

    print("\n" + "="*60)

    print("Para acessar o sistema:")

    print("  - Execute: ./run_server.sh")

    print("  - Acesse: http://127.0.0.1:8000")

    if user:

        print("  - Login: admin / admin123")

    print("="*60)

 

 

if __name__ == '__main__':

    
    csv_file = "INVENTORY KARIO - INVENTORY.csv"

 

    if not os.path.exists(csv_file):

        print(f"❌ Arquivo não encontrado: {csv_file}")

        sys.exit(1)

 

    print("="*60)

    print("IMPORTAÇÃO DE VEÍCULOS - KARIO GARAGE")

    print("="*60)

    print(f"Arquivo: {csv_file}")

    print("="*60)

    print()

 

    import_vehicles_from_csv(csv_file)