$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$exportServer = Start-Process -FilePath python -ArgumentList "-m rts_export.server --port 8791" -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru

try {
    & npm.cmd run dev
} finally {
    if (!$exportServer.HasExited) {
        Stop-Process -Id $exportServer.Id -ErrorAction SilentlyContinue
    }
}
