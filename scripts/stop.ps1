Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Python- und Node-Prozesse wurden beendet."
