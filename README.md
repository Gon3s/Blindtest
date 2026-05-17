# 🎵 Blindtest App

Application de blindtest multijoueur pour soirées privées entre amis.

**Promesse** : Lancer en < 1 min, jouer, révéler, classer.

---

## 🚀 Quick Start

### Prérequis

- Docker & Docker Compose
- Node.js 20+ (pour dev frontend sans Docker)
- Python 3.11+ + uv (pour dev backend sans Docker)

### Lancer le projet complet

```bash
# 1. Cloner + dossier racine
git clone <repo>
cd blindtest-app

# 2. Dev mode (tout dans Docker Compose)
./scripts/dev.sh

# Ou manuellement
docker-compose up -d
```

> **Note** : Les ports 5432 (PostgreSQL) et 8000 (API) doivent être libres.  
> Si une autre instance PostgreSQL tourne sur 5432, l'arrêter avant de lancer la stack.

**Accès** :
- 🌐 Frontend : http://localhost:4200
- 🔌 API : http://localhost:8000
- 📊 Docs API : http://localhost:8000/docs
- 🗄️ DB Admin (optionnel) : http://localhost:8081

### Tests Docker (smoke)

```bash
# Vérifier que les images buildent et la stack démarre (ports 5432 et 8000 libres requis)
bash tests/integration/test_docker_smoke.sh
```

---

## 📁 Structure

```
blindtest-app/
├── frontend/          # Angular 21
├── backend/           # FastAPI
├── packages/          # Contrats, fixtures
├── infra/            # Docker Compose
├── scripts/          # check.sh, dev.sh, test.sh
├── docs/             # Documentation
├── .claude/          # Config Claude Code
├── CLAUDE.md         # Config agents + règles
└── docker-compose.yaml
```

---

## 🛠️ Commandes Dev

```bash
# Quality checks (AVANT tout commit)
./scripts/check.sh

# Tests uniquement
./scripts/test.sh

# Lint + format
./scripts/lint.sh
./scripts/format.sh

# Entrer dans Claude Code
claude
```

---

## 📋 Statut

| Sprint | Status |
|--------|--------|
| Sprint 0 — Infra | ✅ Done |
| Sprint 1 — Domaine métier | ✅ Done |
| Sprint 2 — API salle/lobby | ✅ Done |
| Sprint 3 — Jeu en cours | ✅ Done |
| Sprint 4 — Design & UX Polish | 🔄 En cours |
| Sprint 5 — Features | 🔲 Todo |

Voir la [base de tickets Notion](https://www.notion.so/40d4d409532a4ff9b0403423eb1484b1) pour le détail complet.

---

## 🎯 Règles Clés

- ✅ **TDD strict** : Tests d'abord, toujours
- ✅ **MVP only** : Zéro complexité hors scope
- ✅ **WebSocket ready** : Realtime from day 1
- ✅ **Docker first** : Dev en conteneur
- ✅ **Typage strict** : `mypy --strict`, `tsc --strict`
- ✅ **Notion is source** : Chaque décision → mise à jour Notion

---

## 📚 Documentation

- **Produit** : [Vision](https://www.notion.so/35db6460010081e69058ec99565c47be)
- **Technique** : [Choix & Architecture](https://www.notion.so/35db64600100819dbc06dfb57529adc2)
- **Tickets** : [Base Notion](https://www.notion.so/40d4d409532a4ff9b0403423eb1484b1)

---

## 🚀 Claude Code Setup

```bash
# Dans le projet
claude

# Dans Claude Code
/init                    # Lancer l'initialisation (optionnel)
/ticket T-002            # Démarrer T-002 agents
```

---

## 🤝 Stack Technique

| Couche | Tech |
|--------|------|
| Frontend | Angular 21 |
| Backend | FastAPI + Python 3.11+ |
| DB | PostgreSQL 15+ |
| Realtime | WebSocket FastAPI |
| Infra | Docker Compose |
| Package Manager | uv (Python) |
| Music | Deezer API + fixtures |
| Auth | Aucune (MVP) |

---

## 📞 Support

Voir [Notion](https://www.notion.so/35db64600100815ca0a8d8ed1174d4ac) pour les questions produit et architecture.

---

**Status** : 🔄 Sprint 4 — Design & UX Polish  
**Last Update** : 2026-05-17
