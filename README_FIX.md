# Script de Correção do Banco de Dados

## Uso

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute o script
python fix_database.py
```

## O que o script faz

### 1. Criar Fichas de Inspeção Faltantes

Verifica todos os veículos e cria fichas de inspeção para aqueles que não têm. Isso é essencial para veículos importados via CSV que podem não ter recebido fichas de inspeção.

```
✓ 2021 CHEVY SPARK 1LT - 44 fichas criadas
✓ 2020 HYUNDAI ELANTRA SE - 44 fichas criadas
...
✓ Total: 2200 fichas de inspeção criadas
```

### 2. Corrigir Status de Título

Atualiza veículos com status `NAO_LIMPO` para `REBUILT`, que é o status correto no sistema.

```
✓ 32 veículos atualizados: NAO_LIMPO → REBUILT
```

### 3. Corrigir VINs Vazios Duplicados

Converte VINs vazios (`''`) para `NULL`, permitindo múltiplos veículos sem VIN no banco de dados.

```
✓ 1 veículos com VIN vazio convertidos para NULL
```

### 4. Estatísticas do Banco

Mostra um resumo completo do banco de dados:

```
============================================================
ESTATÍSTICAS DO BANCO DE DADOS
============================================================
Total de veículos: 50

Por Status:
  - Falta Inspeção: 5
  - Disponível: 45
  - Vendido: 0
  - Em Mecânica: 0

Por Título:
  - Limpo: 18
  - Rebuilt: 32

Fichas de Inspeção:
  - Com fichas: 50
  - Sem fichas: 0

VINs:
  - Com VIN: 49
  - Sem VIN: 1
```

## Quando usar

Execute este script sempre que:

- ✓ Importar veículos via CSV
- ✓ Notar que fichas de inspeção estão faltando
- ✓ Precisar corrigir status de títulos
- ✓ Tiver problemas com VINs duplicados
- ✓ Quiser ver estatísticas do banco

## Segurança

O script é **seguro** e **idempotente**:
- ✓ Não remove dados
- ✓ Não sobrescreve informações existentes
- ✓ Pode ser executado múltiplas vezes sem problemas
- ✓ Mostra exatamente o que foi feito

## Outros Problemas Corrigidos

### Erro de VIN Duplicado

**Problema:** Ao adicionar veículo manualmente, erro aparecia:
```
UNIQUE constraint failed: garage_vehicle.vin
```

**Solução:** A view `vehicle_add` agora:
- Verifica se VIN já existe antes de criar
- Mostra mensagem de erro clara
- Converte VIN vazio para NULL

### Worker Timeout do Gunicorn

**Problema:** Operações longas (decode VIN) causavam timeout:
```
[CRITICAL] WORKER TIMEOUT (pid:36045)
```

**Solução:** Timeout do Gunicorn aumentado de 30s para 120s no `run_server.sh`
