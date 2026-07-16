# -*- coding: utf-8 -*-
"""
Carga el batch de VENTA (departamentos en venta) pegado desde Urbania.
Distritos: Surco, Lince, Surquillo, Jesus Maria, San Miguel, San Borja,
San Isidro, Barranco, Magdalena.

- precio = precio de venta en S/ (PEN). Deduplicado entre paginas.
- operacion = 'venta'.
- Excluye tarjetas de PROYECTO/DESARROLLO (rangos "desde") y "Recomendaciones".
"""

import sqlite3
import hashlib

DB = "data/real_estate.db"
FECHA = "2026-07-15"

# (zona, precio_S/, hab, ban, area_m2, estac, badge, direccion, desc)
DATA = [
    # --- pagina 1 ---
    ("San Borja", 1324435, 3, 3, 175, 2, "Area de lavanderia", "Calle Venecia, Chacarilla del Estanque", "Frente a parque, piso 3, 2 salas"),
    ("Santiago de Surco", 620000, 4, 3, 134, 1, "Parrilla", "Paseo de la Castellana, Cond. El Mirador", "Duplex moderno, piso 19-20, terraza"),
    ("San Borja", 1307040, 3, 2, 175, 2, "Cuartos de servicio", "Calle Venecia 209 Piso 3, Chacarilla", "Frente parque Venecia, 83m2 aires"),
    ("Santiago de Surco", 2312000, 3, 3, 404, 2, "Gimnasio", "Circunvalacion Golf Los Incas", "Lujo, vista Golf, arq. Fort Brescia"),
    ("San Borja", 880600, 3, 3, 146, 2, "Cerca a colegios", "Paseo del Bosque, Mariscal Ramon Castilla", "2do piso, frente parque, cerca Pentagonito"),
    ("Magdalena", 652000, 2, 2, 64, 1, "Seguridad", "Calle M. Ugarte y Moscoso", "Piso 9, cerca Real Plaza Salaverry"),
    ("Santiago de Surco", 970000, 3, 4, 122, 1, "Area de lavanderia", "Victor Plascencia", "Frente parque, cerca estacion Jorge Chavez"),
    ("Santiago de Surco", 1003000, 3, 3, 167, 2, "Cuartos de servicio", "Jiron Las Laderas 527, Casuarinas", "Piso 4, zona exclusiva Casuarinas"),
    ("Barranco", 495000, 1, 1, 43, 1, "Piscina", "Av. el Sol Oeste 145", "2do piso, cerca Malecon Paul Harris"),
    ("Santiago de Surco", 1276500, 4, 3, 315, 3, "Gimnasio", "Jiron Navarra 410", "Duplex, terraza, cerca Linea 1"),
    ("San Isidro", 2716600, 3, 3, 328, 3, "Seguridad", "Los Cedros", "Flat 328m2, 10 propietarios, cerca Golf"),
    ("Magdalena", 541534, 5, 2, 122, 0, "Area de lavanderia", "Jr. Arica 163", "2do piso + aires, para remodelar"),
    ("Santiago de Surco", 1297450, 3, 3, 234, 2, "Seguridad", "las Casuarinas", "Duplex, cerro San Francisco, tranquera"),
    ("San Borja", 935000, 4, 3, 169, 1, "Guardiania/Seguridad privada", "Calle 9 al 300, Monterrico Norte", "Duplex, cerca Pentagonito, azotea"),
    ("San Isidro", 484400, 1, 1, 45, 0, "Gimnasio", "Av. Javier Prado / Rivera Navarrete", "Piso 13, centro financiero"),
    # --- pagina 2 ---
    ("Santiago de Surco", 715000, 4, 3, 139, 2, "Seguridad", "Cristobal de Peralta Norte, Valle Hermoso", "Piso 1 con patio, remodelado"),
    ("Santiago de Surco", 1905500, 3, 3, 263, 3, "Piscina", "Avenida Cerros de Camacho 1050", "Flat vista Golf Los Inkas, piso 14"),
    ("San Isidro", 2900000, 2, 2, 188, 2, "Gimnasio", "Av. Coronel Portillo 390 Dpto 1702", "Estreno, frente Golf, piso 17"),
    ("San Isidro", 678449, 3, 2, 71, 0, "Piscina", "Calle Las Palmeras al 200", "2 dorm + sala estar, moderno"),
    ("San Isidro", 815000, 2, 3, 120, 2, "Area de lavanderia", "AV. 2 de Mayo, Country Club", "Remato, +2 cocheras+deposito, cerca Golf"),
    ("Barranco", 2581500, 3, 4, 231, 2, "Cuartos de servicio", "Malecon Paul Harris", "Vista frontal al mar, remodelado"),
    ("San Isidro", 595000, 2, 2, 60, 1, "Guardiania/Seguridad privada", "Av. General Salaverry 3590 Dpto 802", "Edificio Aquilaria, vista mar"),
    ("San Miguel", 274000, 1, 1, 37, 1, "Seguridad", "Calle Casas al 100", "Nuevo, frente parque, piso 4"),
    ("San Isidro", 726950, 2, 2, 120, 2, "Gimnasio", "Los Robles al 200", "Piso 13, esquina Javier Prado"),
    ("Santiago de Surco", 672750, 3, 2, 107, 1, "Seguridad", "Chacarilla del Estanque, Pasaje Mercurio Peruano", "2do piso, 10 niveles"),
    ("San Isidro", 2684640, 4, 6, 890, 10, "Guardiania/Seguridad privada", "Calle Los Naranjos al 200, Orrantia", "890m2 total, piscina, terraza, 10 estac"),
    ("Santiago de Surco", 1162000, 3, 2, 171, 2, "Area de lavanderia", "Jacaranda al 400, Valle Hermoso Residencial", "Duplex estreno, no paga alcabala"),
    ("San Isidro", 3420000, 3, 3, 260, 2, "Seguridad", "Av. Pezet", "Piso 10, terraza, vista, cerca Golf"),
    ("San Isidro", 1479450, 3, 2, 135, 2, "Ascensor", "Calle Republica 833, El Olivar", "Una planta, cerca Parque El Olivar"),
    ("Barranco", 682320, 2, 2, 82, 0, "Cerca a colegios", "Jiron 2 de Mayo 150", "Estreno, Barranco Monumental, cerca Central"),
    # --- pagina 3 ---
    ("Santiago de Surco", 1341662, 3, 4, 204, 3, "Cuartos de servicio", "Reynaldo Vivanco al 200, Chacarilla", "204m2, 3 cocheras, 2 depositos, piso 5"),
    ("Surquillo", 481000, 2, 2, 59, 0, "Seguridad", "Surquillo", "Cerca Malecon de la Reserva, excelentes acabados"),
    ("San Borja", 1557500, 3, 3, 185, 3, "Area de lavanderia", "Calle Alameda Picaflores al 200, Chacarilla", "Vista parque, family room, 3 estac"),
    ("San Isidro", 4430000, 4, 4, 302, 2, "Seguridad", "Av. Coronel Portillo 390 Dpto 1301", "Estreno, frente Golf, piso 13"),
    ("San Isidro", 1759720, 2, 2, 164, 1, "Area de lavanderia", "Los Castanos 400, Country Club", "Loft duplex amoblado, arq. Josip Vuscovic"),
    ("Magdalena", 593400, 2, 2, 67, 1, "Area de lavanderia", "Jr. Maria Parado de Bellido al 100, San Felipe", "Ultimo piso, cochera+deposito"),
    ("San Isidro", 9435000, 3, 3, 827, 4, "Parrilla", "Los Cedros 701", "Penthouse lujo, piscina, arq. Mario Lara"),
    ("San Borja", 612000, 3, 3, 104, 2, "Cerca a colegios", "Calle 10, Monterrico", "Piso 1, cerca Pentagonito, 4 pisos"),
    ("Santiago de Surco", 1176500, 2, 2, 150, 2, "Cuartos de servicio", "las laderas, Casuarinas", "Piso 3, 8 deptos, pet friendly"),
    ("Lince", 582585, 2, 2, 64, 0, "Guardiania/Seguridad privada", "Calle Las Margaritas 171", "Boutique 23 deptos, rooftop, preventa"),
    ("Magdalena", 569520, 3, 2, 100, 1, "Cuartos de servicio", "Av. Antonio Miro Quesada", "Ascensor directo, media cuadra Javier Prado"),
    ("Jesus Maria", 431250, 1, 1, 49, 1, "Area de lavanderia", "Av. Olavegoya 1855", "Piso 19, cerca UP y Rebagliati"),
    ("San Borja", 1346400, 4, 3, 324, 2, "Area de lavanderia", "Calle Otto Muller 12x", "1er piso remodelado tipo casa, jardin"),
    ("San Borja", 1088000, 3, 3, 170, 2, "Cerca a colegios", "Chacarilla, 2 cuadras Colegio El Santisimo", "Piso 2, cocheras paralelas, 7 deptos"),
    ("Lince", 768000, 3, 2, 81, 1, "Gimnasio", "Manuel Villavicencio al 1000", "Frente Parque Castilla, semi-nuevo"),
    # --- pagina 4 ---
    ("San Isidro", 2244500, 2, 3, 165, 2, "Parrilla", "Calle Los Libertadores", "Duplex con terraza, cerca centro financiero"),
    ("Santiago de Surco", 893000, 3, 3, 230, 2, "Bajo de precio", "Jiron 9 al 400, Monterrico Chico", "Duplex frente Jockey Plaza, +75m2 aires"),
    ("Santiago de Surco", 849200, 3, 2, 119, 1, "Area de lavanderia", "Avenida Las Nazarenas Piso 4", "Estreno, 5 deptos, ascensor directo"),
    ("Surquillo", 886600, 4, 3, 157, 0, "Guardiania/Seguridad privada", "Calle montesquieu 200, La Calera", "Duplex piso 9, terraza privada"),
    ("San Isidro", 4590000, 4, 4, 333, 4, "Seguridad", "Alfredo Salazar al 600, San Gabriel", "333m2, terrazas, arq. Mario Lara"),
    ("Santiago de Surco", 2216500, 4, 4, 420, 3, "Seguridad", "Cerros de Camacho", "Flat vista Golf, 2 ascensores directos"),
    ("Jesus Maria", 419000, 2, 2, 58, 0, "Piscina", "Av. Brasil 2347", "Cuadra 23, piso 6, areas comunes"),
    ("Lince", 694555, 2, 2, 119, 1, "Area de lavanderia", "Avenida 2 de Mayo 1300", "Remodelado, cerca Country Club"),
    ("Santiago de Surco", 1440000, 3, 2, 197, 2, "Area de lavanderia", "calle monte real 405", "197m2, Chacarilla, 2do piso"),
    ("Santiago de Surco", 335000, 3, 2, 75, 0, "Seguridad", "Calle 6 al 100, Parques de Surco III", "Piso 8, condominio con areas verdes"),
    ("San Borja", 822500, 3, 3, 114, 2, "Area de lavanderia", "Av San Borja Norte 299", "Vista al parque, ascensor directo"),
    ("San Miguel", 429260, 3, 1, 83, 1, "Remodelado", "Grau 265", "Remodelado, 83m2, 1 estacionamiento"),
    ("San Isidro", 1111557, 3, 2, 134, 2, "Piscina", "Av Javier Prado Oeste 1241 Torre B, Los Robles", "Piso 7, 2 cocheras+deposito"),
    ("San Isidro", 2696200, 3, 2, 287, 2, "Frente a parque", "Parque Jose De Acosta", "Garden house estreno, no paga alcabala"),
    # --- pagina 5 ---
    ("Santiago de Surco", 1666000, 3, 3, 217, 1, "Piscina", "Avenida Cerros de Camacho 6, Camacho", "Duplex, vista Golf, diseno premiado"),
    ("San Isidro", 1995460, 4, 3, 188, 3, "Area de lavanderia", "La Pinta 120, El Olivar", "Estreno, a pasos El Olivar, ultima unidad"),
    ("Santiago de Surco", 1050000, 4, 3, 248, 2, "Area de lavanderia", "Av. El Derby 500", "Duplex terraza 88m2, piscina, cine"),
    ("Santiago de Surco", 907400, 5, 4, 202, 2, "Area de lavanderia", "Calle Ocona 1XX", "Duplex + aires, cerca Ovalo Higuereta"),
    ("Lince", 407500, 2, 2, 88, 0, "Guardiania/Seguridad privada", "Risso al 500", "Duplex estreno, zona Risso, terraza"),
    ("San Miguel", 439000, 3, 2, 75, 0, "Area de lavanderia", "Jiron Jose de Sucre 480", "Piso 4, 2 deptos por piso, vista externa"),
    ("Lince", 575000, 2, 2, 70, 1, "Gimnasio", "Jr. Brigadier Pumacahua 2580", "Frente Parque Ramon Castilla, piso 3, amoblado"),
    ("Santiago de Surco", 763000, 1, 1, 104, 2, "Area de lavanderia", "Av. Alejandro Velasco Astete 1153, Chacarilla", "Duplex lujo, terraza, 2 cocheras"),
    ("San Isidro", 1278864, 3, 2, 170, 1, "Area de lavanderia", "Av. Miguel de Cervantes Saavedra 780", "Remodelado, vista Golf, piso 9"),
    ("Surquillo", 526922, 2, 2, 88, 1, "Area de lavanderia", "Calle Las Palomas", "Duplex estreno + aires, limite San Isidro"),
    ("San Isidro", 734850, 2, 2, 62, 0, "Gimnasio", "Calle Amador Merino Reyna", "Estreno, piso 16, balcon, centro empresarial"),
    ("San Isidro", 11557500, 5, 5, 1277, 5, "Gimnasio", "Avenida Aurelio Miro Quesada", "Penthouse 4 niveles, piscina, vista Golf"),
    ("Barranco", 578116, 2, 2, 55, 0, "Frente a parque", "bustamante", "Boutique, cerca museos y mar"),
    ("Santiago de Surco", 2125000, 4, 2, 405, 2, "Frente a parque", "Calle Monte Carlo, Chacarilla", "1er piso, frente parque, piscina"),
    ("San Miguel", 332500, 1, 1, 39, 0, "Gimnasio", "Av. Costanera 2560", "Vista al mar, piso 11, full amenities"),
    # --- pagina 6 ---
    ("San Isidro", 1565200, 5, 5, 294, 2, "Area de lavanderia", "Av. Alberto del Campo, Country Club", "Penthouse piso 15, vista al mar, jacuzzi"),
    ("San Borja", 2120500, 3, 3, 494, 2, "Parrilla", "Jiron Monte Carmelo Cuadra 5", "Duplex penthouse, 3 terrazas, remodelado"),
    ("San Isidro", 14706000, 4, 4, 719, 6, "Piscina", "Avenida General Pezet, San Gabriel", "Flat piso completo lujo, vista Golf, Lutron"),
    ("Santiago de Surco", 1342660, 3, 3, 381, 2, "Area de lavanderia", "LA Conquista al 200, Monterrico", "Duplex, terraza+parrilla, cerca Markham/El Polo"),
    ("Santiago de Surco", 695430, 3, 2, 207, 1, "Area de lavanderia", "Avenida Higuereta 585", "3 dorm + 104m2 aires, 4to piso sin ascensor"),
    ("Lince", 700000, 4, 2, 93, 0, "Area de lavanderia", "Jiron Manco Segundo", "Piso 2 + aires, frente Parque Bomberos"),
    ("San Miguel", 295000, 1, 1, 35, 1, "Guardiania/Seguridad privada", "Calle Los Nazcas Cuadra 1", "Amoblado, Edificio Serie 17, entrega jul 2026"),
    ("Santiago de Surco", 1064700, 3, 4, 223, 1, "Guardiania/Seguridad privada", "Calle Leon 300", "Duplex estreno con jardin, cerca Benavides"),
    ("Santiago de Surco", 634000, 2, 2, 70, 0, "Gimnasio", "Av. Manuel Olguin al 400", "Piso 19, cerca Jockey Plaza y Golf"),
    ("San Borja", 1016600, 3, 3, 135, 2, "Cuartos de servicio", "Av. San Borja Norte 800", "Estreno, piso 2, no paga alcabala"),
    ("San Isidro", 6532500, 5, 5, 1081, 8, "Gimnasio", "Jorge Basadre al 10xx", "Penthouse 1080m2, piscina, terraza, jardines"),
    ("San Borja", 1337000, 3, 2, 158, 2, "Area de lavanderia", "San Borja, frente parque Chacarilla", "Estreno, 2 terrazas, en lanzamiento"),
    ("Santiago de Surco", 883660, 4, 3, 138, 2, "Area de lavanderia", "Jiron Madreselva 210, Valle Hermoso", "Piso 3, La Floresta, ascensor directo"),
    ("Santiago de Surco", 258260, 1, 1, 45, 0, "Guardiania/Seguridad privada", "Calle Combate de Abtao 185, Cruz de Surco", "Piso 11, cerca Nueva Via Expresa Sur"),
    ("Santiago de Surco", 1288000, 3, 3, 200, 2, "Guardiania/Seguridad privada", "Allamanda, La Floresta de Monterrico", "Frente parque cerrado, piso alto"),
    # --- pagina 7 ---
    ("San Borja", 2043500, 3, 3, 310, 2, "Parrilla", "Av. Los Precursores 400, Chacarilla", "Duplex penthouse lujo, boutique 5 deptos"),
    ("Santiago de Surco", 731000, 3, 2, 115, 2, "Seguridad", "Avenida Coronel Reynaldo Vivanco", "Chacarilla, piso 4, 2 cocheras"),
    ("Santiago de Surco", 935000, 3, 3, 175, 3, "Seguridad", "Jiron Las Laderas, Casuarinas", "1er piso con balcon, 3 cocheras"),
    ("San Isidro", 2728000, 4, 3, 448, 2, "Jardin", "Av. Miroquesada", "Triplex, vista panoramica Golf"),
    ("Jesus Maria", 570000, 3, 3, 97, 1, "Bajo de precio", "Av. San Felipe 955", "Flat piso 13, vista interior, silencioso"),
    ("Santiago de Surco", 840000, 2, 2, 128, 1, "Vista exterior", "Jiron Sevilla", "Piso 3, cerca Higuereta, Parque La Coruna"),
    ("San Isidro", 1025000, 2, 2, 103, 2, "Area de lavanderia", "Urb. Orrantia al 100, Plazuela Arrospide", "Flat 1er piso, frente parque, boutique 14 deptos"),
    ("Santiago de Surco", 1295000, 3, 2, 210, 2, "Seguridad", "Jr. Bellavista 304, Casuarinas", "Flat, condominio seguro, jacuzzi"),
    ("San Borja", 1522700, 3, 3, 158, 2, "Guardiania/Seguridad privada", "C. Buen Retiro, Edificio Andalucia", "Estreno, frente parque, terraza+jardin"),
    ("Santiago de Surco", 413000, 3, 2, 81, 0, "Jardin", "Jr. Combate Iquique 200", "Estreno, no paga alcabala, cerca municipalidad"),
    ("San Isidro", 2550000, 4, 3, 298, 2, "Cuartos de servicio", "Av. Aurelio Miroquesada, Golf", "Flat vista Golf, acceso directo ascensor"),
    ("Barranco", 7661400, 4, 6, 787, 4, "Area de lavanderia", "Jiron Batalla de Junin 267", "Penthouse triplex frente al mar, piscina"),
    ("Santiago de Surco", 707940, 3, 2, 98, 0, "Area de lavanderia", "Ayacucho", "Estreno, piso 1, no paga alcabala"),
    ("Santiago de Surco", 780000, 3, 2, 79, 1, "Gimnasio", "El Derby, cerca U. de Lima", "3 dorm, balcon, entrega jun 2026"),
    ("San Isidro", 960000, 3, 2, 117, 1, "Area de lavanderia", "Av. Carriquiry al 800", "Flat estreno piso 20, vista panoramica"),
    # --- individuales adicionales (paginas venta) ---
    ("San Isidro", 1220000, 3, 2, 226, 2, "Area de lavanderia", "AV. Parque Norte 800, Corpac", "1er piso, cerca Javier Prado"),
    ("Barranco", 436900, 1, 1, 42, 0, "Seguridad", "Avenida Almirante Miguel Grau 1130", "Amoblado, ideal inversion/Airbnb"),
    ("San Isidro", 470700, 2, 2, 46, 0, "Gimnasio", "Av. Javier Prado Este 595 Dpto 1505", "Mini estreno, ideal ejecutivos"),
    ("San Isidro", 476630, 1, 1, 44, 0, "Guardiania/Seguridad privada", "Calle La Perricholi 203", "Piso 8, vista despejada, aire acondicionado"),
    ("Surquillo", 290000, 1, 1, 43, 0, "Guardiania/Seguridad privada", "Av. Tomas Marsano al 1600", "Piso 6, limite Miraflores, areas club"),
    ("San Isidro", 1449000, 3, 2, 290, 1, "Cuartos de servicio", "Octavio Espinosa al 400", "Duplex con gran terraza, remodelado"),
    ("Lince", 479500, 1, 1, 45, 1, "Piscina", "Rivera Navarrete al 2800", "Amoblado con inquilina, limite San Isidro"),
    ("San Isidro", 816000, 2, 2, 80, 1, "Seguridad", "Avenida Coronel Pedro Portillo, Santa Monica", "Frente Golf, piso 2, ideal ejecutivos"),
    ("Santiago de Surco", 1776000, 3, 2, 226, 2, "Jardin", "Av. Circunvalacion Golf Los Incas 148", "Estreno Edificio Moon, cerca Roosevelt"),
    ("Lince", 578000, 2, 2, 91, 1, "Cerca a colegios", "Jiron Manuel Segura & Av. Arequipa", "Edificio Urban Imagina, piso 10, impecable"),
    ("San Borja", 748000, 3, 3, 100, 1, "Area de lavanderia", "Jiron Philipp Von Leonard, Corpac", "1er piso alto, detras Parque Santo Tomas"),
    ("San Borja", 1084800, 3, 3, 235, 4, "Frente a parque", "Avenida Esmeralda al 300, Chacarilla", "1er piso frente Pentagonito, 4 cocheras"),
    ("Santiago de Surco", 1154603, 3, 2, 160, 2, "Cuartos de servicio", "Calle Monte Blanco al 200, Chacarilla", "Vista calle, 6 anos, 2 cocheras paralelas"),
    ("Surquillo", 611520, 4, 2, 156, 0, "Area de lavanderia", "Avenida Villaran cuadra 9", "Flat frente parque, patio/terraza, 25 anos"),
    ("Magdalena", 884000, 3, 2, 132, 0, "Seguridad", "Jr. Daniel Carrion 545", "Flat 1er piso con patio, estreno"),
    ("San Miguel", 510000, 4, 2, 135, 1, "Area de lavanderia", "Calle Manco II", "Duplex, terraza 30m2, frente Parque Simon Bolivar"),
    ("San Borja", 1343000, 4, 3, 230, 2, "Area de lavanderia", "Calle 39, Mariscal Ramon Castilla", "Duplex penthouse, cerca Pentagonito"),
]


