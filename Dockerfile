FROM python:3.9.6-alpine

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "-m", "autotrade.main"]