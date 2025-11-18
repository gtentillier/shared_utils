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

Import :

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

### 2. Module measure_time - Décorateur de timing

Mesurez automatiquement le temps d'exécution d'une fonction avec le décorateur `@measure_time`.

#### Import

```python
from shared_utils import measure_time
```

#### Utilisation

```python
from shared_utils import measure_time

@measure_time
def ma_fonction():
    # ... code à chronométrer
    pass

ma_fonction()
# Affiche: "ma_fonction exécutée en 0.123s"
```

#### Exemples

**Avec une fonction simple :**

```python
from shared_utils import measure_time
import time

@measure_time
def traitement_rapide():
    time.sleep(0.5)

traitement_rapide()
# Affiche: "traitement_rapide exécutée en 0.500s"
```

**Avec une méthode de classe :**

```python
from dataclasses import dataclass
from shared_utils import measure_time

@dataclass
class Calcul:
    valeur: int
    
    @measure_time
    def calcul_couteux(self):
        total = sum(range(self.valeur))
        return total

calc = Calcul(10_000_000)
result = calc.calcul_couteux()
# Affiche: "calcul_couteux exécutée en 0.234s"
```

#### Format d'affichage

La durée est formatée selon les règles suivantes :

- **< 10 secondes** : `"0.123s"` (3 décimales)
- **10s - 60s** : `"12s"` (nombres entiers)
- **≥ 60 secondes** : `"2min 12s"` (minutes entières + secondes)

Exemples :
- 0.5s → `"0.500s"`
- 5.234s → `"5.234s"`
- 12s → `"12s"`
- 65s → `"1min 5s"`
- 125.5s → `"2min 5.500s"`

### 3. Module openAI_requests

Effectuez des appels à l'API OpenAI et calculez automatiquement les coûts associés.

#### Installation des dépendances

```bash
pip install openai
```

#### Imports

```python
from shared_utils import OpenAILLMCaller, PricingCalculator, ModelPricing, ResponsePrice
```

#### 3.1 Appeler l'API OpenAI

```python
from shared_utils import OpenAILLMCaller

# Créer un caller
caller = OpenAILLMCaller(api_key="votre-clé-api")

# Effectuer un appel simple
response = caller.response(model="gpt-4.1-nano", input="Dis-moi un blague", max_output_tokens=100)
print(response.output_text)
```

**Paramètres principaux :**

```python
caller.response(
    model="gpt-4.1-nano",               # Modèle à utiliser
    input="Votre prompt",              # Prompt d'entrée (texte ou liste)
    max_output_tokens=256,              # Longueur max de la réponse
    temperature=0.7,                    # Créativité (0-2)
    service_tier="standard",            # "standard", "priority", ou "flex"
    tools=[...],                        # Outils disponibles (optionnel)
    stream=False,                       # Activer le streaming (optionnel)
)
```

**Modèles disponibles :** `gpt-4.1-nano`, `gpt-4.1-mini`, `gpt-5-mini`, `gpt-5-nano`

#### 3.2 Calculer les coûts

```python
from shared_utils import OpenAILLMCaller, PricingCalculator

# Effectuer un appel
caller = OpenAILLMCaller(api_key="votre-clé-api")
response = caller.response(model="gpt-4.1-nano", input="2 + 2 = ?", max_output_tokens=16)

# Calculer le coût
calculator = PricingCalculator()
price = calculator.get_price(response, service_tier="standard")

price.print_price()  # Affiche: "$... (input, X%) + $... (output, Y%) = $... total"
```

**Service tiers disponibles :**
- `standard` : Tarif normal
- `priority` : Tarif prioritaire (✅ gpt-4.1-*, gpt-5-mini, gpt-5.1, gpt-5)
- `flex` : Tarif réduit (✅ gpt-5-nano, gpt-5-mini, gpt-5.1, gpt-5)

**Exemples supplémentaires :**

```python
# Récupérer le tarif d'un modèle
pricing = calculator.get_pricing("gpt-4.1-nano", service_tier="priority")
print(f"Coût par million de tokens: {pricing.input:.3f}")

# Additionner plusieurs réponses
total = price1 + price2
total.print_price()  # Affiche le détail avec nombre de requêtes
```

### 3.3 Speech-to-Text (STT) avec Whisper

Transcrire des fichiers audio en utilisant soit le modèle Whisper local, soit l'API OpenAI.

#### Installation des dépendances

Pour utiliser le mode local :
```bash
pip install torch whisper
```

#### Imports

```python
from shared_utils import OpenAISTTCaller, PricingCalculator
```

#### Utilisation de base

**Mode local (par défaut) :**

```python
from shared_utils import OpenAISTTCaller
from pathlib import Path

# Créer un caller avec le modèle Whisper local
stt = OpenAISTTCaller(model="turbo")

# Transcrire un fichier audio
result = stt.transcribe(audio_path="audio.mp3")
print(result["text"])  # Texte transcrit
print(result["language"])  # Langue détectée
print(result["duration"])  # Durée de l'audio
```

**Mode API OpenAI :**

