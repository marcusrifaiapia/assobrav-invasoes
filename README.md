# Monitor de Invasões VW — Assobrav

Automação diária que acessa o portal da Assobrav, baixa o relatório pronto de
**Invasão** (Operacionais > Área de Cobertura > Invasão, filtrado em modo
"Grupo Econômico") e gera um relatório consolidado: grupos que mais invadiram,
modelos e chassis, cobrindo as 4 ADVEs do grupo (Araraquara — que já inclui
Matão e Rincão —, Rio Claro, Araras e Pirassununga).

O próprio relatório do Assobrav, em modo "Grupo Econômico", já exclui vendas
entre as lojas do grupo (estoque compartilhado entre as unidades), então toda
linha do relatório já é uma invasão de verdade — não precisamos mais comparar
códigos de loja na mão.

## Status: pipeline completo em produção, rodando sozinho todo dia às 10:00

Validado ponta a ponta com dados reais, inclusive via execução automática (não
só manual):
1. `login_e_download.py` loga no Assobrav e baixa `downloads/<data>/invasao.xlsx`.
2. `processa_relatorio.py` gera `reports/<data>.xlsx` com os rankings.
3. `gera_dashboard.py` gera `reports/<data>.html` (dashboard autônomo).
4. `publica_github.py` publica o dashboard em **https://marcusrifaiapia.github.io/assobrav-invasoes/**
   via GitHub Pages — link público, sem precisar de conta Claude nem GitHub
   para visualizar (o repositório `docs/` é a fonte da página; commit/push
   automático a cada execução).
5. `gera_email_html.py` gera o corpo do e-mail (HTML + texto simples).
6. `cria_rascunho_gmail.py` cria o **rascunho** direto na pasta Rascunhos do
   Gmail via IMAP + Senha de App (nunca envia sozinho). **Não** usa a
   ferramenta `create_draft` do Gmail (MCP) — ela não fica disponível na
   sessão do Claude Code CLI standalone usada pela Tarefa Agendada.
7. Uma Tarefa Agendada do Windows (`Assobrav_Invasoes_Diario`, todo dia às
   10:00) chama o Claude Code CLI com o prompt em `scripts/prompt_diario.txt`,
   que roda todos os passos acima.

Log de cada execução automática fica em `logs/<data>_<hora>.log`.

### Problemas já resolvidos (histórico, para não repetir o diagnóstico)

- **OAuth do Claude Code CLI expirou** (parou de rodar entre 05/08 e 23/08
  sem nenhum aviso — os logs só mostravam "OAuth session expired and could
  not be refreshed"). Corrigido usando `claude setup-token` (token de longa
  duração, válido por 1 ano, guardado em `CLAUDE_CODE_OAUTH_TOKEN` no
  `.env` e exportado por `rodar_diario.ps1`). **Quando esse token expirar de
  novo (~08/2027), repetir**: rodar `claude setup-token` num terminal
  interativo, copiar o token novo pro `.env`.
- **Rascunho de e-mail não era criado na execução automática**: a ferramenta
  `create_draft` do Gmail (MCP) só existe na sessão interativa do app
  Desktop, não no CLI standalone que a Tarefa Agendada usa. Resolvido com
  `cria_rascunho_gmail.py` (IMAP + Senha de App do Gmail, ver `GMAIL_APP_PASSWORD`
  no `.env`).

**Atenção**: o repositório `marcusrifaiapia/assobrav-invasoes` no GitHub é
**público** (exigência do GitHub Pages gratuito) — os dados de invasão
(chassis, grupos concorrentes, municípios) ficam publicamente acessíveis por
link, sem controle de acesso. Decisão consciente, já confirmada.

## Pendências conhecidas

- **"Oportunidades"** (concorrentes vendendo modelo equivalente a algum VW,
  sem ser invasão direta): existia num script anterior (`Desktop\Assobrav\
  assobrav_invasoes.py`) mas com bug real de extração (dados duplicados/
  corrompidos). Adiado — reconstruir exigiria refazer o loop por fabricante
  com mais cuidado, ou achar um relatório pronto equivalente ao de Invasão
  (ainda não encontrado).
- Mapeamento de código DN → nome do grupo em `config/mapa_grupos.json` cobre
  só os grupos já vistos (Discasa, Tarraf, Itacuã, Germânica, Carrera Acelera).
  Novos códigos aparecem como "DN <código> (grupo não cadastrado)" até serem
  cadastrados ali.

## Como as credenciais são guardadas

Copie `config/.env.example` para `config/.env` e preencha usuário e senha do
Assobrav ali. Esse arquivo fica **só no seu computador**, nunca é enviado
para o Claude nem versionado em git.

## Estrutura

```
scripts/
  login_e_download.py   -> Playwright: loga no Assobrav, filtra o relatorio de
                            Invasao (modo Grupo Economico) e exporta o Excel
  processa_relatorio.py -> pandas: le o Excel exportado e gera ranking de
                            grupos invasores, modelos, municipios e detalhe
  gera_dashboard.py     -> gera o dashboard HTML autonomo (light/dark)
  publica_github.py     -> copia o dashboard para docs/ e faz commit+push
                            (publicacao no GitHub Pages, com retentativa)
  gera_email_html.py    -> gera o corpo do e-mail (HTML profissional + texto)
  cria_rascunho_gmail.py -> cria o rascunho no Gmail via IMAP (Senha de App)
  prompt_diario.txt     -> prompt usado pelo Claude Code CLI na execucao diaria
  rodar_diario.ps1      -> wrapper chamado pela Tarefa Agendada do Windows
downloads/<data>/invasao.xlsx  -> relatorio bruto baixado no dia (nao versionado)
reports/<data>.xlsx            -> Excel consolidado (rankings + detalhe, nao versionado)
reports/<data>.html            -> dashboard do dia (nao versionado)
docs/index.html                -> copia publica do dashboard mais recente (versionado, publico)
docs/<data>.html                -> historico de dashboards publicados (versionado, publico)
logs/<data>_<hora>.log         -> log de cada execucao automatica (nao versionado)
config/.env                    -> credenciais + token GitHub (nao versionar)
config/mapa_grupos.json        -> mapa codigo DN -> nome do grupo invasor
```

## Tarefa Agendada do Windows

Nome: `Assobrav_Invasoes_Diario` — roda todo dia às 10:00.
Comandos úteis (PowerShell):
```
Get-ScheduledTask -TaskName "Assobrav_Invasoes_Diario"        # ver status
Start-ScheduledTask -TaskName "Assobrav_Invasoes_Diario"      # rodar agora
Disable-ScheduledTask -TaskName "Assobrav_Invasoes_Diario"    # pausar
Unregister-ScheduledTask -TaskName "Assobrav_Invasoes_Diario" # remover
```
