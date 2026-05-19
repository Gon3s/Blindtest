# Host Token — Mécanisme d'identification

## Principe

À la création d'une salle, le serveur génère un `hostToken` aléatoire (`secrets.token_urlsafe(32)`, 43 caractères URL-safe). Ce token est retourné **une seule fois** dans la réponse `POST /rooms` et n'est jamais réexposé.

Le frontend stocke ce token dans le `localStorage` et l'envoie dans le corps JSON de toutes les actions host.

## Flux

```
POST /rooms
  ← { room_id, code, host_token, ... }   # stocker en localStorage

POST /rooms/{id}/rounds        { host_token, theme }
POST /rooms/{id}/restart       { host_token, theme }
POST /songs/{id}/summary       { host_token }
POST /songs/{id}/override      { host_token, title_accepted, artist_accepted }
POST /songs/{id}/reveal        { host_token }
```

## Erreurs

| Situation | HTTP |
|---|---|
| `host_token` absent | 422 |
| `host_token` incorrect | 403 |

## Ce que ce mécanisme ne garantit pas

- Pas de chiffrement de session (stateless)
- Pas de révocation (token valide tant que la salle existe)
- Pas de protection contre un joueur qui a vu le token (confiance locale entre amis)

Suffisant pour le MVP : empêche un joueur de déclencher accidentellement une action host.
