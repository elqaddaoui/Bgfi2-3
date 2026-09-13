## Réorganisation selon le déroulé officiel des chapitres

La newsletter est désormais structurée exactement selon le tableau de plan fourni : **les 8 chapitres, dans l'ordre, tous mentionnés**. Le contenu éditorial existant n'a pas été modifié — chaque section a été **déplacée telle quelle** (vérification automatique : les 32 sections d'origine sont *byte-identiques*).

### Ordre appliqué

| # | Rubrique | Sections rattachées |
|---|---|---|
| I | Édito du Directeur Général | `#edito` |
| II | Indicateurs clés — Juin 2026 | `#indicateurs`, `#impact` |
| III | Vie sociale et institutionnelle | vœux, retraite Brazzaville, INDABA, séminaire Abidjan, réunion du personnel, banques correspondantes, KBM, BGFI Tour, DRC Mining |
| IV | Innovation projets structurants | transformation digitale, agence Muanda, RakkaCash |
| V | BGFI s'engage et culture d'entreprise | partenariat SBS, Gender Equality, Fête du Travail, Minute SST, Fanzone |
| VI | Valeurs & témoignages | Cynthia Amani, Olivier Mak Makaba |
| VII | Formation — développement des talents | BGFI Étoile, ARC EN CIEL DISC, Anglais |
| VIII | Naissances et mariages | 11 naissances (dont triplés), 5 mariages |

Suivent, hors numérotation, la chronologie, l'abonnement et le finale.

### Une structure lisible, pas un simple re-tri

Chaque chapitre s'ouvre sur une **page de titre** (`.chapitre-divider`) partageant un seul squelette — chapeau → numéro romain + titre → filet → sommaire du chapitre daté. Les huit atmosphères alternent volontairement papier / marine pour que le lecteur *sente* le changement de chapitre :

`I parchment` · `II data` · `III editorial` · `IV circuit` · `V bloom` · `VI beam` · `VII ascend` · `VIII celebration`

Chaque fond est construit en CSS pur (dégradés, trames, formes) — aucun asset ajouté, aucune régression de performance.

### Détails

- **Bloc « triple feature » scindé** : il mélangeait un événement culturel et deux formations. La Fanzone rejoint le chapitre V, les deux formations le chapitre VII — **le texte des cartes est repris mot pour mot**.
- **Pictogrammes chapitre VIII** : ajoutés sur les deux items, comme demandé dans la colonne « observations ».
- **Navigation** : en-tête et menu mobile alignés sur les 8 chapitres (numéraux romains) ; liens du pied de page corrigés (ils pointaient vers des sections masquées).
- **Ton et identité préservés** : palette BGFI (marine / sauge / ivoire), Playfair Display + Cormorant, étoile BGFI, aucune couleur ni police nouvelle.

### Vérifications

- 32 / 32 sections d'origine identiques au bit près ; cartes scindées identiques hors délai d'animation
- 8 dividers présents et dans l'ordre · 43 `<section>` ouvertes / 43 fermées
- 0 ancre cassée · 0 erreur console
- Mobile 390 px : `scrollWidth = 390`, aucun débordement horizontal
- `prefers-reduced-motion` respecté sur toutes les animations ajoutées
