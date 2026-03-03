@echo off
REM Launch all MCP Consulting Kit servers and FusionAL

set PYTHON_CMD=python
where python >nul 2>nul
if errorlevel 1 (
	set PYTHON_CMD=py -3
)

REM Start Business Intelligence MCP
start "BI MCP" cmd /k "cd /d %~dp0showcase-servers\business-intelligence-mcp && %PYTHON_CMD% -m uvicorn main:app --reload --port 8101"

REM Start API Integration Hub
start "API Integration Hub" cmd /k "cd /d %~dp0showcase-servers\api-integration-hub && %PYTHON_CMD% -m uvicorn main:app --reload --port 8102"

REM Start Content Automation MCP
start "Content Automation MCP" cmd /k "cd /d %~dp0showcase-servers\content-automation-mcp && %PYTHON_CMD% -m uvicorn main:app --reload --port 8103"

REM Start FusionAL
start "FusionAL" cmd /k "cd /d C:\Users\puddi\Projects\FusionAL\core && %PYTHON_CMD% -m uvicorn main:app --reload --port 8009"

echo All servers launching in separate windows...
