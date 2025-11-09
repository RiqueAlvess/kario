# Como Importar Veículos do CSV

## Passo 1: Prepare seu arquivo CSV

Salve seus dados de inventário em um arquivo CSV (exemplo: `vehicles.csv`)

O formato esperado é:
```
,,INVENTORY,YEAR,MAKE,MODEL,,,,ENGINE,TRANSMISSION,DRIVE,COLOR,MILES,MPG,CLEAN,VALUE
,,VIN,,,,CHAVE,FOTO,RELATORIO,,,TRAIN,,,,TITLE?,
,SE,KL8CD6SA4MC749858,2021,CHEVY,SPARK 1LT,OK,,OK,"V4,ECOTEC,1.4L",CVT,FWD,BEIGE,37170,33,NO,$11.950
...
```

## Passo 2: Execute o script de importação

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute o script
python import_vehicles.py vehicles.csv
```

## Passo 3: Aguarde a importação

O script irá:
- ✓ Ler o CSV
- ✓ Criar todos os veículos no banco de dados
- ✓ Criar fichas de inspeção para cada veículo
- ✓ Classificar automaticamente o tipo de veículo (Sedan, SUV, etc)
- ✓ Limpar e formatar dados automaticamente

## Mapeamento de Colunas

O script mapeia automaticamente:

| Coluna CSV | Campo no Sistema |
|------------|------------------|
| YEAR | Ano |
| MAKE | Marca |
| MODEL | Modelo |
| VIN | VIN |
| ENGINE | Motor |
| TRANSMISSION | Transmissão |
| DRIVE | Tração |
| COLOR | Cor Exterior |
| MILES | Milhagem |
| MPG | Consumo |
| CLEAN (YES/NO) | Status do Título |
| VALUE | Valor |

## Status dos Veículos

- **SE** → DISPONIVEL
- **E** → DISPONIVEL
- Outros → FALTA_INSPECAO

## Notas

- Veículos sem ano, marca ou modelo serão ignorados
- O script cria automaticamente um usuário admin (admin/admin123) se não existir
- Dados de valores monetários serão limpos automaticamente (remove $, vírgulas, etc)
- A milhagem será convertida para número inteiro
