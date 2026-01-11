FROM python:3.11-slim

WORKDIR /code

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The command is overridden by docker-compose for dev
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]