# Starts the Vellum demo: FastAPI backend on :8000 and the React UI on :5173, both hidden,
# waits until both answer, then opens the browser.
#   powershell -ExecutionPolicy Bypass -File start_demo.ps1
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

function Test-Url($u) { try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 $u).StatusCode -eq 200 } catch { $false } }

if (-not (Test-Url "http://127.0.0.1:8000/api/health")) {
    Start-Process -WindowStyle Hidden -FilePath $py -WorkingDirectory $root `
        -ArgumentList "-m","uvicorn","backend.app:app","--host","127.0.0.1","--port","8000" `
        -RedirectStandardOutput "$root\backend.log" -RedirectStandardError "$root\backend.err.log"
}
if (-not (Test-Url "http://127.0.0.1:5173/")) {
    Start-Process -WindowStyle Hidden -FilePath "cmd.exe" -WorkingDirectory "$root\frontend" `
        -ArgumentList "/c","npx vite --host 127.0.0.1 --port 5173 --strictPort > ..\frontend.log 2>&1"
}

Write-Host "Waiting for backend (models load in ~20 s) and frontend..."
for ($i = 0; $i -lt 90; $i++) {
    if ((Test-Url "http://127.0.0.1:8000/api/health") -and (Test-Url "http://127.0.0.1:5173/")) { break }
    Start-Sleep -Seconds 2
}
Write-Host "Backend : http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:5173/"
Start-Process "http://127.0.0.1:5173/"
