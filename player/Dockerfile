# Dockerfile pour les clients Player
FROM python:3.11-slim

WORKDIR /app

# Copier le script
COPY player.py .

# Rendre le script exécutable
RUN chmod +x player.py

# Variables d'environnement par défaut
ENV PLAYER_ID=player_unknown
ENV NARRATOR_HOST=narrator
ENV NARRATOR_PORT=5000

# Lancement du client
CMD ["python", "-u", "player.py"]
