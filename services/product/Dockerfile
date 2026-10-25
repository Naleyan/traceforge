# 1. Partir d'une image officielle contenant Python
FROM python:3.12-slim

# 2. Se placer dans le dossier /app à l'intérieur de l'image
WORKDIR /app

# 3. Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copier le code
COPY main.py .

# 5. Commande lancée au démarrage du conteneur
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]