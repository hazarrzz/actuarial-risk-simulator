@echo off
echo Risk Simulator baslatiliyor... Lutfen bekleyin (Tarayiciniz otomatik acilacaktir)...
cd /d "%~dp0"
python -m streamlit run app.py
pause
