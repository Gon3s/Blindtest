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

- **MVP First** : Si c'est pas dans le backlog MVP validé, c'est non.
- **TDD Strict** : Jamais de code sans test d'abord.
- **Notion = Source de vérité** : Chaque décision → Notion update.
- **WebSocket Ready** : Dès Sprint 0, penser broadcast temps réel.
- **Docker First** : Dev en Docker Compose, zéro "works on my machine".
- **Typage strict** : Mypy `--strict`, TypeScript `strict: true`.

## 📋 Tickets

### Sprint 0 — Infra ✅ Done

| Ticket | Titre | Status |
|--------|-------|--------|
| T-001 | Initialiser le monorepo | ✅ Done |
| T-002 | Configurer Claude Code et agents | ✅ Done |
| T-003 | Initialiser FastAPI avec uv | ✅ Done |
| T-004 | Initialiser Angular 21 | ✅ Done |
| T-005 | Configurer Docker Compose local | ✅ Done |
| T-006 | Configurer PostgreSQL + migrations | ✅ Done |
| T-007 | Créer les scripts qualité | ✅ Done |

### Sprint 1 — Domaine métier (en cours)

| Ticket | Titre | Status |
|--------|-------|--------|
| T-008 | Entités domaine (Room, Participant, Song) | ✅ Done |
| T-009 | State machine Room | ✅ Done |
| T-010 | State machine Song | ✅ Done |
| T-011 | Normalisation de réponse | ✅ Done |
| T-012 | Validation laxiste V0 | ✅ Done |
| T-013 | Scoring chanson | ✅ Done |
| T-014 | Classements | ✅ Done |

**Prochains tickets** : voir Notion → https://www.notion.so/35db64600100815ca0a8d8ed1174d4ac

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
```

```
# Dans Claude Code
/ticket T-XXX           # Implémenter un ticket (TDD-first)
/review                 # Vérifier ready-to-merge
/tdd-cycle [feature]    # Plan test-first pour feature complexe
/release                # Créer une release semver
```

## 🤖 Agents Spécialisés

Configurés dans `.claude/agents/` :

- **TDD Mentor** : Veille à écrire les tests en premier
- **Backend Reviewer** : Valide FastAPI, models, domain, queries
- **Frontend Reviewer** : Valide Angular, components, services
- **Product Guardian** : Refuse toute dérive hors MVP

## 📝 Slash Commands

- `/ticket T-XXX` — Implémenter un ticket Notion (TDD-first)
- `/review` — Vérifier prêt à merger
- `/tdd-cycle` — Plan test-first pour feature complexe
- `/release` — Créer une release semver (bump + tag + GitHub Release)

## 🚨 Contraintes Non-Négociables

1. **Aucune complexité prématurée** : Si c'est pas demandé dans MVP, c'est non.
2. **Pas de comptes utilisateur** : Pseudos sans auth.
3. **Pas de paiement** : Musique via Deezer + fallback fixtures.
4. **Pas de voix** : Réponses texte libre uniquement.
5. **Pas de licences avancées** : Utiliser preview Deezer si dispo, sinon fixture.
6. **WebSocket from day 1** : Realtime broadcast game state.
7. **PostgreSQL only** : Pas de NoSQL, schéma défini et migré.

## 💰 Cost Optimization

- Agents utilisent `claude-haiku-4-5` (TDD-Mentor, Reviewers, Product Guardian)
- Pas d'auto-review dans `/ticket` — lancer `/review` manuellement après 2-3 tickets
- Batcher les tickets, puis un seul `/review`

## 🔄 Notion Integration

- **Backlog** : https://www.notion.so/35db64600100815ca0a8d8ed1174d4ac
- **Mise à jour** : À chaque ticket, update status dans Notion

## 📚 Context Saved

Ce fichier charge à chaque session Claude Code.  
**À jour** : mise à jour dès décision prise (état, tickets, stack).  
**Taille** : < 250 lignes, garder concis.

## 🔗 GitHub

- **Repo** : https://github.com/Gon3s/Blindtest
- **main** protégé : pas de force-push, pas de suppression

## 🚀 Status

- ✅ Sprint 0 — Infra complète
- ✅ Sprint 1 — Domaine métier (T-008/009/010)
- → Prochains tickets dans Notion
