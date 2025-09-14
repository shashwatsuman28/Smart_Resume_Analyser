@echo off
cd /d C:\Users\HP-PC\Downloads\Smart_Resume_Analyser_App_Py313\Smart_Resume_Analyser_App-master
call venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m streamlit run App.py
pause
