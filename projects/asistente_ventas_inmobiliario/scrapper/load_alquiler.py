# -*- coding: utf-8 -*-
"""
Carga el batch de ALQUILER pegado desde Urbania (departamentos en alquiler,
distritos: Surco, Lince, Surquillo, Jesus Maria, San Miguel, San Borja,
San Isidro, Barranco, Magdalena).

- Anade columna 'operacion' a apartments si no existe.
- Marca las filas existentes (venta) como operacion='venta'.
- Inserta este batch con operacion='alquiler'.
- precio = renta mensual en S/ (PEN). Deduplicado entre paginas.
"""

import sqlite3
import hashlib
from datetime import date

DB = "../data/real_estate.db"
FECHA = "2026-07-15"

# (zona_distrito, precio_S/, habitaciones, banos, area_m2, estac(0/1), badge, direccion, desc_corta)
DATA = [
    # --- pagina 1 ---
    ("San Isidro", 2900, 1, 1, 45, 0, "Gimnasio,Piscina,Parrilla", "Av. Juan de Arona 110", "Nomad Living, 1-2 dorm, semi equipado, areas comunes"),
    ("Barranco", 2380, 1, 1, 45, 0, "Amoblado", "Jr. Carlos Arrieta 289", "Amoblado, balcon, piso 1"),
    ("San Isidro", 3200, 2, 2, 60, 1, "Cerca a colegios,Amoblado", "Dean Valdivia 207 Corpac", "Amoblado, cochera, piso 4"),
    ("San Isidro", 3355, 2, 2, 60, 0, "Area de lavanderia", "Calle Alfz. Mariano Santos Mateos 179", "Santa Ana, balcon, 2 dorm"),
    ("Santiago de Surco", 3470, 3, 2, 105, 1, "Gimnasio", "Jiron las Gardenias 106", "3 dorm, 2 banos, cochera"),
    ("San Isidro", 3150, 1, 1, 45, 0, "Guardiania/Seguridad privada", "Avenida Canaval y Moreyra", "Corpac, vendo/alquilo, 1 dorm"),
    ("San Isidro", 7400, 3, 2, 208, 2, "Amoblado", "Santo Toribio", "A 2 cuadras del Golf, amoblado opcional"),
    ("San Isidro", 2800, 2, 1, 66, 1, "Amoblado", "Av Parque Sur al 300", "Corpac, amoblado, cochera"),
    ("Surquillo", 2250, 2, 2, 60, 1, "Parrilla", "AV PRINCIPAL, Calera", "Cerca estacion Angamos, 2 dorm"),
    ("Magdalena", 2550, 1, 1, 60, 1, "Area de lavanderia", "Jr. Faustino Sanchez Carrion 170", "Duplex, pet friendly, cochera"),
    ("San Isidro", 14000, 6, 6, 240, 3, "Bajo de precio", "Los Pinos 582", "Estreno, linea blanca, 6 dorm"),
    ("San Isidro", 3000, 2, 1, 47, 1, "Area de lavanderia", "Calle Manuel Roaud y Paz Soldan", "Estreno, cochera techada"),
    ("Jesus Maria", 2200, 1, 1, 41, 0, "Gimnasio", "Av Salaverry al 1800", "Semiamoblado, cuadra 18"),
    ("San Isidro", 3470, 2, 2, 61, 1, "Area de lavanderia", "Calle Coronel Andres Reyes", "Jardin, piso 19, vista, cochera"),
    ("San Isidro", 800, 1, 1, 10, 0, "Bajo de precio", "Av. Dos de Mayo 961", "Habitacion, servicios incluidos"),
    ("Jesus Maria", 2000, 3, 2, 77, 0, "Frente a parque", "Jr. Francisco de Zela 915", "3 dorm, edificio pequeno"),
    ("Barranco", 2500, 1, 1, 45, 0, "Area de lavanderia", "Av. El Sol Este 545-555", "Amoblado, areas comunes"),
    ("Barranco", 2250, 1, 1, 50, 0, "Piscina", "Avenida Almirante Miguel Grau 1130", "Amoblado, vista calle"),
    ("Barranco", 3200, 2, 2, 60, 0, "Gimnasio", "Av. el Sol 161", "Amoblado, frente parque Chipoco"),
    ("Magdalena", 2200, 2, 2, 54, 1, "Seguridad", "Jiron Mariscal Castilla", "Moderno, cochera, piso 11"),
    ("San Isidro", 11270, 3, 3, 250, 2, "Seguridad", "Calle Francisco Eguiguren", "250m2, acabados de lujo"),
    ("Barranco", 2550, 1, 1, 46, 1, "Area de lavanderia", "Pedro Martinto al 100", "Cerca al malecon, amoblado"),
    ("San Isidro", 3400, 1, 1, 45, 0, "Seguridad", "Javier Prado / Navarrete", "Estreno, amoblado, cochera opcional"),
    ("San Miguel", 2800, 3, 2, 84, 0, "Amoblado", "Av Costanera", "Costa Castana, vendo/alquilo"),
    ("Magdalena", 2200, 1, 1, 43, 0, "Piscina", "Av. Javier Prado Oeste 881", "Amoblado, linea blanca"),
    ("Jesus Maria", 2650, 3, 2, 74, 1, "Ascensor", "Calle Arnaldo Marquez 1440", "Estreno, piso 16, cochera"),
    ("San Isidro", 3853, 2, 2, 72, 0, "Piscina", "Av. Javier Prado Este 597", "Estreno, sin cochera, rooftop"),
    ("Magdalena", 4140, 3, 2, 123, 0, "Parrilla", "Av. Manuel Gonzales Prada 324", "Triplex, vista al parque"),
    ("San Isidro", 2100, 1, 1, 35, 0, "Ascensor", "Av. Salaverry 3580", "Piso 5, cerca UPC"),
    ("Lince", 3100, 2, 2, 82, 1, "Gimnasio", "Jr. Manuel Villavicencio 1137", "Frente Parque Castilla, piso 9"),
    # --- pagina 2 ---
    ("San Miguel", 1850, 1, 1, 60, 1, "Ascensor", "Avenida Rafael Escardo 600", "Cerca La Marina, con/sin cochera"),
    ("Barranco", 2590, 1, 1, 50, 0, "Frente a parque", "Teodosio Parreno", "Edificio Mood, amoblado"),
    ("San Isidro", 2600, 2, 2, 80, 1, "Gimnasio", "Estacion Domingo Orue", "Piso 10, cerca Metropolitano"),
    ("Surquillo", 2800, 1, 1, 60, 1, "Bajo de precio", "Calle Las Aguilas 100, Limatambo", "Flat amoblado, limite San Isidro"),
    ("San Miguel", 1650, 1, 1, 35, 0, "Gimnasio", "Av. Los Patriotas 415", "Supra Tower, piso 18"),
    ("Barranco", 4673, 2, 2, 110, 1, "Guardiania/Seguridad privada", "Jiron Saenz Pena", "Arq. Armando Paredes, zona monumental"),
    ("San Miguel", 1800, 2, 2, 60, 1, "Seguridad", "edificio Smart, Los Patriotas", "Piso 12, cerca Plaza San Miguel"),
    ("San Isidro", 3730, 2, 2, 65, 0, "Seguridad", "Av. Rivera Navarrete 548", "Pet friendly, piso 10"),
    ("Surquillo", 2500, 3, 2, 70, 0, "Guardiania/Seguridad privada", "Alfa Leon 151, La Calera", "3 dorm, disponibilidad inmediata"),
    ("San Isidro", 3100, 2, 2, 66, 1, "Area de lavanderia", "Av Pablo Carriquiry 894", "Piso 16, piscina, cochera"),
    ("Santiago de Surco", 2500, 3, 1, 80, 0, "Amoblado", "Loma de las Violetas al 200", "117m2 real, 3 dorm, gatos ok"),
    ("San Isidro", 5950, 3, 3, 170, 2, "Guardiania/Seguridad privada", "Tomas Edison 135", "2 cocheras, deposito, a/c"),
    ("Barranco", 2200, 1, 2, 59, 1, "Ascensor", "San Martin", "1 dorm, cochera, deposito"),
    ("San Isidro", 3000, 2, 1, 50, 0, "Area de lavanderia", "C. Manuel Roaud y Paz Soldan", "Estreno, cerca Golf"),
    ("Magdalena", 3000, 3, 2, 73, 0, "Guardiania/Seguridad privada", "Jiron Libertad 11", "Full amoblado, remodelado"),
    ("Magdalena", 2400, 2, 1, 55, 0, "Area de lavanderia", "Av. Faustino Sanchez Carrion 820", "Piso 6, linea blanca"),
    ("San Miguel", 1950, 3, 2, 70, 0, "Piscina", "Av. La Paz 2551", "Estreno, Patio La Paz"),
    ("Surquillo", 2200, 2, 1, 50, 1, "Guardiania/Seguridad privada", "Avenida Paseo de la Republica 5181", "2 dorm+estudio, cochera"),
    ("Santiago de Surco", 3700, 3, 4, 122, 1, "Area de lavanderia", "Calle Victor Plascencia", "Cerca estacion Jorge Chavez"),
    ("San Isidro", 6800, 3, 3, 180, 1, "Area de lavanderia", "Jose del Llano Zapata 100", "Flat 1er piso, Ovalo Gutierrez"),
    ("San Isidro", 3850, 1, 1, 50, 1, "Parrilla", "Calle Los Pinos, Orrantia", "Flat amoblado, cochera"),
    ("San Isidro", 2690, 1, 1, 50, 0, "Guardiania/Seguridad privada", "Los Pinos 561", "Flat amoblado, frente Real"),
    ("San Isidro", 3300, 2, 1, 47, 1, "Parrilla", "Calle Manuel Roaud y Paz Soldan 360", "Estreno, cerca Dasso"),
    ("San Isidro", 9760, 4, 4, 300, 2, "Gimnasio", "Torre Palatino", "Duplex 300m2, Javier Prado Oeste"),
    ("Barranco", 3070, 3, 2, 71, 0, "Cerca a colegios", "Av. el Sol 833", "Amoblado, piso 11"),
    ("Lince", 4300, 3, 2, 90, 0, "Gimnasio", "Jr. Manuel Villavicencio Cuadra 8", "Amoblado, vista Parque Castilla"),
    ("San Isidro", 3325, 2, 2, 62, 0, "Guardiania/Seguridad privada", "Javier Prado Este", "Estreno, vista piscina"),
    ("San Isidro", 2975, 1, 1, 49, 0, "Seguridad", "Av. Ricardo Rivera Navarrete", "Edificio Pionero, amoblado"),
    ("San Isidro", 2750, 2, 1, 62, 0, "Gimnasio", "Javier Prado Este al 500", "Edificio All, estreno 2 dorm"),
    ("San Isidro", 2100, 1, 1, 60, 1, "Piscina", "Avenida Javier Prado Oeste 2367", "Amoblado, limite San Isidro"),
    # --- pagina 3 ---
    ("San Isidro", 4250, 3, 2, 127, 1, "Parrilla", "Calle Roma al 400", "Piso 4, balcon amplio"),
    ("San Miguel", 1800, 1, 1, 41, 1, "Piscina", "Av. Costanera", "Vista al mar, remodelado"),
    ("San Isidro", 6435, 3, 3, 220, 2, "Ascensor", "Av. Arequipa 3000", "Piso 16, vista panoramica, expat"),
    ("Santiago de Surco", 11900, 3, 3, 220, 4, "Ascensor", "Calle Monte Flor, Chacarilla", "Linea blanca, 4 cocheras"),
    ("Santiago de Surco", 1980, 2, 2, 80, 1, "Area de lavanderia", "Lomas de las gardenias, Prolong. Benavides", "3er piso sin ascensor"),
    ("San Isidro", 3400, 2, 2, 69, 0, "Guardiania/Seguridad privada", "Calle Los Naranjos, Orrantia", "Todo incluido, amoblado"),
    ("Lince", 3078, 2, 2, 67, 1, "Gimnasio", "Calle Los Geranios 310", "Amoblado, piso 10, cochera"),
    ("San Isidro", 2242, 1, 1, 36, 0, "Ascensor", "Manuel Roaud y Paz Soldan 300, San Gabriel", "Minidepartamento estreno"),
    ("San Isidro", 1850, 1, 1, 55, 0, "Sin ascensor", "Calle Federico Villarreal 252", "Piso 5 sin ascensor"),
    ("Santiago de Surco", 2200, 3, 3, 120, 0, "Seguridad", "Urbanizacion Santa Rosa de Surco", "2do piso, 3 banos con tina"),
    ("Jesus Maria", 2250, 1, 1, 41, 0, "Seguridad", "Avenida Garibaldi 209", "Estreno, amoblado, embajada Italia"),
    ("San Isidro", 3500, 3, 2, 115, 1, "Amoblado", "Calle Los Olivos, Orrantia", "Amoblado, cochera techada"),
    ("Barranco", 2350, 1, 1, 43, 1, "Gimnasio", "Av. El Sol Este al 100", "Loft amoblado, cochera"),
    ("San Isidro", 2500, 1, 1, 45, 0, "Seguridad", "Calle Chinchon", "Amoblado, balcon, piso 8"),
    ("Santiago de Surco", 7140, 3, 3, 280, 1, "Area de lavanderia", "Jiron Carlos Baca Flor, Las Magnolias", "Duplex 280m2, semi amoblado"),
    ("Santiago de Surco", 9418, 4, 5, 405, 3, "Gimnasio", "Cerros de Camacho", "Flat 405m2, vista, venta/alquiler"),
    ("San Borja", 6120, 3, 3, 200, 0, "Ascensor", "Jr. 2 al 500", "Duplex 200m2, edificio 3 pisos"),
    ("Lince", 2550, 3, 2, 90, 0, "Ascensor", "Jr. Alberto Alexander 2325", "Piso alto, sin cochera"),
    ("San Isidro", 2890, 1, 1, 54, 0, "Ascensor", "Los Laureles al 200", "Amoblado, remodelado, piso 3"),
    ("San Miguel", 2600, 3, 2, 90, 1, "Cerca a colegios", "Av. los Insurgentes & Av. Libertad", "Estreno, programa naval"),
    ("San Isidro", 3000, 1, 1, 48, 0, "Amoblado", "Av. General Salaverry 2675", "Amoblado, vista al parque"),
    ("San Borja", 4375, 3, 3, 125, 0, "Seguridad", "Av Blvrd de Surco 370", "3 dorm, 4 banos, ascensor"),
    ("San Isidro", 3390, 2, 2, 60, 1, "Parrilla", "Av. Javier Prado Oeste 2361", "Amoblado, cochera, piscina"),
    ("San Borja", 2400, 1, 1, 43, 1, "Area de lavanderia", "Avenida San Borja Norte", "Amoblado, cochera, deposito"),
    ("Jesus Maria", 2800, 3, 2, 70, 0, "Area de lavanderia", "Av. 28 de Julio 300", "2 dorm+estudio, pet friendly"),
    ("Lince", 2100, 1, 1, 52, 0, "Area de lavanderia", "Manuel Gomez al 100", "Moderno, cerca Rebagliati"),
    ("Surquillo", 2950, 2, 2, 59, 1, "Seguridad", "Avenida Aramburu 668, Jardines", "Estreno, cerca San Isidro"),
    ("Barranco", 2142, 1, 1, 40, 1, "Area de lavanderia", "Jiron 2 de Mayo al 100", "Amoblado, cerca Puente Suspiros"),
    ("Surquillo", 2300, 3, 2, 78, 0, "Frente a parque", "Pasaje La Union 101, La Calera", "Estreno, vista parque"),
    ("Barranco", 2285, 1, 1, 55, 1, "Area de lavanderia", "Jr. Tacna 440", "Sin amoblar, cochera"),
    # --- pagina 4 ---
    ("Santiago de Surco", 7480, 3, 3, 251, 2, "Area de lavanderia", "Av. Circunvalacion del Golf los Incas", "Duplex 251m2, arq. Malachowski"),
    ("San Isidro", 2550, 1, 1, 45, 0, "Amoblado", "Juan Norberto Elespuru 535", "Amoblado, piso 16"),
    ("Jesus Maria", 2000, 1, 1, 45, 0, "Cerca a colegios", "Pachacutec 2090", "Amoblado, cerca San Felipe"),
    ("Barranco", 2530, 1, 1, 65, 0, "Area de lavanderia", "calle Oroya 103", "Estilo rancho, bohemio"),
    ("San Miguel", 1700, 1, 1, 36, 0, "Ascensor", "Av. Bertolotto", "Estreno, vista al mar, piso 8"),
    ("Santiago de Surco", 2000, 2, 2, 80, 1, "Area de lavanderia", "Av. Paseo de la Castellana con Teniente Ferre", "Piso 5, cochera"),
    ("Magdalena", 3300, 3, 3, 100, 1, "Area de lavanderia", "Avenida Antonio Miro Quesada 559", "Piso 8, limite San Isidro"),
    ("San Borja", 1399, 1, 1, 25, 1, "Bajo de precio", "Avenida San Borja Sur 1070, Las Begonias", "Mini duplex amoblado"),
    ("San Isidro", 4800, 3, 2, 136, 2, "Parrilla", "Calle los Cipreses, Orrantia", "Piso 15, piscina temperada"),
    ("Lince", 2350, 2, 2, 65, 0, "Bajo de precio", "Av. Ignacio Merino 1512, Risso", "Edificio Alma, piso 13"),
    ("Barranco", 2650, 1, 1, 60, 1, "Seguridad", "Ca. Francisco Del Castillo 627", "Semi amoblado, limite Miraflores"),
    ("Jesus Maria", 3000, 2, 2, 66, 1, "Piscina", "jiron huiracocha 2257", "Amoblado, piso 5, cerca UP"),
    ("Barranco", 5807, 3, 3, 159, 2, "Cerca a colegios", "Buenaventura Aguirre 292", "Torres Paz, premio arquitectura"),
    ("Surquillo", 1900, 1, 1, 40, 0, "Reservado", "Avenida Domingo Orue 220", "Estreno, limite Miraflores"),
    ("San Isidro", 5070, 2, 2, 109, 2, "Seguridad", "Calle Los Nogales, Orrantia", "Terraza, piscina, bbq propio"),
    ("Santiago de Surco", 1800, 3, 2, 79, 1, "Gimnasio", "Avenida Paseo la Castellana", "Condominio, piso 15"),
    ("Santiago de Surco", 2600, 1, 1, 63, 1, "Guardiania/Seguridad privada", "Jiron Cristobal de Peralta Sur 119", "Amoblado, piso 2"),
    ("San Borja", 5814, 3, 2, 176, 2, "Seguridad", "Av. Velasco Astete 925, Chacarilla", "Flat con terraza 54m2"),
    ("Jesus Maria", 3700, 2, 1, 120, 0, "Area de lavanderia", "Jiron Rio de Janeiro 195", "Remodelado, primer piso"),
    ("Barranco", 4000, 3, 2, 141, 1, "Seguridad", "Calle Catalino Miranda", "Duplex piso 9, terraza"),
    ("Barranco", 2700, 2, 2, 60, 1, "Guardiania/Seguridad privada", "calle martinto", "1 dorm+estudio, amoblado"),
    ("Santiago de Surco", 5100, 2, 2, 120, 1, "Cerca a colegios", "Cerros de Camacho 421", "Vista Golf, amoblado"),
    ("Santiago de Surco", 2500, 1, 1, 54, 1, "Bajo de precio", "Calle Marcona, Tambo de Monterrico", "Estreno, cochera+deposito"),
    ("Jesus Maria", 2049, 1, 1, 42, 0, "Area de lavanderia", "Jiron Inca Ripac 198", "Estreno, linea blanca, terraza"),
    ("Jesus Maria", 2400, 2, 2, 60, 1, "Cerca a colegios", "Av. 28 de Julio 332", "Estreno, piso 11"),
    ("Santiago de Surco", 4700, 3, 3, 145, 2, "Cerca a colegios", "Aguada Blanca 133, Tambo de Monterrico", "Frente parque, piso 4"),
    ("Surquillo", 2034, 1, 1, 37, 0, "Vista panoramica", "Avenida Sergio Bernales 420", "Barrio Medico, semi amoblado"),
    ("Magdalena", 2700, 2, 2, 65, 1, "Guardiania/Seguridad privada", "Leon de la fuente, Orrantia del Mar", "Frente Cricket Club, piso 8"),
    ("Santiago de Surco", 4590, 3, 3, 120, 0, "Amoblado", "Los Morochucos, Santa Constanza", "Duplex frente Jockey Plaza"),
    ("Barranco", 2565, 1, 1, 47, 0, "Parrilla", "Calle Teodosio Parreno Cdra.2", "Amoblado, piso 17"),
    ("San Isidro", 11583, 2, 2, 165, 2, "Guardiania/Seguridad privada", "Calle Los Eucaliptos", "Flat estreno, vista al parque"),
    ("San Miguel", 2300, 3, 2, 80, 1, "Parrilla", "ALT Cdra 1 Av. Andres Razuri, Maranga", "Piso 5, amoblado o sin"),
    # --- pagina 5 ---
    ("San Isidro", 3230, 1, 1, 50, 1, "Ascensor", "Camino Real", "Remodelado, amoblado, cerca Dasso"),
    ("Santiago de Surco", 7700, 3, 2, 170, 2, "Seguridad", "Avenida de los Precursores 770", "Flat piso 4, 12 deptos"),
    ("Santiago de Surco", 6080, 2, 2, 105, 1, "Cerca a colegios", "Av. Cerros de Camacho", "Golf Park, piscina"),
    ("San Isidro", 3700, 2, 2, 60, 1, "Area de lavanderia", "Javier Prado Este al 500", "Amoblado estreno, piso 17"),
    ("San Isidro", 2800, 1, 1, 45, 0, "Gimnasio", "Camelias San Isidro", "Amoblado, piso 6"),
    ("San Isidro", 15085, 4, 3, 550, 3, "Parrilla", "Av Coronel Pedro Portillo, Santa Monica", "Penthouse duplex 550m2"),
    ("Lince", 2750, 1, 1, 47, 1, "Seguridad", "Sinchi Roca al 2500", "Amoblado, piso 11"),
    ("Barranco", 2500, 1, 1, 42, 1, "Seguridad", "Jiron Pedro Martinto", "Remodelado, amoblado, piscina"),
    ("San Isidro", 9500, 3, 3, 216, 2, "Guardiania/Seguridad privada", "Avenida Santo Toribio, Country Club", "Cerca Swissotel, terraza"),
    ("Santiago de Surco", 11750, 3, 4, 230, 2, "Amoblado", "Avenida Circunvalacion del Golf 148", "Edificio Moon, lujo full amoblado"),
    ("Jesus Maria", 3000, 3, 2, 117, 0, "Area de lavanderia", "Calle Horacio Urteaga 2029", "3 dorm, cuarto de servicio"),
    ("Magdalena", 3600, 2, 2, 94, 1, "Guardiania/Seguridad privada", "calle clemente X 140", "Flat, limite San Isidro"),
    ("San Miguel", 2400, 2, 1, 61, 1, "Parrilla", "Av. de los Patriotas", "Estreno, entrega inmediata"),
    ("San Isidro", 13899, 3, 3, 312, 2, "Seguridad", "Victor Maurtua, Santa Isabel", "Terraza amplia, ascensor directo"),
    ("Barranco", 2200, 1, 1, 50, 0, "Seguridad", "Av. San Martin 207", "Amoblado, a/c, limite Miraflores"),
    ("San Miguel", 1800, 2, 1, 62, 0, "Area de lavanderia", "Mariscal Ramon Castilla", "Primer piso, urb. Castilla"),
    ("Lince", 2600, 3, 2, 75, 2, "Seguridad", "av Arequipa al 2544", "Edificio Arequipa Central, pet friendly"),
    ("Lince", 1850, 2, 2, 60, 0, "Sin ascensor", "Calle Enrique Villar", "Piso 3, cerca Clinica La Luz"),
    ("Magdalena", 2200, 1, 1, 40, 1, "Amoblado", "avenida ejercito 865, Orrantia del Mar", "Vista al mar, piso 8, amoblado"),
    ("San Borja", 3500, 3, 2, 95, 1, "Parrilla", "Durero 490", "Condominio HomeTown"),
    ("Santiago de Surco", 2950, 3, 2, 83, 1, "Amoblado", "Jr. Richard Strauss, Los Alamos de Monterrico", "Amoblado, condominio"),
    ("Magdalena", 2600, 3, 2, 80, 1, "Area de lavanderia", "Jiron Ayacucho 750, Marbella", "Estreno, cochera"),
    ("San Miguel", 2200, 3, 2, 83, 0, "Area de lavanderia", "Jiron Manco II 145, Maranga", "Uptown I, terraza, piso 7"),
    ("Barranco", 2600, 1, 1, 50, 1, "Area de lavanderia", "Jiron Pedro Martinto 114", "Amoblado, cochera, a/c"),
    ("Barranco", 2230, 1, 1, 42, 1, "Area de lavanderia", "Av. El Sol, Agua Dulce Norte", "Amoblado, vista parque"),
    ("Surquillo", 2750, 3, 2, 70, 1, "Parrilla", "Av. Principal 915", "Estreno, cochera techada"),
    ("Santiago de Surco", 2850, 1, 1, 60, 0, "Amoblado", "Jiron Toquepala 200, Tambo de Monterrico", "Amoblado, Chacarilla"),
    ("San Isidro", 2400, 1, 1, 50, 0, "Area de lavanderia", "Alberto del Campo 468", "Amoblado, cancha fronton"),
    ("San Isidro", 54720, 3, 3, 598, 4, "Gimnasio", "Avenida General Pezet", "Flat de lujo 655m2, vista Golf"),
    # --- pagina 6 ---
    ("Magdalena", 1800, 1, 1, 40, 0, "Bajo de precio", "Jr. Faustino Sanchez Carrion 157", "1 dorm, cerca al malecon"),
    ("Santiago de Surco", 4460, 3, 2, 123, 2, "Area de lavanderia", "Avenida el Derby 539", "3 dorm, piscina, cine"),
    ("Santiago de Surco", 3750, 2, 3, 95, 1, "Seguridad", "Caminos del Inca 542", "Piso 3, cochera+deposito"),
    ("Santiago de Surco", 3700, 2, 2, 65, 1, "Amoblado", "Av. Manuel Olguin Cdra", "Edificio Epique, vista hipodromo"),
    ("San Isidro", 2881, 1, 1, 48, 1, "Area de lavanderia", "Av. Arequipa 3235", "Amoblado, piso 8, a/c"),
    ("San Isidro", 4000, 2, 2, 72, 1, "Gimnasio", "Calle Los Pinos 561 - 05SS", "Amoblado, terraza amplia"),
    ("Jesus Maria", 2100, 1, 1, 42, 0, "Ascensor", "Avenida San Felipe 785", "Estreno, piso 7"),
    ("Lince", 3211, 2, 2, 90, 1, "Area de lavanderia", "Calle Luis Pasteur", "2 cocheras, limite San Isidro"),
    ("San Isidro", 4080, 2, 2, 75, 0, "Area de lavanderia", "Rivera Navarrete 500, Corpac", "Amoblado, casi estreno"),
    ("Lince", 1900, 1, 1, 38, 0, "Ascensor", "AV. Arenales 2510", "Sin amoblar, piso 17"),
    ("San Isidro", 2600, 1, 1, 45, 0, "Area de lavanderia", "Av. Ricardo Rivera Navarrete, Corpac", "Estreno, 1 dorm"),
    ("San Miguel", 4140, 3, 2, 144, 2, "Parrilla", "Jr. San Martin 683", "Primer piso, terraza, parrilla"),
    ("San Isidro", 2864, 1, 1, 65, 1, "Area de lavanderia", "Calle Los Alamos 396, Orrantia", "Amoblado, cochera"),
    ("San Isidro", 3850, 2, 2, 110, 1, "Area de lavanderia", "Calle Los Castanos", "2 dorm, cochera"),
    ("San Isidro", 2900, 1, 1, 45, 0, "Ascensor", "Amador Merino Reyna al 300", "Estreno, piso 16"),
    ("San Isidro", 4500, 1, 2, 115, 1, "Area de lavanderia", "Avenida Javier Prado Oeste 1968, Santa Rosa", "Amoblado, piso 7"),
    ("Santiago de Surco", 4068, 2, 2, 65, 1, "Ascensor", "frente al CC El Polo, Liberty Surco", "2 dorm, piso 7"),
    ("Barranco", 2300, 3, 2, 80, 1, "Seguridad", "Barranco, cerca Metropolitano", "3 hab, piso 4, cochera"),
    ("Barranco", 2890, 1, 1, 40, 1, "Parrilla", "El Sol Oeste", "Amoblado, venta/alquiler, cochera"),
    ("San Isidro", 9400, 3, 2, 217, 2, "Piscina", "Eucaliptos 623", "Vista Golf / Country Club"),
    ("Surquillo", 2250, 1, 1, 44, 1, "Parrilla", "AV. Tomas Marsano 300", "Mini amoblado, cochera"),
    ("San Isidro", 3400, 2, 2, 65, 1, "Area de lavanderia", "Perricholi 200", "Amoblado, frente parque"),
    ("Jesus Maria", 3100, 3, 2, 90, 1, "Seguridad", "Av. 28 de Julio 368", "Edificio Ficus, piso 13"),
    ("Magdalena", 2180, 2, 2, 52, 1, "Area de lavanderia", "Jiron Libertad", "Seminuevo, cochera"),
    ("San Isidro", 2900, 1, 1, 47, 1, "Ascensor", "Antequera 580", "Amoblado, edificio exclusivo"),
    ("Jesus Maria", 3000, 2, 3, 66, 1, "Parrilla", "Jiron Huiracocha", "Amoblado, cerca UP"),
    ("Barranco", 9492, 2, 2, 185, 2, "Seguridad", "Malecon Barranco", "Flat vista al mar, piso 5"),
    ("San Isidro", 2200, 1, 1, 46, 0, "Gimnasio", "Av. Javier Prado Este Cdra. 5", "Loft estreno, piso 8"),
    ("Santiago de Surco", 2600, 1, 1, 44, 0, "Gimnasio", "Avenida El Derby 182", "Estreno, piso 12"),
    ("San Borja", 3500, 3, 2, 95, 1, "Seguridad", "Jiron Mercator, Corpac", "Piso 2, limite San Isidro"),
    # --- pagina 7 ---
    ("Surquillo", 2300, 2, 1, 93, 0, "Guardiania/Seguridad privada", "Av. Tomas Marsano 1553", "3er piso, duplex, cerca Open Plaza"),
    ("Santiago de Surco", 1000, 1, 1, 30, 1, "Economico", "ALT CDRA 4 DE AV PROCERES", "Departamento economico, servicios incluidos"),
    ("Santiago de Surco", 2500, 2, 2, 99, 1, "Area de lavanderia", "Calle Loma de Las Violetas, Prolong. Benavides", "2 dorm+escritorio, gatos ok"),
    ("San Miguel", 2300, 3, 2, 76, 0, "Seguridad", "C. Padre Urraca 111, Parques de la Huaca", "Primer piso, frente parque"),
    ("Jesus Maria", 2150, 2, 2, 72, 1, "Seguridad", "Av. San Felipe 1079, Risso", "Vista panoramica, piso 17"),
    ("Lince", 1950, 1, 1, 57, 0, "Cerca a colegios", "Jiron Alberto Alexander", "Remodelado, primer piso"),
    ("San Isidro", 3700, 2, 2, 85, 0, "Cerca a colegios", "Calle Los Eucaliptos 337, Santa Rosa", "Sin amoblar, acabados de lujo"),
    ("San Isidro", 4300, 3, 2, 60, 1, "Seguridad", "Calle Amador Merino Reyna", "Amoblado, estreno, piso 4"),
    ("Barranco", 2010, 1, 1, 45, 1, "Seguridad", "Av. Pedro de Osma 346", "Moderno, cerca clinica Estela Maris"),
    ("Santiago de Surco", 1900, 3, 2, 95, 0, "Cerca a colegios", "Jr. Apolo Sagitario, Sagitario", "2do piso, buen estado"),
    ("Santiago de Surco", 8675, 4, 3, 440, 2, "Ascensor", "Precursores", "PH frente parque, duplex"),
    ("Barranco", 2275, 1, 1, 59, 1, "Parrilla", "Pedro de Osma 307", "Amoblado, terraza, piscina"),
    ("San Isidro", 12075, 3, 3, 250, 3, "Guardiania/Seguridad privada", "Calle Los Castanos, Country Club", "250m2, 3 cocheras"),
    ("San Miguel", 2100, 3, 2, 75, 0, "Gimnasio", "Calle 16 180, Miramar", "Vista al mar, piso 11"),
    ("Barranco", 2400, 3, 2, 72, 0, "Parrilla", "Av Sol con Av Grau", "3er piso, 3 dorm"),
    ("Barranco", 3337, 2, 2, 105, 1, "Bajo de precio", "Jiron Martinez de Pinillos 132", "Piso 3, cerca al malecon"),
    ("Surquillo", 2100, 1, 1, 40, 0, "Area de lavanderia", "Las Codornices 145, Limatambo", "Estreno, frente parque, piso 9"),
    ("Barranco", 8814, 3, 4, 255, 2, "Area de lavanderia", "Malecon Souza", "Vista al mar, piso 4, 2 cocheras"),
    ("Barranco", 2300, 1, 1, 40, 1, "Area de lavanderia", "Jr. Carlos Arrieta 190", "Vista Chipoco/mar, amoblado"),
    ("San Isidro", 2040, 1, 1, 50, 0, "Seguridad", "Calle Guillermo Marconi 300", "Amoblado, piso 2, cochera"),
    ("Magdalena", 2000, 1, 1, 40, 0, "Piscina", "Jiron Faustino Sanchez Carrion", "1 dorm, vista al mar"),
    ("Jesus Maria", 1800, 1, 1, 40, 0, "Bajo de precio", "Av. Gregorio Escobedo 426", "Cocina abierta, piscina"),
    ("Jesus Maria", 1790, 1, 1, 50, 1, "Gimnasio", "Avenida Horacio Urteaga 4", "Amoblado, cerca Campo de Marte"),
    ("San Isidro", 4500, 3, 2, 120, 1, "Guardiania/Seguridad privada", "Av. Paseo Parodi, Jardin", "Amoblado o sin, centro financiero"),
    ("Barranco", 6156, 2, 2, 113, 1, "Area de lavanderia", "San Martin", "Flat arquitectura premiada"),
    ("Barranco", 2000, 1, 1, 36, 0, "Area de lavanderia", "Gastaneta 190", "1 dorm, cerca al mar"),
    ("Santiago de Surco", 1750, 3, 2, 60, 0, "Area de lavanderia", "Calle Z Mz F Lt 6, Santa Rosa", "2do piso, entrada independiente"),
    ("San Isidro", 3051, 1, 1, 70, 0, "Guardiania/Seguridad privada", "Av Coronel Pedro Portillo 400", "Duplex amoblado, frente Golf"),
    ("San Isidro", 4500, 3, 2, 90, 1, "Area de lavanderia", "Calle Manuel Perez de Tudela 274, El Olivar", "Sin amoblar, piso 2"),
    # --- pagina 8 ---
    ("San Borja", 1500, 1, 1, 80, 1, "Guardiania/Seguridad privada", "Av Julio Bailetti 6", "Primer piso, ingreso independiente"),
    ("San Borja", 1800, 1, 1, 29, 0, "Amoblado", "Calle Strauss cuadra 4", "Mini amoblado, 3er piso"),
    ("Magdalena", 2100, 1, 2, 50, 1, "Amoblado", "Jiron Libertad 764", "1 dorm, cochera, linea blanca"),
    ("San Isidro", 5360, 2, 3, 158, 2, "Bajo de precio", "Calle Las Flores, Santa Rosa", "2 dorm+servicio, 2 cocheras"),
    ("Barranco", 2380, 1, 1, 42, 0, "Guardiania/Seguridad privada", "Av. Miguel Grau 1380", "Amoblado, a/c, vista"),
    ("Magdalena", 2700, 2, 2, 65, 0, "Guardiania/Seguridad privada", "Av. Faustino Sanchez Carrion 820", "Amoblado, piso 5"),
    ("San Borja", 3400, 3, 2, 100, 1, "Area de lavanderia", "Rubens", "Flat estreno, zona exclusiva"),
    ("San Isidro", 3000, 2, 2, 60, 1, "Ascensor", "C. German Schreiber Gulsmanco 294, Santa Ana", "2 dorm, sin amoblar"),
    ("San Isidro", 3060, 1, 1, 65, 1, "Guardiania/Seguridad privada", "Avenida Coronel Pedro Portillo", "Duplex amoblado, frente Golf"),
    # --- pagina 9 ---
    ("San Miguel", 1580, 1, 1, 42, 1, "Parrilla", "Av. Costanera 2210", "Condominio Panoramic, vista mar"),
    ("Jesus Maria", 2100, 1, 1, 40, 0, "Parrilla", "Jiron Rio de Janeiro 501", "Estreno, smart home, Alexa"),
    ("Magdalena", 3500, 3, 3, 88, 0, "Guardiania/Seguridad privada", "Miraflores 360, Coral Tower", "Amoblado, piso 14"),
    ("Santiago de Surco", 3500, 2, 2, 58, 1, "Cerca a colegios", "La Castellana", "2 dorm, balcon, parrilla"),
    ("Jesus Maria", 3400, 3, 2, 180, 1, "Duplex", "Avenida Ricardo Tizon y Bueno", "Duplex 180m2, piso 2"),
    ("Barranco", 2230, 1, 1, 40, 0, "Amoblado", "Av. El Sol 161, Studio 4", "Monoambiente amoblado, piso 6"),
    ("Surquillo", 1870, 1, 1, 40, 0, "Seguridad", "BLERIOT 1XX", "Amoblado, edificio pequeno"),
    ("San Isidro", 27200, 4, 3, 371, 4, "Area de lavanderia", "Calle Renan Elias al 200", "Flat de lujo, arq. David Mutal"),
    ("San Isidro", 2550, 1, 1, 46, 0, "Piscina", "Calle Antequera al 500, Walk Street", "Amoblado, proyecto Walk Street"),
    ("Magdalena", 3047, 3, 2, 80, 0, "Amoblado", "Avenida del Ejercito 481", "3 dorm, balcon, piso 4"),
    ("San Isidro", 2800, 1, 1, 63, 1, "Ascensor", "Av. Jose Galvez Barrenechea", "Flat estreno 63m2, club-house"),
    ("San Miguel", 2600, 3, 2, 69, 0, "Piscina", "Av. Bertolotto", "Semi amoblado, vista mar"),
    ("San Isidro", 2300, 1, 1, 37, 0, "Piscina", "C. Manuel Roaud y Paz Soldan 364", "Estreno, cerca Golf"),
    ("Jesus Maria", 2600, 3, 2, 92, 1, "Area de lavanderia", "Avenida General Salaverry 1818", "Remodelado, piso 3"),
    ("San Isidro", 3590, 2, 2, 72, 1, "Guardiania/Seguridad privada", "Galvez Barrenechea al 400, Corpac", "Estreno, 2 dorm, cochera"),
    # --- pagina 10 ---
    ("San Isidro", 3250, 1, 1, 45, 1, "Amoblado", "Piso 19 The Lead", "Amoblado, vista panoramica, cochera"),
    ("San Miguel", 2300, 3, 2, 87, 1, "Bajo de precio", "Av. los Insurgentes & Av. Libertad", "Estreno, 3 dorm, piso 5"),
    ("San Isidro", 3400, 1, 2, 71, 1, "Seguridad", "Calle Gavilanes 195, Limatambo", "Duplex sin amoblar, 71m2"),
    ("Barranco", 2500, 3, 2, 85, 0, "Gimnasio", "Jiron Corpancho al 100", "3 dorm, cerca al malecon"),
    ("San Isidro", 2558, 1, 1, 45, 0, "Bajo de precio", "Calle La Perricholi 203", "Amoblado, piso 9"),
    ("Surquillo", 2600, 2, 2, 80, 1, "Area de lavanderia", "Estacion Domingo Orue", "Estreno, cochera, cerca San Isidro"),
    ("Santiago de Surco", 1950, 3, 3, 110, 0, "Area de lavanderia", "Calle los Cedros 110", "Estreno piso 5 sin ascensor"),
    ("San Isidro", 2500, 1, 1, 45, 0, "Gimnasio", "Av. Rivera Navarrete 665, The Lead by Edifica", "Estreno, piso 4, balcon"),
    ("Lince", 3570, 3, 2, 100, 1, "Ascensor", "Calle Los Mirtos 590", "Edificio 33 pisos, piso 25"),
    ("San Isidro", 4200, 3, 3, 110, 2, "Area de lavanderia", "C. Virrey Toledo", "Impecable, 2 cocheras"),
    ("Barranco", 3200, 1, 2, 75, 1, "Seguridad", "Ca. Francisco Del Castillo", "Duplex amoblado doble altura"),
    ("San Isidro", 4522, 2, 2, 72, 1, "Ascensor", "Javier Prado con Rivera Navarrete", "Estreno, con cochera, 2 dorm"),
    ("Surquillo", 2700, 3, 2, 87, 0, "Cerca a colegios", "Calle Victor Alzamora 641", "Barrio Medico, sin amoblar"),
    ("Magdalena", 2975, 2, 2, 90, 1, "Seguridad", "Tomas Ramsey 883", "Semi amoblado, piso 12"),
    ("Barranco", 5100, 3, 3, 198, 2, "Area de lavanderia", "Jiron Las Mimosas", "Penthouse duplex, 2 cocheras"),
    ("Santiago de Surco", 4381, 3, 3, 164, 0, "Area de lavanderia", "Urb. Las Gardenias", "Duplex frente parque"),
    ("San Borja", 4500, 3, 3, 120, 2, "Bajo de precio", "Galeon 207, Chacarilla", "3 dorm, cerca parque"),
    ("Santiago de Surco", 3760, 2, 2, 95, 1, "Ascensor", "Av Caminos del Inca", "Estreno, Chacarilla, cochera+deposito"),
    # --- pagina 11 ---
    ("San Isidro", 2900, 1, 1, 45, 0, "Gimnasio", "Av. Gral. Felipe Salaverry 3590", "Estreno amoblado, cerca al malecon"),
    ("San Isidro", 3450, 1, 1, 46, 1, "Ascensor", "Calle Amador Merino Reyna 332", "Amoblado ejecutivo, cochera"),
    # --- pagina 12 ---
    ("San Isidro", 7300, 3, 2, 155, 2, "Area de lavanderia", "Calle Los Eucaliptos 600, Santa Rosa", "Vista al Golf, 2 cocheras"),
    ("Santiago de Surco", 4062, 3, 2, 140, 2, "Area de lavanderia", "Jiron Tambo Real 200, Huertos de San Antonio", "3er piso, remodelado, 2 cocheras"),
]


