# /release — Créer une release semver

Processus complet : bump version → commit → tag → GitHub Release.

## Étape 1 — Vérifications préalables

```bash
git status --porcelain
git log --oneline origin/main..HEAD
```

S'il y a des fichiers non commités, **stop** et demande à l'utilisateur de commiter ou stasher d'abord.

## Étape 2 — Déterminer la prochaine version

Récupère la dernière version taguée :

```bash
git tag --sort=-v:refname | head -5
```

Demande à l'utilisateur quel type de bump :
- **patch** (0.1.0 → 0.1.1) : bugfix, hotfix
- **minor** (0.1.0 → 0.2.0) : nouvelle fonctionnalité rétrocompatible
- **major** (0.1.0 → 1.0.0) : breaking change

Ou laisse-lui entrer une version précise (ex: `1.2.3`).

## Étape 3 — Bump des fichiers de version

Met à jour la version dans ces fichiers (seulement s'ils existent) :

- `backend/pyproject.toml` : champ `version = "X.Y.Z"` (ligne 3)
- `frontend/package.json` : champ `"version": "X.Y.Z"`

Utilise l'outil Edit pour chaque fichier. Vérifie avant et après.

## Étape 4 — Commit de version

```bash
git add backend/pyproject.toml frontend/package.json
git commit -m "chore: bump version to vX.Y.Z"
```

## Étape 5 — Tag git annoté

```bash
git tag -a "vX.Y.Z" -m "Release vX.Y.Z"
git push origin main --tags
```

## Étape 6 — GitHub Release

```bash
gh release create "vX.Y.Z" \
  --title "vX.Y.Z" \
  --generate-notes \
  --latest
```

`--generate-notes` génère automatiquement les notes depuis les commits depuis le tag précédent.

## Étape 7 — Confirmation

Affiche le lien vers la release :

```bash
gh release view "vX.Y.Z" --web 2>/dev/null || echo "https://github.com/Gon3s/Blindtest/releases/tag/vX.Y.Z"
```

Résume ce qui a été fait : version bumpée, tag créé, release publiée.
