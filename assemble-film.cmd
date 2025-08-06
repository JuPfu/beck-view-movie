@echo off
rem This script is used to execute 'beck-view-digitize' with Python DLL being found.
set PATH="C:\Users\Peter lokal\AppData\Local\Programs\Python\Python313";%PATH%
set PYTHONHOME="C:\Users\Peter lokal\AppData\Local\Programs\Python\Python313"
cd "%~dp0"
beck-view-movie.exe %*
rem call venv\Scripts\activate.bat
rem python beck-view-movie.py %*
rem deactivate