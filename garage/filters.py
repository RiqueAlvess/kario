import django_filters
from .models import Vehicle

class VehicleFilter(django_filters.FilterSet):
    """
    Django Filter for Vehicle model with comprehensive filtering options
    """
    # Search across multiple fields
    search = django_filters.CharFilter(method='filter_search', label='Buscar')

    # Exact match filters
    make = django_filters.CharFilter(lookup_expr='iexact', label='Marca')
    year = django_filters.NumberFilter(label='Ano')
    car_type = django_filters.ChoiceFilter(choices=Vehicle.CAR_TYPE_CHOICES, label='Tipo de Carro')
    status = django_filters.ChoiceFilter(choices=Vehicle.STATUS_CHOICES, label='Status')
    title_status = django_filters.ChoiceFilter(choices=Vehicle.TITLE_STATUS_CHOICES, label='Status do Título')

    # Range filters
    value_min = django_filters.NumberFilter(field_name='value', lookup_expr='gte', label='Valor Mínimo')
    value_max = django_filters.NumberFilter(field_name='value', lookup_expr='lte', label='Valor Máximo')

    miles_min = django_filters.NumberFilter(field_name='miles', lookup_expr='gte', label='Milhas Mínima')
    miles_max = django_filters.NumberFilter(field_name='miles', lookup_expr='lte', label='Milhas Máxima')

    class Meta:
        model = Vehicle
        fields = ['search', 'make', 'year', 'car_type', 'status', 'title_status', 'value_min', 'value_max', 'miles_min', 'miles_max']

    def filter_search(self, queryset, name, value):
        """
        Custom search filter that searches across make, model, and VIN
        """
        if value:
            from django.db.models import Q
            return queryset.filter(
                Q(make__icontains=value) |
                Q(model__icontains=value) |
                Q(vin__icontains=value)
            )
        return queryset
