# Configuração OAuth 2.0 para Google Drive

## Visão Geral

O sistema Kario agora utiliza **OAuth 2.0 para aplicativos de desktop** para autenticar com o Google Drive e acessar fotos e arquivos.

## Requisitos

1. Arquivo de credenciais OAuth 2.0 do Google Cloud Console
2. Python 3.x com as dependências do requirements.txt instaladas

## Configuração Inicial

### 1. Obter Credenciais OAuth 2.0

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie ou selecione um projeto
3. Ative a **Google Drive API**
4. Vá em "Credenciais" → "Criar Credenciais" → "ID do cliente OAuth 2.0"
5. Selecione "Aplicativo de desktop"
6. Baixe o arquivo JSON de credenciais

### 2. Instalar o Arquivo de Credenciais

Renomeie e coloque o arquivo na raiz do projeto:

```bash
# O arquivo deve ter este nome exato:
client_secret_74999281138-kop5n416pehjtrumlq3vrcvk7rmmjaeu.apps.googleusercontent.com.json
```

**Localização:** `/home/user/kario/`

### 3. Escopos de Permissão

O sistema solicita os seguintes escopos OAuth:

- `https://www.googleapis.com/auth/drive` - Acesso completo ao Google Drive
- `https://www.googleapis.com/auth/drive.file` - Acesso a arquivos criados pela aplicação
- `https://www.googleapis.com/auth/drive.photos.readonly` - Leitura de fotos do Google Drive

## Fluxo de Autenticação

### Primeira Execução

1. Ao executar a aplicação pela primeira vez, a função `get_drive_service()` será chamada
2. Um navegador será aberto automaticamente
3. Faça login com sua conta Google
4. Autorize o acesso às permissões solicitadas
5. Um arquivo `token.json` será criado automaticamente na raiz do projeto

### Execuções Subsequentes

- O sistema usará o `token.json` armazenado
- Não será necessário reautenticar
- Se o token expirar, será renovado automaticamente usando o refresh token

## Estrutura de Arquivos

```
kario/
├── client_secret_74999281138-kop5n416pehjtrumlq3vrcvk7rmmjaeu.apps.googleusercontent.com.json  # Credenciais OAuth (não commitar)
├── token.json  # Token de acesso (gerado automaticamente, não commitar)
├── garage/
│   └── views.py  # Implementação do OAuth 2.0
└── .gitignore  # Exclui arquivos sensíveis
```

## Segurança

⚠️ **IMPORTANTE:**

- ✅ O `.gitignore` já está configurado para **NÃO** commitar:
  - `token.json`
  - `client_secret_*.json`
  - `api0-*.json`

- ❌ **NUNCA** compartilhe ou commite estes arquivos no Git
- ❌ **NUNCA** exponha as credenciais em logs ou mensagens de erro

## Implementação Técnica

### Função Principal: `get_drive_service()`

Localização: `garage/views.py:34-68`

```python
def get_drive_service():
    """Get authenticated Google Drive service using OAuth 2.0 for Desktop Apps"""
    # 1. Verifica se existe token salvo
    # 2. Valida o token
    # 3. Refresh se expirado
    # 4. Ou inicia novo fluxo OAuth se necessário
    # 5. Salva token para reutilização
    # 6. Retorna serviço autenticado
```

### Bibliotecas Utilizadas

- `google-auth-oauthlib` - Fluxo OAuth 2.0
- `google-auth` - Gerenciamento de credenciais
- `google-api-python-client` - Cliente da API do Google Drive

## Troubleshooting

### Erro: "Arquivo de credenciais não encontrado"

- Verifique se o arquivo `client_secret_74999281138-kop5n416pehjtrumlq3vrcvk7rmmjaeu.apps.googleusercontent.com.json` está na raiz do projeto
- Verifique se o nome do arquivo está correto

### Erro: "Token inválido"

- Delete o arquivo `token.json`
- Execute a aplicação novamente para reautenticar

### Navegador não abre automaticamente

- O sistema usará `run_local_server(port=0)` que seleciona uma porta disponível
- Verifique seu firewall
- Certifique-se de que há um navegador instalado no sistema

## Migração da Service Account

### Mudanças Principais

**Antes (Service Account):**
- Arquivo: `api0-450008-858cfa3a3501.json`
- Tipo: Service Account
- Escopo: `https://www.googleapis.com/auth/drive`

**Agora (OAuth 2.0 Desktop):**
- Arquivo: `client_secret_74999281138-kop5n416pehjtrumlq3vrcvk7rmmjaeu.apps.googleusercontent.com.json`
- Tipo: OAuth 2.0 Client ID (Desktop)
- Escopos: Drive completo + Photos readonly

### Vantagens do OAuth 2.0

✅ Autenticação em nome do usuário
✅ Refresh tokens automáticos
✅ Melhor controle de permissões
✅ Conformidade com políticas do Google
✅ Acesso a recursos do usuário (não apenas service account)

## Referências

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Drive API v3](https://developers.google.com/drive/api/v3/about-sdk)
- [Python Quickstart](https://developers.google.com/drive/api/quickstart/python)
