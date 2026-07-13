# Chamado pelo Agendador de Tarefas do Windows todo dia.
# Roda uma sessao do Claude Code CLI (sem interacao humana) que executa o
# pipeline de invasoes VW ponta a ponta: download, processamento, dashboard
# e rascunho de e-mail.

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

$projeto = "C:\Users\marcusrifai\Desktop\Coude\assobrav-invasoes"
Set-Location $projeto

$prompt = Get-Content "$projeto\scripts\prompt_diario.txt" -Raw
$logDir = "$projeto\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = "$logDir\$(Get-Date -Format 'yyyy-MM-dd_HHmm').log"

& "C:\Users\marcusrifai\.local\bin\claude.exe" -p $prompt --permission-mode bypassPermissions *> $logFile
