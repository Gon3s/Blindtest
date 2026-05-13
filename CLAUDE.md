# Blindtest App — Claude Code Configuration

## 🎮 Produit

**Blindtest App** : Application de blindtest multijoueur pour soirées privées entre amis.

**Promesse** : Lancer un blindtest en moins d'une minute, jouer des manches courtes (10 chansons en ~5 min), révéler les réponses et garder un classement clair.

**Boucle à protéger** (tout le reste doit être challengé) :
```
Créer → Rejoindre → Jouer → Répondre → Valider → Révéler → Classer → Relancer
```

## 🏗️ Stack Technique

| Couche | Tech | Version |
|--------|------|---------|
| Frontend | Angular | 21+ (latest) |
| Backend | FastAPI | latest |
| Python | Python | 3.11+ |
| Package Manager | uv | latest |
| Database | PostgreSQL | 15+ |
| Temps réel | WebSocket FastAPI | - |
| Déploiement | Docker Compose | - |
| Auth | Aucune (MVP) | - |
| Musique | Deezer via `MusicProvider` + fixtures | - |

## 📁 Structure Monorepo

```
blindtest-app/
├── frontend/              # Angular 21 app
│   ├── src/
│   ├── angular.json
│   ├── package.json
│   └── tsconfig.json
├── backend/               # FastAPI app
│   ├── src/
│   │   ├── domain/       # Logique métier pure (pas de dépendances)
│   │   ├── application/  # Services applicatifs
│   │   ├── infrastructure/  # FastAPI, DB, WebSocket
│   │   └── api/          # Routes FastAPI
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
├── packages/
│   ├── contracts/        # Types partagés (JSON schemas, DTOs)
│   └── test-fixtures/    # Données de test partagées
├── infra/
│   └── compose.yaml      # Docker Compose local
├── scripts/
│   ├── check.sh          # Lint + test + type check global
│   ├── test.sh           # Tests uniquement
│   ├── dev.sh            # Dev mode (docker compose + watch)
│   ├── lint.sh           # Lint + format check
│   └── format.sh         # Auto-format code
├── docs/                 # Documentation
├── .claude/              # Config Claude Code
│   ├── agents/
│   ├── commands/
│   └── rules.md
├── README.md
├── .gitignore
└── docker-compose.yaml   # Ou dans infra/

```

## 🎯 Règles Développement

### Definition of Done (Avant tout commit)

Un ticket est **Done** ssi :

1. ✅ Tests écrits **avant** implémentation (TDD strict)
2. ✅ Tous les tests passent (`pytest`, `ng test`)
3. ✅ Lint passe (`ruff check`, `eslint`)
4. ✅ Typage passe (`mypy --strict`, `tsc --noEmit`)
5. ✅ `./scripts/check.sh` retourne 0
6. ✅ Doc utile mise à jour
7. ✅ Zéro dérive hors MVP

### Principes Core

- **MVP First** : Si c'est pas dans les T-001 à T-007, c'est non.
- **TDD Strict** : Jamais de code sans test d'abord.
- **Notion = Source de vérité** : Chaque décision → Notion update.
- **WebSocket Ready** : Dès Sprint 0, penser broadcast temps réel.
- **Docker First** : Dev en Docker Compose, zéro "works on my machine".
- **Typage strict** : Mypy `--strict`, TypeScript `strict: true`.

## 📋 Sprint 0 — Tickets

| Ticket | Titre | Status | Labels |
|--------|-------|--------|--------|
| T-001 | Initialiser le monorepo | À faire | setup, infra, tdd |
| T-002 | Configurer Claude Code et agents | À faire | setup, tdd, product |
| T-003 | Initialiser FastAPI avec uv | À faire | backend, setup, tdd |
| T-004 | Initialiser Angular 21 | À faire | frontend, setup, tdd |
| T-005 | Configurer Docker Compose local | À faire | infra, backend, frontend, database |
| T-006 | Configurer PostgreSQL + migrations | À faire | database, backend, tdd |
| T-007 | Créer les scripts qualité | À faire | setup, tdd, infra |

**Ordre strict** : T-001 → T-002 → T-003/T-004 (parallèle) → T-005 → T-006 → T-007

## 🛠️ Commandes Essentielles

```bash
# Check suite AVANT tout commit (obligation absolue)
./scripts/check.sh

# Dev mode (watch + docker compose up)
./scripts/dev.sh

# Tests uniquement
./scripts/test.sh

# Lint + format
./scripts/lint.sh
./scripts/format.sh

# Entrer dans Claude Code
claude

# Dans Claude Code
/init                    # Générer CLAUDE.md amélioré (si besoin)
/ticket T-XXX           # Implémenter un ticket
/review                 # Vérifier ready-to-merge
```

## 🤖 Agents Spécialisés

Les agents suivants sont configurés et seront créés en T-002 :

- **TDD Mentor** : Veille à écrire les tests en premier
- **Backend Reviewer** : Valide FastAPI, models, domain, queries
- **Frontend Reviewer** : Valide Angular, components, services
- **Product Guardian** : Refuse toute dérive hors MVP
- **Security Checker** : Alerte sur secrets, valeurs hardcodées
- **Infra Lead** : Docker, migrations, scripts, deployments

## 📝 Slash Commands (à créer en T-002)

- `/ticket T-XXX` — Implémenter un ticket Notion
- `/review` — Vérifier prêt à merge
- `/tdd-cycle` — Plan test-first pour feature complexe
- `/new-ticket` — Créer un nouveau ticket Notion
- `/check-scope` — Vérifier qu'on reste en MVP

## 🚨 Contraintes Non-Négociables

1. **Aucune complexité prématurée** : Si c'est pas demandé dans MVP, c'est non.
2. **Pas de comptes utilisateur** : Pseudos sans auth.
3. **Pas de paiement** : Musique via Deezer + fallback fixtures.
4. **Pas de voix** : Réponses texte libre uniquement.
5. **Pas de licences avancées** : Utiliser preview Deezer si dispo, sinon fixture.
6. **WebSocket from day 1** : Realtime broadcast game state.
7. **PostgreSQL only** : Pas de NoSQL, schéma défini et migré.

## 🔄 Notion Integration

- **Page source** : https://www.notion.so/35db64600100815ca0a8d8ed1174d4ac
- **Tickets Sprint 0** : https://www.notion.so/35db6460-0100-8108-b0b9-ec19b6238ac5
- **Mise à jour** : À chaque ticket, update status, assignee si applicable

## 📚 Context Saved

Ce fichier charge à chaque session Claude Code.  
**À jour** : mise à jour dès décision prise (état, tickets, stack).  
**Taille** : < 250 lignes, garder concis.

## 🚀 Prochaines étapes

1. ✅ Structure créée
2. → **T-002 : Créer agents + commands Claude Code**
3. → T-003/004 : Backend + Frontend setup
4. → T-005/006/007 : Infra + Docker + scripts qualité

**Status** : Prêt pour `/ticket T-001` après T-002.
