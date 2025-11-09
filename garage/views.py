from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from datetime import datetime
import requests
import csv
import cloudinary.uploader
from .models import Vehicle, InspectionTemplate, VehicleInspection, Photo, Sale
from .filters import VehicleFilter
import os
from pathlib import Path
import shutil

# Local storage setup
BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_IMAGES_DIR = BASE_DIR / "media" / "images"

def ensure_local_images_dir():
    """Ensure local images directory exists"""
    try:
        LOCAL_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating local images directory: {e}")
        return False

def is_staff_user(user):
    """Check if user is staff (admin) to allow modifications"""
    return user.is_staff or user.is_superuser

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Usuário ou senha inválidos')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    totals = Vehicle.objects.aggregate(
        disponivel=Count('id', filter=Q(status='DISPONIVEL')),
        vendido=Count('id', filter=Q(status='VENDIDO')),
        mecanica=Count('id', filter=Q(status='MECANICA')),
        falta_inspecao=Count('id', filter=Q(status='FALTA_INSPECAO')),
        limpo=Count('id', filter=Q(title_status='LIMPO')),
        nao_limpo=Count('id', filter=~Q(title_status='LIMPO'))
    )
    
    vehicles = Vehicle.objects.all()
    fichas_completas = 0
    fichas_incompletas = 0
    
    for vehicle in vehicles:
        if vehicle.is_inspection_complete():
            fichas_completas += 1
        else:
            fichas_incompletas += 1
    
    # Agrupar vendas por mês (compatível com SQLite e PostgreSQL)
    sales_by_month = Sale.objects.annotate(
        month=TruncMonth('sale_date')
    ).values('month').annotate(total=Count('id')).order_by('month')

    # Formatar labels no formato YYYY-MM
    chart_labels = [s['month'].strftime('%Y-%m') if s['month'] else '' for s in sales_by_month]
    chart_data = [s['total'] for s in sales_by_month]
    
    context = {
        'totals': totals,
        'fichas_completas': fichas_completas,
        'fichas_incompletas': fichas_incompletas,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'dashboard.html', context)

@login_required
def vehicle_list(request):
    # Use django-filter for comprehensive filtering
    vehicle_filter = VehicleFilter(request.GET, queryset=Vehicle.objects.all())

    # Get distinct values for dropdowns
    makes = Vehicle.objects.values_list('make', flat=True).distinct().order_by('make')
    years = Vehicle.objects.values_list('year', flat=True).distinct().order_by('-year')
    car_types = Vehicle.objects.values_list('car_type', flat=True).distinct().order_by('car_type')

    return render(request, 'vehicle_list.html', {
        'filter': vehicle_filter,
        'vehicles': vehicle_filter.qs,
        'makes': makes,
        'years': years,
        'car_types': car_types,
    })

@login_required
def decode_vin(request):
    if request.method == 'POST':
        vin = request.POST.get('vin', '').strip()
        year = request.POST.get('year', '')
        
        if len(vin) != 17:
            return render(request, 'decode_vin.html', {'error': 'VIN deve ter 17 caracteres'})
        
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json&modelyear={year}"
        
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            results = {item['Variable']: item['Value'] for item in data.get('Results', [])}
            
            vehicle_data = {
                'vin': vin,
                'year': results.get('Model Year', year),
                'make': results.get('Make', ''),
                'model': results.get('Model', ''),
                'trim': results.get('Trim', ''),
                'engine': results.get('Engine Model', ''),
                'transmission': results.get('Transmission Style', ''),
            }
            
            request.session['vehicle_data'] = vehicle_data
            return redirect('vehicle_add')
            
        except Exception as e:
            return render(request, 'decode_vin.html', {'error': f'Erro ao consultar VIN: {str(e)}'})
    
    return render(request, 'decode_vin.html')

@login_required
@user_passes_test(is_staff_user, login_url='/dashboard/')
def vehicle_add(request):
    vehicle_data = request.session.get('vehicle_data', {})

    if request.method == 'POST':
        vehicle = Vehicle.objects.create(
            year=request.POST.get('year'),
            make=request.POST.get('make'),
            model=request.POST.get('model'),
            trim=request.POST.get('trim', ''),
            vin=request.POST.get('vin', ''),
            engine=request.POST.get('engine', ''),
            transmission=request.POST.get('transmission', ''),
            train=request.POST.get('train', ''),
            car_type=request.POST.get('car_type', 'OUTROS'),
            exterior_color=request.POST.get('exterior_color'),
            interior_color=request.POST.get('interior_color', ''),
            miles=request.POST.get('miles'),
            mpg=request.POST.get('mpg', ''),
            title_status=request.POST.get('title_status'),
            title_problem_description=request.POST.get('title_problem_description', ''),
            value=request.POST.get('value'),
            general_notes=request.POST.get('general_notes', ''),
            status='FALTA_INSPECAO',
            updated_by=request.user
        )

        for template in InspectionTemplate.objects.all():
            VehicleInspection.objects.create(vehicle=vehicle, template=template)

        if 'vehicle_data' in request.session:
            del request.session['vehicle_data']

        messages.success(request, 'Veículo adicionado! Complete a ficha técnica.')
        return redirect('inspection_update', pk=vehicle.id)

    return render(request, 'vehicle_form.html', {'vehicle_data': vehicle_data})

