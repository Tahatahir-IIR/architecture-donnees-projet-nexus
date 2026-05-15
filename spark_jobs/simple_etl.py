import json
import pandas as pd
from datetime import datetime
import os

def run_simple_etl():
    print("🚀 Démarrage de l'ETL Simple (Fallback Spark)...")
    
    # 1. BRONZE LAYER (Lecture JSON)
    if not os.path.exists("ecommerce_sales.json"):
        print("❌ Erreur : ecommerce_sales.json introuvable.")
        return
        
    with open("ecommerce_sales.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    print(f"📥 {len(df)} lignes chargées de la couche Bronze.")

    # 2. SILVER LAYER (Nettoyage)
    df_silver = df[df['current_price'] > 0].copy()
    df_silver['is_promotion'] = df_silver['discount_percent'] > 0
    df_silver['processed_at'] = datetime.now().isoformat()
    df_silver = df_silver.drop_duplicates(subset=['product_id'])
    print("✨ Couche Silver créée.")

    # 3. GOLD LAYER (Agrégations)
    df_gold = df_silver.groupby('category').agg(
        total_items=('product_id', 'count'),
        avg_price=('current_price', 'mean'),
        total_discounts=('discount_percent', 'sum')
    ).reset_index()
    
    df_gold['avg_price'] = df_gold['avg_price'].round(2)
    df_gold['total_discounts'] = df_gold['total_discounts'].round(2)
    
    print("🏆 Couche Gold créée (Agrégations) :")
    print(df_gold)

    # 4. EXPORT
    # Sauvegarde locale pour le Dashboard Streamlit
    df_gold.to_json("gold_analytics.json", orient="records", indent=4)
    print("✅ Données sauvegardées dans gold_analytics.json")

if __name__ == "__main__":
    run_simple_etl()
