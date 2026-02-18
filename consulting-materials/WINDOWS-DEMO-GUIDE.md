# Windows Demo Guide
## Run Your First MCP Server in 15 Minutes

This guide walks you through running the **Content Automation MCP** server on your Windows machine. No coding required — just copy-paste commands.

---

## Before You Start

**You'll need:**
- Windows 10 or 11
- 30 minutes of focused time
- Internet connection
- Admin access to install Docker (one-time only)

**What you'll accomplish:**
- Run a working MCP server locally
- Test it with API calls
- See exactly what clients will experience
- Build confidence for your first install

---

## STEP 1: Install Docker Desktop (One-Time Setup)

### Check If You Already Have Docker

Open **PowerShell** and run:
```powershell
docker --version
```

**If you see:** `Docker version 24.x.x` or similar → **Skip to Step 2**

**If you see:** `docker: The term 'docker' is not recognized` → **Continue below**

### Install Docker Desktop

1. **Download Docker Desktop**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"
   - File will be ~500MB, takes 2-5 minutes to download

2. **Run the Installer**
   - Double-click `Docker Desktop Installer.exe`
   - Click "OK" to accept settings
   - Wait 3-5 minutes for installation
   - Click "Close" when finished

3. **Restart Your Computer**
   - Docker requires a restart to enable virtualization
   - Save your work and reboot now

4. **Start Docker Desktop**
   - After restart, open Docker Desktop from Start Menu
   - You'll see a whale icon in your system tray (bottom-right)
   - Wait until it says "Docker Desktop is running"
   - First startup takes 2-3 minutes

5. **Verify Installation**
   ```powershell
   docker --version
   ```
   Should show: `Docker version 24.x.x, build xxxxx`

**Troubleshooting:**
- If Docker won't start, you may need to enable WSL 2 (Docker will prompt you)
- If you see "Hardware virtualization is not enabled", enable it in BIOS (Google: "enable virtualization [your PC brand]")

---

## STEP 2: Navigate to Your Repository

Open **PowerShell** and go to your repository:

```powershell
cd C:\Users\puddi\mcp-consulting-kit
```

Verify you're in the right place:
```powershell
Get-ChildItem
```

You should see folders like:
- `showcase-servers/`
- `consulting-materials/`
- `README.md`

---

## STEP 3: Choose a Server to Run

For your first demo, use **Content Automation MCP** (simplest):

```powershell
cd showcase-servers\content-automation-mcp
```

Check what's in this folder:
```powershell
Get-ChildItem
```

You'll see:
- `main.py` (the server code)
- `requirements.txt` (dependencies)
- `Dockerfile` (Docker configuration)
- `mcp_tools.py` (automation tools)

---

## STEP 4: Create Environment File

The server needs API keys to work. For your local demo, you'll use test credentials.

Create a file called `.env` (note the dot at the start):

```powershell
@"
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
API_KEY=demo-local-key-12345
RSS_FEEDS=https://news.ycombinator.com/rss,https://www.reddit.com/r/technology/.rss
"@ | Out-File -FilePath .env -Encoding utf8
```

**Important:** Replace `sk-ant-YOUR-KEY-HERE` with your actual Anthropic API key.

**Don't have an Anthropic API key?**
1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Click "Get API Keys"
4. Create a new key
5. Copy it and paste into the command above

**Check your .env file:**
```powershell
Get-Content .env
```

Should show your API key and settings.

---

## STEP 5: Build the Docker Image

This creates a containerized version of the server (one-time process, takes 2-5 minutes):

```powershell
docker build -t content-automation-mcp .
```

**What you'll see:**
- Lots of text scrolling (this is normal)
- Lines like `Step 1/10 : FROM python:3.11-slim`
- Downloads of Python packages
- Final line: `Successfully tagged content-automation-mcp:latest`

**This creates a Docker image** — think of it as a template for running the server.

**Troubleshooting:**
- If you see "Cannot connect to Docker daemon", make sure Docker Desktop is running (check the whale icon in system tray)
- If build fails with "no space left", free up 2-3GB disk space and try again

---

## STEP 6: Run the Server

Start the server in a container:

```powershell
docker run --env-file .env -p 8103:8103 content-automation-mcp
```

