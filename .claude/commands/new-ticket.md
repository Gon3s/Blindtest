# /new-ticket

Crée un nouveau ticket dans la DB Notion Blindtest de façon **itérative et interactive**.

## Usage

```
/new-ticket Ajouter un mode spectateur sur /spectate/:code
/new-ticket Le bouton Relancer ne fonctionne pas sur mobile
/new-ticket
```

Si aucun argument, demander à l'utilisateur de décrire le ticket.

## Workflow obligatoire (5 étapes)

### Étape 1 — Déterminer le prochain numéro T-XXX

Chercher dans Notion le numéro le plus élevé :
- DB : `collection://e203248a-c5b6-4b0c-866a-45bbdb18babd`
- Query : chercher tous les tickets et trouver le T-XXX max
- Incrémenter de 1 → prochain numéro

⚠️ Ne jamais deviner ou utiliser le numéro depuis CLAUDE.md — toujours vérifier Notion en live.

### Étape 2 — Générer le draft complet

Analyser `$ARGUMENTS` et produire :

**Propriétés :**
| Champ | Valeur générée par l'agent |
|-------|--------------------------|
| Ticket | `T-XXX — <titre court et précis>` |
| Type | Un seul : `setup` / `backend` / `frontend` / `realtime` / `product` / `infra` / `music` / `database` / `qa` |
| Labels | Liste cohérente parmi : `setup`, `backend`, `frontend`, `database`, `realtime`, `music`, `domain`, `tdd`, `infra`, `product`, `p0`, `p1`, `qa` |
| Sprint | Sprint le plus adapté au contexte (Sprint 4 = Sprint en cours) |
| Statut | `À faire` (toujours) |

**Body de la page (format Markdown Notion) :**

```
**Problème constaté**
<description concise du problème ou du besoin>

**Objectif** : <ce que le ticket doit accomplir>

## Prompt Claude Code
```
Implémente le ticket T-XXX — <titre>.

Contexte : <contexte technique précis, fichiers concernés, comportement actuel>.

Fichiers à modifier :
- <fichier 1>
- <fichier 2>

TDD strict :
1. RED — Écris les tests :
   - '<test 1>'
   - '<test 2>'
2. GREEN — Implémenter :
   - <étape 1>
   - <étape 2>
3. REFACTOR — Vérifier ./scripts/check.sh
```

## Critères d'acceptation
- <critère 1>
- <critère 2>

## Dépendances
<T-XXX si applicable, sinon "Aucune">
```

### Étape 3 — Demander la priorité à l'utilisateur

Afficher le draft complet formaté, puis poser la question :

> **Priorité ?** `P0` — bloquant / `P1` — important / `P2` — nice-to-have

Attendre la réponse avant de continuer.

### Étape 4 — Itérer jusqu'à validation

Intégrer la priorité choisie et afficher le draft final.

Proposer des ajustements si l'utilisateur en fait. Continuer jusqu'à obtenir une confirmation explicite du type : **"ok"**, **"créer"**, **"go"**, **"valider"**, **"c'est bon"** ou équivalent.

⚠️ **Ne jamais créer dans Notion sans confirmation explicite.**

### Étape 5 — Créer dans Notion

Utiliser le MCP Notion (`notion-create-pages`) :

```json
{
  "parent": { "type": "data_source_id", "data_source_id": "e203248a-c5b6-4b0c-866a-45bbdb18babd" },
  "pages": [{
    "properties": {
      "Ticket": "T-XXX — <titre>",
      "Type": "<type>",
      "Labels": "[\"label1\", \"label2\"]",
      "Sprint": "<sprint>",
      "Statut": "À faire",
      "Priorité": "<P0|P1|P2>"
    },
    "content": "<body markdown>"
  }]
}
```

Après création, afficher l'URL Notion du ticket créé et mettre à jour le tableau du sprint approprié dans CLAUDE.md.

## Règles non-négociables

1. Le numéro T-XXX vient toujours de Notion en live — jamais deviné.
2. Le Prompt d'implémentation inclut toujours RED / GREEN / REFACTOR.
3. Zéro création sans confirmation explicite de l'utilisateur.
4. Mettre à jour CLAUDE.md après création (ligne dans le tableau du sprint).