```python
from shared_utils import OpenAISTTCaller

# Créer un caller avec l'API OpenAI
stt = OpenAISTTCaller(api_key="votre-clé-api", use_api=True)

# Transcrire un fichier audio
result = stt.transcribe(audio_path="audio.mp3", model="whisper-1")
print(result["text"])  # Texte transcrit
```

#### Paramètres de transcription

```python
stt.transcribe(
    audio_path="chemin/vers/audio.mp3",  # Chemin du fichier audio
    model="turbo",                        # Modèle à utiliser
    language="fr",                        # Code langue (ex: "fr", "en")
    response_format="verbose_json",       # Format de réponse
    timestamp_granularities=["segment"],  # Granularité des timestamps
    task="transcribe",                    # "transcribe" ou "translate"
)
```

**Paramètres détaillés :**

- **audio_path** : Chemin vers le fichier audio
- **model** : 
  - Mode local : `"turbo"` (par défaut) ou `"large"`
  - Mode API : `"whisper-1"`, `"gpt-4o-mini-transcribe"`, ou `"gpt-4o-transcribe"`
- **language** : Code langue ISO 639-1 (ex: `"fr"`, `"en"`, `"es"`). Si `None`, détection automatique
- **response_format** : Format de sortie (`"json"`, `"text"`, `"verbose_json"`, `"srt"`, `"vtt"`)
- **timestamp_granularities** : Niveau de détail des timestamps (`["segment"]`, `["word"]`, ou `["word", "segment"]`)
- **task** : `"transcribe"` (par défaut) ou `"translate"` (vers l'anglais)

#### Format de réponse (verbose_json)

```python
result = stt.transcribe(audio_path="audio.mp3", response_format="verbose_json")

# Structure de la réponse
{
    "text": "Texte transcrit complet",
    "language": "fr",
    "duration": 15.5,
    "segments": [
        {
            "id": 0,
            "seek": 0,
            "start": 0.0,
            "end": 2.5,
            "text": "Bonjour...",
            "tokens": [...],
            "temperature": 0.0,
            "avg_logprob": -0.3,
            "compression_ratio": 1.2,
            "no_speech_prob": 0.001
        },
        # ... autres segments
    ],
    "usage": {"seconds": 15.5, "type": "duration"}
}
```

#### Calcul du coût STT

```python
from shared_utils import OpenAISTTCaller, PricingCalculator

# Transcrire un audio
stt = OpenAISTTCaller(use_api=True, api_key="votre-clé-api")
result = stt.transcribe(audio_path="audio.mp3", model="whisper-1")

# Calculer le coût basé sur la durée
calculator = PricingCalculator()
duration = result["usage"]["seconds"]
price = calculator.get_price_for_stt("whisper-1", duration)

price.print_price()  # Affiche le coût de transcription
# Exemple: "$0.00025 total (x1 appels, $0.00025 par appel)"
```

#### Accéder à la durée d'exécution

```python
stt = OpenAISTTCaller()
result = stt.transcribe(audio_path="audio.mp3")

# Temps total de transcription (en secondes)
print(f"Transcription réalisée en {stt.last_duration:.2f}s")
```

#### Modèles et performances

| Modèle | Mode | Taille | Vitesse | Précision |
|--------|------|--------|---------|-----------|
| `turbo` | Local | ~758 MB | Très rapide | Très bonne |
| `large` | Local | ~2.87 GB | Lent | Excellente |
| `whisper-1` | API | - | Très rapide | Excellente |

#### Exemples complets

**Transcrire et traduire un audio en français :**

```python
from shared_utils import OpenAISTTCaller

stt = OpenAISTTCaller(model="turbo")
result = stt.transcribe(
    audio_path="interview_fr.mp3",
    language="fr",
    task="transcribe"
)
print(f"Texte : {result['text']}")
print(f"Langue : {result['language']}")
```

**Utiliser l'API avec timestamps au niveau du mot :**

```python
from shared_utils import OpenAISTTCaller

stt = OpenAISTTCaller(use_api=True, api_key="votre-clé-api")
result = stt.transcribe(
    audio_path="audio.mp3",
    model="whisper-1",
    response_format="verbose_json",
    timestamp_granularities=["word", "segment"]
)

# Afficher le timing mot par mot
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s] {segment['text']}")
```

**Traiter plusieurs audios et calculer le coût total :**

```python
from shared_utils import OpenAISTTCaller, PricingCalculator
from pathlib import Path

stt = OpenAISTTCaller(use_api=True, api_key="votre-clé-api")
calculator = PricingCalculator()

audio_files = list(Path("audios/").glob("*.mp3"))
total_cost = calculator.get_price_for_stt("whisper-1", 0)  # Initialiser à 0

for audio_file in audio_files:
    result = stt.transcribe(audio_file, model="whisper-1")
    duration = result["usage"]["seconds"]
    cost = calculator.get_price_for_stt("whisper-1", duration)
    total_cost += cost

total_cost.print_price()  # Affiche le coût total avec la moyenne par appel
```

## Contribution

Les contributions sont les bienvenues ! Veuillez soumettre une issue ou une pull request pour toute amélioration ou correction de bug.

## A faire

- [ ] tester les tools openaiLLM