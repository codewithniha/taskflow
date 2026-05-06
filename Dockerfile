FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["bash", "-c", "python -c 'from app import app, db; app.app_context().__enter__(); db.create_all()' && python app.py"]