@login_required
@user_passes_test(is_staff_user, login_url='/dashboard/')
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        vehicle.year = request.POST.get('year', vehicle.year)
        vehicle.make = request.POST.get('make', vehicle.make)
        vehicle.model = request.POST.get('model', vehicle.model)
        vehicle.trim = request.POST.get('trim', vehicle.trim or '')
        vehicle.vin = request.POST.get('vin', vehicle.vin or '')
        vehicle.engine = request.POST.get('engine', vehicle.engine or '')
        vehicle.transmission = request.POST.get('transmission', vehicle.transmission or '')
        vehicle.train = request.POST.get('train', vehicle.train or '')
        vehicle.car_type = request.POST.get('car_type', vehicle.car_type)
        vehicle.exterior_color = request.POST.get('exterior_color', vehicle.exterior_color)
        vehicle.interior_color = request.POST.get('interior_color', vehicle.interior_color or '')
        vehicle.miles = request.POST.get('miles', vehicle.miles)
        vehicle.mpg = request.POST.get('mpg', vehicle.mpg or '')
        vehicle.title_status = request.POST.get('title_status', vehicle.title_status)
        vehicle.title_problem_description = request.POST.get('title_problem_description', vehicle.title_problem_description or '')
        vehicle.value = request.POST.get('value', vehicle.value)
        vehicle.status = request.POST.get('status', vehicle.status)
        vehicle.general_notes = request.POST.get('general_notes', vehicle.general_notes or '')
        vehicle.updated_by = request.user
        vehicle.save()

        messages.success(request, 'Veículo atualizado com sucesso!')
        return redirect('vehicle_detail', pk=vehicle.id)

    return render(request, 'vehicle_form.html', {'vehicle': vehicle})

def calculate_utah_financing(vehicle_value):
    """
    Calculate financing estimate for Utah, USA
    Assumptions:
    - 20% down payment
    - 6.5% APR
    - 60 months (5 years) term
    """
    down_payment_percent = 0.20
    annual_rate = 0.065
    months = 60

    down_payment = float(vehicle_value) * down_payment_percent
    loan_amount = float(vehicle_value) - down_payment

    # Monthly interest rate
    monthly_rate = annual_rate / 12

    # Calculate monthly payment using loan formula
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    else:
        monthly_payment = loan_amount / months

    return {
        'vehicle_value': float(vehicle_value),
        'down_payment': round(down_payment, 2),
        'loan_amount': round(loan_amount, 2),
        'monthly_payment': round(monthly_payment, 2),
        'total_interest': round((monthly_payment * months) - loan_amount, 2),
        'total_cost': round((monthly_payment * months) + down_payment, 2),
        'apr': annual_rate * 100,
        'term_months': months
    }

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    inspections = vehicle.inspections.select_related('template').order_by('template__order')
    photos = vehicle.photos.all()

    # Calculate financing for Utah
    financing = calculate_utah_financing(vehicle.value)

    return render(request, 'vehicle_detail.html', {
        'vehicle': vehicle,
        'inspections': inspections,
        'photos': photos,
        'financing': financing,
        'is_staff': request.user.is_staff or request.user.is_superuser
    })

