# GitHub Auth Setup + Recovery (Windows)

This runbook standardizes Git auth for `FusionAL`, `mcp-consulting-kit`, and `Christopher-AI`.

## Current Recommended Mode

- Remote URL type: HTTPS
- Credential helper: Git Credential Manager (`manager`)
- Identity:
  - `user.name= JonathanMelton-FusionAL`
  - `user.email= puddintang6988@gmail.com`

## 1) Verify Auth State

```powershell
Set-Location "c:\Users\puddi\Projects\FusionAL"
git remote -v
git config --get credential.helper
git config --get user.name
git config --get user.email
git ls-remote --heads origin
```

Repeat for:

- `c:\Users\puddi\Projects\mcp-consulting-kit`
- `c:\Users\puddi\Projects\Christopher-AI`

If `git ls-remote` works, auth is valid.

## 2) Standardize Global Git Config

```powershell
git config --global credential.helper manager
git config --global user.name "JonathanMelton-FusionAL"
git config --global user.email "puddintang6988@gmail.com"
```

## 3) If Push/Pull Starts Failing

### A) Clear stale GitHub credential from Windows Credential Manager

1. Open **Credential Manager**
2. Go to **Windows Credentials**
3. Remove entries for `git:https://github.com`
4. Retry `git pull` or `git push` and sign in again

### B) Re-auth with GitHub CLI (optional but recommended)

```powershell
gh auth login
gh auth status
```

### C) Ensure remotes point to your repos

```powershell
Set-Location "c:\Users\puddi\Projects\FusionAL"
git remote set-url origin https://github.com/JonathanMelton-FusionAL/FusionAL

Set-Location "c:\Users\puddi\Projects\mcp-consulting-kit"
git remote set-url origin https://github.com/JonathanMelton-FusionAL/FusionAL-mcp-consulting-kit.git

Set-Location "c:\Users\puddi\Projects\Christopher-AI"
git remote set-url origin https://github.com/JonathanMelton-FusionAL/Christopher-AI.git
```

## 4) Optional SSH Mode (Only if you prefer SSH)

If you switch to SSH, do it consistently for all repos.

```powershell
ssh-keygen -t ed25519 -C "puddintang6988@gmail.com"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

Add the public key to GitHub, then test:

```powershell
ssh -T git@github.com
```

Then switch remotes to SSH.

## 5) Quick Health Check Command (All Repos)

```powershell
Set-Location "c:\Users\puddi\Projects\FusionAL"; git ls-remote --heads origin | Select-Object -First 1;
Set-Location "c:\Users\puddi\Projects\mcp-consulting-kit"; git ls-remote --heads origin | Select-Object -First 1;
Set-Location "c:\Users\puddi\Projects\Christopher-AI"; git ls-remote --heads origin | Select-Object -First 1
```

If all three return refs, Git auth is healthy.
