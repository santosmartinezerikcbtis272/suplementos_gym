from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client.suplementos_gym
products = db.products

# Limpiar colección antes de insertar
products.delete_many({})

# Insertar productos de ejemplo
products.insert_many([
    {"name": "Proteína Whey", "price": 25, "description": "Proteína de suero", "image": "whey.jpg"},
    {"name": "Creatina", "price": 15, "description": "Mejora tu fuerza", "image": "creatina.jpg"},
    {"name": "BCAA", "price": 20, "description": "Recuperación muscular", "image": "bcaa.jpg"}
])

print("Productos añadidos a la base de datos.")
