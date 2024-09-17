FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create the templates directory
RUN mkdir -p /app/app/templates

# Copy the templates
COPY app/templates /app/app/templates

ENV PATH="/root/.local/bin:${PATH}"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
