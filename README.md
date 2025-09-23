# World Embalage - Gestion d'Atelier de Fabrication de Cartons

## Aperçu

Une application de bureau complète pour gérer les opérations d'un atelier de fabrication de cartons, construite avec PyQt6 et SQLAlchemy.

## Fonctionnalités Implémentées

### ✅ Fonctionnalités Principales

- **Gestion des Données de Base**: Fournisseurs et Clients avec détails de contact
- **Gestion des Matières Premières**: Commandes fournisseurs avec spécifications matériaux
- **Traitement des Commandes Clients**: Devis et suivi des commandes
- **Gestion de la Production**: Création et suivi des lots de production
- **Réception des Matières**: Gestion d'inventaire avec emplacements de stockage
- **Génération de Documents**: Modèles PDF pour documents commerciaux

### 🎯 Flux de Travail Métier

#### 1. Gestion des Matières Premières

- **Commandes Fournisseurs**: Créer des bons de commande avec spécifications matériaux

  - Système de numérotation des références
  - Type de matériau, dimensions, quantités
  - Dates de livraison prévues
  - Suivi du statut des commandes

- **Réception des Matières**: Suivre les livraisons de matériaux entrants
  - Lien vers les commandes fournisseurs
  - Quantités reçues et emplacements de stockage
  - Gestion des livraisons partielles

#### 2. Traitement des Commandes Clients

- **Devis**: Générer des devis clients

  - Sélection client et spécifications produit
  - Tarification et conditions de livraison
  - Conversion en commandes confirmées

- **Gestion des Commandes**: Suivre les commandes du devis à la livraison
  - Progression du statut des commandes
  - Planification de production
  - Suivi des livraisons

#### 3. Contrôle de Production

- **Lots de Production**: Créer et suivre les lots de production
  - Lien vers les commandes clients
  - Génération de codes de lot
  - Suivi des étapes de production (Découpe/Impression → Collage/Éclipsage → Terminé)
  - Suivi des quantités et déchets

#### 4. Génération de Documents

- Modèles PDF pour:
  - Bons de Commande
  - Devis
  - Bons de Livraison
  - Factures
  - Étiquettes

## Architecture Technique

### Schéma de Base de Données

- **SQLAlchemy 2.0** ORM avec support SQLite/MySQL
- **Modèles**: Fournisseurs, Clients, Commandes, Production, Mouvements de Stock
- **Alembic** migrations pour versioning du schéma
- **Relations**: Contraintes de clés étrangères et cascades appropriées

### Interface Utilisateur

- **PyQt6** application de bureau
- **Interface à Onglets**: Organisée par fonction métier
- **Boîtes de Dialogue Modales**: Saisie de données basée sur formulaire
- **Grilles de Données**: Vues de données triables et filtrables

### Couche Services

- **Service Documents**: Génération PDF avec ReportLab
- **Service Commandes**: Logique métier pour traitement des commandes
- **Service Production**: Gestion du flux de travail de fabrication
- **Service Matériaux**: Contrôle d'inventaire et de stock

## Installation et Configuration

### Prérequis

- Python 3.11+
- Support d'environnement virtuel

### Démarrage Rapide

1. Exécuter la tâche VS Code "Setup Environment" (crée un venv et installe les dépendances)
2. Lancer la tâche "Setup and Run World Embalage Application" (ou exécuter `python src/main.py`)

### Installation Manuelle

