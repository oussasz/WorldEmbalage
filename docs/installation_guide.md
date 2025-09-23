## Guide d'installation et de déploiement

Ce guide décrit l'installation de l'application World Embalage sur Windows et Linux, ainsi que la configuration, le lancement et le packaging optionnel en exécutable.

### 1) Prérequis

- Python 3.11 ou 3.12 recommandé
- Accès internet pour installer les dépendances Python
- Facultatif (Base de données) : MySQL/MariaDB si vous n'utilisez pas SQLite
- Facultatif (Windows) : PowerShell et autorisations pour exécuter des scripts

Dépendances Python (déjà listées dans `requirements.txt`) :

- PyQt6, SQLAlchemy, PyMySQL, python-dotenv, reportlab, PyPDF2, Pillow, python-dateutil, alembic, loguru

### 2) Récupération du projet

Placez le dossier du projet sur votre machine, par exemple :

- Windows: `C:\Users\<vous>\World Embalage`
- Linux: `/home/<vous>/World Embalage`

### 3) Configuration de l'environnement virtuel

Sous Linux (Bash) — commandes optionnelles (une par ligne) :

```bash
cd "/home/<vous>/World Embalage"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Sous Windows (PowerShell) — commandes optionnelles (une par ligne) :

```powershell
cd "C:\Users\<vous>\World Embalage"
py -3 -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Astuce VS Code: utilisez la tâche "Setup Environment" fournie pour automatiser ces étapes.

### 4) Configuration de la base de données (.env)

Par défaut, l'application peut fonctionner avec SQLite (fichier local). Vous pouvez définir MySQL via un fichier `.env` à la racine du projet.

Exemple `.env` (MySQL) :

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=world
DB_PASSWORD=secret
DB_NAME=world_embalage
# Optionnel: URL DSN complète si vous préférez remplacer tout
# DATABASE_URL=mysql+pymysql://world:secret@127.0.0.1:3306/world_embalage

# Logs et sorties (créés automatiquement si manquants)
LOG_DIR=logs
REPORTS_DIR=generated_reports
```

Notes:

- Sans `.env` ou si MySQL est indisponible, une base SQLite locale sera utilisée.
- Les dossiers `logs/` et `generated_reports/` sont créés automatiquement au lancement.

### 5) Lancer l'application

Option VS Code:

- Exécuter "Setup and Run World Embalage Application"

Manuellement (Linux) — commandes optionnelles :

```bash
source venv/bin/activate
python src/main.py
```

Manuellement (Windows PowerShell) — commandes optionnelles :

```powershell
./venv/Scripts/Activate.ps1
python src/main.py
```

Au démarrage:

- La fenêtre principale s'ouvre maximisée (tout en conservant les contrôles de fenêtre standards).
- Le Tableau de Bord (Dashboard) est défilable verticalement.

### 6) Packaging (exécutable Windows optionnel)

Un fichier spec PyInstaller est fourni: `packaging/WorldEmbalage.spec`.

Étapes (Windows, PowerShell) — commandes optionnelles :

```powershell
./venv/Scripts/Activate.ps1
pip install pyinstaller
pyinstaller packaging/WorldEmbalage.spec
```

Résultat: `dist/WorldEmbalage/WorldEmbalage.exe`

Le fichier spec inclut:

- `LOGO.jpg`
- Tous les PDF du dossier `template/`

### 7) Dépannage

- Problème PyQt6/Qt platform plugin:

  - Vérifiez que l'environnement virtuel est bien activé et que PyQt6 est installé.
  - Sous Linux, assurez-vous que les bibliothèques système nécessaires à Qt sont présentes.

- Problème MySQL (connexion refusée):

  - Testez les identifiants depuis un client MySQL.
  - Vérifiez le pare-feu et le port `DB_PORT`.
  - À défaut, laissez l'app basculer en SQLite pour démarrer.

- PDF non générés:

  - Validez la présence des modèles dans `template/`.
  - Vérifiez les permissions d'écriture dans `generated_reports/`.

- Logs:
  - Consultez `logs/app.log` pour les messages d'initialisation et erreurs applicatives.

### 8) Mise à jour

Pour mettre à jour les dépendances, relancez l'installation des requirements dans le venv:

```bash
pip install -r requirements.txt
```

Pour modifier les ressources packagées (templates, logo), ajustez si besoin la spec PyInstaller.
