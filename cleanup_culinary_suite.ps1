$ROOT = "C:\culinary_decision_suite"

Write-Host "Start cleanup..." -ForegroundColor Cyan

# -------------------------
# Remove __pycache__
# -------------------------
Get-ChildItem -Path $ROOT -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Write-Host "Removing $($_.FullName)"
    Remove-Item $_.FullName -Recurse -Force
}

# -------------------------
# Remove pytest cache
# -------------------------
$pytest = Join-Path $ROOT ".pytest_cache"
if (Test-Path $pytest) {
    Write-Host "Removing .pytest_cache"
    Remove-Item $pytest -Recurse -Force
}

# -------------------------
# Remove test image
# -------------------------
$testImage = Join-Path $ROOT "tests\peet_test_image.png"
if (Test-Path $testImage) {
    Write-Host "Removing test image"
    Remove-Item $testImage -Force
}

# -------------------------
# Create _project_notes
# -------------------------
$notes = Join-Path $ROOT "_project_notes"
if (!(Test-Path $notes)) {
    Write-Host "Creating _project_notes"
    New-Item -ItemType Directory -Path $notes | Out-Null
}

# -------------------------
# Move documentation files
# -------------------------
$filesToMove = @(
    "baken 11-1.txt",
    "baken 14.04",
    "baken_carrd_streamlit_desktop.txt",
    "bakens.ml",
    "CHAT_STARTBLOCK.md",
    "_inventaris_culinary_decision_suite.csv"
)

foreach ($file in $filesToMove) {
    $source = Join-Path $ROOT $file
    if (Test-Path $source) {
        Write-Host "Moving $file to _project_notes"
        Move-Item $source $notes
    }
}

# -------------------------
# Move legacy prompt to _deprecated
# -------------------------
$legacyPrompt = Join-Path $ROOT "core\orginele _prompts.py"
$deprecatedDir = Join-Path $ROOT "_deprecated"

if (Test-Path $legacyPrompt) {
    if (!(Test-Path $deprecatedDir)) {
        New-Item -ItemType Directory -Path $deprecatedDir | Out-Null
    }

    Write-Host "Archiving legacy prompt"
    Move-Item $legacyPrompt $deprecatedDir
}

Write-Host "Cleanup complete!" -ForegroundColor Green
