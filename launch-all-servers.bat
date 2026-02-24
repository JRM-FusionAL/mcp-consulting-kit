@echo off
REM Launch all MCP Consulting Kit servers and FusionAL

REM Start Business Intelligence MCP
start "BI MCP" cmd /k "cd /d %~dp0showcase-servers\business-intelligence-mcp && c:\python314\python.exe -m uvicorn main:app --reload --port 8101"

REM Start API Integration Hub
start "API Integration Hub" cmd /k "cd /d %~dp0showcase-servers\api-integration-hub && c:\python314\python.exe -m uvicorn main:app --reload --port 8102"

REM Start Content Automation MCP
start "Content Automation MCP" cmd /k "cd /d %~dp0showcase-servers\content-automation-mcp && c:\python314\python.exe -m uvicorn main:app --reload --port 8103"

REM Start FusionAL
start "FusionAL" cmd /k "cd /d C:\Users\puddi\Projects\FusionAL\core && c:\python314\python.exe -m uvicorn main:app --reload --port 8089"

echo All servers launching in separate windows...
