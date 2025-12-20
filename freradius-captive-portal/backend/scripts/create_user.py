import psycopg2
import os
import sys

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Connexion à la base de données
    conn = psycopg2.connect("postgresql://radius:radiuspass@postgres:5432/radius")
    cursor = conn.cursor()
    
    # Lecture du fichier SQL
    with open("scripts/create_test_user.sql", 'r') as file:
        sql = file.read()
    
    # Exécution des requêtes
    cursor.execute(sql)
    conn.commit()
    
    print("Utilisateurs créés avec succès !")
    
except Exception as e:
    print(f"Erreur lors de la création des utilisateurs: {str(e)}")
    
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
