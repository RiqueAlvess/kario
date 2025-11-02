from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_add, name='vehicle_add'),
    path('vehicles/decode/', views.decode_vin, name='decode_vin'),
    path('vehicles/<uuid:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<uuid:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<uuid:pk>/sell/', views.vehicle_sell, name='vehicle_sell'),
    path('vehicles/<uuid:pk>/inspection/', views.inspection_update, name='inspection_update'),
    path('vehicles/<uuid:pk>/photos/', views.photo_upload, name='photo_upload'),
    path('photos/<uuid:pk>/delete/', views.photo_delete, name='photo_delete'),
    path('reports/inventory/', views.report_inventory, name='report_inventory'),
    path('reports/mechanics/', views.report_mechanics, name='report_mechanics'),
    path('reports/sales/', views.report_sales, name='report_sales'),
]