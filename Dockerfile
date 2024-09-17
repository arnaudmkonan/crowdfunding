FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create the templates and static directories
RUN mkdir -p /app/app/templates /app/app/static

# Copy the templates and static files
COPY app/templates /app/app/templates
COPY app/static /app/app/static

ENV PATH="/root/.local/bin:${PATH}"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
