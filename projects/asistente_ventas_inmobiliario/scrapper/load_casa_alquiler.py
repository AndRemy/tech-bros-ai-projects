# -*- coding: utf-8 -*-
"""
Carga batch de CASAS EN ALQUILER (Urbania). Muchas de uso oficina/comercial.
- Agrega columna 'tipo' (departamento/casa) si no existe; backfill existentes='departamento'.
- operacion='alquiler', tipo='casa'. precio = renta mensual S/.
"""

import sqlite3
import hashlib

DB = "../data/real_estate.db"
FECHA = "2026-07-15"

# (zona, precio_S/, hab, ban, area, estac, badge, dir, desc)
DATA = [
    # pagina 1
    ("San Isidro", 27600, 7, 2, 443, 0, "Comercial", "Santa Luisa", "2 pisos esquina, ideal comercial/gastronomico"),
    ("Magdalena", 5000, 3, 2, 73, 0, "Comercial", "Jr. Rodolfo Rutte 115", "2 pisos, uso profesional/comercial"),
    ("San Isidro", 13260, 4, 4, 375, 0, "Area de lavanderia", "Calle Manuel Ugarte y Moscoso 1150, Orrantia", "Amoblada, corporativo, cerca Parque de la Pera"),
    ("Jesus Maria", 5500, 4, 3, 180, 2, "Comercial", "Jiron Mayta Capac", "2 pisos, ideal empresas/oficinas"),
    ("San Isidro", 18975, 6, 6, 670, 0, "Area de lavanderia", "Calle Baltazar La Torre 150, San Felipe", "Remodelada, vivienda/oficina"),
    ("Santiago de Surco", 20366, 4, 4, 680, 3, "Piscina", "jr Bellavista 2xx, Casuarinas", "Vista ciudad, Lutron, piscina"),
    ("San Isidro", 8500, 3, 2, 230, 0, "Area de lavanderia", "Alfredo salazar", "Townhouse, cerca Ovalo Gutierrez"),
    ("San Borja", 12806, 4, 4, 650, 2, "Area de lavanderia", "Jr. Tintoretto al 200", "2 pisos+azotea, cerca La Rambla"),
    ("Santiago de Surco", 20340, 4, 6, 1242, 3, "Piscina", "Urb Casuarinas, tranquera", "Niveles, vistas, Lutron, piscina"),
    ("San Isidro", 18975, 3, 3, 330, 0, "Area de lavanderia", "Pasaje El Aromito, El Olivar", "Ultra moderna, cerca al Olivar"),
    ("San Isidro", 12240, 10, 6, 536, 0, "Comercial", "Golondrinas", "2 plantas oficina, cerca Canaval y Moreyra"),
    ("Santiago de Surco", 9800, 3, 3, 500, 0, "Guardiania/Seguridad privada", "El Golf Los Incas, Los Granados", "Condominio, cerca U. de Lima, sauna"),
    ("San Isidro", 7777, 3, 2, 130, 0, "Area de lavanderia", "A 2 cuadras Country Club, Golf", "2 pisos, azotea terraza"),
    ("Santiago de Surco", 15000, 4, 4, 220, 0, "Parrilla", "Av. Morro Solar / Monterrico Sur", "Casa oficina/almacen"),
    ("San Borja", 23800, 4, 4, 640, 0, "Comercial", "Av. del Pinar 335", "3 niveles, residencial/corporativo"),
    ("Surquillo", 11939, 0, 0, 0, 2, "Comercial", "Los Faisanes, Limatambo", "Casa 3 pisos para oficinas, 14 ambientes"),
    ("San Isidro", 18950, 9, 7, 450, 0, "Cerca a colegios", "Pasaje Prescott", "2 pisos, 9 ambientes, oficinas"),
    ("San Borja", 6300, 3, 3, 243, 2, "Parrilla", "Los Recuerdos al 115, Chacarilla", "Town house 3 pisos, terraza parrilla"),
    ("Santiago de Surco", 18700, 6, 5, 340, 0, "Guardiania/Seguridad privada", "Avenida Caminos del Inca 700, Higuereta", "Comercial, piscina 20m3"),
    ("Santiago de Surco", 13520, 4, 3, 420, 0, "Piscina", "Jiron La Conquista 300, Monterrico", "Amoblada, condominio, 4 niveles"),
    ("Santiago de Surco", 7500, 6, 6, 401, 0, "Parrilla", "Jr. Irma Gamero de Planas 143, El Doral", "Frente parque, 3 niveles"),
    ("San Isidro", 12100, 3, 5, 284, 2, "Bajo de precio", "Parque la Pera", "Frente Parque de la Pera, 2 cocheras"),
    ("San Borja", 11900, 4, 2, 111, 0, "Area de lavanderia", "Av. Angamos Este, Juan XXIII", "Uso comercial, 4 hab"),
    ("San Isidro", 20010, 6, 5, 316, 3, "Comercial", "Av Petit Thouars", "Corporativa remodelada, 12 ambientes"),
    ("San Isidro", 11900, 4, 4, 339, 0, "Area de lavanderia", "Calle Paul de Beaudiez al 500", "Chalet en condominio 4 viviendas"),
    ("San Isidro", 13770, 3, 2, 215, 2, "Comercial", "Catalina Huanca 110", "Local comercial, restaurantes/showroom"),
    ("San Isidro", 8750, 3, 2, 200, 0, "Amoblado", "Calle Los Cisnes 100", "Amoblada, 3 plantas, remodelada"),
    ("San Isidro", 11108, 4, 3, 150, 0, "Area de lavanderia", "Calle Los Libertadores 401", "3 pisos, cerca Golf, vivienda/oficina"),
    ("San Isidro", 20400, 7, 6, 450, 3, "Area de lavanderia", "Calle Guillermo Marconi 340", "2 casas independientes, casa/oficina"),
    ("San Isidro", 11795, 4, 4, 154, 2, "Area de lavanderia", "Calle Paul de Beaudiez 500", "Condominio, 3 plantas, jacuzzi"),
    # pagina 2
    ("San Isidro", 44200, 0, 0, 1000, 4, "Comercial", "Av. Jorge Basadre al 300", "2 pisos, 990m2, multifamiliar/comercial"),
    ("Santiago de Surco", 25500, 0, 3, 612, 4, "Area de lavanderia", "Los Fresnos al 100", "Corporativa, 15 ambientes"),
    ("San Isidro", 19546, 6, 5, 465, 0, "Cerca a colegios", "Av. Jose Galvez Barrenechea 134, Corpac", "3 pisos, oficinas/consultorios"),
    ("San Borja", 15500, 5, 5, 612, 0, "Area de lavanderia", "Jiron, Monterrico Norte", "Oficina/geriatrico, 4 estac"),
    ("Santiago de Surco", 28026, 5, 6, 300, 0, "Area de lavanderia", "Calle Aldebaran / Los Alisos, Polo Hunt", "Corporativo 3 pisos, cerca Embajada"),
    ("Santiago de Surco", 4420, 2, 1, 130, 0, "Cerca a colegios", "Av. Coronel Reynaldo Vivanco 637, Chacarilla", "Condominio, terraza jardin"),
    ("Santiago de Surco", 12950, 3, 3, 324, 0, "Piscina", "Calle Tomasal", "Condominio Britanico, piscina"),
    ("San Isidro", 25500, 3, 4, 640, 0, "Seguridad", "Calle Roma", "Residencia 640m2, ideal embajada"),
    ("San Isidro", 23000, 6, 4, 730, 4, "Guardiania/Seguridad privada", "Tomas Edison xxxx, Orrantia", "2 plantas, ideal embajada"),
    ("San Isidro", 23814, 9, 6, 343, 0, "Area de lavanderia", "Av. 2 de Mayo", "8 ambientes, oficina/cafeteria"),
    ("San Borja", 10250, 4, 3, 500, 0, "Parrilla", "Calle Jacinto Guerrero, Las Magnolias", "Jardin interior, cerca Caminos del Inca"),
    ("San Borja", 26900, 11, 4, 360, 0, "Area de lavanderia", "Av. Aviacion", "Comercial, 3 niveles"),
    ("San Isidro", 8200, 7, 4, 204, 0, "Comercial", "Calle Baltazar La Torre", "Oficina comercial, zonif RDB"),
    ("Santiago de Surco", 11220, 7, 6, 234, 0, "Parrilla", "Jiron El Galeon 231", "Oficinas/empresas, terraza bar"),
    ("San Isidro", 6800, 3, 4, 300, 0, "Cerca a colegios", "Calle Manuel Ugarte y Moscoso", "2 pisos, chalet 4 casas"),
    ("Santiago de Surco", 6200, 4, 4, 190, 0, "Parrilla", "Av La Encalada 1471", "Remodelada, condominio, cerca El Polo"),
    ("Santiago de Surco", 7140, 3, 2, 350, 1, "Cerca a colegios", "Marcona, Higuereta", "Duplex remodelado"),
    ("San Isidro", 33400, 3, 4, 431, 4, "Area de lavanderia", "El Olivar", "Remodelada, ascensor interno, piscina"),
    ("Santiago de Surco", 20700, 4, 5, 1420, 0, "Piscina", "Jiron Bellavista, Casuarinas Sur", "Doble altura, piscina"),
    ("Santiago de Surco", 23000, 3, 3, 284, 0, "Cerca a colegios", "Av. caminos del inca 1153", "Local 10m frente, comercial"),
    ("Santiago de Surco", 7500, 3, 4, 187, 2, "Parrilla", "Valle Hermoso, una planta", "Una planta, accesible discapacidad"),
    ("Santiago de Surco", 7119, 3, 2, 146, 2, "Area de lavanderia", "Calle Batallon Tarma 143", "3 plantas, impecable"),
    ("Magdalena", 7000, 4, 2, 92, 0, "Comercial", "Jr. Felix Dibos 125", "2 niveles+azotea, vivienda/oficina"),
    ("Santiago de Surco", 9633, 3, 3, 480, 2, "Guardiania/Seguridad privada", "Avenida Golfs los incas S/N", "Condominio Golfs Los Incas, sauna"),
    ("Magdalena", 5000, 3, 1, 120, 1, "Comercial", "Rodolfo Rutte 100, Orrantia del Mar", "Casa oficina, cerca Javier Prado"),
    ("Santiago de Surco", 9000, 3, 3, 330, 2, "Comercial", "Jr. el Cortijo 390, Monterrico", "Al costado Embajada EEUU, jardin"),
    ("Santiago de Surco", 27600, 4, 3, 650, 0, "Parrilla", "Av. del Pinar, Chacarilla", "2 pisos, piscina, parrilla"),
    ("San Isidro", 27600, 4, 4, 482, 4, "Piscina", "Frente Parque Acosta", "Remodelada, piscina, parrilla"),
    ("San Miguel", 5000, 3, 1, 200, 2, "Area de lavanderia", "Pedrerias", "Amoblada, residencial centrica"),
    # pagina 3
    ("Surquillo", 6200, 5, 3, 150, 1, "Guardiania/Seguridad privada", "codornices xxx, Limatambo", "2 pisos, empresas, cerca Aramburu"),
    ("San Miguel", 5800, 2, 2, 113, 0, "Cerca a colegios", "Av. Rafael Escardo 740", "Comercial, zonif CV"),
    ("Santiago de Surco", 10509, 5, 8, 185, 0, "Reservado", "Av. Monterrico Chico, Santa Teresa", "Condominio 8 casas, 3 niveles"),
    ("San Isidro", 10140, 5, 4, 440, 0, "Area de lavanderia", "Av. Gral. Salaverry, Santa Rosa", "2 pisos, comercial/vivienda"),
    ("Magdalena", 12500, 5, 0, 250, 5, "Cerca a colegios", "Rodolfo rutte 400, Jacaranda", "Local, deposito/oficinas"),
    ("San Isidro", 16750, 5, 4, 378, 2, "Guardiania/Seguridad privada", "General la Fuente 199, Orrantia", "Remodelada, esquina"),
    ("San Borja", 11500, 4, 3, 700, 3, "Reservado", "calle Trinidad 200", "Una planta, cerca Pentagonito"),
    ("Santiago de Surco", 18008, 0, 0, 640, 0, "Comercial", "Jr. Venegas Fundo Parque Alto 800", "Almacen 531m2, logistica"),
    ("San Isidro", 13560, 3, 2, 333, 3, "Area de lavanderia", "Calle Dellepiani 749, Orrantia del Mar", "Remodelada, cerca malecon"),
    ("San Isidro", 17000, 10, 4, 375, 0, "Area de lavanderia", "Corpac", "Esquina, vivienda/oficina"),
    ("San Isidro", 30400, 3, 3, 900, 4, "Parrilla", "Manuel Salazar 1", "Esquina, piscina, nueva"),
    ("Santiago de Surco", 23310, 4, 4, 1600, 0, "Area de lavanderia", "Calle Los Molles, Casuarinas", "1650m2 terreno, vista ciudad, piscina"),
    ("San Isidro", 8500, 8, 3, 197, 3, "Comercial", "Mariano de los Santos al 100", "Oficina corporativa, 2 pisos"),
    ("San Isidro", 28900, 4, 4, 300, 4, "Parrilla", "Calle Alvarez Calderon N 7xx", "3 plantas, piscina"),
    ("San Isidro", 13600, 10, 3, 375, 0, "Area de lavanderia", "Los Petirrojos 495", "Esquina, vivienda/oficinas"),
    ("Jesus Maria", 36000, 15, 7, 783, 8, "Area de lavanderia", "Calle Ribero de Ustaris 2XX", "Oficina implementada, 2 pisos"),
    ("San Isidro", 23500, 21, 8, 950, 7, "Ascensor", "Av Pablo Carriquiry 250", "Oficina 3 pisos, frente parque"),
    ("San Isidro", 27120, 3, 2, 443, 2, "Area de lavanderia", "Calle Santa Luisa 2XX", "2 niveles, jardin, zona comercial"),
    ("Barranco", 5440, 3, 3, 172, 2, "Area de lavanderia", "Jiron Lima al 600", "Vivienda/negocio, cerca Plaza Butters"),
    ("Magdalena", 13000, 9, 6, 325, 0, "Comercial", "Jiron Grau al 200", "Comercial remodelada, 3 niveles"),
    ("Santiago de Surco", 11220, 3, 3, 400, 2, "Cerca a colegios", "LOS CENTINELAS 1XX, Casuarinas", "Condominio, vista panoramica"),
    ("Santiago de Surco", 33500, 4, 5, 600, 2, "Guardiania/Seguridad privada", "Av El Cortijo N 2, Los Granados", "Una planta, piscina, cerca ULima"),
    ("San Isidro", 12950, 7, 5, 426, 4, "Area de lavanderia", "Raymundo Morales de la Torre", "3 niveles, cerca Olivar"),
    ("San Isidro", 62134, 4, 4, 783, 4, "Seguridad", "Pezet al 100, Golf", "Penthouse 783m2, piscina privada"),
    ("San Isidro", 15300, 7, 6, 375, 3, "Area de lavanderia", "Av Jose Galvez Barrenechea, Corpac", "650m2, vivienda"),
    ("Santiago de Surco", 22035, 3, 5, 1080, 0, "Guardiania/Seguridad privada", "Jiron Las Morenas, Camacho", "Una planta, piscina, cerca Roosevelt"),
    ("San Isidro", 36260, 4, 4, 915, 4, "Area de lavanderia", "Calle Octavio Espinosa 1, San Gabriel", "Nueva, piscina, 600m2 AC"),
    ("San Isidro", 12276, 6, 4, 380, 0, "Seguridad", "Calle dos, Corpac", "Cerca clinica Ricardo Palma, familia grande"),
    # pagina 4
    ("Magdalena", 10200, 7, 5, 400, 1, "Comercial", "Jiron Rodolfo Rutte 724", "3 niveles, oficinas/consultorios/vivienda"),
    ("San Borja", 18000, 3, 3, 251, 2, "Area de lavanderia", "Jr. alejandro Scarlatti al 100", "Comercial/vivienda, vista parque"),
    ("San Borja", 7500, 5, 6, 255, 1, "Area de lavanderia", "Calle Las Letras 395", "4 niveles, cerca La Rambla"),
    ("San Isidro", 32300, 4, 4, 600, 0, "Comercial", "Calle Alvarez Calderon al 700", "Lujo, arq. Mario Lara, 3 niveles+sotano"),
    ("San Isidro", 20340, 5, 4, 300, 0, "Cerca a colegios", "Calle Los Libertadores", "Oficinas, jardin y sotano"),
    ("San Borja", 10695, 7, 6, 224, 0, "Area de lavanderia", "Av. San Borja Nte.", "3 pisos, familia/oficinas"),
    ("San Isidro", 12900, 4, 3, 576, 2, "Parrilla", "Calle Los Cedros", "Cerca Golf, remodelada"),
    ("Santiago de Surco", 8800, 5, 4, 500, 4, "Area de lavanderia", "Calle Los Cipreses 1, Valle Hermoso", "Calle cerrada, jardines"),
    ("Santiago de Surco", 9576, 3, 3, 600, 2, "Area de lavanderia", "Avenida Golf Los Incas 300", "Condominio privado, mascotas ok"),
    ("San Isidro", 14280, 5, 4, 572, 1, "Area de lavanderia", "Urbanizacion Corpac", "3 pisos, vivienda/negocio"),
    ("San Isidro", 24150, 4, 0, 1477, 4, "Area de lavanderia", "Nogales 720", "Casona remodelada, piscina, diplomaticos"),
    ("Santiago de Surco", 8875, 6, 5, 350, 2, "Parrilla", "Castilla La Vieja 175, La Castellana", "Frente parque, cerco electrico"),
    ("Santiago de Surco", 16800, 3, 2, 160, 2, "Parrilla", "Pucala", "2 pisos, vivienda/comercial"),
    ("San Isidro", 22200, 4, 4, 314, 3, "Guardiania/Seguridad privada", "Paul Harris al 400", "Cerca Golf, 2 niveles"),
    ("San Isidro", 25181, 10, 5, 467, 0, "Comercial", "Avenida Pablo Carriquiry", "Oficinas, 826m2, sotano"),
    ("Jesus Maria", 26960, 10, 4, 526, 8, "Seguridad", "Calle Caracas N22xx", "Oficina, 3 pisos, 8 autos"),
    ("San Isidro", 36500, 4, 3, 474, 4, "Seguridad", "Calle Lord Cochrane 1XX", "Embajada/ONG, 3 pisos+sotano"),
    ("Barranco", 4080, 3, 2, 126, 0, "Area de lavanderia", "Av. Almirante Miguel Grau al 103", "Chalet duplex en condominio"),
    ("Jesus Maria", 10500, 4, 1, 160, 0, "Area de lavanderia", "Mariscal Toribio Luzuriaga 623", "Casa comercial, oficinas"),
    ("Santiago de Surco", 10000, 8, 3, 250, 2, "Area de lavanderia", "Mariscal Ramon Castilla al 300", "Local comercial 3 pisos, limite Miraflores"),
    ("San Isidro", 20400, 14, 6, 210, 0, "Gimnasio", "Calle Los Libertadores", "Oficinas/vivienda, zonif CZ"),
    ("Magdalena", 10000, 5, 3, 136, 0, "Guardiania/Seguridad privada", "Jiron Domingo Ponte, Oyague", "Casa oficina empresarial, 4 niveles"),
    ("San Isidro", 34000, 7, 7, 923, 0, "Area de lavanderia", "Clemente X", "Para remodelar, ideal embajadas"),
    ("Santiago de Surco", 11832, 4, 4, 385, 0, "Area de lavanderia", "Casuarinas", "Townhouse amoblado, 4 niveles"),
    ("San Isidro", 69000, 7, 3, 1000, 5, "Cerca a colegios", "AV. Arequipa cuadra 26", "Corporativa 1000m2, clasica"),
    ("Santiago de Surco", 10170, 7, 6, 464, 0, "Comercial", "Las Caobas 191", "7 suites, residencial, frente Jockey"),
    ("Santiago de Surco", 11900, 5, 4, 265, 1, "Comercial", "Maria Luisa 141", "50 anos, 5 suites, para renovar"),
    ("San Isidro", 27200, 5, 5, 600, 3, "Piscina", "Guardia Civil Corpac", "700m2, piscina, comercial"),
    # pagina 5
    ("San Isidro", 64500, 0, 10, 1450, 8, "Comercial", "Javier Prado Oeste Cdra 16", "Oficina, 1000m2 terreno, remodelada"),
    ("Santiago de Surco", 21395, 4, 3, 500, 4, "Area de lavanderia", "Batallon Libres de Trujillo 2, Chacarilla", "Una planta, piscina"),
    ("Magdalena", 6000, 3, 3, 90, 0, "Cerca a colegios", "Jr. Trujillo", "3 niveles, familias/profesionales"),
    ("Barranco", 5550, 3, 2, 180, 0, "Amoblado", "Avenida Saenz Pena 103", "Amoblada, patrimonio UNESCO, jardin"),
    ("Santiago de Surco", 7525, 5, 4, 160, 1, "Area de lavanderia", "Calle Kandinsky 234, Vipep", "7 ambientes, limite Surquillo"),
    ("Barranco", 8200, 5, 3, 300, 3, "Seguridad", "Pedro de Osma 411", "Moderna, condominio, 3 terrazas"),
    ("San Borja", 8450, 5, 3, 230, 2, "Area de lavanderia", "Tiziano 118", "3 pisos, cerca La Rambla"),
    ("San Isidro", 26800, 4, 4, 483, 4, "Cerca a colegios", "C. Jose de Acosta", "Remodelada, frente parque, piscina"),
    ("Santiago de Surco", 22490, 5, 4, 2900, 0, "Piscina", "Calle Los Molles, Casuarinas", "Vista panoramica, piscina"),
    ("San Isidro", 13600, 3, 4, 338, 2, "Reservado", "Calle Las Garzas 475", "Corpac, vivienda/oficina"),
    ("San Isidro", 22425, 6, 5, 390, 4, "Area de lavanderia", "Av Alberto del Campo 176", "Amoblada, 3 plantas"),
    ("San Isidro", 42600, 1, 0, 1312, 4, "Guardiania/Seguridad privada", "Calle Tomas Edison", "1312m2, vivienda/oficina"),
    ("Santiago de Surco", 19800, 14, 8, 440, 6, "Area de lavanderia", "Francisco de Cuellar 201, Las Flores de Monterrico", "Empresas/mineras/oficinas"),
    ("San Borja", 5000, 4, 3, 320, 0, "Area de lavanderia", "Calle Redond", "Esquina, vivienda/uso mixto"),
    ("San Isidro", 21775, 5, 3, 320, 2, "Area de lavanderia", "Calle Paul Harris, Golf", "Cerca Golf, zona parques"),
    ("San Isidro", 67000, 6, 4, 1298, 12, "Gimnasio", "Calle Anchorena", "Moderna, jardines, piscina, embajadas"),
    ("Santiago de Surco", 9492, 3, 3, 500, 2, "Comercial", "Golf Los Incas", "Condominio, antigua bien cuidada"),
    ("Santiago de Surco", 10200, 4, 4, 220, 2, "Cerca a colegios", "Jr. Oceano Artico cuadra 3, Santa Constanza", "Frente Jockey Plaza"),
    ("Jesus Maria", 5500, 3, 3, 115, 1, "Area de lavanderia", "Arnaldo Marquez al 2300", "Chalet 2 pisos, jardin"),
    ("San Isidro", 13908, 6, 2, 400, 3, "Area de lavanderia", "Avenida Aramburu 3", "Local comercial, licencia restaurante"),
    ("San Isidro", 16800, 5, 4, 378, 3, "Parrilla", "San Isidro esquina", "Esquina, impecable"),
    ("Santiago de Surco", 8575, 3, 3, 243, 2, "Cerca a colegios", "CALLE ORION S/N, Los Granados", "Condominio, cerca U. de Lima"),
    ("San Borja", 7000, 4, 2, 348, 0, "Area de lavanderia", "AVOGADRO", "Chalet 4 pisos"),
    ("San Isidro", 72645, 0, 11, 1645, 7, "Comercial", "Javier Prado Oeste Cdra 16 Esquina", "Oficina esquina, 1461m2 terreno"),
    ("Santiago de Surco", 6100, 3, 2, 200, 1, "Frente a parque", "Calle Gerona 451", "2 niveles, jardin privado"),
    ("San Isidro", 17536, 5, 0, 640, 8, "Comercial", "Octavio Espinosa al 100", "En obra, 640m2"),
    ("Santiago de Surco", 9900, 3, 4, 279, 0, "Frente a parque", "Simon Salguero", "Amoblada, frente parque, limite Miraflores"),
    ("Santiago de Surco", 8270, 10, 4, 163, 12, "Ascensor", "Jiron Morro Solar N 10 Piso 9", "Oficina flat implementada (precio USD*3.5)"),
    # pagina 6 (nuevas)
    ("Santiago de Surco", 11725, 4, 8, 440, 0, "Comercial", "Francisco de Cuellar 201, primer piso", "Primer piso, oficinas, cerca Av. Polo"),
    ("San Isidro", 5780, 3, 4, 200, 0, "Bajo de precio", "Calle Ricardo Angulo", "3 niveles, familias"),
    ("San Borja", 4400, 2, 2, 200, 0, "Area de lavanderia", "Fray Luis De Leon 1026", "Solo 1er piso, oficina"),
    ("Santiago de Surco", 8500, 4, 3, 232, 1, "Amoblado", "Ps La Castellana con Hermanos Quintero", "Amoblada, jardin interior"),
    ("San Borja", 17150, 5, 4, 600, 3, "Area de lavanderia", "Beethoven S/N", "5 dorm, vivienda/oficina"),
    ("Santiago de Surco", 10000, 9, 6, 0, 4, "Comercial", "Av. Central 128 / Aster", "9 suites"),
    ("Santiago de Surco", 25666, 4, 6, 1030, 0, "Area de lavanderia", "Jiron Las Laderas, Casuarinas", "Estilo campestre, piscina"),
    ("San Borja", 15500, 7, 4, 600, 3, "Area de lavanderia", "jockey plaza, Monterrico Norte", "Frente Jockey, mezzanine"),
    ("Santiago de Surco", 22200, 4, 4, 1000, 12, "Parrilla", "Jiron Francisco Cuellar 3, Las Flores de Monterrico", "Una planta, piscina, 4884m2 terreno"),
    ("San Isidro", 17250, 4, 3, 378, 2, "Area de lavanderia", "Calle General La Fuente", "Esquina, jardin, terraza"),
    ("San Isidro", 12882, 5, 3, 250, 2, "Frente a parque", "Calle Carolina Vargas de Vargas", "Amoblada, vista al Olivar"),
]


