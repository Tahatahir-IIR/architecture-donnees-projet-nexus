import subprocess
import time
import sys
import os

def run_project():
    print("🚀 Démarrage de la synchronisation totale du pipeline Big Data...")
    
    # 1. Scraping des données (Batch)
    print("\n--- ÉTAPE 1 : Scraping (Jumia/MarjaneMall) ---")
    subprocess.run(["python", "scrapers/ecommerce_scraper.py"])
    
    # 2. Upload vers le Data Lake (MinIO)
    print("\n--- ÉTAPE 2 : Stockage Medallion (MinIO) ---")
    subprocess.run(["python", "upload_medallion.py"])
    
    # 3. Transformation ETL (Spark/Pandas)
    print("\n--- ÉTAPE 3 : Transformation & Analytics (Postgres) ---")
    subprocess.run(["python", "spark_jobs/simple_etl.py"])
    
    # 4. Lancement du Streaming & Dashboard
    print("\n--- ÉTAPE 4 : Lancement du Temps Réel (Kafka & Streamlit) ---")
    
    # Ouvrir le Consumer Kafka dans un nouveau terminal
    print("📡 Lancement du Consommateur Kafka...")
    subprocess.Popen(["start", "cmd", "/k", "python", "kafka_consumer.py"], shell=True)
    
    # Ouvrir le Producer Kafka dans un nouveau terminal
    print("📡 Lancement du Producteur Kafka...")
    subprocess.Popen(["start", "cmd", "/k", "python", "kafka_producer.py"], shell=True)
    
    # Lancer le Dashboard Streamlit
    print("📊 Lancement du Dashboard Senior...")
    try:
        subprocess.Popen(["python", "-m", "streamlit", "run", "dashboard/ecommerce_app_v_senior.py"])
    except Exception as e:
        print(f"⚠️ Erreur lors du lancement de Streamlit : {e}")

    print("\n✅ TOUT EST SYNCHRONISÉ !")
    print("1. Regardez les fenêtres noires qui se sont ouvertes pour Kafka.")
    print("2. Votre navigateur va s'ouvrir sur le Dashboard.")
    print("3. Les données sont à jour dans Postgres et MinIO.")

if __name__ == "__main__":
    run_project()
