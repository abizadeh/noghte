# Noghte (نقطه)

Prototype d'application de lecture et d'écriture du persan pour des adolescents qui parlent déjà persan (registre familier de Téhéran), connaissent l'alphabet, mais font des erreurs de points et manquent de vocabulaire du registre écrit. Langue d'appui : le français uniquement.

## Ce que contient le prototype

- Test de départ (points, orthographe, registre, vocabulaire) et estimation de couverture de lecture.
- Jour 1 « Arrivée à Téhéran » et Jour 2 « Chez les cousins » : neuf leçons et trois lectures. Jours 3 et 4 : voir plus bas.
- Types d'exercices : paires minimales à l'oreille, « mets les points » (squelette sans points, on tape au-dessus ou en dessous), mot mal pointé à repérer, choix d'orthographe entre homophones (س ص ث, ز ذ ض ظ, ت ط, ح ه, غ ق), familier → soutenu (choix et reconstruction de phrase), lettres à assembler, cartes de vocabulaire avec paraphrase en persan.
- Lecture en registre soutenu avec définition au toucher, chat de famille en registre familier écrit, karaoké avec paroles synchronisées.
- Dot Rush (mini-jeu de 45 secondes), streak, XP, objectif du jour, badges, nom en nastaliq, mascotte Pashmak.
- Tout le contenu est végétarien ou végane.

## Fichiers

- `index.html` : l'application complète (une page, sans dépendance de build). Ouvrable telle quelle sur un serveur statique ou en « Ajouter à l'écran d'accueil » sur iPhone.
- `artifact.html` : la même page sans l'enveloppe `<html>/<head>`, pour la publication comme artefact claude.ai. Généré par `build.py`.
- `content.json` : tout le contenu (mots, exercices, textes, chat, paroles). C'est le fichier à modifier pour ajouter des leçons. Les scripts qui le modifient passent par `contentfmt.py` (`load`, `dump`) pour garder sa mise en forme.
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

## Jours 3 et 4 (novembre 2026)

Construits d'après les retours sur les Jours 1 et 2 : séances courtes, lecture avant écoute, chat à embranchements, poème et chanson lus d'abord.

- **Jour 3, au bazar de Tajrish** : 11 séances. Chiffres persans, fruits, acheter, politesse, prix, registre (می‌شه, می‌تونم, واسه, دیگه, یه), lire une étiquette quand on est végétarien ou végane, un texte, un chat (pique-nique), une révision.
- **Jour 4, une soirée chez les cousins** : 11 séances. Musique, cinéma, foot, sentiments, mots de liaison de l'écrit, registre (passé pluriel, ـش collé, تو pour در), orthographe, un texte au choix (film ou foot, selon les intérêts), une chanson, une révision. Le poème بنی‌آدم de Saadi a été retiré après écoute : la voix de synthèse lit mal la poésie classique. Son texte, sa traduction et ses notes sont gardés dans `content.json` sous `parked`, pour le jour où un humain l'enregistre.
- 49 mots nouveaux en tout, cinq au maximum par séance.

Ce qui a été ajouté au moteur :

- **Type d'exercice `mc`** (`content.json` › `mc`) : une question générale. `show` affiche un chiffre, un prix ou une étiquette (`box: true` pour un encadré), `audio` fait entendre la consigne, `options` et `answer` donnent les choix, `optFa: true` si les choix sont en persan.
- **Carte `explain` générale** : `cols` change les en-têtes, `eyebrow` le sur-titre. Une cellule n'est cliquable que si un clip existe pour son texte.
- **Séance de révision** (`kind: "review"`) : reconstruite à chaque ouverture. Elle reprend jusqu'à six exercices que cet apprenant a ratés au premier essai (`S.miss`), complétés par des exercices déjà vus. Un exercice sort de la liste quand il est réussi au premier essai.
- **Texte au choix** : une leçon de lecture peut avoir `variants` (plusieurs textes, chacun avec ses `interests`). Les textes qui correspondent aux intérêts de l'apprenant sont mis en avant ; un seul suffit pour valider.
- **Poème** : même écran que le karaoké, avec `label`, `whole` et `done` pour les libellés. Non utilisé pour l'instant (voir `parked`).
- **Écoute de contrôle** : `check.html` liste tous les clips des unités nommées dans `check_units`, leçon par leçon, avec une case « faux ». À faire écouter par un locuteur avant de donner un nouveau jour aux enfants ; les clips cochés se corrigent ensuite dans la carte `tts` ou au labo.

