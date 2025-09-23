## Manuel Utilisateur — World Embalage

Bienvenue dans l'application de gestion d'atelier de fabrication de cartons. Ce manuel couvre les éléments essentiels pour prendre en main l'outil et exécuter les opérations quotidiennes.

### 1) Démarrage

- Lancez l'application via le raccourci (ou `python src/main.py`).
- La fenêtre principale s'ouvre maximisée, avec les contrôles standards disponibles (minimiser, restaurer, fermer).
- Le Tableau de Bord (Dashboard) présente un résumé avec défilement vertical si nécessaire.

### 2) Navigation

- Barre de menus et/ou onglets selon votre version: accès aux modules clés.
- Sections courantes:
  - Données de Base (Fournisseurs, Clients)
  - Matières Premières (Commandes Fournisseurs, Réceptions)
  - Ventes (Devis, Commandes Clients)
  - Production (Lots de production)
  - Documents (Génération PDF)

Le Dashboard affiche notamment:

- Statistiques synthétiques et activités récentes
- Deux blocs majeurs côte à côte:
  - Commandes MP en cours
  - Activité récente (AR)

Remarques UI:

- Le “Top 10 PF en stock” et la tuile “PF en stock” ont été retirés selon les spécifications actuelles.
- Le contenu du Dashboard peut défiler verticalement.

### 3) Données de base

#### Fournisseurs

- Créez un nouveau fournisseur via le menu correspondant.
- Saisissez les informations de contact, adresse, et activités.

#### Clients

- Ajoutez les clients avec leurs coordonnées et informations business.

### 4) Matières Premières

#### Commandes Fournisseurs (MP)

- Créez un bon de commande fournisseur avec les spécifications de la matière (type, dimensions, quantités).
- Suivez le statut (en cours, partiel, terminé) et les dates.

#### Réceptions

- Enregistrez les livraisons entrantes.
- Gérez les réceptions partielles et l'emplacement de stockage.

### 5) Ventes

#### Devis

- Créez des devis client en sélectionnant le client et les lignes de produit.
- Les références (DEV-YYYYMMDD-HHMMSS-NNNN) sont générées automatiquement.

#### Commandes Clients

- Convertissez un devis en commande confirmée.
- Suivez les statuts jusqu'à la livraison.

### 6) Production

#### Lots de Production

- Créez un lot lié à une commande client.
- Suivez l'avancement par étapes (Découpe/Impression → Collage/Éclipsage → Terminé).
- Consignez les quantités et déchets.

### 7) Documents PDF

- L'application génère des documents (Devis, Bons de Commande, Factures, Fiches PF, Étiquettes MP).
- Les modèles se trouvent dans `template/` et les sorties dans `generated_reports/`.
- Les références suivent une norme unifiée (voir documentation dédiée).

### 8) Recherche et filtres

- Les listes (fournisseurs, clients, commandes, etc.) proposent tri/recherche.
- Utilisez les champs de recherche et les colonnes triables.

### 9) Journalisation et diagnostic

- Les logs sont écrits dans `logs/app.log`.
- En cas de souci (base de données, génération PDF), consultez le log.

### 10) Bonnes pratiques

- Créez d'abord les données de base (fournisseurs/clients) avant les opérations.
- Vérifiez la configuration `.env` si vous utilisez MySQL.
- Sauvegardez régulièrement les fichiers de sortie si importants (PDF, rapports).

### 11) Raccourcis et conseils

- Ctrl+S (si disponible dans les dialogues) pour sauvegarder rapidement.
- Double-clic sur une ligne d'une liste pour ouvrir les détails (selon module).
- Redimensionnez les colonnes si nécessaire; l'application mémorise certains états selon votre version.

### 12) FAQ rapide

- Rien ne s'affiche / Erreur Qt:
  - Vérifiez PyQt6 installé dans le venv et relancez.
- Impossible de se connecter MySQL:
  - Testez les identifiants et laissez l'application basculer en SQLite si besoin.
- PDF non générés:
  - Vérifiez `template/` et les permissions d'écriture de `generated_reports/`.

just a simple software for
