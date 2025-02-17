FROM python:3.9.6-alpine

COPY . .

RUN apk update && apk add python3-dev \
                          gcc \
                          libc-dev \
                          libffi-dev

RUN pip install -r requirements.txt

CMD ["python", "-m", "autotrade.main"]