**What you'll see:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8103 (Press CTRL+C to quit)
```

**This means it's working!** ✅

The server is now running and listening on port 8103.

**Leave this PowerShell window open** — the server runs here.

---

## STEP 7: Test the Server

Open a **NEW PowerShell window** (keep the first one running).

### Test 1: Health Check

```powershell
curl http://localhost:8103/health
```

**Expected response:**
```json
{"status":"healthy"}
```

✅ **Success!** The server is responding.

### Test 2: List Available Tools

```powershell
curl http://localhost:8103/tools
```

**Expected response:** JSON list of available automation tools like:
- `fetch_rss_feed`
- `extract_webpage_content`
- `generate_summary`
- `format_content`

### Test 3: Fetch RSS Feed

```powershell
$body = @{
    tool = "fetch_rss_feed"
    params = @{
        feed_url = "https://news.ycombinator.com/rss"
    }
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:8103/execute -ContentType "application/json" -Body $body
```

**Expected response:** JSON with latest Hacker News articles (titles, links, dates).

If you see article data → **Your server is fully operational!** 🎉

---

## STEP 8: Understanding What You Just Did

**What happened:**
1. You built a Docker image (a self-contained server environment)
2. You started a container running that image (an instance of the server)
3. The server exposed port 8103 to your machine
4. You sent HTTP requests to test the automation tools

**What this means for clients:**
- This exact server will run on their machines
- They'll interact with it through Claude Desktop (not curl)
- Claude will send requests to the server and get structured data back
- Users just type natural language prompts — the automation happens invisibly

**What you can demo:**
- "This is the content automation engine running on your laptop"
- "It can fetch RSS feeds, scrape webpages, and generate summaries"
- "Claude Desktop will use these tools when you ask it to research or summarize content"

---

## STEP 9: Stop the Server

When you're done testing:

1. Go back to the **first PowerShell window** (where the server is running)
2. Press **CTRL+C**
3. The server will shut down gracefully

**To run it again:**
```powershell
docker run --env-file .env -p 8103:8103 content-automation-mcp
```

---

## STEP 10: Record Your Demo (Optional but Recommended)

Use **Loom** or **Windows Screen Recorder** to capture a 2-minute demo:

**Demo script:**
1. "Here's the Content Automation MCP server running locally on Windows"
2. Show the health check: `curl http://localhost:8103/health`
3. Show fetching an RSS feed
4. "This is what your team will use through Claude to automate content research"
5. "Setup takes 15 minutes, then your team has instant access to real-time data"

**Why record this:**
- Proof for clients that it's real and working
- Confidence booster for yourself
- Sales asset for outreach emails
- Reference for future installs

---

## Common Issues & Fixes

### "Port 8103 is already in use"

**Problem:** Another process is using that port.

**Fix:**
```powershell
# Find what's using the port
netstat -ano | findstr :8103

# Kill that process (replace PID with the number from above)
taskkill /PID [number] /F

# Try running the server again
docker run --env-file .env -p 8103:8103 content-automation-mcp
```

### "Cannot connect to Docker daemon"

**Problem:** Docker Desktop isn't running.

**Fix:**
1. Check system tray (bottom-right) for whale icon
2. If not there, open Docker Desktop from Start Menu
3. Wait 1-2 minutes for it to fully start
4. Try your command again

### "curl: command not found"

**Problem:** PowerShell on older Windows doesn't have curl.

**Fix:** Use `Invoke-WebRequest` instead:
```powershell
Invoke-WebRequest -Uri http://localhost:8103/health
```

### "API key is invalid"

**Problem:** The Anthropic API key in your `.env` file isn't correct.

**Fix:**
1. Check your key at https://console.anthropic.com/
2. Edit `.env` with the correct key
3. Stop the server (CTRL+C)
4. Run it again with the updated `.env`

### Docker build is very slow

**Normal:** First build downloads ~500MB of Python packages (5-10 minutes on slower connections).

**Speed it up:** Once built, you won't need to rebuild unless you change the code.

---

## Next Steps

**Now that you've run your first server:**

1. **Try another server** → Business Intelligence MCP or API Integration Hub
2. **Integrate with Claude Desktop** → Configure Claude to use your local server
3. **Customize for a client** → Edit the RSS feeds or add new sources
4. **Practice your pitch** → Use this demo to explain the value proposition

**When you're ready to install for a client:**

1. Follow the same steps on their machine
2. Use their actual API credentials (not demo keys)
3. Configure their specific data sources
4. Train them on example prompts
5. Hand off the documentation

---

## Testing Checklist

Before you do your first paid install, verify:

- [ ] You can build and run the server in under 15 minutes
- [ ] All three test commands return valid responses
- [ ] You understand what each tool does
- [ ] You can explain the value in plain English
- [ ] You can stop and restart the server cleanly
- [ ] You've recorded a demo video (even just for yourself)

**Once you check all those boxes → you're ready to prospect clients.**

---

## Questions?

**"Can I run multiple servers at once?"**
Yes, they use different ports (8101, 8102, 8103, etc.). Run each in a separate PowerShell window.

**"Do I need to rebuild after changes?"**
Only if you change the server code itself. Changing `.env` doesn't require rebuild.

**"How do clients access this?"**
They don't access it directly — Claude Desktop connects to it locally on their machine and uses the tools automatically when they ask relevant questions.

**"What if I don't have an Anthropic API key?"**
You can still test the server with curl commands, but you won't be able to integrate with Claude Desktop until you have a key.

**"Is this production-ready?"**
For local demos and small team deployments, yes. For enterprise scale (100+ users), you'd need additional hardening (already on your ROADMAP).

---

## You're Ready

You now have:
- A working MCP server running locally
- Practical experience with Docker
- Test commands to validate functionality
- Troubleshooting knowledge
- Confidence to demo for clients

**Your first install will be 80% following this exact process** on the client's machine with their credentials.

Go book that discovery call. 🚀
