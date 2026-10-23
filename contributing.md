# Contribuer à yamcps-docs

Python ≥ 3.12. Installer d'abord un moteur yamcps compatible depuis sa distribution,
son wheel ou, pour travailler sur les deux dépôts, `python -m pip install -e ../yamcps`.
Depuis la racine de ce dépôt dans un environnement activé :

```sh
python -m pip install -e '.[dev,formats]'
ruff format --check src tests
ruff check src tests
mypy src
radon cc src -s -a
bandit -r src
coverage run --source=yamcps_docs -m pytest -q
coverage report --show-missing --fail-under=81
python -m unittest discover -s tests -p 'test_*.py'
python -m build
```

Les sources et les tests de ce dépôt ne nécessitent pas le dépôt source du moteur.
Le moteur est une dépendance Python installée. Sur poste hors ligne, fournir les
wheels de toutes les dépendances, dont `hatchling` et `editables` pour le mode
editable ; utiliser `--no-index --find-links /chemin/wheels` et construire avec
`python -m build --no-isolation` après installation des outils.

Suivre PEP 8 (100 caractères), typer les interfaces publiques, documenter en anglais
au format Google ; guides en français. Utiliser unittest pour les nouveaux tests,
conserver les tests existants et simuler les API. Garder stdout pour MCP stdio,
les secrets hors des logs, et aucun appel réseau à l'import ou à l'enregistrement.
Tester une installation wheel hors du dépôt, sans PYTHONPATH vers ses sources.
Conserver une couverture >80 %, examiner Radon/Bandit et signaler les limites.
Ne pas publier sur PyPI ni déclencher une release sans demande explicite.

## Intégration au moteur

Le connecteur utilise la capacité RAG native de yamcps : `rag_config()` déclare
les chemins et `configure_rag()` reçoit le contexte paresseux géré par le moteur.
`required_configs()` déclare les champs non secrets `index` et `model`, puis
`configure_configs()` reçoit leurs valeurs. Aucun package RAG séparé n'est requis.
L'ingestion CLI résout la même configuration que le serveur.

Conserver la séparation entre ingestion explicite et outils MCP en lecture seule,
sans accès aux fichiers sources depuis les paramètres MCP. Les formats, limites,
commandes et règles de citation sont décrits dans le [README](README.md).
