## Documentation API (Vue Développeur)

Cette documentation décrit les points d'extension et les services applicatifs destinés aux développeurs souhaitant intégrer ou étendre World Embalage. L'application est une app de bureau PyQt6; l'API est principalement interne (services Python et modèles ORM).

### 1) Architecture

- UI: `src/ui/` (PyQt6)
- Services métier: `src/services/`
- Modèles: `src/models/` (SQLAlchemy)
- Génération PDF: `src/services/pdf_form_filler.py` et `src/reports/`
- Config & DB: `src/config/`

### 2) Modèles (ORM SQLAlchemy)

Les modèles se trouvent dans `src/models/` (ex. `clients.py`, `orders.py`, `documents.py`). Ils définissent:

- Entités (Client, Fournisseur, Devis, Commande, Lot, etc.)
- Relations et clés étrangères
- Types de colonnes et indices

Utilisation type:

```python
from src.config.database import SessionLocal
from src.models.clients import Client

with SessionLocal() as session:
	clients = session.query(Client).all()
```

### 3) Services

#### 3.1 Génération de PDF

`src/services/pdf_form_filler.py` — remplit ou superpose des données sur des modèles PDF. Exemples de fonctions typiques:

- Génération devis (DEV)
- Bon de commande fournisseur (BC)
- Fiche produit fini (FPF)
- Étiquette matière première (MP)
- Facture (FAC)

Entrées (contrat simplifié):

- Données métier (client, lignes, totaux, références)
- Chemin du modèle PDF (depuis `template/`)
  Sorties:
- Fichier PDF dans `generated_reports/`

Erreurs:

- Fichier modèle manquant → exception
- Données invalides → messages dans les logs

#### 3.2 Connexion base de données

`src/config/database.py` construit l'engine SQLAlchemy et expose `SessionLocal`.
Comportement:

- Lecture `.env` via `src/config/settings.py`
- MySQL si disponible; sinon fallback SQLite
- Logs d'initialisation dans `logs/app.log`

#### 3.3 Journalisation

`src/config/logging_config.py` configure Loguru:

- Fichier `logs/app.log` avec rotation
- Formatage lisible, niveaux INFO+ en production

### 4) Génération de références

Le système de références est standardisé: voir `REFERENCE_UNIFICATION.md`.
Utilisation (exemple générique):

```python
from src.utils.reference_generator import ReferenceGenerator
ref = ReferenceGenerator.generate('quotation')  # DEV-...
```

### 5) UI (PyQt6)

L'UI charge les widgets depuis `src/ui/`.
Points clés:

- Démarrage maximisé tout en conservant les contrôles de fenêtre
- Dashboard défilable verticalement
- Sections principales: Commandes MP en cours et Activité récente (côte à côte)

### 6) Extensions et intégrations

- Ajoutez de nouveaux services dans `src/services/` pour votre logique métier.
- Ajoutez de nouveaux modèles/colonnes via Alembic (générer un migration script, appliquer).
- Pour de nouveaux PDF, stockez le modèle dans `template/` et implémentez une fonction dédiée dans le service PDF.

### 7) Gestion des erreurs

- Exceptions métiers: journalisées via Loguru
- Problèmes de connexion DB: fallback SQLite + message dans le log
- PDF/IO: vérifiez droits d'écriture, chemins, existence des templates

### 8) Bonnes pratiques de contribution

- Respecter la structure des modules (config/models/services/ui)
- Ajouter des tests légers pour les services critiques
- Mettre à jour `requirements.txt` si de nouvelles dépendances sont nécessaires
- Migrations Alembic à jour pour tout changement de schéma
