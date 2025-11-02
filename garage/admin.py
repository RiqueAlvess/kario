from django.contrib import admin
from .models import Vehicle, InspectionTemplate, VehicleInspection, Photo, Sale

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['year', 'make', 'model', 'status', 'title_status', 'value', 'created_at']
    list_filter = ['status', 'title_status', 'make']
    search_fields = ['make', 'model', 'vin']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(InspectionTemplate)
class InspectionTemplateAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'order']
    ordering = ['order']

@admin.register(VehicleInspection)
class VehicleInspectionAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'template', 'status']
    list_filter = ['status']
    search_fields = ['vehicle__make', 'vehicle__model']

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'vehicle', 'inspection', 'uploaded_at']
    list_filter = ['uploaded_at']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'sale_price', 'sale_date', 'buyer_name']
    list_filter = ['sale_date']
    search_fields = ['vehicle__make', 'vehicle__model', 'buyer_name']
    readonly_fields = ['created_at']