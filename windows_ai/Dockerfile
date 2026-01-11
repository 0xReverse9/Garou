# Dockerfile pour l'IA d'analyse (Windows bonus)
FROM python:3.11-slim

WORKDIR /app

# Copier le script
COPY ai.py .

# Rendre le script exécutable
RUN chmod +x ai.py

# Variables d'environnement par défaut
ENV PLAYER_ID=decision_ai
ENV NARRATOR_HOST=narrator
ENV NARRATOR_PORT=5000

# Lancement de l'IA
CMD ["python", "-u", "ai.py"]