@login_required
def vehicle_sell(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        Sale.objects.create(
            vehicle=vehicle,
            sale_price=request.POST.get('sale_price'),
            sale_date=request.POST.get('sale_date'),
            buyer_name=request.POST.get('buyer_name', ''),
            notes=request.POST.get('notes', '')
        )
        vehicle.status = 'VENDIDO'
        vehicle.save()
        messages.success(request, 'Veículo vendido com sucesso!')
        return redirect('vehicle_list')
    
    return render(request, 'vehicle_sell.html', {'vehicle': vehicle})

@login_required
def inspection_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('status_'):
                inspection_id = key.replace('status_', '')
                inspection = VehicleInspection.objects.get(id=inspection_id)
                inspection.status = value
                inspection.observation = request.POST.get(f'obs_{inspection_id}', '')
                inspection.save()
        
        if vehicle.is_inspection_complete():
            vehicle.status = 'DISPONIVEL'
            vehicle.save()
            messages.success(request, 'Ficha técnica completa! Veículo marcado como DISPONÍVEL.')
        else:
            messages.info(request, f'Ficha técnica atualizada! Progresso: {vehicle.inspection_progress()}%')
        
        return redirect('vehicle_detail', pk=vehicle.id)
    
    inspections = vehicle.inspections.select_related('template').order_by('template__order')
    return render(request, 'inspection_form.html', {'vehicle': vehicle, 'inspections': inspections})

def save_image_locally(file, vehicle, filename):
    """
    Save image to local directory media/images/
    Filename format: NomeCarro_Ano_Modelo_originalname.ext
    Returns the local file path or None if failed
    """
    try:
        # Ensure directory exists
        if not ensure_local_images_dir():
            return None

        # Create filename: NomeCarro_Ano_Modelo_originalname.ext
        # Clean vehicle name for filename
        clean_make = vehicle.make.replace(' ', '_').replace('/', '_')
        clean_model = vehicle.model.replace(' ', '_').replace('/', '_')

        # Get file extension
        file_ext = os.path.splitext(filename)[1]
        base_name = os.path.splitext(filename)[0]

        # Create new filename
        new_filename = f"{clean_make}_{vehicle.year}_{clean_model}_{base_name}{file_ext}"

        # Full path
        file_path = LOCAL_IMAGES_DIR / new_filename

        # Save file
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return str(file_path)
    except Exception as e:
        print(f"Error saving file locally: {e}")
        return None

def delete_local_image(file_path):
    """Delete image from local storage"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting local file: {e}")
    return False

@login_required
@user_passes_test(is_staff_user, login_url='/dashboard/')
def photo_upload(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        description = request.POST.get('description', '')

        for file in files:
            try:
                # Upload to Cloudinary FIRST (before reading the file for local storage)
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder=f"kario_garage/vehicles/{vehicle.id}",
                    resource_type="auto"
                )

                # Reset file pointer to beginning before saving locally
                file.seek(0)

                # Save to local storage
                local_path = save_image_locally(file, vehicle, file.name)

                if not local_path:
                    messages.error(request, f'Erro ao salvar imagem localmente: {file.name}')
                    continue

                Photo.objects.create(
                    vehicle=vehicle,
                    image_url=upload_result['secure_url'],
                    cloudinary_public_id=upload_result['public_id'],
                    google_drive_id=local_path,  # Storing local path in this field now
                    description=description,
                    uploaded_by=request.user
                )
            except Exception as e:
                messages.error(request, f'Erro ao fazer upload da imagem: {str(e)}')
                continue

        messages.success(request, f'{len(files)} foto(s) adicionada(s) e salvas em media/images/')
        return redirect('vehicle_detail', pk=vehicle.id)

    return render(request, 'photo_upload.html', {'vehicle': vehicle})

@login_required
@user_passes_test(is_staff_user, login_url='/dashboard/')
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    vehicle_id = photo.vehicle.id

    try:
        if photo.cloudinary_public_id:
            cloudinary.uploader.destroy(photo.cloudinary_public_id)
    except Exception as e:
        messages.warning(request, f'Foto removida do banco, mas erro ao deletar do Cloudinary: {str(e)}')

    # Delete from local storage if exists
    if photo.google_drive_id:  # This field now stores local path
        delete_local_image(photo.google_drive_id)

    photo.delete()
    messages.success(request, 'Foto removida!')
    return redirect('vehicle_detail', pk=vehicle_id)

@login_required
def report_inventory(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="inventario_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ano', 'Marca', 'Modelo', 'VIN', 'Cor', 'Milhas', 'Valor', 'Status', 'Título'])
    
    for vehicle in Vehicle.objects.filter(status='DISPONIVEL'):
        writer.writerow([vehicle.year, vehicle.make, vehicle.model, vehicle.vin, vehicle.exterior_color, 
                        vehicle.miles, vehicle.value, vehicle.status, vehicle.title_status])
    
    return response

@login_required
def report_mechanics(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mecanica_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ano', 'Marca', 'Modelo', 'VIN', 'Itens para Reparar'])
    
    for vehicle in Vehicle.objects.filter(status='MECANICA'):
        repairs = vehicle.inspections.filter(status='SIM').values_list('template__item_name', flat=True)
        writer.writerow([vehicle.year, vehicle.make, vehicle.model, vehicle.vin, ', '.join(repairs)])
    
    return response

@login_required
def report_sales(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="vendas_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Data', 'Ano', 'Marca', 'Modelo', 'VIN', 'Preço Venda', 'Comprador'])
    
    for sale in Sale.objects.select_related('vehicle').order_by('-sale_date'):
        writer.writerow([sale.sale_date, sale.vehicle.year, sale.vehicle.make, sale.vehicle.model, 
                        sale.vehicle.vin, sale.sale_price, sale.buyer_name])
    
    return response