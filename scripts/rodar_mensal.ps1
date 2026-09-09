# Chamado pelo Agendador de Tarefas do Windows todo dia 01 do mes.
# Roda uma sessao do Claude Code CLI (sem interacao humana) que executa o
# FECHAMENTO MENSAL de invasoes VW: mes anterior inteiro, ponta a ponta.

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

$projeto = "C:\Users\marcusrifai\Desktop\Coude\assobrav-invasoes"
Set-Location $projeto

foreach ($linha in Get-Content "$projeto\config\.env") {
    if ($linha -match '^CLAUDE_CODE_OAUTH_TOKEN=(.+)$') {
        $env:CLAUDE_CODE_OAUTH_TOKEN = $matches[1]
    }
}

$prompt = Get-Content "$projeto\scripts\prompt_mensal.txt" -Raw
$logDir = "$projeto\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = "$logDir\mensal_$(Get-Date -Format 'yyyy-MM-dd_HHmm').log"

& "C:\Users\marcusrifai\.local\bin\claude.exe" -p $prompt --permission-mode bypassPermissions *> $logFile
