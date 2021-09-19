FROM python:3.9-slim-buster

# -v $(pwd)/config.yaml:/app/config.yaml:ro
WORKDIR /app
COPY . .

ENV INSIDE_DOCKER "True"

CMD ["python", "./main.py"]