- **Jour en préparation** : une unité avec `"draft": true` dans `content.json` n'apparaît qu'en mode démo (Profil). Les Jours 3 et 4 ont été publiés le 17 novembre 2026, après l'écoute de contrôle et la série 6 du labo. Pour publier un jour, retirer `"draft": true` de son unité, relancer `python build.py --no-audio` et pousser.

Pour ajouter un jour : ajouter les mots dans `words`, les exercices dans les listes (`pairs`, `spell`, `dots`, `fixdots`, `register_mc`, `register_build`, `build`, `mc`, toujours à la fin, car les leçons y renvoient par numéro), l'unité dans `units`, les textes dans `readings` avec leurs mots dans `lexicon`, puis lancer `python build.py` et faire l'écoute de contrôle.

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

Autres réglages de la voix dans `content.json` :

- `"in"` dans une entrée `tts` : la lecture à utiliser quand le mot est dans une phrase, différente de celle du mot seul (بالاخره : seul, Farid sans retouche ; dans une phrase, بِلَخَره).
- Une phrase entière peut être une clé de `tts` : la voix reçoit alors exactement le texte donné, sans autre remplacement.
- `mute` : textes sans lecture acceptable pour l'instant. Aucun clip n'est généré et l'app n'affiche pas de haut-parleur pour eux.
- `tts_frozen` : lectures figées de clips déjà écoutés, pour qu'une correction des règles de `build.py` ne les modifie pas.
- `build.py` supprime les clips qu'aucun texte n'utilise plus.

Ce qu'on a appris au fil des séries :

- Partir de l'orthographe simple. Ajouter des voyelles aide une fois sur deux et casse l'autre fois (بنابراین, منتظر, دخترعمو étaient justes sans voyelles).
- Pour un mot isolé mal accentué (خونه, خاله), la voix de Farid sans retouche marche souvent mieux.
- Un sukun bloque une voyelle parasite (کَشْک). Doubler la lettre force une géminée (عَمْمه).
- Si la voix a une lecture fausse figée pour un mot (رسم lu « resm »), le réécrire avec une lettre homophone (رَصْمِ) l'oblige à suivre les voyelles.
- Pour faire entendre un ezafé non écrit, l'écrire avec un ه pour la voix (نونه سنگک pour « nun-e sangak »). Le kasra seul n'a pas suffi.
- Un -o familier écrit و est lu « u » (کتابو). Le remplacer par un zamma pour la voix (کتابُ). Mais اینو et رو étaient justes tels quels : vérifier avant de toucher.
- L'ezafé non écrit est la première cause d'erreur (8 signalements sur 25 pour les Jours 3 et 4). Selon la phrase, c'est le ه (ساعته ده, دمه دره) ou le kasra (ساعَتِ ده, عاشِقِ) qui marche : toujours proposer les deux au labo.
- Un ezafé parasite se supprime avec une virgule pour la voix (شیرینیش، گیاهی ; انار کیلویی، چند است).
- Pour un mot isolé mal accentué, la voix de Farid sans retouche a gagné six fois sur neuf à la série 6.
- La poésie classique ne passe pas en voix de synthèse : il faut un lecteur humain.
- Le ton des questions fermées (série 8). Mesuré sur tous les clips de questions : la voix ne finit jamais haut, la hauteur redescend toujours. Sur une question soutenue (می‌شود تخفیف بدهید؟) elle redescend autant que dans une affirmation. Ni آیا, ni la ponctuation, ni لطفاً, ni un clip coupé avant « یا نه » n'y changent rien. Les études sur l'intonation du persan (Sadat-Tehrani 2011 ; Sadeghi 2021) décrivent une fin haute après un creux, avec un dernier accent plus haut. Le service refuse une courbe de hauteur, mais accepte deux blocs côte à côte : `twopart.py` dit la fin de la phrase plus haut (tout le dernier mot, ou sa dernière syllabe : `بِدَ|هید؟`). Dans `lab_build.py`, une variante s'écrit alors `(texte avec |, voix, hauteur[, vitesse])`. `build.py` ne connaît pas encore cette forme : à ajouter si une variante est retenue.
- Rien n'est vérifiable sans oreille : chaque changement passe par le labo ou par un signalement dans l'app (drapeau en haut de chaque écran, liste dans Profil).

## Limites connues du prototype

- Les voix sont synthétiques. Une version publique devrait utiliser des enregistrements ou l'API Azure officielle.
- Pas de compte ni de synchronisation : la progression reste sur l'appareil.
- Les intérêts (modifiables dans Profil) ne changent pas encore les textes.
- Les paroles du karaoké sont un texte original (pas de licence à gérer).
