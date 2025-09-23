## Schéma de base de données — Vue d'ensemble

Cette documentation présente l'architecture de données utilisée par World Embalage, les entités principales, ainsi que les considérations de connexion et de migration.

### 1) Technologies

- ORM: SQLAlchemy 2.x
- Migrations: Alembic
- SGBD: SQLite (défaut) ou MySQL/MariaDB (recommandé en production)

### 2) Connexion et configuration

- Le DSN est construit depuis les variables d'environnement (via `.env`) dans `src/config/settings.py` et `src/config/database.py`.
- En absence de configuration valide MySQL, l'application bascule sur SQLite (fichier local `world_embalage_dev.db`).
- Les sessions SQLAlchemy sont gérées de manière scoped pour l'UI.

### 3) Entités principales (logique métier)

Remarque: Les noms exacts des classes peuvent varier selon les modules (`src/models/`). Voici les concepts clés généralement présents:

- Fournisseur (Supplier)

  - Coordonnées, activité, statut
  - Relations: Commandes Fournisseurs (Raw Material Orders)

- Client

  - Coordonnées, informations business/activité
  - Relations: Devis, Commandes Clients, Factures

- Devis (Quotation)

  - Référence normalisée `DEV-...`, client, lignes, totaux, conditions
  - Peut être converti en Commande Client

- Commande Client (Sales Order)

  - Référence `CMD-...`, lien client, lignes, statut
  - Relations: Lots de Production, Livraisons, Factures

- Commande Fournisseur MP (Supplier Order)

  - Référence `BC-...`, lien fournisseur, spécifications MP, dates
  - Suivi de statut (en cours, partiel, terminé)

- Réception (Reception / Inbound)

  - Lien Commande Fournisseur, quantités reçues, emplacement
  - Gestion des livraisons partielles

- Lot de Production (Production Batch)

  - Lien Commande Client, code lot, étapes (Découpe/Impression → Collage/Éclipsage → Terminé)
  - Quantités produites, rebuts

- Mouvement de Stock (Stock Movement)

  - Mouvement entrée/sortie, emplacement, justification

- Facture (Invoice)
  - Référence `FAC-...`, client, lignes, totaux, paiement

### 4) Relations typiques

- Client 1—N Devis, 1—N Commandes, 1—N Factures
- Fournisseur 1—N Commandes Fournisseurs
- Commande Client 1—N Lots de Production
- Commande Fournisseur 1—N Réceptions (partielles possibles)

### 5) Migrations Alembic

- Les scripts Alembic se trouvent dans `alembic/versions/`.
- Ils assurent l'évolution du schéma (ajout de colonnes, nouvelles tables, flags, etc.).
- Utilisez Alembic pour mettre à niveau une base existante en production.

### 6) Performance et intégrité

- Clés étrangères et index sont configurés selon les relations pour la cohérence et la rapidité d'accès.
- Certaines colonnes peuvent être de type chaîne (ex: quantités sous forme texte dans certaines révisions), se référer aux migrations correspondantes.

### 7) Références unifiées

- Les références utilisées dans l'application suivent une norme: `PREFIX-YYYYMMDD-HHMMSS-NNNN[-SUFFIX]`.
- Voir `REFERENCE_UNIFICATION.md` pour les détails et l'implémentation.

### 8) Bonnes pratiques DBA

- Sauvegardez régulièrement la base (SQLite: fichier DB, MySQL: dump régulier).
- En production, préférez MySQL/MariaDB pour la concurrence et la robustesse.
- Tenez à jour les migrations Alembic lors des mises à jour applicatives.
