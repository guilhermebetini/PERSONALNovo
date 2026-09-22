# OpiniAki — Sistema de Avaliações do Restaurante Oishi

Projeto Django desenvolvido para o restaurante japonês **Oishi**. O sistema permite aos clientes criar conta, fazer login, visualizar o cardápio, avaliar pratos e comentar sobre o atendimento e o ambiente do restaurante.

Como o sistema é voltado para um único restaurante (e não uma plataforma multi-restaurante), o app `restaurantes` foi ajustado para representar as informações fixas do **Oishi** (endereço, horário de funcionamento, fotos do ambiente) em vez de um cadastro genérico de vários estabelecimentos.

## Integrantes e Responsabilidades

| Integrante   | App | Responsabilidade Principal |
|--------------|---|---|
| Guilherme    | `contas` | Autenticação e gerenciamento de usuários |
| Lucivânia    | `restaurantes` | Cadastro de restaurante e pratos |
| Emanuele     | `pratos_avaliacoes` | Avaliações e comentários sobre pratos |
| Luiz Gustavo | `experiencia` | Avaliações sobre atendimento e ambiente |

---

## Estrutura do Projeto

```
projeto_avaliacoes/
├── contas/
├── restaurantes/
├── pratos_avaliacoes/
├── experiencia/
├── core/          # templates base, home, arquivos estáticos compartilhados
├── templates/
├── static/
├── media/
└── projeto_avaliacoes/  # settings, urls raiz
```

---

## App 1: `contas`

**Finalidade:** Cadastro, login, logout e gerenciamento de perfil de usuário.

**Integrante responsável:** Guilherme

### Models
- `Usuario` (ou `Profile` com `OneToOneField` para `User`) — foto, bio, data de cadastro

### Views
- `CadastroView`
- `LoginView`
- `LogoutView`
- `PerfilView`
- `EditarPerfilView`

### Arquivos criados/modificados
- `contas/models.py`
- `contas/views.py`
- `contas/forms.py`
- `contas/urls.py`
- `templates/contas/cadastro.html`
- `templates/contas/login.html`
- `templates/contas/perfil.html`
- `projeto_avaliacoes/settings.py` (configuração de `AUTH_USER_MODEL`, se aplicável)

### Responsabilidades específicas
- [ ] Decidir e configurar o modelo de usuário (`AUTH_USER_MODEL` ou `Profile`) **antes da primeira migration**
- [ ] Criar formulários de cadastro e login com validação
- [ ] Implementar proteção de rotas com `@login_required`
- [ ] Criar página de perfil do usuário

---

## App 2: `restaurantes`

**Finalidade:** Gerenciar as informações do restaurante Oishi (endereço, horário, fotos do ambiente) e o cadastro dos pratos do cardápio.

**Integrante responsável:** Lucivânia

> Como o sistema atende apenas ao Oishi, o model `Restaurante` pode ser único (registro fixo/singleton) ou simplesmente omitido, guardando os dados do restaurante direto no `settings.py` ou em uma página estática — a decisão fica a critério do grupo. Abaixo considera-se a versão com model, para manter flexibilidade caso o Oishi abra outra unidade no futuro.

### Models
- `Restaurante` — nome ("Oishi"), endereço, horário de funcionamento, telefone, foto do ambiente, descrição
- `Prato` — `ForeignKey(Restaurante)`, nome, descrição, preço, foto, categoria (ex: sushi, temaki, yakisoba, sobremesa, bebida)

### Views
- `HomeOishiView` (página inicial com dados do restaurante)
- `ListaPratosView` (cardápio, com filtro por categoria)
- `DetalhePratoView`
- `CadastrarPratoView`
- `EditarPratoView`

### Arquivos criados/modificados
- `restaurantes/models.py`
- `restaurantes/views.py`
- `restaurantes/forms.py`
- `restaurantes/urls.py`
- `templates/restaurantes/home.html`
- `templates/restaurantes/cardapio.html`
- `templates/restaurantes/detalhe_prato.html`
- `templates/restaurantes/form_prato.html`
- `projeto_avaliacoes/settings.py` (`MEDIA_ROOT`, `MEDIA_URL`)

### Responsabilidades específicas
- [ ] Cadastrar as informações fixas do Oishi (via fixture, migration de dados ou admin)
- [ ] Modelar relacionamento Restaurante → Prato (1:N)
- [ ] Configurar upload de imagens dos pratos e do ambiente
- [ ] Implementar filtro do cardápio por categoria (ex: sushi, temaki, yakisoba)

---

## App 3: `pratos_avaliacoes`

**Finalidade:** Avaliações e comentários dos usuários sobre os pratos.

**Integrante responsável:** Emanuele

### Models
- `AvaliacaoPrato` — `ForeignKey(Usuario)`, `ForeignKey(Prato)`, nota (1-5), comentário, data
- `RespostaComentario` *(opcional)*

### Views
- `CriarAvaliacaoPratoView`
- `ListaAvaliacoesPratoView`
- `EditarAvaliacaoView`
- `ExcluirAvaliacaoView`

### Arquivos criados/modificados
- `pratos_avaliacoes/models.py`
- `pratos_avaliacoes/views.py`
- `pratos_avaliacoes/forms.py`
- `pratos_avaliacoes/urls.py`
- `templates/pratos_avaliacoes/form_avaliacao.html`
- `templates/pratos_avaliacoes/lista.html`

### Responsabilidades específicas
- [ ] Garantir que um usuário avalie o mesmo prato apenas uma vez (`unique_together`)
- [ ] Calcular média de notas por prato (`aggregate`/`annotate`)
- [ ] Permitir editar/excluir avaliação apenas pelo autor

---

## App 4: `experiencia`

**Finalidade:** Avaliações sobre atendimento e ambiente do restaurante.

**Integrante responsável:** Luiz Gustavo

### Models
- `AvaliacaoExperiencia` — `ForeignKey(Usuario)`, `ForeignKey(Restaurante)`, nota atendimento, nota ambiente, comentário, data

### Views
- `CriarAvaliacaoExperienciaView`
- `ListaAvaliacoesExperienciaView`
- `EditarAvaliacaoExperienciaView`
- `ExcluirAvaliacaoExperienciaView`

### Arquivos criados/modificados
- `experiencia/models.py`
- `experiencia/views.py`
- `experiencia/forms.py`
- `experiencia/urls.py`
- `templates/experiencia/form_avaliacao.html`
- `templates/experiencia/lista.html`

### Responsabilidades específicas
- [ ] Definir critérios de nota (ex: 1-5 estrelas para atendimento e ambiente)
- [ ] Exibir médias agregadas na página do restaurante
- [ ] Implementar paginação/ordenação cronológica dos comentários

---

## Decisões a alinhar antes de iniciar o desenvolvimento

- [ ] **Modelo de usuário:** `User` padrão + `Profile` OU `AUTH_USER_MODEL` customizado (afeta todos os apps)
- [ ] **Namespaces de URL:** cada app deve definir `app_name` em seu `urls.py`
- [ ] **Template base compartilhado:** `base.html` no app `core` com navbar/footer comuns
- [ ] **Fluxo de Git:** branches por app/feature, convenção de commits e revisão de merge

---

## Tecnologias

- Python / Django
- SQLite (desenvolvimento) — *definir banco de produção, se aplicável*
- PyCharm
- Git / GitHub

---