def gen_id(dire, precio, area):
    raw = f"{dire}|{precio}|{area}".lower()
    return "ven_" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def main():
    conn = sqlite3.connect(DB)
    conn.text_factory = str
    cur = conn.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(apartments)")]
    if "operacion" not in cols:
        cur.execute("ALTER TABLE apartments ADD COLUMN operacion TEXT")
        cur.execute("UPDATE apartments SET operacion='venta' WHERE operacion IS NULL")

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
                fecha_publicacion, descripcion, url, operacion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (rid, zona, float(precio), hab, ban, float(area), amen,
             FECHA, descripcion, "", "venta"),
        )
        inserted += 1

    conn.commit()

    print("=== CARGA VENTA ===")
    print(f"Listados en batch:  {len(DATA)}")
    print(f"Insertados:         {inserted}")
    print(f"Duplicados (id):    {skipped}")

    total = cur.execute("SELECT COUNT(*) FROM apartments").fetchone()[0]
    alq = cur.execute("SELECT COUNT(*) FROM apartments WHERE operacion='alquiler'").fetchone()[0]
    ven = cur.execute("SELECT COUNT(*) FROM apartments WHERE operacion='venta'").fetchone()[0]
    print(f"\nTotal en BD: {total}  (alquiler={alq}, venta={ven})")

    print("\n--- Venta por zona ---")
    for z, c, pmin, pmax in cur.execute(
        """SELECT zona, COUNT(*), MIN(precio), MAX(precio)
           FROM apartments WHERE operacion='venta'
           GROUP BY zona ORDER BY COUNT(*) DESC"""):
        print(f"  {z:<20} {c:>3}   S/{pmin:>10,.0f} - S/{pmax:>12,.0f}")

    conn.close()


if __name__ == "__main__":
    main()
