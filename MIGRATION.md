# Origine et migration

Sources extraites de [JoReci2/yamcps](https://github.com/JoReci2/yamcps/tree/d444e3ae014a552edada3e4a7641e9d3b6fea54e)
au commit `d444e3ae014a552edada3e4a7641e9d3b6fea54e`.
Le code métier, les noms des distributions/modules, les entry points et les URI
MCP sont conservés. L'historique avant extraction reste consultable dans ce dépôt
source ; ce dépôt autonome garde son commit initial et reçoit l'import.

Installer une version distribuée de `yamcps` compatible (ou son wheel fourni par
l'opérateur), puis le plugin dans le même environnement. Les capacités configs/RAG
nécessitent un moteur qui les expose : vérifier les imports publics avant usage.
La configuration, les secrets et les données utilisateur ne sont pas migrés et ne
doivent pas être ajoutés au dépôt. Aucun appel métier externe n'est nécessaire
pour les tests ; aucun workflow de publication n'est ajouté.

La migration est préparée sur `refactor/plugins` dans les quatre dépôts.
Intégrer d'abord les trois dépôts de plugins, puis la branche du moteur.
