# Chamado pelo Agendador de Tarefas do Windows todo dia.
# Roda uma sessao do Claude Code CLI (sem interacao humana) que executa o
# pipeline de invasoes VW ponta a ponta: download, processamento, dashboard
# e rascunho de e-mail.

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

$projeto = "C:\Users\marcusrifai\Desktop\Coude\assobrav-invasoes"
Set-Location $projeto

# Usa o token de longa duracao (claude setup-token) em vez da sessao OAuth
# normal, que expira apos um tempo e nao se renova sozinha num processo
# desatendido -- foi a causa da automacao ter parado silenciosamente antes.
foreach ($linha in Get-Content "$projeto\config\.env") {
    if ($linha -match '^CLAUDE_CODE_OAUTH_TOKEN=(.+)$') {
        $env:CLAUDE_CODE_OAUTH_TOKEN = $matches[1]
    }
}

$prompt = Get-Content "$projeto\scripts\prompt_diario.txt" -Raw
$logDir = "$projeto\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = "$logDir\$(Get-Date -Format 'yyyy-MM-dd_HHmm').log"

& "C:\Users\marcusrifai\.local\bin\claude.exe" -p $prompt --permission-mode bypassPermissions *> $logFile
