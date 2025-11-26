# Migration de Données CSV vers MongoDB

## Vue d'ensemble

Ce projet permet de migrer des données de santé depuis un fichier CSV vers une base de données MongoDB avec transformation, normalisation et gestion des rôles utilisateurs.

## Architecture du Projet

```
P5/
├── script/
│   ├── migrate_csv_to_mongodb.py  # Script principal de migration
│   └── roles.py                   # Gestion des rôles MongoDB
├── data/
│   └── healthcare_dataset.csv     # Fichier source CSV
├── docker-compose.yml             # Orchestration des services
├── Dockerfile                     # Image pour le script de migration
├── requirements.txt               # Dépendances Python
└── .env                          # Variables d'environnement
```

## Prérequis

- Docker et Docker Compose installés
- Fichier `.env` configuré avec les variables suivantes :

```env
MONGO_USER=votre_utilisateur
MONGO_PASS=votre_mot_de_passe
MONGO_DB_NAME=nom_de_la_base
```

## Comment Effectuer la Migration

### 1. Préparation

Assurez-vous que le fichier CSV source se trouve dans `data/healthcare_dataset.csv`

### 2. Lancement de la Migration

```bash
docker-compose up
```

Cette commande va :
- Démarrer un conteneur MongoDB (version 6)
- Construire l'image Docker du script de migration
- Exécuter automatiquement la migration

### 3. Vérification

Le script affichera le nombre de documents insérés :
```
{X} documents insérés avec succès !
```

## Ce Qui Se Passe Pendant la Migration

### Étape 1 : Démarrage de MongoDB ([docker-compose.yml](docker-compose.yml):1-14)

- **Service** : `mongo`
- **Image** : MongoDB version 6
- **Port** : 27017 exposé
- **Authentification** : Créée avec les identifiants du `.env`
- **Persistance** : Volume `mongo_data` pour conserver les données

### Étape 2 : Construction du Conteneur de Migration ([Dockerfile](Dockerfile))

- **Image de base** : Python 3.12 slim
- **Installation** : Dépendances Python (pandas, pymongo, python-dotenv)
- **Copie** : Tous les fichiers du projet dans `/app`

### Étape 3 : Création des Rôles ([script/roles.py](script/roles.py))

Six rôles MongoDB sont créés avec des privilèges différents :

| Rôle | Privilèges | Description |
|------|-----------|-------------|
| **DataModifier** | find, insert, update, remove | Gestion complète des données |
| **StructureGestion** | find, createCollection, createIndex, dropIndex | Gestion de la structure de la base |
| **UsersAdmin** | createUser, dropUser, grantRole, revokeRole | Administration des utilisateurs |
| **Gestionnaire** | find, insert, update | Lecture et modification sans suppression |
| **Utilisateur** | find | Lecture seule |
| **Consultant** | aucun | Rôle sans privilèges |

### Étape 4 : Transformation des Données ([script/migrate_csv_to_mongodb.py](script/migrate_csv_to_mongodb.py):49-57)

#### 4.1 Nettoyage

- **Noms** : Conversion en Title Case (Première Lettre En Majuscule)
- **Dates** : Conversion en format DateTime (`Date of Admission`, `Discharge Date`)
- **Montants** : Conversion en `Decimal128` pour préserver la précision

#### 4.2 Mapping Énuméré

Les valeurs textuelles sont converties en codes numériques :

**Genre** : `Male` → 1, `Female` → 2

**Groupe Sanguin** : `A+` → 1, `A-` → 2, `B+` → 3, `B-` → 4, `O+` → 5, `O-` → 6, `AB+` → 7, `AB-` → 8

**Condition Médicale** : `Cancer` → 1, `Diabetes` → 2, `Obesity` → 3, `Asthma` → 4, `Hypertension` → 5, `Healthy` → 6

**Assurance** : `Blue Cross` → 1, `Aetna` → 2, `Medicare` → 3, `Medicaid` → 4, `Cigna` → 5

**Type d'Admission** : `Urgent` → 1, `Emergency` → 2, `Elective` → 3

**Médicament** : `Paracetamol` → 1, `Ibuprofen` → 2, `Aspirin` → 3, `Penicillin` → 4, `Insulin` → 5

**Résultats Tests** : `Normal` → 1, `Abnormal` → 2, `Inconclusive` → 3

