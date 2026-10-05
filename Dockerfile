FROM python:3.13-slim AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN export DJANGO_VW_TYPE2_ID_SECRET_KEY=build \
    && python manage.py compilemessages \
    && python manage.py collectstatic --noinput

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --no-create-home app
COPY --from=build /app .
USER app
EXPOSE 8000
CMD ["gunicorn", "vw_type2_id.wsgi", "--bind", "0.0.0.0:8000", \
     "--workers", "2", "--access-logfile", "-"]
