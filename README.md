# Algorithmique Scala 2.13 — Anki

Deck Anki unique pour réviser rapidement les réflexes d’algorithmique en **Scala 2.13**, avec des exemples volontairement impératifs, explicites et faciles à réutiliser sous chrono.

Le repository garde la **source canonique en JSON lisible et diffable**. Le fichier importable par Anki / AnkiDroid est un **`.apkg`** ; le script Python `scripts/build_deck.py` assemble les sources JSON et produit `dist/scala-algorithms-anki.apkg`.

## Contenu actuel

**146 cartes** dans un seul deck, avec tags hiérarchiques.

Types de cartes :

- `type::method` — méthodes Scala utiles (`toCharArray`, `take`, `drop`, `indices`, `sorted`, etc.)
- `type::import` — imports complets des collections utiles
- `type::operator` — opérateurs Scala / JVM (`%`, `/`, bitwise, shifts, etc.)
- `type::tip` — micro-réflexes techniques (digit, parité, puissance de 2, bit masks…)
- `type::signal` — formulation d’un problème → **un seul réflexe principal** → template → exercice concret
- `type::difference` — différence entre deux concepts et impact de complexité
- `type::error` — petites cartes « corrige l’erreur »
- `type::thinking` — réflexes de résolution et de gestion du chrono

Le choix éditorial est volontaire : lorsqu’un réflexe générique suffit, le deck évite de proposer plusieurs solutions concurrentes. Exemple : pour compter des occurrences, le réflexe standard est **HashMap**, pas « HashMap ou frequency array selon… ».

## Structure du repository

```text
data/deck.json                  # métadonnées du deck unique
data/cards/*.json               # source des cartes, répartie par thème/type pour des diffs lisibles
schema/deck.schema.json         # validation des métadonnées
schema/cards.schema.json        # validation des fichiers de cartes
scripts/build_deck.py           # assemblage JSON -> APKG + coloration Scala
requirements.txt                # dépendances Python
.github/workflows/build.yml     # validation/build automatique sur push et PR
dist/                           # sortie locale ; les .apkg générés ne sont pas commités
```

Les fichiers JSON sont séparés uniquement pour rendre les PR et les diffs plus faciles à relire. **Ils sont tous assemblés dans un seul deck Anki.**

## Prérequis Python

Le générateur est un petit utilitaire Python. **Python 3.10+** est recommandé ; le CI utilise Python 3.12.

Créer un environnement virtuel à la racine du repository :

```bash
python -m venv .venv
```

L’activer sous Windows :

```powershell
.venv\Scripts\activate
```

Ou sous macOS / Linux :

```bash
source .venv/bin/activate
```

Puis installer les dépendances :

```bash
python -m pip install -r requirements.txt
```

Les dépendances sont volontairement limitées :

- `genanki` — construction du package `.apkg`
- `Pygments` — coloration syntaxique Scala intégrée directement au HTML des cartes
- `jsonschema` — validation des sources JSON

## Utiliser les utilitaires Python

### Construire et valider le deck

Depuis la racine du repository :

```bash
python scripts/build_deck.py
```

Le script :

1. charge `data/deck.json` ;
2. charge tous les fichiers `data/cards/*.json` dans l’ordre alphabétique ;
3. valide les métadonnées et chaque fichier de cartes avec les JSON Schemas ;
4. refuse les IDs de cartes dupliqués, même s’ils sont dans des fichiers différents ;
5. transforme les blocs Scala en HTML avec coloration syntaxique Pygments ;
6. génère **un seul deck Anki** avec des GUID stables ;
7. écrit le résultat dans :

```text
dist/scala-algorithms-anki.apkg
```

Un build réussi affiche par exemple :

```text
Built 146 cards -> .../dist/scala-algorithms-anki.apkg
```

Le build sert aussi de validation. Il n’y a volontairement pas un second script à retenir :

```bash
python scripts/build_deck.py
```

est la commande unique à lancer après une modification.

### Choisir un autre fichier de sortie

Le script accepte `--output` :

```bash
python scripts/build_deck.py --output /tmp/my-scala-deck.apkg
```

Sous Windows :

```powershell
python scripts/build_deck.py --output C:\Temp\scala-algorithms-anki.apkg
```

## Importer dans AnkiDroid

1. Générer ou télécharger `scala-algorithms-anki.apkg`.
2. Copier/télécharger le fichier sur Android.
3. Dans AnkiDroid : **Import file**.
4. Sélectionner le `.apkg`.

Les cartes ont des GUID stables dérivés de leur `id`. Une version régénérée peut donc mettre à jour les cartes existantes au lieu de créer systématiquement des doublons, à condition de conserver les mêmes IDs.

## Modifier les flashcards

Le contenu doit être modifié dans **`data/cards/*.json`**. Ces JSON sont la source de vérité du deck et sont volontairement organisés en fichiers assez petits pour garder les diffs Git lisibles.

Une carte ressemble à :

```json
{
  "id": "signal-two-sum",
  "type": "signal",
  "tags": ["type::signal", "topic::hashmap", "topic::two-sum"],
  "question": "…",
  "answer": {
    "reflex": "…",
    "template": "…",
    "example": {
      "prompt": "…",
      "code": "…"
    }
  }
}
```

Règles importantes :

- `id` doit rester stable une fois une carte distribuée : il sert à produire son GUID Anki ;
- `id` doit être unique dans tout le deck ;
- les blocs Scala restent du **texte Scala brut** dans le JSON ;
- ne pas commiter le `.apkg` généré : `dist/*.apkg` est ignoré par Git ;
- après une modification, lancer `python scripts/build_deck.py`.

## Coloration syntaxique

La coloration n’est pas faite avec JavaScript dans AnkiDroid. Pendant le build, `Pygments` convertit chaque bloc Scala en HTML coloré et le CSS nécessaire est incorporé dans le modèle Anki.

Cela permet de garder :

- un JSON source simple ;
- du Scala lisible dans les diffs Git ;
- une présentation colorée dans Anki et AnkiDroid.

## Convention de code des cartes

- Scala 2.13 simple ; pas de syntaxe Scala 3.
- Variables explicites : `currentIndex`, `leftIndex`, `currentNumber`, `neighbourRow`…
- Style impératif privilégié pour rendre la mécanique algorithmique visible.
- `Array`, `mutable.HashSet`, `mutable.HashMap` comme structures de base quand elles suffisent.
- Pour les cartes de « signal », privilégier **un réflexe principal unique**, générique et facile à remobiliser.
- Les variantes plus compactes / bitwise peuvent apparaître dans les cartes de tips ; les patterns complets restent lisibles et commentés.

## CI GitHub Actions

`.github/workflows/build.yml` s’exécute sur :

- chaque `push` ;
- chaque pull request ;
- lancement manuel avec `workflow_dispatch`.

Le workflow installe les dépendances, exécute :

```bash
python scripts/build_deck.py
```

puis publie `dist/scala-algorithms-anki.apkg` comme artifact GitHub Actions nommé **`scala-algorithms-anki`**.

Cela permet de vérifier chaque PR et de récupérer un `.apkg` prêt à importer sans devoir installer Python localement.

## Références format

- AnkiDroid User Manual — import : https://docs.ankidroid.org/
- Anki Manual — packaged decks : https://docs.ankiweb.net/importing/packaged-decks.html
- genanki : https://github.com/kerrickstaley/genanki
