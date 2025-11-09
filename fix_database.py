#!/usr/bin/env python
"""
Script para corrigir problemas nos registros do banco de dados
- Criar fichas de inspeção faltantes
- Corrigir status de título (NAO_LIMPO → REBUILT)
- Limpar VINs vazios duplicados
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kario.settings')
django.setup()

from garage.models import Vehicle, InspectionTemplate, VehicleInspection


def fix_missing_inspections():
    """Criar fichas de inspeção para veículos que não têm"""
    print("\n" + "="*60)
    print("1. CORRIGINDO FICHAS DE INSPEÇÃO FALTANTES")
    print("="*60)

    templates = InspectionTemplate.objects.all()
    if not templates.exists():
        print("⚠ Nenhum template de inspeção encontrado!")
        print("Execute: python manage.py populate_inspection")
        return 0

    vehicles = Vehicle.objects.all()
    fixed = 0

    for vehicle in vehicles:
        inspection_count = vehicle.inspections.count()
        template_count = templates.count()

        if inspection_count < template_count:
            # Faltam fichas de inspeção
            missing = template_count - inspection_count
            existing_template_ids = vehicle.inspections.values_list('template_id', flat=True)

            for template in templates:
                if template.id not in existing_template_ids:
                    VehicleInspection.objects.create(
                        vehicle=vehicle,
                        template=template
                    )
                    fixed += 1

            print(f"✓ {vehicle.year} {vehicle.make} {vehicle.model} - {missing} fichas criadas")

    if fixed == 0:
        print("✓ Todas as fichas de inspeção estão OK!")
    else:
        print(f"\n✓ Total: {fixed} fichas de inspeção criadas")

    return fixed


def fix_title_status():
    """Corrigir status de título NAO_LIMPO para REBUILT"""
    print("\n" + "="*60)
    print("2. CORRIGINDO STATUS DE TÍTULO")
    print("="*60)

    # Encontrar veículos com NAO_LIMPO
    vehicles = Vehicle.objects.filter(title_status='NAO_LIMPO')
    count = vehicles.count()

    if count == 0:
        print("✓ Nenhum veículo com título NAO_LIMPO encontrado")
        return 0

    # Atualizar para REBUILT
    vehicles.update(title_status='REBUILT')

    print(f"✓ {count} veículos atualizados: NAO_LIMPO → REBUILT")

    for vehicle in vehicles[:10]:  # Mostrar primeiros 10
        print(f"  - {vehicle.year} {vehicle.make} {vehicle.model}")

    if count > 10:
        print(f"  ... e mais {count - 10} veículos")

    return count


def fix_duplicate_empty_vins():
    """Corrigir VINs vazios duplicados"""
    print("\n" + "="*60)
    print("3. CORRIGINDO VINs VAZIOS DUPLICADOS")
    print("="*60)

    # Encontrar veículos com VIN vazio
    empty_vin_vehicles = Vehicle.objects.filter(vin='')
    count = empty_vin_vehicles.count()

    if count == 0:
        print("✓ Nenhum veículo com VIN vazio encontrado")
        return 0

    # Atualizar para NULL (permitir múltiplos)
    for vehicle in empty_vin_vehicles:
        vehicle.vin = None
        vehicle.save()

    print(f"✓ {count} veículos com VIN vazio convertidos para NULL")
    return count


def show_statistics():
    """Mostrar estatísticas do banco"""
    print("\n" + "="*60)
    print("ESTATÍSTICAS DO BANCO DE DADOS")
    print("="*60)

    total = Vehicle.objects.count()
    print(f"Total de veículos: {total}")

    # Por status
    print("\nPor Status:")
    for status, label in Vehicle.STATUS_CHOICES:
        count = Vehicle.objects.filter(status=status).count()
        print(f"  - {label}: {count}")

    # Por título
    print("\nPor Título:")
    for title, label in Vehicle.TITLE_STATUS_CHOICES:
        count = Vehicle.objects.filter(title_status=title).count()
        if count > 0:
            print(f"  - {label}: {count}")

    # Fichas de inspeção
    vehicles_with_inspections = 0
    vehicles_without_inspections = 0

    for vehicle in Vehicle.objects.all():
        if vehicle.inspections.exists():
            vehicles_with_inspections += 1
        else:
            vehicles_without_inspections += 1

    print("\nFichas de Inspeção:")
    print(f"  - Com fichas: {vehicles_with_inspections}")
    print(f"  - Sem fichas: {vehicles_without_inspections}")

    # VINs
    with_vin = Vehicle.objects.exclude(vin__isnull=True).exclude(vin='').count()
    without_vin = total - with_vin
    print("\nVINs:")
    print(f"  - Com VIN: {with_vin}")
    print(f"  - Sem VIN: {without_vin}")


if __name__ == '__main__':
    print("="*60)
    print("CORREÇÃO DE REGISTROS DO BANCO DE DADOS")
    print("="*60)
    print()

    try:
        # Executar correções
        inspections_fixed = fix_missing_inspections()
        titles_fixed = fix_title_status()
        vins_fixed = fix_duplicate_empty_vins()

        # Mostrar estatísticas
        show_statistics()

        # Resumo
        print("\n" + "="*60)
        print("RESUMO DAS CORREÇÕES")
        print("="*60)
        print(f"✓ Fichas de inspeção criadas: {inspections_fixed}")
        print(f"✓ Títulos corrigidos: {titles_fixed}")
        print(f"✓ VINs vazios corrigidos: {vins_fixed}")
        print("="*60)
        print("\n✓ Correções concluídas com sucesso!")
        print()

    except Exception as e:
        print(f"\n❌ Erro durante a correção: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
