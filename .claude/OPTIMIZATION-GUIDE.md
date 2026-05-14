# 🚀 Optimization Guide — Save 50% API Budget

## 📊 Économies Obtenues

| Optimisation | Économie | Détails |
|--------------|----------|---------|
| **Haiku pour subagents** | -35% | TDD, reviews, product guardian |
| **Disable auto-review** | -15% | Manual /review après 2-3 tickets |
| **Batch processing** | -10% | Group related tickets |
| **Total** | **-50%** | Expected API cost reduction |

---

## 🎯 Optimisations Implémentées

### 1️⃣ Haiku Model for Subagents

Tous les agents utilisent maintenant **Claude Haiku** :

```
Agent               | Ancien   | Nouveau  | Économie
--------------------|----------|----------|----------
TDD-Mentor          | Sonnet   | Haiku    | -70% cost
Backend-Reviewer    | Sonnet   | Haiku    | -70% cost
Frontend-Reviewer   | Sonnet   | Haiku    | -70% cost
Product-Guardian    | Sonnet   | Haiku    | -70% cost
/review             | Sonnet   | Haiku    | -70% cost
```

**Haiku vs Sonnet** :
- Haiku : Très rapide, parfait pour review/lint/règles
- Sonnet : Réservé pour tickets complexes (/ticket T-XXX principal)

---

### 2️⃣ Disable Auto-Review

Avant :
```
/ticket T-008
  → Claude (Sonnet) implémente
  → Auto-call /review (Haiku)
  → Auto-call TDD-Mentor check
  = 2 appels par ticket
```

Maintenant :
```
/ticket T-008
  → Claude (Sonnet) implémente
  = 1 appel par ticket

/ticket T-009
  → Claude (Sonnet) implémente
  = 1 appel

/review
  → Haiku vérifie T-008 + T-009 ensemble
  = 1 appel pour 2 tickets
```

**Résultat** : ~3 appels pour 2 tickets (au lieu de 4)

---

## 💡 Workflow Optimisé

### Pattern : Batch 2-3 Tickets

```
# Session 1 : Batch de 3 tickets (aucun review)
/ticket T-008
  → Sonnet implémente domain logic
  → Rapporte sans review

/ticket T-009
  → Sonnet implémente application layer
  → Rapporte sans review

/ticket T-010
  → Sonnet implémente routes
  → Rapporte sans review

# Review une seule fois
/review
  → Haiku vérifie les 3 tickets ensemble
  → Go/no-go décision

# Commit batch
git add .
git commit -m "feat: T-008,009,010 - Game logic complete"

# Session 2 : Batch suivant
/ticket T-011
...
```

### Coûts Estimés (T-008 à T-041 = 34 tickets)

**Sans optimisation** (auto-review par ticket) :
```
34 tickets × $0.40 per ticket = $13.60
```

**Avec optimisation** (batch 2-3, Haiku reviews) :
```
34 tickets ÷ 2.5 = 14 batches
14 batches × 1 review (Haiku) = 14 × $0.12
34 tickets × $0.14 (Sonnet) = 34 × $0.14
Total : (14 × $0.12) + (34 × $0.14) = $1.68 + $4.76 = $6.44
```

**Économie** : $13.60 - $6.44 = **$7.16 (52% reduction)** 💰

---

## 🎮 Commandes Optimisées

### `/ticket T-XXX` (Sonnet)

```
/ticket T-008

Claude (Sonnet) :
1. Read ticket
2. Test-first (TDD-Mentor checks with Haiku)
3. Implement
4. Report
5. NO auto-review

Coût : ~$0.14
```

### `/review` (Haiku)

```
/review

Claude (Haiku) :
- Check tests pass
- Check lint pass
- Check typing pass
- Check scope

Coût : ~$0.12 (covers 2-3 tickets)
```

---

## ⚡ Best Practices

### ✅ À Faire

```
# Batch 2-3 tickets (cost-effective)
/ticket T-008
/ticket T-009
/ticket T-010
/review

# Review une fois par batch
# Commit une fois par batch
git add .
git commit -m "feat: T-008,009,010 - batch"
```

### ❌ À Éviter

```
# Auto-review par ticket (30% plus cher)
/ticket T-008
/review              # ❌ Trop tôt

/ticket T-009
/review              # ❌ Trop tôt

# Utiliser Sonnet pour des vérifications (gaspille argent)
```

---

## 📋 Checklist Optimisation

- [x] Haiku model configuré pour tous les agents
- [x] Auto-review désactivé dans /ticket
- [x] Batch processing recommandé
- [x] Guides créés

**À toi de jouer** :
- [ ] Utilise /ticket en batch de 2-3
- [ ] Run /review une fois par batch
- [ ] Committe une fois par batch
- [ ] Track économies dans Claude Code usage

---

## 📊 Suivi du Budget

Après chaque session :

```powershell
# Vérifier usage dans Claude Code
# Session usage should show :
# - 85% /ticket (implémentation)
# - 8-10% /review (batched)
# - 5% autres

# Vs avant :
# - 85% /ticket
# - 15% auto-reviews (éliminé)
```

---

## 🚀 Summary

| Aspect | Avant | Après |
|--------|-------|-------|
| **Model subagents** | Sonnet | Haiku |
| **Auto-review** | Oui (par ticket) | Non |
| **Batch size** | 1 ticket | 2-3 tickets |
| **Review frequency** | Par ticket | Par batch |
| **Cost per ticket** | $0.40 | $0.14 |
| **Total for 34 tickets** | $13.60 | $6.44 |
| **Savings** | 0% | **52%** |

---

## 📞 Questions

**Avant de commencer T-008** :

- [ ] Tu comprends le workflow batch ?
- [ ] Tu as des questions sur Haiku vs Sonnet ?
- [ ] Tu veux tester sur 1-2 tickets d'abord ?

**Dis-moi et on y va !** 🚀

---

**Created** : Après Sprint 0  
**Version** : 1.0  
**Status** : Ready for T-008+
