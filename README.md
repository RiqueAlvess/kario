# Kario - Sistema de Gestão de Veículos

Sistema Django para gerenciamento de inventário de veículos, inspeções e vendas.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone <repository-url>
cd kario
```

### 2. Crie e ative o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados

**IMPORTANTE:** Execute as migrações para criar as tabelas do banco de dados:

```bash
python manage.py migrate
```

### 5. Popule os templates de inspeção

**OBRIGATÓRIO:** Crie os itens do checklist de inspeção (44 itens):

```bash
python manage.py populate_inspection
```

Este comando cria todos os itens do checklist de inspeção que aparecerão na ficha técnica de cada veículo.

### 6. Crie um superusuário (opcional, para acessar o admin)

```bash
python manage.py createsuperuser
```

### 7. Execute o servidor

Para desenvolvimento:
```bash
./run_dev.sh
```

Para produção com Gunicorn:
```bash
./run_server.sh
```

## Problemas Comuns

### Checklist de Inspeção Vazio

Se a ficha técnica de inspeção não mostrar as perguntas (aparece vazio), você precisa popular os templates:

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Popule os templates de inspeção
python manage.py populate_inspection
```

Este comando cria 44 itens de inspeção que incluem verificações de:
- Pintura, vidros e lataria
- Pneus, rodas e componentes externos
- Motor e fluidos
- Interior e limpeza
- Eletrônicos e funcionalidades
- Sistema de segurança

### Erro: "no such table: garage_vehicle"

Este erro ocorre quando as migrações do banco de dados não foram executadas. Para resolver:

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute as migrações
python manage.py migrate
```

### Erro: "No module named 'django'"

Certifique-se de que o ambiente virtual está ativado e as dependências foram instaladas:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Estrutura do Projeto

- `garage/` - Aplicação principal do sistema
  - `models.py` - Modelos de dados (Vehicle, VehicleInspection, Photo, Sale)
  - `views.py` - Lógica das views
  - `urls.py` - Rotas da aplicação
  - `migrations/` - Migrações do banco de dados
- `kario/` - Configurações do projeto Django
- `templates/` - Templates HTML
- `static/` - Arquivos estáticos (CSS, JS, imagens)

## Funcionalidades

- Cadastro e gestão de veículos
- Sistema de inspeção de veículos
- Upload e gestão de fotos
- Registro de vendas
- Dashboard com estatísticas
- Autenticação de usuários

## Desenvolvimento

### Criar novas migrações

Após modificar os models:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Executar testes

```bash
python manage.py test
```

## Suporte

Para problemas ou dúvidas, abra uma issue no repositório do projeto.
