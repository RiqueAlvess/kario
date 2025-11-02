from django.core.management.base import BaseCommand
from garage.models import InspectionTemplate

class Command(BaseCommand):
    help = 'Popula os templates de inspeção'

    def handle(self, *args, **kwargs):
        InspectionTemplate.objects.all().delete()
        
        items = [
            'PINTURA RUIM?',
            'VIDRO QUEBRADO?',
            'PLÁSTICOS FALTANDO?',
            'SÍMBOLO FALTANDO?',
            'PALHETA DO LIMPADOR DE PARA-BRISA QUEBRADA?',
            'PNEU CARECA OU SUJO?',
            'LATARIA ENFERRUJADA?',
            'CALOTA FALTANDO OU QUEBRADA?',
            'FENDER LINER FALTANDO OU QUEBRADO?',
            'POLIR FARÓIS?',
            'MOTOR SUJO?',
            'ÓLEO PARA BRISA?',
            'COOLANT?',
            'PALHETA/CAPÔ FALTANDO?',
            'LUZES?',
            'MALA SUJA?',
            'TAMPA DA MALA?',
            'STEP?',
            'MACACO?',
            'CHAVE DE RODA?',
            'MAU CHEIRO?',
            'FUMANDO?',
            'POEIRA?',
            'ASPIRAR?',
            'VIDROS LIMPOS?',
            'DESENHO NO CHÃO?',
            'TAPETES?',
            'BANCO RASGADO OU SUJO?',
            'DESCANSO DE BRAÇO RASGADO?',
            'CHAVE RESERVA?',
            'ADESIVO DO ÓLEO?',
            'LUZ AIR BAG?',
            'LUZ DE PNEU?',
            'LIMPADOR?',
            'GASOLINA?',
            'AR CONDICIONADO?',
            'PORTA COPOS?',
            'VIDROS ELÉTRICOS?',
            'TRAVAS ELÉTRICAS?',
            'RÁDIO?',
            'SOM?',
            'CINTO DE SEGURANÇA FUNCIONANDO?',
            'ESCAPAMENTO FUMANDO?',
            'CÂMERA DE RÉ FUNCIONANDO?',
        ]
        
        for idx, item in enumerate(items, 1):
            InspectionTemplate.objects.create(
                item_name=item,
                order=idx
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ {len(items)} templates de inspeção criados!'))