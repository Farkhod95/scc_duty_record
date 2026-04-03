FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Kerakli tizim kutubxonalarini o'rnatish
RUN apt-get update && apt-get install -y gcc libpq-dev fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/

# Proto fayllardan Python stub larini generatsiya qilish
RUN python -m grpc_tools.protoc \
    -I ./proto \
    --python_out=./proto \
    --grpc_python_out=./proto \
    ./proto/location_service.proto

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "main.asgi:application"]
