# yamcps-docs

## Description

Recherche documentaire locale en lecture seule via le RAG natif du moteur yamcps.
TXT/Markdown de base, PDF texte et DOCX avec l'extra `formats`. Sans OCR.
Le [guide d'utilisation](docs/usage.md) décrit le manifeste, l'extraction, les
citations et les modèles locaux. Voir [contributing.md](contributing.md) pour les
tests et [MIGRATION.md](MIGRATION.md) pour l'origine du package.

## Quickstart

Python ≥ 3.12 et moteur yamcps compatible avec configs/RAG natifs requis. Depuis
la racine de ce dépôt, dans un environnement activé :

```sh
python -m pip install -e '.[formats]'
yamcps configs set --connector docs
yamcps-docs ingest examples/manifest.json
yamcps serve --connector docs
```

Laisser les champs vides pour le mode lexical et l'index par défaut. Depuis le
client MCP, rechercher `SSS-REQ-0042` dans `demo/specifications`. Le manifeste est
un snapshot complet : une révision retirée est supprimée à l'ingestion. Ne pas
utiliser cet exemple pour remplacer un corpus existant. Le serveur n'ingère rien
au démarrage. Utiliser le même compte/configuration pour ingestion et serveur.

## Outils

| Outil | Description |
| --- | --- |
| `docs_search` | Recherche de passages sourcés dans un corpus explicite |
| `docs_get_document` | Lecture du texte extrait d'une révision précise |
| `docs_get_passage` | Lecture d'un passage cité et de sa provenance |
| `docs_index_status` | Mode, compteurs et date des passages modifiés |

Les ressources `docs://source/{corpus}/{document_id}/{revision}` et
`docs://passage/{passage_id}` exposent aussi les références citées.

## Skills

| Skill | Description |
| --- | --- |
| [docs-research](src/yamcps_docs/skills/docs-research/SKILL.md) | Rechercher des preuves documentaires et citer leurs révisions |

## Variable de configuration

| Variable | Nom du champ | Description | Obligatoire | Valeur par défaut |
| --- | --- | --- | --- | --- |
| `YAMCPS_DOCS_INDEX` | `index` | Chemin de l'index SQLite | Non | Chaîne vide : index du moteur pour `docs` |
| `YAMCPS_DOCS_MODEL` | `model` | Dossier d'un modèle local | Non | Chaîne vide : mode lexical |

Configurer avec `yamcps configs set --connector docs`, sans export. Les chemins
absolus évitent les différences de répertoire courant. Les anciennes variables
d'environnement restent un repli compatible. Un nouveau modèle exige un nouvel
index et une réingestion ; voir le guide pour l'extra `yamcps[rag]`.

## Secret

| Secret | Nom du champ | Description | Obligatoire |
| --- | --- | --- | --- |
| Aucun | — | — | — |
