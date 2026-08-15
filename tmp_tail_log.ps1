$log = (Get-ChildItem 'f:\Kernschmied\artifacts\logs\backend-*.log' | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
Write-Host "Tailing log: $log"
Get-Content -Path $log -Tail 0 -Wait | Select-String -Pattern 'CHAT_ROUTE_ENTRY|CHAT_CONTEXT|CONFIG_PROMPT|PROMPT_CHAIN|EFFECTIVE_PROMPT|prompt_resolution_completed|Pre-insert system prompt|GENERATION_REQUEST|model_service_generation_handoff|OLLAMA_PAYLOAD' -SimpleMatch
