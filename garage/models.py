from django.db import models
from django.contrib.auth.models import User
import uuid

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('FALTA_INSPECAO', 'Falta Inspeção'),
        ('DISPONIVEL', 'Disponível'),
        ('VENDIDO', 'Vendido'),
        ('MECANICA', 'Em Mecânica'),
    ]
    
    TITLE_STATUS_CHOICES = [
        ('LIMPO', 'Limpo'),
        ('SALVAGE', 'Salvage'),
        ('REBUILT', 'Rebuilt'),
        ('OUTROS', 'Outros'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.IntegerField()
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    trim = models.CharField(max_length=100, blank=True, null=True)
    vin = models.CharField(max_length=17, blank=True, null=True, unique=True)
    engine = models.CharField(max_length=200, blank=True, null=True)
    transmission = models.CharField(max_length=100, blank=True, null=True)
    train = models.CharField(max_length=50, blank=True, null=True)
    exterior_color = models.CharField(max_length=50)
    interior_color = models.CharField(max_length=50)
    miles = models.IntegerField()
    mpg = models.CharField(max_length=50, blank=True, null=True)
    title_status = models.CharField(max_length=20, choices=TITLE_STATUS_CHOICES, default='LIMPO')
    title_problem_description = models.TextField(blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FALTA_INSPECAO')
    general_notes = models.TextField(blank=True, null=True, verbose_name='Observações Gerais')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model}"
    
    def inspection_progress(self):
        total = InspectionTemplate.objects.count()
        if total == 0:
            return 0
        completed = self.inspections.exclude(status='NAO_RESPONDIDO').count()
        return int((completed / total) * 100)
    
    def is_inspection_complete(self):
        total = InspectionTemplate.objects.count()
        completed = self.inspections.exclude(status='NAO_RESPONDIDO').count()
        return completed == total and total > 0

class InspectionTemplate(models.Model):
    item_name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.item_name

class VehicleInspection(models.Model):
    STATUS_CHOICES = [
        ('SIM', 'Sim'),
        ('NAO', 'Não'),
        ('NAO_RESPONDIDO', 'Não Respondido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='inspections')
    template = models.ForeignKey(InspectionTemplate, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NAO_RESPONDIDO')
    observation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['vehicle', 'template']
    
    def __str__(self):
        return f"{self.vehicle} - {self.template.item_name}"

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    inspection = models.ForeignKey(VehicleInspection, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    image_url = models.URLField(max_length=500)
    cloudinary_public_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo {self.id}"

class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.OneToOneField(Vehicle, on_delete=models.CASCADE, related_name='sale')
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateField()
    buyer_name = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Venda - {self.vehicle}"