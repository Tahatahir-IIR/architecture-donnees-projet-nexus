import boto3
import os
import json
from botocore.client import Config

def upload_medallion_layers():
    # Configuration de la connexion
    s3 = boto3.client('s3',
                    endpoint_url='http://localhost:9000',
                    aws_access_key_id='admin',
                    aws_secret_access_key='password',
                    config=Config(signature_version='s3v4'),
                    region_name='us-east-1')

    # Liste des couches et fichiers correspondants
    layers = [
        {"bucket": "bronze", "file": "ecommerce_sales.json", "object": "ecommerce/raw_data.json"},
        {"bucket": "silver", "file": "ecommerce_sales.json", "object": "ecommerce/cleaned_data.json"}, # Simulé
        {"bucket": "gold", "file": "gold_analytics.json", "object": "analytics/category_reports.json"}
    ]

    for layer in layers:
        bucket = layer["bucket"]
        file_path = layer["file"]
        object_name = layer["object"]

        if not os.path.exists(file_path):
            print(f"⚠️ Saut de {bucket} : {file_path} n'existe pas encore.")
            continue

        try:
            # Créer le bucket s'il n'existe pas
            try:
                s3.head_bucket(Bucket=bucket)
            except:
                print(f"📦 Création du bucket '{bucket}'...")
                s3.create_bucket(Bucket=bucket)
            
            s3.upload_file(file_path, bucket, object_name)
            print(f"✅ Succès : {file_path} envoyé dans {bucket}/{object_name}")
        except Exception as e:
            print(f"❌ Erreur pour {bucket}: {e}")

if __name__ == "__main__":
    upload_medallion_layers()
