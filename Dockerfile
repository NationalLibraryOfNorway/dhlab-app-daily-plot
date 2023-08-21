FROM python:3.11-bookworm
WORKDIR /app/
COPY requirements.txt /app/

RUN pip3 install -r requirements.txt

COPY DHlab_logo_web_en_black.png app.py titles.csv /app/

CMD streamlit run app.py --browser.gatherUsageStats=False --server.baseUrlPath /dagsplott
