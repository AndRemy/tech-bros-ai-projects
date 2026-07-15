import os
from apify_client import ApifyClient
from dotenv import load_dotenv
import json
import time

load_dotenv()

# Configuración
DISTRITOS = [
    "San Borja", "Santiago de Surco", "La Molina", "San Miguel", 
    "Lince", "Jesus Maria", "Surquillo", "Miraflores", "San Isidro"
]
OPERACIONES = ["alquiler", "venta"]
PROPIEDADES = ["departamentos", "casas"]

def generar_url(distrito, operacion, propiedad):
    distrito_slug = distrito.lower().replace(" ", "-").replace("á", "a").replace("í", "i")
    # Ajuste manual para el caso de 'Jesús María' que suele ser 'jesus-maria'
    if distrito_slug == "jesus-maria":
        distrito_slug = "jesus-maria"
    
    url = f"https://urbania.pe/buscar/{operacion}-de-{propiedad}-en-{distrito_slug}--lima--lima"
    return url

def run_orchestrator():
    token = os.getenv("APIFY_API_TOKEN")
    if not token:
        print("Error: APIFY_API_TOKEN no configurado en .env")
        return

    client = ApifyClient(token)
    actor_id = "sian.agency/urbania-property-scraper"
    
    # Generar lista de tareas
    tareas = []
    for d in DISTRITOS:
        for o in OPERACIONES:
            for p in PROPIEDADES:
                tareas.append({
                    "url": generar_url(d, o, p),
                    "distrito": d,
                    "operacion": o,
                    "propiedad": p
                })
    
    print(f"Total de tareas a ejecutar: {len(tareas)}")
    
    all_results = []
    
    for i, tarea in enumerate(tareas):
        print(f"[{i+1}/{len(tareas)}] Ejecutando: {tarea['operacion']} de {tarea['propiedad']} en {tarea['distrito']}...")
        
        run_input = {
            "startUrls": [{"url": tarea['url']}],
            "limit": 10, # Ajustar según necesidad
        }
        
        try:
            run = client.actor(actor_id).call(run_input=run_input)
            dataset = client.dataset(run.default_dataset_id)
            items = dataset.list_items().items
            
            # Filtrar desarrollos
            filtered = [item for item in items if item.get("posting_kind") != 'DEVELOPMENT']
            
            # Añadir metadatos
            for item in filtered:
                item['metadata'] = {'distrito': tarea['distrito'], 'operacion': tarea['operacion'], 'propiedad': tarea['propiedad']}
            
            all_results.extend(filtered)
            print(f"   -> Encontrados {len(filtered)} resultados.")
            
            # Evitar saturar el scraper
            time.sleep(2)
            
        except Exception as e:
            print(f"   -> Error en {tarea['url']}: {e}")
            
    # Guardar todo
    with open('resultados_finales.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Proceso completo. Total resultados: {len(all_results)}. Guardado en 'resultados_finales.json'.")

if __name__ == '__main__':
    run_orchestrator()
