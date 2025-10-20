# ================================
# Push Local Docker Images to GitLab Container Registry
# Project: expenseinsights/expenseinsights
# ================================

# --- Step 1: Variables ---
$GitLabRegistry = "registry.gitlab.com"
$GitLabProject  = "expenseinsights/expenseinsights"
$Username       = "<YOUR_GITLAB_USERNAME>"       # e.g. dineshp
$Token          = "<YOUR_PERSONAL_ACCESS_TOKEN>" # Must have write_registry scope

# --- Step 2: Login ---
Write-Host "`n🔐 Logging in to $GitLabRegistry..." -ForegroundColor Cyan
docker logout $GitLabRegistry | Out-Null
$Token | docker login $GitLabRegistry -u $Username --password-stdin

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Login failed. Please check your token or username." -ForegroundColor Red
    exit 1
}

# --- Step 3: Tag all local images ---
Write-Host "`n🏷️  Tagging local images for GitLab registry..." -ForegroundColor Cyan
docker tag fireflyiii/data-importer:latest "$GitLabRegistry/$GitLabProject/fireflyiii-data-importer:latest"
docker tag alpine:latest                    "$GitLabRegistry/$GitLabProject/alpine:latest"
docker tag fireflyiii/core:latest           "$GitLabRegistry/$GitLabProject/fireflyiii-core:latest"
docker tag postgres:latest                  "$GitLabRegistry/$GitLabProject/postgres:latest"

# --- Step 4: Push all images ---
Write-Host "`n🚀 Pushing images to GitLab Container Registry..." -ForegroundColor Cyan
$images = @(
    "fireflyiii-data-importer:latest",
    "alpine:latest",
    "fireflyiii-core:latest",
    "postgres:latest"
)

foreach ($img in $images) {
    $fullPath = "$GitLabRegistry/$GitLabProject/$img"
    Write-Host "➡️  Pushing $fullPath..." -ForegroundColor Yellow
    docker push $fullPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed: $img" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Failed to push: $img" -ForegroundColor Red
    }
}

Write-Host "`n🎉 All done! Check your GitLab project → Deploy → Container Registry." -ForegroundColor Cyan
