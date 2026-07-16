# -*- coding: utf-8 -*-
"""
Carga batch de CASAS EN VENTA (Urbania). tipo='casa', operacion='venta'.
precio = precio de venta en S/ (PEN). Deduplicado entre paginas.
Excluye tarjetas "Recomendaciones" (otros distritos).
"""

import sqlite3
import hashlib

DB = "data/real_estate.db"
FECHA = "2026-07-15"

# (zona, precio_S/, hab, ban, area, estac, badge, dir, desc)
DATA = [
    # pagina 1
    ("San Isidro", 7935000, 3, 3, 312, 4, "Area de lavanderia", "Samanez Ocampo", "Lujo esquina, arq. Rodrigo Mazure, ascensor"),
    ("San Borja", 2132000, 5, 3, 380, 4, "Cuartos de servicio", "Jiron Pietro Torrigiano", "3 pisos, 50 anos, cerca Plaza Vea"),
    ("Santiago de Surco", 6192750, 5, 4, 1207, 5, "Gimnasio", "Av. Circunvalacion Club Golf los Incas 400", "Piscina, estilo espanol mediterraneo"),
    ("Santiago de Surco", 1696600, 8, 5, 370, 2, "Piscina", "Jeronimo de Aliaga al 300, Valle Hermoso", "Piscina, frente parque, mini depa"),
    ("Santiago de Surco", 2030610, 3, 3, 310, 2, "Area de lavanderia", "Juan Castilla al 100, Las Gardenias", "Frente parque, mini depa, param 4 pisos"),
    ("San Isidro", 6500000, 4, 4, 662, 4, "Cuartos de servicio", "Agustin de la Torre Gonzales", "Cerca El Olivar, mini depa independiente"),
    ("Santiago de Surco", 3545000, 6, 7, 1014, 8, "Cuartos de servicio", "Calle Palma Real 121, Camacho", "Piscina, bungalow, 6 hab con bano"),
    ("San Isidro", 4590000, 6, 3, 640, 4, "Cuartos de servicio", "Las Palmeras", "Tradicional, param 5 pisos, jardin"),
    ("Santiago de Surco", 7682340, 4, 7, 1361, 10, "Parrilla", "Calle batallones libres de trujillo, Santa Teresa", "Piscina, acabados madera caoba"),
    ("Magdalena", 3310800, 4, 6, 376, 4, "Gimnasio", "Jr. Trujillo", "Mini depa, family room, atelier"),
    ("San Borja", 1880000, 4, 3, 300, 2, "Cuartos de servicio", "Jiron Leonardo da Vinci al 400, San Borja Norte", "Para remodelar, cerca Aviacion"),
    ("San Isidro", 4509000, 4, 4, 604, 2, "Area de lavanderia", "Los Naranjos 200", "Remodelada, 3 pisos, ascensor"),
    ("Santiago de Surco", 1802000, 3, 2, 306, 0, "Jardin", "Av. Las Casuarinas", "A valor de terreno, esquina, param 4 pisos"),
    ("San Borja", 2352000, 5, 4, 358, 0, "Piscina", "Lopez de Ayala, San Borja Sur", "Remodelada, piscina temperada, terraza"),
    ("Santiago de Surco", 7770000, 3, 5, 1250, 4, "Area de lavanderia", "Los Alamos, cerca U. Lima", "Una planta 1000m2, piscina, remodelada"),
    ("San Isidro", 11900000, 4, 5, 750, 3, "Gimnasio", "Calle Paul Harris al 400, Golf", "Frente parque privado, remodelada 2023"),
    ("San Isidro", 18130000, 4, 4, 1280, 12, "Cuartos de servicio", "Calle Valle Riestra 480", "Rubio Arquitectos, piscina, jacuzzi"),
    ("Santiago de Surco", 15525000, 6, 6, 3287, 8, "Area de lavanderia", "Cerro San Francisco 500, Casuarinas", "Mansion, cancha tenis, capilla"),
    ("Santiago de Surco", 1504800, 3, 4, 114, 0, "Cerca a colegios", "Batallon Callao Norte", "Estreno, condominio 7 casas"),
    ("San Isidro", 1980700, 2, 2, 236, 2, "Cuartos de servicio", "Las Moreras al 200", "3 niveles, techos dobles, pasos Golf"),
    ("Santiago de Surco", 2110480, 4, 3, 697, 2, "Area de lavanderia", "Mar Adriatico, Neptuno", "Clasica, cerca Jockey Plaza"),
    ("Santiago de Surco", 2340000, 12, 11, 558, 3, "Cuartos de servicio", "Urb. El Rosal", "Precio terreno, 12 hab, ideal B&B"),
    ("Santiago de Surco", 8344458, 0, 0, 2711, 0, "Piscina", "Jiron Las Poncianas 214, Casuarinas", "Terreno 2711m2, doble frente"),
    ("Santiago de Surco", 5100000, 3, 3, 610, 4, "Area de lavanderia", "Francisco de Cuellar, cerca El Polo", "Remodelada, calle cerrada cul-de-sac"),
    ("Santiago de Surco", 1945320, 6, 7, 300, 3, "Area de lavanderia", "Marginal de la Selva 212, Higuereta", "Casa/terreno, depto independiente, param 5 pisos"),
    ("San Isidro", 2660000, 6, 4, 375, 3, "Area de lavanderia", "Calle 20, Corpac", "Ideal 2 familias, casa secundaria"),
    ("Santiago de Surco", 3315500, 5, 5, 350, 4, "Piscina", "Calle los Centinelas 125, Casuarinas", "Piscina, vista 360, ascensor interno"),
    ("Santiago de Surco", 7030000, 3, 3, 1200, 5, "Jardin", "Las Canteras 1XX, Casuarinas", "Cul de sac, piscina, bar climatizado"),
    ("San Isidro", 2183000, 3, 3, 178, 2, "Gimnasio", "Calle Punta Negra al 400", "Esquina, ascensor, cerca Parque de la Pera"),
    ("San Isidro", 5130000, 4, 4, 610, 5, "Area de lavanderia", "Pasaje Arrospide Loyola, Orrantia", "Condominio, param 5 pisos, cerca Javier Prado"),
    # pagina 2
    ("Santiago de Surco", 1036000, 5, 5, 110, 1, "Area de lavanderia", "Cerro Bello 381, San Ignacio de Loyola", "3 pisos, para rentar habitaciones"),
    ("Santiago de Surco", 8707000, 5, 6, 2000, 6, "Piscina", "Casuarinas al 1200", "Arq. Malacowski, piscina, jardin"),
    ("San Isidro", 4590000, 5, 5, 603, 3, "Cuartos de servicio", "Bernardo Monteagudo, Orrantia del Mar", "490m2, mini depa, param 3 pisos"),
    ("Santiago de Surco", 2193750, 6, 6, 396, 2, "Jardin", "Leon Garcia", "1 piso, ex nido, oportunidad inversion"),
    ("Santiago de Surco", 6212500, 4, 4, 945, 4, "Area de lavanderia", "Eucalipto 179, El Cortijo (El Derby)", "3 niveles, piscina, remodelada"),
    ("Barranco", 2178990, 0, 0, 448, 4, "Guardiania/Seguridad privada", "Ramon Ribeyro al 1000, Tejada Alta", "Limite Miraflores/Surco, acabados caoba"),
    ("San Borja", 1900000, 5, 4, 300, 0, "Cuartos de servicio", "San Borja", "Remodelada, plana, jardin privado"),
    ("San Borja", 2675400, 3, 3, 205, 0, "Jardin", "Av San Borja Norte al 1700", "1 piso, param 8 pisos, cerca Pentagonito"),
    ("Santiago de Surco", 2084850, 4, 3, 205, 2, "Jardin", "Jr. Los Amancaes, Casuarinas Sur", "Piscina, oficina indep, 3 niveles"),
    ("Santiago de Surco", 8425000, 4, 4, 3350, 20, "Piscina", "cerro san francisco 800, Casuarinas", "Terreno 3350m2, vista panoramica"),
    ("San Isidro", 3227000, 3, 3, 311, 2, "Area de lavanderia", "Ricardo Rossel, Chacarilla Santa Cruz", "Cerca El Olivar, param 4 pisos"),
    ("Santiago de Surco", 937409, 3, 1, 126, 1, "Area de lavanderia", "Delfos, Sagitario", "Frente parque, patio con parrilla"),
    ("Santiago de Surco", 5121847, 4, 3, 995, 4, "Area de lavanderia", "Batallon Tarma al 400, Chacarilla", "Casa/terreno $1500/m2, piscina"),
    ("Santiago de Surco", 3220000, 4, 4, 685, 2, "Jardin", "Miguel Angel Buonarrotti, Los Alamos de Monterrico", "Piscina, salida a parque privado"),
    ("San Borja", 2040000, 5, 5, 300, 0, "Parrilla", "Estacion San Borja Sur, Las Magnolias", "Frente parque, piscina con cascada, jacuzzi"),
    ("Santiago de Surco", 2016000, 4, 3, 1200, 2, "Area de lavanderia", "Alameda el Corregidor, La Molina Vieja", "Piscina, 2 pisos"),
    ("Santiago de Surco", 2234400, 4, 5, 450, 2, "Cuartos de servicio", "Las Begonias 200, La Molina Vieja II", "Terraza y jardin, 2 niveles"),
    ("Santiago de Surco", 867000, 5, 4, 201, 1, "Vista exterior", "Salvador Dali", "4 pisos, depto independiente"),
    ("San Isidro", 2312000, 4, 4, 339, 0, "Cuartos de servicio", "Calle Paul de Beaudiez al 500", "Condominio 4 viviendas, param jacuzzi"),
    ("Santiago de Surco", 9767665, 6, 6, 1198, 9, "Guardiania/Seguridad privada", "Cerros de san francisco, Casuarinas", "Condominio, casa de huespedes 3 dorm"),
    # pagina 3
    ("San Isidro", 5270000, 3, 3, 360, 3, "Area de lavanderia", "Psje. Aromito, El Olivar", "Moderna, espejo de agua, jardin vertical"),
    ("Santiago de Surco", 1800000, 6, 4, 300, 4, "Cuartos de servicio", "Francisco Lanata al 100", "Casa como terreno, frente parque, cerca tren"),
    ("Santiago de Surco", 4439630, 5, 4, 618, 2, "Jardin", "C. San Camilo, Lima Polo Hunt", "Calle privada 4 casas, jardin, arboles frutales"),
    ("Santiago de Surco", 1674330, 5, 4, 312, 2, "Cuartos de servicio", "Morales Duarez 101, Chacarilla", "Remodelada, cerca Pentagonito"),
    ("Santiago de Surco", 12132000, 6, 9, 3000, 15, "Cuartos de servicio", "Jiron Cerro San Francisco 1, Casuarinas", "800m2 AC, piscina, 2 saunas"),
    ("San Borja", 1650000, 5, 3, 312, 2, "Area de lavanderia", "Chacarilla del Estanque, cerca Primavera", "Remodelada, cerca UPC/ESAN/Jockey"),
    ("San Isidro", 5780000, 7, 5, 650, 0, "Piscina", "Country Club, zona embajadas", "Piscina, depto independiente, jacuzzi"),
    ("San Miguel", 828500, 6, 5, 140, 0, "Seguridad", "Bahia de Salinas", "3 pisos, urb cerrada seguridad 24h"),
    ("San Borja", 2859000, 5, 4, 357, 0, "Area de lavanderia", "Calle Andalucia 180, Chacarilla", "Para remodelar, frente Pentagonito"),
    ("San Isidro", 10931000, 5, 4, 880, 0, "Cuartos de servicio", "Avenida del Parque Norte", "Esquina, frente parque, sucesion"),
    ("Santiago de Surco", 1750000, 4, 2, 271, 2, "Area de lavanderia", "Jr. Pucala, Centro Comercial Monterrico", "Remodelada, azotea, techos altos"),
    ("San Borja", 1774000, 5, 4, 312, 2, "Parrilla", "Av. Buena Vista, Chacarilla del Estanque", "Triplex remodelado, terraza 45m2"),
    ("Santiago de Surco", 1870000, 3, 2, 350, 2, "Piscina", "El Virreynato al 100, Monterrico", "Piscina temperada, calle cerrada"),
    # pagina 4
    ("Santiago de Surco", 32560000, 6, 8, 3100, 10, "Area de lavanderia", "Calle El Cascajal, Casuarinas", "Lujo, 2 anos, ganadora bienal arquitectura"),
    ("Santiago de Surco", 941500, 12, 8, 267, 0, "Bajo de precio", "Don Pompeyo 168, Santa Rosa de Surco", "6 niveles, vivienda/negocio/inversion"),
    ("San Borja", 1977800, 7, 7, 231, 0, "Area de lavanderia", "Jr. Fray Luis de Leon", "Remodelada 2016, 3 minidepas"),
    ("San Miguel", 1250600, 4, 2, 215, 1, "Jardin", "Calle Putumayo", "3 pisos, cerca Catolica y Plaza San Miguel"),
    ("Santiago de Surco", 1954600, 4, 3, 339, 0, "Jardin", "Urbanizacion Chama", "Casa/terreno, param 4 pisos"),
    ("Surquillo", 1069500, 4, 4, 210, 1, "Jardin", "Los Halcones 275, Limatambo", "Remodelada, salida parque, param 3er piso"),
    ("San Isidro", 11781000, 0, 0, 1000, 4, "Comercial", "Av. Jorge Basadre al 300", "Casa multifamiliar/comercial, 990m2"),
    ("San Miguel", 1616000, 8, 0, 365, 1, "Area de lavanderia", "Jr. Maria Jose de Arce, Maranga", "Vivienda/proyecto, gas natural"),
    ("Santiago de Surco", 774400, 3, 1, 144, 0, "Area de lavanderia", "Alameda Toribio Rodriguez de Mendoza, Los Precursores", "Conjunto habitacional, 2 pisos"),
    ("Santiago de Surco", 1900000, 4, 3, 300, 2, "Cuartos de servicio", "Jiron Aracena al 200, Higuereta", "Jardin, techos altos, param 4 pisos"),
    ("Lince", 605020, 4, 3, 132, 0, "Area de lavanderia", "Jr. Sinchi Roca al 2400, Risso", "3 pisos, cerca Parque Ramon Castilla"),
    ("San Borja", 1341606, 4, 2, 250, 2, "Seguridad", "Calle Verrocchio 1", "Casa/oficina, terraza"),
    ("Santiago de Surco", 1552500, 3, 3, 210, 2, "Jardin", "Av Las Nazarenas, Las Gardenias", "2 cocheras, jardin privado"),
    ("Santiago de Surco", 1580480, 6, 3, 295, 2, "Cuartos de servicio", "Diego Aguero al 100, Valle Hermoso", "Jardin interior, cerca Primavera"),
    ("Santiago de Surco", 3213000, 5, 6, 470, 4, "Parrilla", "Calle Tres Marias 300, Los Granados", "Arq. Malachowski, condominio 5 casas, piscina"),
    ("Santiago de Surco", 1750000, 6, 3, 302, 0, "Gimnasio", "Jiron Juan de Rada, Liguria", "3 pisos, azotea 200m2"),
    ("San Miguel", 3060000, 5, 3, 480, 2, "Jardin", "Jr. San Martin", "Terreno RDM, cerca malecon Bertolotto"),
    ("San Borja", 2450000, 4, 3, 400, 2, "Area de lavanderia", "Pietro Marchand, San Borja Sur", "Casa como terreno, param, azotea"),
    ("Santiago de Surco", 2412000, 6, 4, 430, 3, "Cuartos de servicio", "Jiron Galeano, Los Rosales", "Jardines amplios, 2 plantas"),
    ("Santiago de Surco", 1837500, 4, 3, 311, 2, "Jardin", "El Baron 153, Prolongacion Benavides", "4 pisos, terraza parrilla"),
    ("San Isidro", 1628600, 3, 3, 248, 3, "Cuartos de servicio", "Calle Bilbao 3, Orrantia del Mar", "Remodelada, condominio frente parque"),
    ("Santiago de Surco", 1532160, 5, 6, 250, 0, "Cuartos de servicio", "Av. Velasco Astete", "Remodelada, 2 plantas"),
    ("San Isidro", 4304750, 4, 3, 460, 3, "Cuartos de servicio", "Paul Harris, Country Club", "Cerca todo, 2 salas, remodelada"),
    # pagina 5
    ("San Borja", 1932000, 4, 3, 338, 0, "Area de lavanderia", "Amadeo Avogadro", "2 pisos, patio con bar/bbq, cerca Aviacion"),
    ("San Isidro", 2966250, 4, 4, 330, 3, "Gimnasio", "calle 30 corpac", "Frente parque interno, bbq, chimenea"),
    ("San Borja", 1470000, 6, 3, 260, 3, "Cuartos de servicio", "Avenida Geminis", "Remodelada, jardin interior"),
    ("Santiago de Surco", 19720000, 4, 7, 1623, 0, "Piscina", "Casuarinas alta", "Lujo estreno, ascensor, vista panoramica"),
    ("Jesus Maria", 897800, 4, 2, 250, 0, "Cerca a colegios", "Calle Horacio Urtega", "3 pisos, minidepa, cerca Campo de Marte"),
    ("Santiago de Surco", 2120400, 4, 4, 285, 2, "Cuartos de servicio", "Av. Central 1000, Los Alamos de Monterrico", "Piscina, arboles frutales, 2 suites"),
    ("San Isidro", 2244000, 5, 3, 211, 2, "Parrilla", "Andres Reyes, Jardin", "Ideal notaria/oficina, param 5 pisos"),
    ("San Isidro", 4210554, 3, 4, 378, 2, "Jardin", "Calle 54 Corpac", "Remodelada, elevador, techos altos"),
    ("San Miguel", 1368000, 6, 3, 189, 2, "Frente a parque", "Calle Micaela Bastidas 155, Maranga II", "Frente Parque Simon Bolivar, 2 familias"),
    ("San Isidro", 2516000, 4, 3, 357, 4, "Cuartos de servicio", "Los Petirrojos al 400, Corpac", "Casa terreno, 16m frente, param 4 pisos"),
    ("Santiago de Surco", 3383220, 3, 4, 383, 3, "Area de lavanderia", "Casuarinas", "Condominio seguro, piscina, iluminada"),
    ("Santiago de Surco", 1877580, 7, 5, 300, 3, "Area de lavanderia", "Jiron Diego de Aguero 286, Monterrico", "2 casas, familia numerosa"),
    ("San Miguel", 1122000, 7, 5, 220, 0, "Area de lavanderia", "Calle Puerto Viejo 140, Maranga", "2 deptos renta, vivienda/inversion"),
    ("Santiago de Surco", 1641200, 3, 3, 255, 2, "Cuartos de servicio", "A un paso de Chacarilla, Santa Teresa", "Estreno, condominio, ultimas unidades"),
    ("Santiago de Surco", 1612000, 4, 4, 223, 0, "Area de lavanderia", "Loma Ponciana 290", "Esquina, cerca parque Loma Amarilla"),
    ("San Isidro", 3296500, 6, 5, 361, 0, "Cerca a colegios", "Calle Los Naranjos, Orrantia", "Lujo, 2 plantas, remodelada"),
    ("Santiago de Surco", 1015000, 5, 4, 120, 2, "Area de lavanderia", "Calle Ares", "2 pisos + azotea, param 5 pisos"),
    ("San Isidro", 1977800, 4, 3, 285, 0, "Area de lavanderia", "Calle 54 19x, Corpac", "Remodelada, mini depa independiente"),
    ("Santiago de Surco", 1462000, 7, 4, 261, 2, "Cuartos de servicio", "Monte de los Olivos al 100, Prolongacion Benavides", "3 niveles, terraza parrilla"),
    ("Santiago de Surco", 2341920, 8, 7, 217, 2, "Jardin", "via lactea, Haras Tyber", "Comercial, param 10 pisos, depto renta"),
    ("Surquillo", 1035000, 3, 2, 160, 0, "Por remodelar", "Hortencia, Los Sauces", "Por remodelar, cerca Ovalo Higuereta"),
    ("Santiago de Surco", 1746500, 7, 5, 264, 0, "Jardin", "Av. Caminos del Inca", "Licencia negocio, mini depa"),
    ("Santiago de Surco", 2980000, 7, 4, 386, 1, "Cerca a colegios", "Franz Schubert 178, Los Alamos de Monterrico", "Sauna, piscina, cerca UPC"),
    ("Santiago de Surco", 2800000, 5, 5, 270, 6, "Piscina", "Centinelas, Casuarinas", "Remodelada, vista panoramica, desniveles"),
    ("San Isidro", 3128000, 0, 0, 354, 0, "Area de lavanderia", "AV Salaverry al 3700", "Casa como terreno, frente Parque de la Pera"),
    ("San Borja", 2088000, 12, 5, 342, 4, "Frente a parque", "cerca parque de la familia, San Borja", "Casa como terreno, frente parque"),
    ("Santiago de Surco", 1734000, 4, 3, 271, 2, "Cerca a colegios", "Centro Comercial Monterrico", "Semi remodelada, media cuadra parque"),
    ("Santiago de Surco", 10880000, 4, 4, 1870, 6, "Guardiania/Seguridad privada", "Calle las Poncianas, Casuarinas", "Casa de Cristal, piscina, jacuzzi, sauna"),
]


