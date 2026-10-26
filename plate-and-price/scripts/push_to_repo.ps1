# Copy this project into the clone of github.com/panurjoma/Mecha (folder _repo) and push the current branch.
# usage (PowerShell, from anywhere):  .\push_to_repo.ps1 "commit message"
# First time only:  git clone https://github.com/panurjoma/Mecha ..\_repo   (Git Credential Manager asks you to sign in)
# Skipped on purpose: raw footage, rendered outputs, wav files, .env, the clone itself, caches.
param([Parameter(Mandatory = $true)][string]$Message)
$proj = Split-Path -Parent $PSScriptRoot
$repo = Join-Path $proj "_repo"
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Clone the repo first: git clone https://github.com/panurjoma/Mecha `"$repo`"" }
$dest = Join-Path $repo "plate-and-price"
New-Item -ItemType Directory -Force $dest | Out-Null
robocopy $proj $dest /MIR /XD _repo output __pycache__ .git /XF .env raw*.mp4 *.wav *.pyc /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }
Set-Location $repo
# git writes CRLF warnings to stderr, so check exit codes instead of stopping on stderr
git add plate-and-price 2>$null
if (-not (git status --porcelain)) { "Nothing to commit"; return }
git commit -m $Message
if ($LASTEXITCODE -ne 0) { throw "commit failed" }
git push -u origin HEAD
if ($LASTEXITCODE -ne 0) { throw "push failed" }
