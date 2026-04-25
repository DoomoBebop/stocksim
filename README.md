# stocksim — backtester d'investissement

Simulateur de stratégies d'investissement basé sur des données historiques réelles (Yahoo Finance). Testez n'importe quelle combinaison d'actifs, de conditions d'achat/vente et de paramètres (levier, type de produit) avant d'investir quoi que ce soit.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat&logo=flask)
![License](https://img.shields.io/badge/license-MIT-green?style=flat)

---

## Fonctionnalités

- **Marchés couverts** : S&P 500, CAC 40, NASDAQ 100, Crypto, ETF
- **Conditions d'achat** : par date fixe ou condition de prix (ex. "acheter si prix < 150 €")
- **Conditions de vente** : par date fixe ou condition de prix (ex. "vendre si prix > 200 €")
- **Produits** : actions, ETF, CFD, options CALL, options PUT (short)
- **Levier** : de ×1 à ×20
- **Résultats détaillés** : P&L, rendement %, valeur finale, sparkline par position
- **Positions multiples** : simulez plusieurs trades en même temps et voyez le bilan global

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend   | Python / Flask |
| Données   | yfinance, Stooq, Binance API, FRED |
| Frontend  | HTML + CSS + Vanilla JS |
| Charts    | Chart.js |

---

## Sources de données

Choisissez la source via le menu déroulant dans l'interface. Une note contextuelle s'affiche pour rappeler le bon format de ticker.

| Source | Gratuit | Couverture | Format ticker |
|--------|---------|------------|---------------|
| **Yahoo Finance** | ✅ | Actions, ETF, crypto, indices — historique illimité | `AAPL`, `BTC-USD`, `MC.PA`, `^GSPC` |
| **Stooq** | ✅ | Actions US, EU, JP | `AAPL.US`, `CDR.PL`, `7203.JP` |
| **Binance API** | ✅ | Crypto uniquement — très fiable | `BTC-USD`, `ETH-USD`, `SOL-USD` |
| **FRED** | ✅ | Données macro — taux, indices éco, inflation | `SP500`, `NASDAQCOM`, `DGS10`, `CPIAUCSL` |

> Google Finance n'a plus d'API publique depuis 2012. Alpha Vantage est gratuit mais limité à 25 calls/jour sans clé API.

---

## Installation

**Prérequis** : Python 3.10+ installé.

```bash
# 1. Cloner le repo
git clone https://github.com/<votre-username>/stocksim.git
cd stocksim

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
python app.py
```

L'application est accessible sur **http://localhost:5000**

---

## Utilisation

### 1. Choisir un actif

- Sélectionnez un **marché** (S&P 500, CAC 40, NASDAQ, Crypto, ETF)
- La liste des actifs disponibles se charge automatiquement
- Le **prix actuel** s'affiche en temps réel à côté du ticker

### 2. Paramétrer la position

| Champ | Description |
|-------|-------------|
| Type de produit | Action, ETF, CFD, Option CALL, Option PUT (short) |
| Levier | Multiplicateur ×1 à ×20. Un levier ×3 triple les gains **et** les pertes. |
| Montant | Capital investi en euros |

### 3. Condition d'achat

- **Par date** : achat au prix de clôture du jour spécifié (ou du prochain jour de bourse)
- **Par condition** : achat dès que le prix franchit le seuil défini

  > Exemple : "acheter si prix descend sous 150 €" → le simulateur parcourt l'historique et trouve la première date où c'est vrai.

### 4. Condition de vente

- **Par date** : vente au prix de clôture du jour spécifié
- **Par condition** : vente dès que le prix franchit le seuil défini

  > Si la condition n'a pas encore été atteinte, la position est marquée **ouverte** avec le prix actuel.

### 5. Lancer la simulation

Cliquez **"simuler tout →"** pour lancer le calcul sur toutes vos positions.

---

## Interprétation des résultats

### Résumé global

| Indicateur | Signification |
|-----------|---------------|
| Investi total | Somme de tous les montants engagés |
| Valeur finale | Valeur actuelle de tout le portefeuille |
| P&L total | Gain ou perte en euros |
| Rendement | Performance totale en % |

### Par position

Chaque carte de résultat affiche :

- **Date et prix d'achat** réels (premier jour de bourse disponible)
- **Date et prix de vente** réels ou situation si toujours ouvert
- **Rendement** avec et sans levier
- **Sparkline** de l'évolution du prix sur la période

### Cas particuliers

| Cas | Explication affichée |
|-----|--------------------|
| Condition d'achat jamais atteinte | "Achat non déclenché — la condition n'a jamais été satisfaite dans l'historique disponible." |
| Position toujours ouverte | Badge **POSITION OUVERTE** avec le prix actuel comme prix de vente théorique |
| Ticker invalide | Message d'erreur précis |

---

## Limitations & avertissements

- **Pas de conseil financier** — outil de simulation uniquement.
- Les données Yahoo Finance peuvent présenter des lacunes sur certains actifs peu liquides.
- Le levier est simulé de façon linéaire — en pratique, les produits à levier (CFD, turbos) ont des mécanismes de margin call et de rollover non simulés ici.
- Les frais de courtage, spreads et impôts ne sont pas inclus.
- L'historique disponible varie selon les actifs (5 ans max via yfinance en mode gratuit).

---

## Structure du projet

```
stocksim/
├── app.py                  # Backend Flask — routes + logique de simulation
├── requirements.txt        # Dépendances Python
├── README.md
├── templates/
│   └── index.html          # Template HTML principal
└── static/
    ├── css/
    │   └── style.css       # Styles (thème terminal dark)
    └── js/
        └── app.js          # Logique frontend — formulaire + rendu résultats
```

---

## Ajouter un marché / des tickers

Dans `app.py`, le dictionnaire `MARKETS` contient tous les marchés et leurs tickers :

```python
MARKETS = {
    "Mon Marché": {
        "index": "^TICKER_INDEX",
        "tickers": [
            ("TICKER", "Nom de l'actif"),
            ...
        ]
    }
}
```

Ajoutez simplement une nouvelle entrée — elle apparaît automatiquement dans le menu déroulant.

---

## Licence

MIT — libre d'utilisation, de modification et de distribution.
