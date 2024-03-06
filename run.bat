@echo off

echo ensuring requirements...
start /w pip install -r requirements.txt
echo .

echo running main program...
start python main.py
echo .
pause