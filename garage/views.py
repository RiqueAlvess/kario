from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
from datetime import datetime
import requests
import csv
import cloudinary.uploader
from .models import Vehicle, InspectionTemplate, VehicleInspection, Photo, Sale

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
    vehicles = Vehicle.objects.all()
    
    search = request.GET.get('search', '')
    if search:
        vehicles = vehicles.filter(
            Q(make__icontains=search) | 
            Q(model__icontains=search) | 
            Q(vin__icontains=search)
        )
    
    make_filter = request.GET.get('make', '')
    if make_filter:
        vehicles = vehicles.filter(make=make_filter)
    
    year_filter = request.GET.get('year', '')
    if year_filter:
        vehicles = vehicles.filter(year=year_filter)
    
    title_filter = request.GET.get('title_status', '')
    if title_filter:
        vehicles = vehicles.filter(title_status=title_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)
    
    value_min = request.GET.get('value_min', '')
    if value_min:
        vehicles = vehicles.filter(value__gte=value_min)
    
    value_max = request.GET.get('value_max', '')
    if value_max:
        vehicles = vehicles.filter(value__lte=value_max)
    
    makes = Vehicle.objects.values_list('make', flat=True).distinct().order_by('make')
    years = Vehicle.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    return render(request, 'vehicle_list.html', {
        'vehicles': vehicles,
        'makes': makes,
        'years': years,
        'search': search,
        'make_filter': make_filter,
        'year_filter': year_filter,
        'title_filter': title_filter,
        'status_filter': status_filter,
        'value_min': value_min,
        'value_max': value_max,
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
            exterior_color=request.POST.get('exterior_color'),
            interior_color=request.POST.get('interior_color'),
            miles=request.POST.get('miles'),
            mpg=request.POST.get('mpg', ''),
            title_status=request.POST.get('title_status'),
            title_problem_description=request.POST.get('title_problem_description', ''),
            value=request.POST.get('value'),
            general_notes=request.POST.get('general_notes', ''),
            status='FALTA_INSPECAO'
        )
        
        for template in InspectionTemplate.objects.all():
            VehicleInspection.objects.create(vehicle=vehicle, template=template)
        
        if 'vehicle_data' in request.session:
            del request.session['vehicle_data']
        
        messages.success(request, 'Veículo adicionado! Complete a ficha técnica.')
        return redirect('inspection_update', pk=vehicle.id)
    
    return render(request, 'vehicle_form.html', {'vehicle_data': vehicle_data})

@login_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        vehicle.year = request.POST.get('year')
        vehicle.make = request.POST.get('make')
        vehicle.model = request.POST.get('model')
        vehicle.trim = request.POST.get('trim', '')
        vehicle.vin = request.POST.get('vin', '')
        vehicle.engine = request.POST.get('engine', '')
        vehicle.transmission = request.POST.get('transmission', '')
        vehicle.train = request.POST.get('train', '')
        vehicle.exterior_color = request.POST.get('exterior_color')
        vehicle.interior_color = request.POST.get('interior_color')
        vehicle.miles = request.POST.get('miles')
        vehicle.mpg = request.POST.get('mpg', '')
        vehicle.title_status = request.POST.get('title_status')
        vehicle.title_problem_description = request.POST.get('title_problem_description', '')
        vehicle.value = request.POST.get('value')
        vehicle.status = request.POST.get('status')
        vehicle.general_notes = request.POST.get('general_notes', '')
        vehicle.save()
        
        messages.success(request, 'Veículo atualizado com sucesso!')
        return redirect('vehicle_detail', pk=vehicle.id)
    
    return render(request, 'vehicle_form.html', {'vehicle': vehicle})

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    inspections = vehicle.inspections.select_related('template').order_by('template__order')
    photos = vehicle.photos.all()
    return render(request, 'vehicle_detail.html', {
        'vehicle': vehicle, 
        'inspections': inspections,
        'photos': photos
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

@login_required
def photo_upload(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        files = request.FILES.getlist('photos')
        description = request.POST.get('description', '')
        
        for file in files:
            try:
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder=f"kario_garage/vehicles/{vehicle.id}",
                    resource_type="auto"
                )
                
                Photo.objects.create(
                    vehicle=vehicle,
                    image_url=upload_result['secure_url'],
                    cloudinary_public_id=upload_result['public_id'],
                    description=description
                )
            except Exception as e:
                messages.error(request, f'Erro ao fazer upload da imagem: {str(e)}')
                continue
        
        messages.success(request, f'{len(files)} foto(s) adicionada(s)!')
        return redirect('vehicle_detail', pk=vehicle.id)
    
    return render(request, 'photo_upload.html', {'vehicle': vehicle})

@login_required
def photo_delete(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    vehicle_id = photo.vehicle.id
    
    try:
        if photo.cloudinary_public_id:
            cloudinary.uploader.destroy(photo.cloudinary_public_id)
    except Exception as e:
        messages.warning(request, f'Foto removida do banco, mas erro ao deletar do Cloudinary: {str(e)}')
    
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