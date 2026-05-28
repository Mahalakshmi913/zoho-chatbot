$ErrorActionPreference = "Stop"
$files = @(
    "backend/auth/__init__.py",
    "backend/auth/zoho_oauth.py",
    "backend/auth/token_store.py",
    "backend/agents/__init__.py",
    "backend/agents/graph.py",
    "backend/agents/query_agent.py",
    "backend/agents/action_agent.py",
    "backend/tools/__init__.py",
    "backend/tools/zoho_tools.py",
    "backend/memory/__init__.py",
    "backend/memory/memory_store.py",
    "backend/__init__.py",
    "backend/main.py",
    "backend/zoho_client.py",
    "backend/config.py",
    "frontend/.keep"
)

foreach ($f in $files) {
    $dir = Split-Path $f -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    New-Item -ItemType File -Force -Path $f | Out-Null
}
