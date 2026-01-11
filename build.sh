#!/bin/bash
# Script de build pour construire toutes les images Docker

set -e

# Version tag (par défaut: latest, peut être surchargé par BUILD_TAG)
VERSION=${BUILD_TAG:-latest}

echo "========================================="
echo "  Construction des images Docker"
echo "  Version: $VERSION"
echo "========================================="
echo ""

echo "[1/3] Construction de l'image narrator..."
cd narrator
docker build -t localhost:443/garou-narrator:$VERSION -t localhost:443/garou-narrator:latest .
cd ..
echo "✓ narrator OK"
echo ""

echo "[2/3] Construction de l'image player..."
cd player
docker build -t localhost:443/garou-player:$VERSION -t localhost:443/garou-player:latest .
cd ..
echo "✓ player OK"
echo ""

echo "[3/3] Construction de l'image AI..."
cd windows_ai
docker build -t localhost:443/garou-ai:$VERSION -t localhost:443/garou-ai:latest .
cd ..
echo "✓ AI OK"
echo ""

echo "========================================="
echo "  ✓ Toutes les images sont prêtes !"
echo "  Images construites:"
echo "    - localhost:443/garou-narrator:$VERSION"
echo "    - localhost:443/garou-player:$VERSION"
echo "    - localhost:443/garou-ai:$VERSION"
echo "========================================="
echo ""
echo "Pour tester en local :"
echo "  docker-compose -f docker-compose-local.yml up"
echo ""
echo "Pour déployer sur VM1 :"
echo "  docker-compose -f docker-compose-vm1-linux.yml up"
echo ""
echo "Pour déployer sur VM2 :"
echo "  docker-compose -f docker-compose-vm2-windows.yml up"
echo ""
echo "Pour déployer sur VM3 :"
echo "  docker-compose -f docker-compose-vm3-linux.yml up"
echo ""
echo "Pour construire avec un tag spécifique :"
echo "  BUILD_TAG=v1.0.0 ./build.sh"
echo ""
