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

### Workflow Ticket Notion (obligatoire)

Dès qu'un ticket est pris en charge, mettre à jour son statut dans Notion via MCP :

| Moment | Statut Notion |
|--------|--------------|
| Début de travail | **In Progress** |
| Blocage identifié | **Blocked** + note du blocage dans le ticket |
| check.sh vert + tests OK | **Done** |

### Principes Core

- **MVP First** : Si c'est pas dans le backlog MVP validé, c'est non.
- **TDD Strict** : Jamais de code sans test d'abord.
- **Notion = Source de vérité** : Chaque décision → Notion update (statut ticket inclus).
- **WebSocket Ready** : Dès Sprint 0, penser broadcast temps réel.
- **Docker First** : Dev en Docker Compose, zéro "works on my machine".
- **Typage strict** : Mypy `--strict`, TypeScript `strict: true`.

## 📋 Tickets

> Sprints 0–3 terminés. Détail complet → [Notion](https://www.notion.so/40d4d409532a4ff9b0403423eb1484b1)

### Sprint 4 — Design & UX Polish

| Ticket | Titre | Status |
|--------|-------|--------|
| T-043 | Design System — Tokens & Thème | ✅ Done |
| T-044 | Design System — Composants Partagés | ✅ Done |
| T-045 | Responsive Design — Desktop & Tablet | 🔲 Todo |
| T-046 | Page Spectateurs / Mode TV (/spectate/:code) | 🔲 Todo |
| T-059 | Front — Intégrer l'identité visuelle HitRoom | 🔲 Todo |
| T-060 | Front — Champ Thème manquant dans le Lobby (P0) | 🔲 Todo |
| T-123 | Fix — clearSession manquant sur clic Quitter (P0) | 🔲 Todo |
| T-124 | Fix — Validation shape session localStorage (P2) | 🔲 Todo |
| T-125 | Fix — Reconnexion phase REVEAL atterrit sur lobby (P0) | 🔲 Todo |
| T-126 | Front/Back — Afficher l'image de l'album au reveal (P0) | 🔲 Todo |

#### 🗄️ Archive P0 — Sprint 4

| Ticket | Titre | Status |
|--------|-------|--------|
| T-114 | Fix — Timer s'arrête à 1 au lieu de 0 à la fin de la chanson | ✅ Done |
| T-122 | Fix — Auto-révéler après fin du timer (supprimer écran intermédiaire) | ✅ Done |

### Sprint 5 — Features

| Ticket | Titre | Status |
|--------|-------|--------|
| T-047 | API — Classement Global Anonyme | 🔲 Todo |
| T-048 | Front — Page Classement & Historique | 🔲 Todo |
| T-049 | DB & Domain — Entité SavedPlaylist | 🔲 Todo |
| T-050 | Deezer — Import Playlist par URL | 🔲 Todo |
| T-051 | API — CRUD Blindtests Sauvegardés | 🔲 Todo |
| T-052 | Front — Interface Admin /admin | 🔲 Todo |
| T-111 | Backend — Sélection chansons + RoomConfig source de vérité | ✅ Done |
| T-112 | Cleanup — constante _DEFAULT_MAX_SONGS + DB query start_song | 🔲 Todo |
| T-115 | Feature — Mode de réponse configurable par manche (P1) | 🔲 Todo |

**Backlog complet** : voir Notion → https://www.notion.so/40d4d409532a4ff9b0403423eb1484b1

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
/new-ticket <description>  # Créer un ticket Notion (itératif, avec prompt)
/review                    # Vérifier ready-to-merge
/tdd-cycle [feature]       # Plan test-first pour feature complexe
/release                   # Créer une release semver
```

## 🤖 Agents Spécialisés

Configurés dans `.claude/agents/` :

- **TDD Mentor** : Veille à écrire les tests en premier
- **Backend Reviewer** : Valide FastAPI, models, domain, queries
- **Frontend Reviewer** : Valide Angular, components, services
- **Product Guardian** : Refuse toute dérive hors MVP

## 📝 Slash Commands

- `/new-ticket <description>` — Créer un ticket Notion (itératif : draft → priorité → validation → création)
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
- Pas d'auto-review — lancer `/review` manuellement après 2-3 tickets
- Batcher les tickets, puis un seul `/review`

## 🔄 Notion Integration

- **Tickets DB** : https://www.notion.so/40d4d409532a4ff9b0403423eb1484b1
- **Produit / Vision** : https://www.notion.so/35db64600100815ca0a8d8ed1174d4ac
- **Mise à jour** : À chaque ticket, update status dans la DB Notion

## 📚 Context Saved

Ce fichier charge à chaque session Claude Code.  
**À jour** : mise à jour dès décision prise (état, tickets, stack).  
**Taille** : < 250 lignes, garder concis.

## 🔗 GitHub

- **Repo** : https://github.com/Gon3s/Blindtest
- **main** protégé : pas de force-push, pas de suppression

## 🚀 Status

- ✅ Sprint 0 — Infra complète
- ✅ Sprint 1 — Domaine métier (T-008–T-014)
- ✅ Sprint 2 — API salle/lobby (T-015–T-020)
- ✅ Sprint 3 — Jeu en cours (T-025–T-042)
- 🔄 Sprint 4 — Design & UX Polish (T-043 ✅, T-044 ✅, T-045–T-046–T-059–T-060 🔲)
- 🔲 Sprint 5 — Features (T-047–T-052)