### Étape 5 : Structuration des Documents ([script/migrate_csv_to_mongodb.py](script/migrate_csv_to_mongodb.py):59-97)

Chaque ligne CSV devient un document MongoDB structuré :

```javascript
{
  "patient": {
    "name": {
      "first": "John",
      "last": "Doe"
    },
    "age": 45,
    "gender": 1,               // Code numérique
    "bloodType": 1,            // Code numérique
    "condition": 2,            // Code numérique
    "insurance": {
      "provider": 3            // Code numérique
    }
  },
  "encounter": {
    "admissionDate": ISODate("2024-01-15T00:00:00Z"),
    "dischargeDate": ISODate("2024-01-20T00:00:00Z"),
    "admissionType": 1,        // Code numérique
    "room": 305,
    "medication": 4,           // Code numérique
    "testResults": 1,          // Code numérique
    "doctor": {
      "id": "uuid-unique",     // UUID généré
      "name": "Dr. Smith"
    },
    "hospital": {
      "id": "uuid-unique",     // UUID généré
      "name": "City Hospital"
    },
    "billingAmount": Decimal128("15000.50")
  }
}
```

#### Gestion des Références

- **Docteurs et Hôpitaux** : Attribution d'UUID uniques via un système de cache
- **Même docteur/hôpital** = même UUID dans tous les documents
- Évite la duplication et permet les relations

### Étape 6 : Création des Index ([script/migrate_csv_to_mongodb.py](script/migrate_csv_to_mongodb.py):42-47)

Quatre index sont créés pour optimiser les requêtes :

```javascript
db.patients.createIndex({ "patient.name.last": 1 })      // Recherche par nom
db.patients.createIndex({ "encounter.admissionDate": 1 }) // Recherche par date
db.patients.createIndex({ "encounter.hospital.id": 1 })   // Recherche par hôpital
db.patients.createIndex({ "encounter.doctor.id": 1 })     // Recherche par docteur
```

### Étape 7 : Insertion en Base ([script/migrate_csv_to_mongodb.py](script/migrate_csv_to_mongodb.py):112)

- **Méthode** : `insert_many()` en mode non-ordonné
- **Avantage** : Continue l'insertion même si un document échoue
- **Performance** : Insertion en lot (plus rapide que document par document)

## Variables d'Environnement

Le fichier [.env](.env) doit contenir :

```env
# Connexion MongoDB
MONGO_USER=admin
MONGO_PASS=password123
MONGO_DB_NAME=healthcare_db

# Configuration automatique (ne pas modifier)
MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASS}@mongo:27017/?authSource=admin
COLLECTION_NAME=patients
```

## Vérification Post-Migration

### Connexion à MongoDB

```bash
docker exec -it mongo mongosh -u admin -p password123
```

### Commandes de Vérification

```javascript
// Utiliser la base de données
use healthcare_db

// Compter les documents
db.patients.countDocuments()

// Afficher un exemple de document
db.patients.findOne()

// Vérifier les index
db.patients.getIndexes()

// Lister les rôles créés
db.getRoles()
```

## Arrêt et Nettoyage

```bash
# Arrêter les conteneurs
docker-compose down

# Supprimer également les volumes (ATTENTION : perte de données)
docker-compose down -v
```

## Résolution de Problèmes

### Le script ne démarre pas
- Vérifiez que le fichier `.env` existe et est correctement configuré
- Vérifiez que `data/healthcare_dataset.csv` existe

### Erreurs d'insertion
- Vérifiez le format du CSV (colonnes requises)
- Consultez les logs : `docker-compose logs migrate`

### Connexion MongoDB échoue
- Attendez quelques secondes que MongoDB démarre complètement
- Le script `migrate` a `depends_on: mongo` mais MongoDB peut mettre du temps à être prêt

## Structure de la Base de Données Finale

```
healthcare_db
└── patients (collection)
    ├── Documents avec structure patient/encounter
    └── Index sur :
        ├── patient.name.last
        ├── encounter.admissionDate
        ├── encounter.hospital.id
        └── encounter.doctor.id
```

## Technologies Utilisées

- **Python 3.12** : Langage de script
- **Pandas** : Manipulation de données CSV
- **PyMongo** : Driver MongoDB pour Python
- **MongoDB 6** : Base de données NoSQL
- **Docker** : Conteneurisation
- **Docker Compose** : Orchestration multi-conteneurs
