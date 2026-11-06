# Noghte (نقطه)

Prototype d'application de lecture et d'écriture du persan pour des adolescents qui parlent déjà persan (registre familier de Téhéran), connaissent l'alphabet, mais font des erreurs de points et manquent de vocabulaire du registre écrit. Langue d'appui : le français uniquement.

## Ce que contient le prototype

- Test de départ (points, orthographe, registre, vocabulaire) et estimation de couverture de lecture.
- Jour 1 « Arrivée à Téhéran » et Jour 2 « Chez les cousins » : neuf leçons et trois lectures.
- Types d'exercices : paires minimales à l'oreille, « mets les points » (squelette sans points, on tape au-dessus ou en dessous), mot mal pointé à repérer, choix d'orthographe entre homophones (س ص ث, ز ذ ض ظ, ت ط, ح ه, غ ق), familier → soutenu (choix et reconstruction de phrase), lettres à assembler, cartes de vocabulaire avec paraphrase en persan.
- Lecture en registre soutenu avec définition au toucher, chat de famille en registre familier écrit, karaoké avec paroles synchronisées.
- Dot Rush (mini-jeu de 45 secondes), streak, XP, objectif du jour, badges, nom en nastaliq, mascotte Pashmak.
- Tout le contenu est végétarien ou végane.

## Fichiers

- `index.html` : l'application complète (une page, sans dépendance de build). Ouvrable telle quelle sur un serveur statique ou en « Ajouter à l'écran d'accueil » sur iPhone.
- `artifact.html` : la même page sans l'enveloppe `<html>/<head>`, pour la publication comme artefact claude.ai. Généré par `build.py`.
- `content.json` : tout le contenu (mots, exercices, textes, chat, paroles). C'est le fichier à modifier pour ajouter des leçons.
- `content.js` : généré à partir de `content.json`, avec la carte des fichiers audio et les timings du karaoké.
- `audio/` : clips persans générés (voix neuronales fa-IR Dilara et Farid via edge-tts).
- `build.py` : génère les clips manquants et réécrit `content.js` et `artifact.html`.
- `make_icon.py` : dessine les icônes.

## Regénérer après une modification du contenu

```bash
pip install edge-tts pillow
```

```bash
python build.py
```

`build.py` ne régénère que les clips manquants. Pour forcer un clip, supprimer son fichier dans `audio/`.

## Héberger pour les iPhones

Copier le dossier sur n'importe quel hébergement statique (GitHub Pages, Netlify, un serveur web). Ouvrir l'adresse dans Safari, puis Partager › Sur l'écran d'accueil. L'application s'ouvre alors en plein écran avec son icône. La progression est enregistrée sur l'appareil.

## Limites connues du prototype

- Les voix sont synthétiques. Une version publique devrait utiliser des enregistrements ou l'API Azure officielle.
- Pas de compte ni de synchronisation : la progression reste sur l'appareil.
- Les intérêts choisis au départ ne changent pas encore les textes.
- Les paroles du karaoké sont un texte original (pas de licence à gérer).
