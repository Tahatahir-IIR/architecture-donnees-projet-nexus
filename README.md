# E-commerce Market Intelligence Data Pipeline

Ce projet est une architecture Big Data complète (pipeline de données de bout en bout) visant à collecter, transformer, stocker et visualiser en temps réel les données issues du e-commerce (Jumia et MarjaneMall).

## Architecture du Projet

L'architecture est construite autour du concept **Medallion (Bronze / Silver / Gold)** et utilise les technologies suivantes :
- **Scraping** : Python (BeautifulSoup) pour l'extraction des données.
- **Message Broker (Temps Réel)** : Kafka pour le streaming des données.
- **Data Lake** : MinIO pour le stockage des couches Bronze (raw), Silver (cleansed) et Gold (analytics).
- **Data Warehouse** : PostgreSQL pour la manipulation relationnelle, administré via pgAdmin.
- **ETL** : Pandas / PySpark pour le traitement et les agrégations.
- **Dashboarding** : Streamlit & Plotly pour une interface exécutive d'aide à la décision.
- **Conteneurisation** : Docker & Docker Compose pour le déploiement local (MinIO, Postgres, Kafka, Zookeeper).

## Comment exécuter le projet ?

### 1. Prérequis
- Docker et Docker Compose installés.
- Dépendances Python installées.

### 2. Démarrer l'infrastructure
\\\ash
docker-compose up -d
\\\`n
### 3. Lancer le Pipeline Total
Exécutez l'orchestrateur qui s'occupe du Scraping, de l'ETL, de Kafka et qui ouvre l'interface automatiquement :
\\\ash
python run_full_pipeline.py
\\\`n
## Interfaces Accessibles
Une fois le projet lancé, vous pouvez accéder à :
- **Dashboard Streamlit** : [http://localhost:8501](http://localhost:8501)
- **MinIO Console (Data Lake)** : [http://localhost:9001](http://localhost:9001) (admin / password)
- **pgAdmin (Data Warehouse)** : [http://localhost:5050](http://localhost:5050) (admin@admin.com / admin)
# architecture-donnees-projet-nexus