def gen_id(dire, precio, area):
    raw = f"{dire}|{precio}|{area}".lower()
    return "cve_" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def main():
    conn = sqlite3.connect(DB)
    conn.text_factory = str
    cur = conn.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(apartments)")]
    if "tipo" not in cols:
        cur.execute("ALTER TABLE apartments ADD COLUMN tipo TEXT")
        cur.execute("UPDATE apartments SET tipo='departamento' WHERE tipo IS NULL")

    inserted, skipped = 0, 0
    for zona, precio, hab, ban, area, estac, badge, dire, desc in DATA:
        rid = gen_id(dire, precio, area)
        amen = badge + (",Estacionamiento" if estac else "")
        descripcion = f"{dire} - {desc}"
        cur.execute("SELECT 1 FROM apartments WHERE id=?", (rid,))
        if cur.fetchone():
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO apartments
               (id, zona, precio, habitaciones, banos, area_m2, amenities,
                fecha_publicacion, descripcion, url, operacion, tipo)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, zona, float(precio), hab, ban, float(area), amen,
             FECHA, descripcion, "", "venta", "casa"),
        )
        inserted += 1

    conn.commit()

    print("=== CARGA CASA VENTA ===")
    print(f"Listados en batch:  {len(DATA)}")
    print(f"Insertados:         {inserted}")
    print(f"Duplicados (id):    {skipped}")

    total = cur.execute("SELECT COUNT(*) FROM apartments").fetchone()[0]
    print(f"\nTotal en BD: {total}")
    print("Matriz tipo x operacion:")
    for t, o, c in cur.execute(
        "SELECT tipo, operacion, COUNT(*) FROM apartments GROUP BY tipo, operacion ORDER BY tipo, operacion"):
        print(f"  {t:<13} {o:<10} {c}")

    print("\n--- Casa venta por zona ---")
    for z, c, pmin, pmax in cur.execute(
        """SELECT zona, COUNT(*), MIN(precio), MAX(precio)
           FROM apartments WHERE tipo='casa' AND operacion='venta'
           GROUP BY zona ORDER BY COUNT(*) DESC"""):
        print(f"  {z:<20} {c:>3}   S/{pmin:>10,.0f} - S/{pmax:>12,.0f}")

    conn.close()


if __name__ == "__main__":
    main()