def gen_id(dire, precio, area):
    raw = f"{dire}|{precio}|{area}".lower()
    return "cas_" + hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def main():
    conn = sqlite3.connect(DB)
    conn.text_factory = str
    cur = conn.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(apartments)")]
    if "tipo" not in cols:
        cur.execute("ALTER TABLE apartments ADD COLUMN tipo TEXT")
        cur.execute("UPDATE apartments SET tipo='departamento' WHERE tipo IS NULL")
        print("Columna 'tipo' anadida; filas existentes marcadas como 'departamento'.")

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
             FECHA, descripcion, "", "alquiler", "casa"),
        )
        inserted += 1

    conn.commit()

    print("=== CARGA CASA ALQUILER ===")
    print(f"Listados en batch:  {len(DATA)}")
    print(f"Insertados:         {inserted}")
    print(f"Duplicados (id):    {skipped}")

    total = cur.execute("SELECT COUNT(*) FROM apartments").fetchone()[0]
    print(f"\nTotal en BD: {total}")
    print("Por tipo x operacion:")
    for t, o, c in cur.execute(
        "SELECT tipo, operacion, COUNT(*) FROM apartments GROUP BY tipo, operacion ORDER BY tipo, operacion"):
        print(f"  {t:<13} {o:<10} {c}")

    print("\n--- Casa alquiler por zona ---")
    for z, c, pmin, pmax in cur.execute(
        """SELECT zona, COUNT(*), MIN(precio), MAX(precio)
           FROM apartments WHERE tipo='casa'
           GROUP BY zona ORDER BY COUNT(*) DESC"""):
        print(f"  {z:<20} {c:>3}   S/{pmin:>7,.0f} - S/{pmax:>8,.0f}")

    conn.close()


if __name__ == "__main__":
    main()
