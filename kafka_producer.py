import json
import time
import random
from kafka import KafkaProducer
from scrapers.ecommerce_scraper import EcommerceScraper

def run_kafka_producer():
    # Connexion à Kafka (le serveur tourne dans Docker sur le port 9092)
    try:
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        print("✅ Connecté à Kafka ! Début de l'envoi des données en temps réel...")
    except Exception as e:
        print(f"❌ Erreur de connexion Kafka : {e}")
        return

    scraper = EcommerceScraper()
    topic_name = 'ecommerce_events'

    while True:
        # On simule le scraping d'un produit à la fois
        product = scraper.scrape_jumia_deals()[0] # On prend un produit au hasard
        
        # Envoi dans le topic Kafka
        producer.send(topic_name, value=product)
        print(f"📡 [PRODUCER] Produit envoyé : {product['name']} | Prix: {product['current_price']} MAD")
        
        # On attend 3 secondes avant d'envoyer le prochain (simulation de flux continu)
        time.sleep(3)

if __name__ == "__main__":
    run_kafka_producer()
