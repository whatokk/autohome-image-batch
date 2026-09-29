@echo off
chcp 65001 >nul
cd /d %~dp0
echo ============================================
echo   批量出图工具
echo   配置: config.json   提示词: prompts-cp001.txt
echo ============================================
node batch.mjs
echo.
pause
