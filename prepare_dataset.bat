@echo off
chcp 65001 >nul
cd /d "%~dp0"
python ml\prepare_dataset.py --source ml\data\chest_xray --output ml\data\chest_xray_split
pause


