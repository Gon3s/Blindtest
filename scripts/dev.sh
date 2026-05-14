#!/bin/bash
set -e

echo "🚀 Blindtest App — Dev Mode"
echo "───────────────────────────"

# Lancer Docker Compose en mode dev
docker-compose up -d

echo ""
echo "✅ Services lancés :"
echo "  🌐 Frontend  : http://localhost:4200"
echo "  🔌 API      : http://localhost:8000"
echo "  📊 API Docs : http://localhost:8000/docs"
echo "  🗄️  DB Admin : http://localhost:8081"
echo ""
echo "📊 Statut services :"
docker-compose ps

echo ""
echo "💡 Commandes utiles :"
echo "  docker-compose logs -f backend    # Backend logs"
echo "  docker-compose logs -f frontend   # Frontend logs"
echo "  docker-compose down              # Arrêter"
