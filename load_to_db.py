import json
import sqlite3
from datetime import datetime

def load_data():
    # Cargar datos extraídos
    with open('resultados_finales.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Conectar a la base de datos local
    # Nota: Ajusta la ruta si es necesario. Basado en tu estructura es ./data/real_estate.db
    conn = sqlite3.connect('./data/real_estate.db')
    cursor = conn.cursor()

    # Asegurar que la tabla existe según el esquema del repo (adaptado a sqlite)
    # Tabla: apartments
    # Columnas: id (TEXT), zona (TEXT), precio (REAL), habitaciones (INTEGER), banos (INTEGER), 
    #           area_m2 (REAL), amenities (TEXT), fecha_publicacion (TEXT), descripcion (TEXT), url (TEXT)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apartments (
            id TEXT PRIMARY KEY,
            zona TEXT,
            precio REAL,
            habitaciones INTEGER,
            banos INTEGER,
            area_m2 REAL,
            amenities TEXT,
            fecha_publicacion TEXT,
            descripcion TEXT,
            url TEXT
        )
    ''')

    count = 0
    for item in data:
        try:
            # Mapeo de Apify -> Esquema Repo
            # Nota: Apify devuelve muchos campos, necesitamos extraer los correctos.
            # Asumiremos valores por defecto si faltan datos en el scraper.
            
            # Ejemplo de mapeo básico
            apartamento = (
                str(item.get("id")),
                item.get("metadata", {}).get("distrito", "Desconocido"),
                float(item.get("price", 0.0)),
                int(item.get("bedrooms", 0) or 0),
                int(item.get("bathrooms", 0) or 0),
                float(item.get("area", 0.0) or 0.0),
                ",".join(item.get("features", [])),
                datetime.now().isoformat(), # Fecha por defecto
                item.get("description", "")[:200],
                item.get("url", "")
            )
            
            cursor.execute('''
                INSERT OR IGNORE INTO apartments 
                (id, zona, precio, habitaciones, banos, area_m2, amenities, fecha_publicacion, descripcion, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', apartamento)
            count += 1
        except Exception as e:
            print(f"Error mapeando ítem: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Se han cargado {count} registros en la base de datos.")

if __name__ == '__main__':
    load_data()
