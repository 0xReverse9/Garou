# Dockerfile pour le serveur Narrator
FROM python:3.11-slim

WORKDIR /app

# Copier le script
COPY narrator.py .

# Rendre le script exécutable
RUN chmod +x narrator.py

# Exposition du port TCP
EXPOSE 5000

# Variables d'environnement par défaut
ENV NARRATOR_HOST=0.0.0.0
ENV NARRATOR_PORT=5000
ENV EXPECTED_PLAYERS=3

# Lancement du serveur
CMD ["python", "-u", "narrator.py"]
