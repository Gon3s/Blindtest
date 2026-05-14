#!/bin/bash
set -e

echo "Blindtest App - Dev Mode"
echo "------------------------"

# Workaround: docker-compose v1.29.2 + Docker v29 bug (ContainerConfig removed from API).
# Fresh containers don't trigger it; only recreates do. So we remove stopped containers first.
docker rm -f blindtest-postgres blindtest-backend blindtest-frontend blindtest-adminer 2>/dev/null || true

docker-compose up -d

echo ""
echo "Services lances :"
echo "  Frontend  : http://localhost:4200"
echo "  API       : http://localhost:8000"
echo "  API Docs  : http://localhost:8000/docs"
echo "  DB Admin  : http://localhost:8081"
echo ""
echo "Statut services :"
docker-compose ps

echo ""
echo "Commandes utiles :"
echo "  docker-compose logs -f backend    # Backend logs"
echo "  docker-compose logs -f frontend   # Frontend logs"
echo "  docker-compose down               # Arreter"
