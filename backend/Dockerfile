FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install gunicorn==23.0.0

COPY backend/requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY backend/ .
COPY data/ /app/data/

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