def gen_id(dire, precio, area):
    raw = f"{dire}|{precio}|{area}".lower()
    return "alq_" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def main():
    conn = sqlite3.connect(DB)
    conn.text_factory = str  # utf-8
    cur = conn.cursor()

    # 1) columna operacion
    cols = [r[1] for r in cur.execute("PRAGMA table_info(apartments)")]
    if "operacion" not in cols:
        cur.execute("ALTER TABLE apartments ADD COLUMN operacion TEXT")
        cur.execute("UPDATE apartments SET operacion='venta' WHERE operacion IS NULL")
        print("Columna 'operacion' anadida; filas existentes marcadas como 'venta'.")

    inserted, skipped = 0, 0
    for zona, precio, hab, ban, area, estac, badge, dire, desc in DATA:
        rid = gen_id(dire, precio, area)
        amen = badge
        if estac:
            amen = (amen + ",Estacionamiento") if amen else "Estacionamiento"
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
             FECHA, descripcion, "", "alquiler"),
        )
        inserted += 1

    conn.commit()

    print(f"\n=== CARGA ALQUILER ===")
    print(f"Listados en batch:  {len(DATA)}")
    print(f"Insertados:         {inserted}")
    print(f"Duplicados (id):    {skipped}")

    total = cur.execute("SELECT COUNT(*) FROM apartments").fetchone()[0]
    alq = cur.execute("SELECT COUNT(*) FROM apartments WHERE operacion='alquiler'").fetchone()[0]
    ven = cur.execute("SELECT COUNT(*) FROM apartments WHERE operacion='venta'").fetchone()[0]
    print(f"\nTotal en BD: {total}  (alquiler={alq}, venta={ven})")

    print("\n--- Alquiler por zona ---")
    for z, c, pmin, pmax in cur.execute(
        """SELECT zona, COUNT(*), MIN(precio), MAX(precio)
           FROM apartments WHERE operacion='alquiler'
           GROUP BY zona ORDER BY COUNT(*) DESC"""):
        print(f"  {z:<20} {c:>3} deptos   S/{pmin:>7,.0f} - S/{pmax:>7,.0f}")

    conn.close()


if __name__ == "__main__":
    main()
