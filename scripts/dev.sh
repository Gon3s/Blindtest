#!/bin/bash
set -e

echo "Blindtest App - Dev Mode"
echo "------------------------"

# Remove any orphan containers left by docker-compose v1 (ID-prefixed names)
docker ps -a --filter "label=com.docker.compose.project=blindtest" -q \
  | xargs --no-run-if-empty docker rm -f 2>/dev/null || true

docker compose up -d

echo ""
echo "Services lances :"
echo "  Frontend  : http://localhost:4200"
echo "  API       : http://localhost:8000"
echo "  API Docs  : http://localhost:8000/docs"
echo "  DB Admin  : http://localhost:8081"
echo ""
echo "Statut services :"
docker compose ps

echo ""
echo "Commandes utiles :"
echo "  docker compose logs -f backend    # Backend logs"
echo "  docker compose logs -f frontend   # Frontend logs"
echo "  docker compose down               # Arreter"
