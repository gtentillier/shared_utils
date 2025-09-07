# shared_utils

Outils utilitaires de développement Python

## Description

Ce dépôt contient les modules suivants :
- paths : accéder rapidement au chemin du projet et au chemin d'accès aux données.

## Installation

### Option 1 : Installation directe avec pip
```bash
pip install git+https://github.com/gtentillier/shared_utils.git@v0.1.0#egg=shared_utils
```

### Option 2 : Si vous utilisez un fichier requirements.txt
1. Ajoutez la ligne suivante dans votre `requirements.txt` pour installer depuis le dépôt GitHub (remplacez `v0.1.0` par la version souhaitée) :

```text
git+https://github.com/gtentillier/shared_utils.git@v0.1.0#egg=shared_utils
```

2. Installez les dépendances :

```bash
pip install -r requirements.txt
```


## Utilisation

### 1. Module paths

Import principal :

```python
from shared_utils import path_data, path_project
```

Exemples :

```python
# Chemin racine du projet
root = path_project
print(root)

# Chemin vers un fichier de données (ex : "data/dataset.csv")
data_path = path_data('dataset.csv')
print(data_path)
```

## Contribution

Les contributions sont les bienvenues ! Veuillez soumettre une issue ou une pull request pour toute amélioration ou correction de bug.