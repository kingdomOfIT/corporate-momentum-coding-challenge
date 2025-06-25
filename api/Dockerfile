FROM python:3.12

ENV PYTHONUNBUFFERED True
ENV PYTHONPATH "${PYTHONPATH}:/app"

RUN apt update && apt install -y make

WORKDIR /app

ADD requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

ENV PORT 8000

CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
