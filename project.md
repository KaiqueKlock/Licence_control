# Projeto Demo para Publicacao no GitHub

## Objetivo

Criar uma versao publica que represente o fluxo do projeto original sem expor:

- dados pessoais
- nomes de empresa
- links internos
- arquivos de base reais

## O que foi feito

1. Criado um projeto paralelo em `demo_public/`.
2. Criadas bases sinteticas em `demo_public/data/`.
3. Implementado gerador de dashboards em `demo_public/src/generate_demo_dashboard.py`.
4. Configurado `.gitignore` com politica de seguranca para publicar somente demo + docs.

## Funcionalidades da demo

- Leitura de bases CSV de usuarios e licencas.
- Cruzamento de dados por `user_id`.
- Classificacao de status por ultimo login:
  - `Active` (ate 45 dias)
  - `Warning` (46 a 90 dias)
  - `Inactive` (acima de 90 dias)
  - `No record` (sem logon)
- Pagina central (`home.html`) com cards por unidade.
- Dashboards por unidade com:
  - visao geral por servico
  - tabela de licencas de infraestrutura
  - tabela de licencas SAP

## Como rodar

No terminal:

```bash
cd demo_public
python -m pip install -r requirements.txt
python src/generate_demo_dashboard.py
```

Arquivos gerados:

- `demo_public/output/home.html`
- `demo_public/output/index_<LOCATION>.html`

## Estrutura de pastas

```text
demo_public/
  data/
    users_directory.csv
    license_inventory.csv
    sap_assignments.csv
  src/
    generate_demo_dashboard.py
  output/
  requirements.txt
  README.md
```

## Checklist antes de publicar

1. Rodar varredura de termos sensiveis:
   - `rg -n -i "<company_name>|<internal_domain>|<private_link>"`
2. Conferir o que vai para commit:
   - `git status`
   - `git add .`
   - `git diff --cached`
3. Confirmar que somente `demo_public/`, `.gitignore`, `project.md` e `README.md` estao staged.
