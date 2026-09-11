FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt frontend/requirements.txt

RUN python -m pip install --no-cache-dir -r frontend/requirements.txt

COPY frontend frontend

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]