# MASCHERA 2.5.0

**Les professions et les rôles familiaux sont désormais masqués eux aussi, avec un nouveau modèle.**

- Deux nouveaux types de données personnelles : les **professions** (« cheffe de projet »,
  « chef d'office », « Head of Legal ») et les **rôles familiaux** (père, grand-mère,
  curateur). Avec leur contexte, ils mènent à une personne. Les deux sont masqués et
  peuvent rester visibles dans les réglages, sous « Personne ».
- **Nouveau modèle `ch-v71f`.** Il poursuit le modèle précédent au lieu de repartir de
  zéro. Il reconnaît les noms dans l'en-tête des procès-verbaux comme des personnes et
  non plus comme une organisation. Sur les neuf documents de référence : 6 fuites comme
  avant, micro-F1 0,757 au lieu de 0,736. Le Flatpak demande avant de télécharger le
  nouveau modèle (1,2 Go).
- **Clic droit sur l'ID ou le type dans le vocabulaire** : le même menu que dans le texte
  masqué, pour changer le type ou retirer le masque. Les tags utilisés récemment sont en
  haut.
- **Dialogue « Utilisation »** avec de petites scènes : poser un masque, changer son type,
  le retirer. Il s'affiche après le premier masquage jusqu'à ce que tu le désactives, et
  il figure dans le menu.
- **Notes de version** dans le menu, dans les quatre langues. Elles voyagent avec l'app,
  rien n'est chargé depuis Internet.
- Affichage étroit : les tuiles suivent la hauteur de la fenêtre, « Reprise dans le
  prompt » figure aussi sous le vocabulaire, et le vocabulaire omet la colonne « Type »
  pour qu'on puisse lire la valeur d'origine.
- Les infobulles apparaissent au-dessus du bouton et non plus sous le pointeur.
- Un modèle avec l'ancien contrat de labels ne se charge pas dans cette version
  (désormais 47 tags, 95 labels).
