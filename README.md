# yamcps-docs

Recherche documentaire locale via le RAG natif du moteur
[yamcps](https://github.com/JoReci2/yamcps). Le plugin expose les documents indexés
en lecture seule dans MCP ; l'ingestion se fait séparément en ligne de commande.
Aucun secret n'est requis.

TXT et Markdown UTF-8 sont pris en charge de base ; PDF texte et DOCX nécessitent
l'extra `formats`. L'extraction ne fait ni OCR, ni extraction de figures, ni
reconstruction de la mise en page.

## Démarrage rapide

Python ≥ 3.12 et un moteur yamcps compatible avec les configurations et le RAG
natifs sont requis. Installer le plugin dans le même environnement que le moteur :

```sh
python -m pip install 'yamcps-docs[formats]'
yamcps configs set --connector docs
```

Laisser les champs `index` et `model` vides pour utiliser l'index par défaut du
moteur et la recherche lexicale. Depuis la racine de ce dépôt, essayer le devis de travaux
fictif fourni :

```sh
yamcps-docs ingest examples/manifest.json
yamcps serve --connector docs
```

Les fichiers d'exemple sont disponibles dans [examples](examples) ; hors du dépôt,
les copier ensemble dans un dossier local. Depuis le client MCP, demander de
rechercher `DEV-2026-0042` dans le corpus `demo/travaux`.

Le serveur n'ingère rien au démarrage. Utiliser le même compte et la même
configuration pour l'ingestion et le serveur. Le manifeste remplace le contenu du
corpus désigné : ne pas utiliser l'exemple pour remplacer un corpus existant.

Par exemple, demander ensuite : « Quel est le montant TTC du devis et quel acompte
est prévu ? » ou « La peinture est-elle comprise dans le poste TRV-003 ? », avec
les passages sources à l'appui.

## Configuration

Configurer les chemins avec `yamcps configs set --connector docs` ; aucun export
de variable d'environnement n'est nécessaire. Les valeurs sont enregistrées dans
un fichier JSON local. Préférer des chemins absolus pour éviter les différences
de répertoire courant.

| Champ | Description | Valeur par défaut | Ancienne variable de repli |
| --- | --- | --- | --- |
| `index` | Chemin de l'index SQLite | Vide : index du moteur pour `docs` | `YAMCPS_DOCS_INDEX` |
| `model` | Dossier d'un modèle sémantique local | Vide : recherche lexicale | `YAMCPS_DOCS_MODEL` |

Les deux champs sont facultatifs. Voir le
[guide de configuration du moteur](https://github.com/JoReci2/yamcps/blob/main/docs/configuration.md)
pour leur priorité, `--config-file` et le mode non interactif. Pour un fichier de
configuration personnalisé, le transmettre aux deux commandes :

```sh
yamcps-docs ingest /chemin/vers/manifest.json --config-file /chemin/vers/config.json
yamcps serve --connector docs --config-file /chemin/vers/config.json
```

### Recherche sémantique locale optionnelle

Sans modèle, la recherche est lexicale et ne comprend pas les synonymes. Pour
activer la recherche hybride avec un modèle déjà présent sur la machine :

```sh
python -m pip install 'yamcps[rag]>=0.1,<0.2'
yamcps configs set --connector docs --name model --value /chemin/absolu/vers/modele-local
yamcps configs set --connector docs --name index --value /chemin/absolu/docs-hybrid.sqlite3
yamcps-docs ingest /chemin/vers/manifest.json
yamcps serve --connector docs
```

Utiliser le même modèle pour l'ingestion et la recherche. Un changement de modèle
exige un nouvel index et une réingestion. Aucun modèle n'est fourni ni téléchargé,
et aucun code distant n'est autorisé. Côté serveur, le modèle est chargé au premier
appel MCP, dans un thread, jamais à l'import ou à l'enregistrement du plugin.
Évaluer sa qualité sur vos questions métier ; aucune qualification IVVQ n'est
revendiquée.

## Ingestion d'un corpus

Créer un manifeste JSON à côté des fichiers à indexer. Par exemple, avec `devis-travaux.md`
dans le même dossier que `manifest.json` :

```json
{
  "corpus": "demo/travaux",
  "sources": [
    {
      "path": "devis-travaux.md",
      "document_id": "DEV-2026-0042",
      "revision": "1.0",
      "metadata": {"project": "renovation-salon", "status": "example", "type": "devis"}
    }
  ]
}
```

Puis lancer :

```sh
yamcps-docs ingest /chemin/vers/manifest.json
```

Le manifeste est un **snapshot complet d'un seul corpus** : retirer une source
supprime cette révision de l'index. Garder explicitement les anciennes révisions
souhaitées. Les métadonnées sont facultatives et associent des clés à des valeurs
textuelles ; elles servent aux filtres de recherche. L'extraction de toutes les
sources se termine avant la synchronisation atomique du corpus. Une ingestion
identique réutilise les passages existants.

Les chemins des sources sont relatifs au dossier du manifeste. Les chemins
absolus, les traversées `..` et les liens symboliques sont refusés. Chaque source
est limitée à 20 MiB et à 4 millions de caractères extraits ; un texte vide est
refusé. N'ingérer que des fichiers de confiance.

Le découpage utilise au plus 1200 caractères par passage, sans chevauchement.
L'option `--chunk-size` permet une valeur de 64 à 16000. Un passage peut couper une
phrase ou un tableau. Les contenus sont stockés en clair dans SQLite : protéger
le dossier avec les droits du système et sauvegarder l'index si nécessaire.

## Recherche et citations dans MCP

| Outil | Paramètres | Description |
| --- | --- | --- |
| `docs_search` | `query`, `corpus`, `filters=None`, `limit=5` | Recherche de passages sourcés ; limite de 1 à 20 |
| `docs_get_document` | `corpus`, `document_id`, `revision` | Texte extrait d'une révision précise |
| `docs_get_passage` | `passage_id` | Passage cité et provenance exacte |
| `docs_index_status` | `corpus` | Mode, compteurs et date du dernier passage modifié |

Toujours préciser le corpus lors d'une recherche. Les filtres correspondent
exactement aux métadonnées du manifeste, par exemple
`{"project": "renovation-salon", "type": "devis"}` ; ils ne constituent pas des droits
d'accès.

Les ressources `docs://source/{corpus}/{document_id}/{revision}` (segments encodés)
et `docs://passage/{passage_id}` exposent aussi les références citées. Pour une
citation vérifiable, conserver `document_id`, `revision`, `source_uri`,
`passage_id` et les offsets `start`/`end` renvoyés. Ces offsets désignent des
caractères dans le texte extrait, début inclus et fin exclue ; ils ne garantissent
pas une pagination dans le document original.

L'index est une copie des sources au moment de l'ingestion. La date indiquée par
`docs_index_status` concerne les passages modifiés et ne prouve pas la fraîcheur
des fichiers sources. Un index absent produit une erreur explicative au premier
appel, sans empêcher les autres plugins de démarrer. Aucune mutation de l'index
n'est exposée au modèle via MCP.

Le skill embarqué
[docs-research](src/yamcps_docs/skills/docs-research/SKILL.md) guide la recherche de
preuves et la citation des révisions exactes.

## Contribution et origine

Voir [contributing.md](contributing.md) pour l'installation de développement,
l'intégration au moteur et les validations, et [MIGRATION.md](MIGRATION.md) pour
l'origine du package et les notes de migration.
