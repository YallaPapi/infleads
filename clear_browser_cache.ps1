# Browser Cache Cleaner Script

Write-Host "Starting browser cache cleanup..." -ForegroundColor Yellow
Write-Host ""

# Clear Chrome cache
$chromeCachePaths = @(
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache2",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\GPUCache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Service Worker\CacheStorage",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Service Worker\ScriptCache"
)

Write-Host "Clearing Chrome cache..." -ForegroundColor Cyan
foreach ($path in $chromeCachePaths) {
    if (Test-Path $path) {
        Write-Host "  Clearing: $path"
        try {
            Get-ChildItem -Path $path -File -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
            Get-ChildItem -Path $path -Directory -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "    Note: Some files in use, partial clear" -ForegroundColor Gray
        }
    }
}

# Clear Edge cache
$edgeCachePaths = @(
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache2",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Code Cache",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\GPUCache",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Service Worker\CacheStorage",
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Service Worker\ScriptCache"
)

Write-Host ""
Write-Host "Clearing Edge cache..." -ForegroundColor Cyan
foreach ($path in $edgeCachePaths) {
    if (Test-Path $path) {
        Write-Host "  Clearing: $path"
        try {
            Get-ChildItem -Path $path -File -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
            Get-ChildItem -Path $path -Directory -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "    Note: Some files in use, partial clear" -ForegroundColor Gray
        }
    }
}

# Clear Firefox cache
Write-Host ""
Write-Host "Clearing Firefox cache..." -ForegroundColor Cyan
$firefoxProfiles = "$env:LOCALAPPDATA\Mozilla\Firefox\Profiles"
if (Test-Path $firefoxProfiles) {
    Get-ChildItem $firefoxProfiles -Directory | ForEach-Object {
        $cachePath = Join-Path $_.FullName "cache2"
        if (Test-Path $cachePath) {
            Write-Host "  Clearing: $cachePath"
            try {
                Get-ChildItem -Path $cachePath -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            } catch {
                Write-Host "    Note: Some files in use, partial clear" -ForegroundColor Gray
            }
        }
    }
}

# Clear Windows temp files
Write-Host ""
Write-Host "Clearing Windows temp files..." -ForegroundColor Cyan
$tempPaths = @(
    $env:TEMP,
    "$env:WINDIR\Temp"
)

foreach ($path in $tempPaths) {
    if (Test-Path $path) {
        Write-Host "  Clearing: $path"
        try {
            Get-ChildItem -Path $path -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddHours(-1) } | Remove-Item -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "    Note: Some files in use, partial clear" -ForegroundColor Gray
        }
    }
}

# Clear DNS cache
Write-Host ""
Write-Host "Flushing DNS cache..." -ForegroundColor Cyan
try {
    ipconfig /flushdns | Out-Null
    Write-Host "  DNS cache flushed successfully" -ForegroundColor Green
} catch {
    Write-Host "  Could not flush DNS cache" -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Cache clearing complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "1. Close and restart your browser for best results" -ForegroundColor White
Write-Host "2. Use Ctrl+F5 to force refresh the page" -ForegroundColor White
Write-Host "3. Try opening in an incognito/private window" -ForegroundColor White
Write-Host ""
Write-Host "Now try accessing: http://localhost:5000" -ForegroundColor Cyan