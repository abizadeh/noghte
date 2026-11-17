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

## Mécanismes ajoutés après les premiers retours (novembre 2026)

- **Reprise d'une leçon.** Quitter une leçon en route garde la place (`S.resume[id]` : exercices restants, exercices à refaire, score). Le parcours affiche « Reprendre » et propose de reprendre ou de recommencer. Si la liste d'exercices d'une leçon change, la reprise enregistrée est ignorée.
- **Chat à embranchements.** Dans `chats.<id>.script`, chaque option d'un `choice` peut porter `"reply": [ {from, text, fr, note} ]` : ces lignes répondent à ce choix précis, puis le fil commun reprend. Écrire le fil commun pour qu'il fonctionne après n'importe quelle réponse.
- **Karaoké : lire d'abord.** L'apprenant lit une ligne à voix haute, l'écoute, puis se note lui-même (« sans buter » ou « j'ai buté »). La note ne change pas les XP. `build.py` génère un clip par ligne (`audio/karaoke_<id>_<n>.mp3`) en plus du clip complet. La reconnaissance vocale a été écartée pour l'instant : la dictée persane n'est pas fiable sur iPhone et il faudrait envoyer la voix des enfants à un service externe.
- **Dot Rush.** Le jeu utilise `rush_base` (mots du quotidien connus à l'oral, avec leur sens) plus les mots appris en leçon, jamais les mots des leçons non faites. Les mots sont distribués comme un paquet de cartes (pas de répétition avant la fin du paquet). Un mot raté revient quatre tours plus tard, puis plus souvent aux parties suivantes, jusqu'à trois bonnes réponses de suite (`S.rush.w`, boîtes 0 à 3). Le jeu retient aussi les familles de lettres et les paires confondues (`S.rush.f`, `S.rush.c`) pour choisir la lettre à trouver et les mauvaises réponses proposées. Le sens du mot est affiché sous le mot, car deux pointages différents donnent parfois deux vrais mots (خاله et چاله).
- **Écrans de fin honnêtes.** Une précision n'est affichée que si quelque chose a été noté. Le chat affiche le nombre de messages lus, le karaoké les lignes lues sans buter d'après l'apprenant.

## Règles pour les nouvelles leçons (retours des enfants)

- **Leçons courtes.** Une leçon = 8 à 12 exercices, 3 à 4 minutes, 5 mots nouveaux au maximum. Retour d'un des enfants : devant une leçon longue comme La mehmooni (14 mots, 24 exercices), il se dit « je n'ai peut-être pas le temps » et ne la commence pas. Mieux vaut deux ou trois petites leçons sur le même thème.
- **Les lectures, le chat et le karaoké gardent leur longueur.** Elles conviennent telles quelles.
- **Ne pas redécouper les leçons existantes des Jours 1 et 2** (décision du 17 novembre 2026). La règle vaut pour les nouveaux jours.
- **Lire avant d'entendre.** Rien n'est lu automatiquement quand la tâche est de lire (carte de mot, sens du mot, registre, chat, texte). Le son se lance seul seulement quand il est la consigne (écoute, orthographe, points, lettres à assembler).
- **Mauvaise réponse** : « Réessayer » tout de suite ou passer ; l'exercice revient de toute façon à la fin de la leçon.

## Prononciation : la carte `tts` et le labo

La voix de synthèse devine mal certaines voyelles courtes. Le texte affiché à l'apprenant reste toujours l'orthographe normale ; seule la voix reçoit une autre version.

- `content.json` › `tts` : pour un mot, soit un texte de remplacement (`"لبنیات": "لَبَنِیّات"`), soit un objet `{"text": ..., "voice": "male", "solo": true}`. `voice` choisit Farid pour le mot lu seul. `solo` limite l'entrée au mot lu seul ; les phrases qui le contiennent ne sont pas touchées.
- `words.<id>.para_voice` : voix de la phrase de définition d'un mot (ex. تعارف, lue par Farid).
- `build.py` régénère uniquement les clips dont le texte lu ou la voix a changé (`audio/manifest.json`), et versionne les URL audio pour éviter les caches.
- `lab.html` + `lab_build.py` : le labo d'écoute. On met dans `GROUPS` plusieurs variantes d'un mot (voyelles, voix), on augmente `ROUND`, on lance `python lab_build.py`, on pousse. Un locuteur écoute sur `/lab.html?r=<ROUND>`, coche la meilleure variante, copie ses choix. Ces choix vont dans la carte `tts`.

Ce qu'on a appris en quatre séries :

- Partir de l'orthographe simple. Ajouter des voyelles aide une fois sur deux et casse l'autre fois (بنابراین, منتظر, دخترعمو étaient justes sans voyelles).
- Pour un mot isolé mal accentué (خونه, خاله), la voix de Farid sans retouche marche souvent mieux.
- Un sukun bloque une voyelle parasite (کَشْک). Doubler la lettre force une géminée (عَمْمه).
- Si la voix a une lecture fausse figée pour un mot (رسم lu « resm »), le réécrire avec une lettre homophone (رَصْمِ) l'oblige à suivre les voyelles.
- Rien n'est vérifiable sans oreille : chaque changement passe par le labo ou par un signalement dans l'app (drapeau en haut de chaque écran, liste dans Profil).

## Limites connues du prototype

- Les voix sont synthétiques. Une version publique devrait utiliser des enregistrements ou l'API Azure officielle.
- Pas de compte ni de synchronisation : la progression reste sur l'appareil.
- Les intérêts (modifiables dans Profil) ne changent pas encore les textes.
- Les paroles du karaoké sont un texte original (pas de licence à gérer).
