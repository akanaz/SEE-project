@echo off
start "MEDICORE-Backend" cmd /k "cd /d backend && call venv\Scripts\activate && uvicorn app.main:app --reload"
start "MEDICORE-Frontend" cmd /k "cd /d frontend && npm run dev"
echo ====================
echo Both frontend and backend should now be running!
echo Press any key to exit this window...
pause > nul
exit
