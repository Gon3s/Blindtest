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

**Accès** :
- 🌐 Frontend : http://localhost:4200
- 🔌 API : http://localhost:8000
- 📊 Docs API : http://localhost:8000/docs
- 🗄️ DB Admin (optionnel) : http://localhost:8081

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

## 📋 Tickets Sprint 0

| Ticket | Titre | Status |
|--------|-------|--------|
| T-001 | Initialiser le monorepo | ✅ En cours |
| T-002 | Configurer Claude Code + agents | → Suivant |
| T-003 | FastAPI + uv | |
| T-004 | Angular 21 | |
| T-005 | Docker Compose | |
| T-006 | PostgreSQL + migrations | |
| T-007 | Scripts qualité | |

Voir [Notion](https://www.notion.so/35db6460-0100-8108-b0b9-ec19b6238ac5) pour les détails complets.

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
- **Tickets** : [Sprint 0-6](https://www.notion.so/35db6460-0100-8108-b0b9-ec19b6238ac5)

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

Voir [Notion](https://www.notion.so/35db64600100815ca0a8d8ed1174d4ac) pour les questions produit, architecture, et tracage des tickets.

---

**Status** : 🟡 Sprint 0 en cours  
**Last Update** : 2026-05-13
