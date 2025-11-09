from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
from datetime import datetime
import requests
import csv
import cloudinary.uploader
from .models import Vehicle, InspectionTemplate, VehicleInspection, Photo, Sale
from .filters import VehicleFilter
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
from pathlib import Path
import json

# Google Drive setup
BASE_DIR = Path(__file__).resolve().parent.parent
GOOGLE_DRIVE_FOLDER_ID = '1uWYLWudLgN0MDB94beKdKIQKcwYMwP3j'
SERVICE_ACCOUNT_FILE = BASE_DIR / 'api0-450008-858cfa3a3501.json'

def get_drive_service():
    """Get authenticated Google Drive service"""
    try:
        if not SERVICE_ACCOUNT_FILE.exists():
            return None
        credentials = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"Error initializing Google Drive: {e}")
        return None

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
    
    sales_by_month = Sale.objects.extra(
        select={'month': "TO_CHAR(sale_date, 'YYYY-MM')"}
    ).values('month').annotate(total=Count('id')).order_by('month')
    
    chart_labels = [s['month'] for s in sales_by_month]
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

def get_or_create_drive_folder(service, vehicle):
    """
    Create or get Google Drive folder for vehicle
    Folder name format: Nome_Modelo_Ano (e.g., Toyota_Camry_2020)
    """
    folder_name = f"{vehicle.make}_{vehicle.model}_{vehicle.year}"

    # Search for existing folder
    query = f"name='{folder_name}' and '{GOOGLE_DRIVE_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    try:
        results = service.files().list(q=query, fields='files(id, name)').execute()
        folders = results.get('files', [])

        if folders:
            return folders[0]['id']

        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    except Exception as e:
        print(f"Error creating/getting Google Drive folder: {e}")
        return None

def upload_to_drive(service, file, folder_id, filename):
    """Upload file to Google Drive"""
    try:
        from googleapiclient.http import MediaIoBaseUpload
        import io

        # Reset file pointer
        file.seek(0)

        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(file.read()),
            mimetype=file.content_type,
            resumable=True
        )

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        return uploaded_file.get('id')
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        return None

@login_required
@user_passes_test(is_staff_user, login_url='/dashboard/')
def photo_upload(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        description = request.POST.get('description', '')

        # Initialize Google Drive service
        drive_service = get_drive_service()
        drive_folder_id = None

        if drive_service:
            drive_folder_id = get_or_create_drive_folder(drive_service, vehicle)

        for file in files:
            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder=f"kario_garage/vehicles/{vehicle.id}",
                    resource_type="auto"
                )

                google_drive_id = None

                # Upload to Google Drive
                if drive_service and drive_folder_id:
                    google_drive_id = upload_to_drive(drive_service, file, drive_folder_id, file.name)

                Photo.objects.create(
                    vehicle=vehicle,
                    image_url=upload_result['secure_url'],
                    cloudinary_public_id=upload_result['public_id'],
                    google_drive_id=google_drive_id,
                    description=description,
                    uploaded_by=request.user
                )
            except Exception as e:
                messages.error(request, f'Erro ao fazer upload da imagem: {str(e)}')
                continue

        messages.success(request, f'{len(files)} foto(s) adicionada(s)!')
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

    # Delete from Google Drive if exists
    if photo.google_drive_id:
        try:
            drive_service = get_drive_service()
            if drive_service:
                drive_service.files().delete(fileId=photo.google_drive_id).execute()
        except Exception as e:
            print(f"Error deleting from Google Drive: {e}")

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