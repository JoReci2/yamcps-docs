# Contribuer à yamcps-docs

Python ≥ 3.12 et yamcps 0.3.0. Depuis la racine de ce dépôt, créer un
environnement isolé et installer la version exacte du moteur pour la validation :

```sh
python -m venv .venv
# Activer cet environnement selon le système.
python -m pip install -e '.[dev,all]' 'yamcps==0.3.0'
python -c "from importlib.metadata import version; print(version('yamcps'), version('mcp'))"
ruff format --check src tests .github/workflows
ruff check src tests .github/workflows
mypy src .github/workflows
radon cc src .github/workflows -s -a
bandit -r src .github/workflows
coverage run --source=yamcps_docs -m pytest -q
coverage report --show-missing --fail-under=81
python -m unittest discover -s tests -p 'test_*.py'
python -m build
```

Les sources et les tests de ce dépôt ne nécessitent pas le dépôt source du moteur.
Le moteur est une dépendance Python installée. Sur poste hors ligne, fournir les
wheels de toutes les dépendances, dont `hatchling`, `hatch-vcs` et `editables` pour le mode
editable ; utiliser `--no-index --find-links /chemin/wheels` et construire avec
`python -m build --no-isolation` après installation des outils.

Suivre PEP 8 (100 caractères), typer les interfaces publiques, documenter en anglais
au format Google ; guides en français. Utiliser unittest pour les nouveaux tests,
conserver les tests existants et simuler les API. Garder stdout pour MCP stdio,
les secrets hors des logs, et aucun appel réseau à l'import ou à l'enregistrement.
Tester une installation wheel hors du dépôt, sans PYTHONPATH vers ses sources :

```sh
python -m venv /tmp/yamcps-docs-wheel-check
/tmp/yamcps-docs-wheel-check/bin/python -m pip install /chemin/absolu/plugin.whl 'yamcps==0.3.0' pytest pytest-asyncio pypdf python-docx openpyxl xlrd python-pptx
cd /tmp
/tmp/yamcps-docs-wheel-check/bin/python -c "from importlib.metadata import version; print(version('yamcps'))"
/tmp/yamcps-docs-wheel-check/bin/python -m unittest discover -s /chemin/absolu/yamcps-docs/tests -p 'test_core_integration.py'
/tmp/yamcps-docs-wheel-check/bin/python -m unittest discover -s /chemin/absolu/yamcps-docs/tests -p 'test_docs.py'
/tmp/yamcps-docs-wheel-check/bin/python -m unittest discover -s /chemin/absolu/yamcps-docs/tests -p 'test_excel.py'
/tmp/yamcps-docs-wheel-check/bin/python -m unittest discover -s /chemin/absolu/yamcps-docs/tests -p 'test_powerpoint.py'
```

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

## Versionnement et publication

La version est calculée par `hatch-vcs` depuis les tags Git `v<version>`, par
exemple `v0.2.0` ; ne pas ajouter de version fixe dans `pyproject.toml`.
Conserver l'historique et les tags lors du clonage. Entre deux tags, la version
est une version de développement. Une archive source construite conserve sa
version pour permettre de reconstruire le wheel sans dépôt Git.

Le workflow `.github/workflows/workflow.yaml` se déclenche uniquement à la
publication d'une release GitHub. Il extrait le tag avec tout l'historique,
vérifie que le commit appartient à `main`, construit le wheel et l'archive source,
puis vérifie leur identité `yamcps-docs` et leur version exacte face au tag.
Twine contrôle les métadonnées avant le transfert des artefacts au job de
publication. Les contrôles de développement restent exécutés en local.

Configurer l'environnement GitHub `pypi` et un Trusted Publisher sur PyPI pour
le projet `yamcps-docs`, le dépôt `JoReci2/yamcps-docs`, le workflow `workflow.yaml`
et l'environnement `pypi`. La publication utilise OIDC, sans token PyPI stocké.
Voir la [documentation PyPI](https://docs.pypi.org/trusted-publishers/using-a-publisher/).
Une nouvelle publication nécessite un nouveau tag et une nouvelle version.
Aucune release ni publication n'est déclenchée par la mise en place du workflow.
