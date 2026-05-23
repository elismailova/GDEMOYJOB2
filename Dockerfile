FROM python:3.10-slim

WORKDIR /app

# Минимальные системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# CPU-версия PyTorch (~500 МБ вместо ~2 ГБ GPU-версии)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Зависимости проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Предзагрузка NLP-модели в слой образа — бот стартует мгновенно
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

COPY . .

CMD ["python", "-m", "bot.main"]
