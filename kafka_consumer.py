import json
import time
from kafka import KafkaConsumer
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaConsumer")

def start_consumer():
    """
    Consomme les messages du topic 'ecommerce_events' en temps réel.
    """
    try:
        consumer = KafkaConsumer(
            'ecommerce_events',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='ecommerce-monitoring-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        logger.info("📡 Consommateur Kafka démarré... En attente de nouveaux produits...")

        for message in consumer:
            product = message.value
            
            # Simulation d'un traitement en temps réel
            price = product.get('price', 0)
            name = product.get('name', 'Inconnu')
            source = product.get('source', 'Inconnue')
            
            print(f"\n--- [NOUVEL EVENEMENT REÇU] ---")
            print(f"📦 Produit : {name}")
            print(f"💰 Prix    : {price} DH")
            print(f"🌐 Source  : {source}")
            print(f"-------------------------------")

            # Ici, on pourrait ajouter une alerte prix
            if price < 100:
                print(f"🔥 ALERTE : Prix exceptionnel détecté !")

    except Exception as e:
        logger.error(f"❌ Erreur lors de la consommation : {e}")

if __name__ == "__main__":
    start_consumer()
