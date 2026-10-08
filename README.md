# OpiniAki

Site Django de avaliações do restaurante Sabor Cacoal. Clientes podem pesquisar
o conteúdo do site, avaliar pratos, atendimento e estabelecimento, e criar
contas para acessar o painel.

## Executar no Windows

Na pasta do projeto, execute `run.bat`. O script cria o ambiente virtual,
instala as dependências, aplica as migrações e inicia o servidor em
http://127.0.0.1:8000/.

Também é possível iniciar manualmente:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Se a porta 8000 já estiver ocupada, use `run.bat 8001` e abra
http://127.0.0.1:8001/. Para encerrar o servidor, pressione `Ctrl+C` no
terminal.

## Funcionalidades

- Busca por páginas e avaliações; a busca ignora diferenças entre letras
  maiúsculas e minúsculas e acentos.
- Cadastro e login com usuários armazenados no banco de dados Django.
- Painéis protegidos por sessão, com opção de sair.
- Envio de avaliações com nota e comentário; avaliações ficam no SQLite e
  alimentam os contadores, gráficos e listas dos painéis.
- Cadastro de pratos no painel. A lista de pratos é armazenada no navegador
  atual; avaliações e contas são armazenadas no banco de dados.

Não há uma conta administrativa padrão. Crie uma conta pela opção
**Cadastrar-se** e use-a para entrar no painel.

### Login com Google

O login utiliza o botão oficial do Google Identity Services e o Client ID
configurado no Django. Não precisa de Client Secret. No Google Cloud, adicione
à lista de origens JavaScript autorizadas a origem usada para abrir o site,
como `http://127.0.0.1:8000` (ou `http://localhost:8000`). O Django valida
assinatura, público e validade da credencial Google antes de criar ou autenticar
uma conta.

## Verificações

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test config
```

## Estrutura principal

- `config/`: configurações Django, rotas, API, autenticação, busca e testes.
- `HTML/`: páginas e templates.
- `css/`, `js/` e `imgs/`: estilos, scripts e imagens servidos pelo Django.
- `db.sqlite3`: banco de dados local de desenvolvimento.

O servidor de desenvolvimento e as configurações atuais são apenas para uso
local; antes de publicar o site, configure os parâmetros de produção do Django.
