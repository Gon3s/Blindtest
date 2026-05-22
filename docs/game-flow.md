# Schéma des cas de jeu — Blindtest App

## 1. Machine à états — Salle (`Room`)

```mermaid
stateDiagram-v2
    [*] --> CREATED : POST /rooms
    CREATED --> WAITING : host rejoint (open)
    WAITING --> ROUND_IN_PROGRESS : POST /rooms/{id}/rounds\n(start_round)
    ROUND_IN_PROGRESS --> REVEAL : auto-lock dernière chanson\n→ reveal
    REVEAL --> ROUND_FINISHED : song.revealed broadcast\n(round_finished=true)
    ROUND_FINISHED --> WAITING : POST /rooms/{id}/restart\n(nouvelle manche)
    ROUND_FINISHED --> FINISHED : host ferme la salle
    WAITING --> FINISHED : host ferme sans jouer
    FINISHED --> [*]
```

## 2. Machine à états — Chanson (`Song`)

```mermaid
stateDiagram-v2
    [*] --> UPCOMING : créée avec le round

    UPCOMING --> PLAYING : start_song\n(broadcast song.started + preview_url)

    PLAYING --> LOCKED : auto-lock après 30s\n(background task)

    LOCKED --> VALIDATION : host consulte le résumé\n(GET /songs/{id}/summary)\net corrige des réponses
    LOCKED --> REVEALED : host révèle directement\n(POST /songs/{id}/reveal)

    VALIDATION --> REVEALED : POST /songs/{id}/reveal\naprès corrections host

    REVEALED --> SCORED : scoring calculé\n(broadcast song.revealed)

    SCORED --> [*]
```

## 3. Cycle complet d'une manche (diagramme de séquence)

```mermaid
sequenceDiagram
    participant H as Host
    participant B as Backend
    participant WS as WebSocket
    participant J as Joueur(s)

    Note over H,J: Phase LOBBY
    H->>B: POST /rooms (create_room)
    B-->>H: room_id, code
    J->>B: POST /rooms/{code}/join
    B->>WS: broadcast participant.joined
    WS-->>H: participant.joined
    WS-->>J: participant.joined

    Note over H,J: Démarrage manche
    H->>B: POST /rooms/{id}/rounds (theme)
    B->>WS: broadcast round.started
    B->>WS: broadcast song.started (preview_url, ends_at)
    WS-->>H: round.started + song.started
    WS-->>J: round.started + song.started

    loop 10 chansons
        Note over H,J: Chanson en cours (30s)
        J->>B: POST /songs/{id}/answers (texte libre)
        B-->>J: validation_status (NOT_FOUND|FOUND|DOUBTFUL)

        Note over B: Auto-lock après 30s
        B->>WS: broadcast song.locked

        alt Le host corrige (cas DOUBTFUL)
            H->>B: GET /songs/{id}/summary
            B-->>H: liste réponses + doubtful
            H->>B: PATCH /songs/{id}/answers/{aid} (override)
            B-->>H: score recalculé
        end

        H->>B: POST /songs/{id}/reveal
        B->>WS: broadcast song.revealed\n(titre, artiste, scores, mini-leaderboard)
        WS-->>H: song.revealed
        WS-->>J: song.revealed

        alt Pas la dernière chanson
            H->>B: POST /rounds/{id}/songs/{idx}/start
            B->>WS: broadcast song.started
        else Dernière chanson (index 9)
            B->>WS: broadcast round.finished\n(classement final de manche)
            WS-->>H: round.finished
            WS-->>J: round.finished
        end
    end

    Note over H,J: Fin de manche
    alt Nouvelle manche
        H->>B: POST /rooms/{id}/restart (nouveau thème)
        B->>WS: broadcast round.started
    else Fin de partie
        Note over H,J: Host ferme la salle
    end
```

## 4. Cas de validation d'une réponse joueur

```mermaid
flowchart TD
    A([Joueur soumet une réponse]) --> B[Normalisation texte\nlower + strip accents]
    B --> C{Titre trouvé ?}

    C -- Oui --> D{Artiste trouvé ?}
    C -- Non --> E{Artiste trouvé ?}

    D -- Oui --> FOUND["✅ FOUND\ntitle_found=true\nartist_found=true\n+2 pts"]
    D -- Non --> DOUBTFUL_T["⚠️ DOUBTFUL\ntitle_found=true\nartist_found=false\n→ host review"]

    E -- Oui --> DOUBTFUL_A["⚠️ DOUBTFUL\ntitle_found=false\nartist_found=true\n→ host review"]
    E -- Non --> NOT_FOUND["❌ NOT_FOUND\ntitle_found=false\nartist_found=false\n+0 pts"]

    DOUBTFUL_T --> F{Host override ?}
    DOUBTFUL_A --> F

    F -- Accepte titre+artiste --> FOUND2["✅ FOUND → +2 pts"]
    F -- Accepte titre seul --> TITLE["titre +1 pt"]
    F -- Accepte artiste seul --> ARTIST["artiste +1 pt"]
    F -- Rejette --> NOT_FOUND2["❌ +0 pts"]
    F -- Pas de correction --> AUTO["Score auto\ntitle +1, artist +1"]
```

## 5. Événements WebSocket émis par le backend

| Événement | Déclencheur | Destinataires | Payload clé |
|-----------|-------------|---------------|-------------|
| `participant.joined` | POST /rooms/{code}/join | Toute la salle | participant_id, nickname |
| `round.started` | POST /rooms/{id}/rounds | Toute la salle | round_id, theme, song_count |
| `song.started` | start_song | Toute la salle | song_id, song_index, preview_url, ends_at |
| `song.locked` | auto-lock background task | Toute la salle | song_id |
| `song.revealed` | POST /songs/{id}/reveal | Toute la salle | titre, artiste, scores, mini_leaderboard |
| `round.finished` | reveal dernière chanson | Toute la salle | round_leaderboard |

## 6. Rôles et permissions

```mermaid
flowchart LR
    subgraph HOST["🎤 Host"]
        H1[Créer la salle]
        H2[Démarrer une manche]
        H3[Voir le résumé des réponses]
        H4[Corriger les réponses douteuses]
        H5[Révéler la chanson]
        H6[Passer à la chanson suivante]
        H7[Relancer une manche]
    end

    subgraph PLAYER["🎮 Joueur"]
        P1[Rejoindre via code]
        P2[Écouter le preview audio]
        P3[Soumettre une réponse]
        P4[Voir le résultat reveal]
        P5[Voir le classement]
    end
```
