#!/bin/bash
set -e

cd narrator
docker build -t localhost:443/garou-narrator:latest -t localhost:443/garou-narrator:latest .
docker push localhost:443/garou-narrator:latest
cd ..

cd player
docker build -t localhost:443/garou-player:latest -t localhost:443/garou-player:latest .
docker push localhost:443/garou-player:latest
cd ..