```bash
cd "/home/oussasz/World Embalage"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Windows (PowerShell)

```powershell
cd "C:\path\to\World Embalage"
py -3 -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
python src/main.py
```

## Structure de l'Application

```
src/
├── main.py                 # Point d'entrée de l'application
├── config/                 # Gestion de la configuration
│   ├── database.py        # Connexion base de données
│   ├── settings.py        # Paramètres d'environnement
│   └── logging_config.py  # Configuration logging
├── models/                # Modèles de données SQLAlchemy
│   ├── base.py           # Classes de modèles de base
│   ├── suppliers.py      # Entité Fournisseur
│   ├── clients.py        # Entité Client
│   ├── orders.py         # Entités Commande
│   ├── production.py     # Entités Production
│   └── ...
├── ui/                   # Interface utilisateur PyQt6
│   ├── main_window.py    # Fenêtre principale application
│   ├── dialogs/          # Boîtes de dialogue saisie
│   │   ├── supplier_order_dialog.py
│   │   ├── quotation_dialog.py
│   │   ├── reception_dialog.py
│   │   ├── production_dialog.py
│   │   └── ...
│   └── widgets/          # Composants UI réutilisables
├── services/             # Couche logique métier
├── reports/              # Génération PDF
└── utils/               # Utilitaires d'aide
```

## Guide d'Utilisation

### Pour Commencer

1. **Lancer l'Application**: Utiliser la tâche VS Code ou exécuter `python src/main.py`
2. **Créer les Données de Base**: Ajouter fournisseurs et clients via le menu "Données de Base"
3. **Traiter les Commandes**: Utiliser les menus de flux de travail métier pour les opérations

### Options du Menu Principal

#### Données de Base

- **Nouveau Fournisseur**: Ajouter fournisseur avec détails de contact
- **Nouveau Client**: Ajouter client avec informations de contact

#### Matières Premières

- **Nouveau Bon de Commande**: Créer bons de commande fournisseurs
- **Réception Matières**: Enregistrer livraisons de matériaux

#### Ventes

- **Nouveau Devis**: Créer devis clients

#### Production

- **Nouveau Lot de Production**: Créer lots de production

### Vues de Données

- **Fournisseurs**: Liste fournisseurs avec filtrage
- **Clients**: Liste clients avec recherche
- **Commandes Clients**: Suivi commandes clients
- **Commandes Fournisseurs**: Gestion commandes fournisseurs
- **Production**: Surveillance lots de production

## Configuration

### Configuration Base de Données

- **Par Défaut**: SQLite pour développement (world_embalage_dev.db)
- **Production**: Support MySQL avec variables d'environnement
- **Environnement**: Utiliser fichier `.env` pour identifiants base de données

### Logging

- **Logging Fichier**: logs/app.log avec rotation
- **Sortie Console**: Débogage développement
- **Configuration Niveau**: Niveau INFO pour production

## Statut de Développement

### ✅ Fonctionnalités Terminées

- Structure et architecture du projet
- Modèles de base de données et relations
- UI de base avec interface à onglets
- Gestion données de base (fournisseurs/clients)
- Boîtes de dialogue métier principales
- Intégration système de menus
- Configuration environnement virtuel
- Configuration des tâches
- Tableau de bord moderne avec statistiques en temps réel
- Interface utilisateur traduite en français

## Création d'un exécutable Windows (optionnel)

Méthode rapide avec PyInstaller (GUI, sans console):

```powershell
# Dans PowerShell, après activation du venv
pip install pyinstaller
pyinstaller packaging/WorldEmbalage.spec
```

Le binaire se trouve dans `dist/WorldEmbalage/WorldEmbalage.exe`.

Notes:

- Les templates PDF sont inclus via la spec (`template/`), ainsi que `LOGO.jpg`.
- Les dossiers `logs/` et `generated_reports/` sont créés au runtime si absents.
- Si vous déplacez des ressources, mettez à jour la spec ou conservez les chemins existants.

### 🚧 En Cours / Étapes Suivantes

- Implémentation complète logique métier dans services
- Modèles de documents PDF améliorés
- Recherche et filtrage avancés
- Finalisation flux de travail production
- Fonctionnalités gestion d'inventaire
- Génération de rapports et analytics

### 🎯 Améliorations Futures

- Support multi-utilisateur
- Planification de production avancée
- Intégration portail client
- Application mobile complémentaire
- Analytics avancées et KPIs

## Support et Documentation

- **Guide d'Installation**: `docs/installation_guide.md`
- **Documentation API**: `docs/api_documentation.md`
- **Schéma Base de Données**: `docs/database_schema.md`
- **Manuel Utilisateur**: `docs/user_manual.md`

---

**World Embalage** - Rationaliser les opérations de fabrication de cartons avec la technologie de bureau moderne.
