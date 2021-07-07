import gmaps
import googlemaps
import pandas as pd
import pymongo
from main.scenarios.config import *

# ----------------------- GCloud configuration ----------------------
API_KEY = GC_APIKEY
gmaps.configure(api_key=API_KEY)
gmaps_services = googlemaps.Client(key=API_KEY)


# ---------------------- WareHouses Configuration -----------------
# Auxiliar function
def getFirstIfExists(response):
    if response:
        return response[0]
    else:
        return ""


warehouses_titles = """Polígono Industrial de la Pedrosa
Polígono Industrial Táctica
Polígono Industrial Camposol
Poligono Industrial La Negrilla
Santa María de Benquerencia (Polígono)
Parque Empresarial San Fernando de Henares
Centrolid
Polígono do Tambre
Polígono Industrial del Espíritu Santo Oviedo
Poligono nueva montaña
Poligono Industrial Sur Expacio Merida
Edificio Iwer
Poligono Industrial El Burgo De Ebro
OPCSA
Baleària Palma
Baleària Ceuta
Baleària Melilla""".split("\n")

warehouses = []
for i in warehouses_titles:
    warehouse_geolocation = gmaps_services.geocode(i + ", España")
    failed_to_geolocate = []
    if len(warehouse_geolocation) > 0:
        warehouse_geolocation = warehouse_geolocation[0]
        warehouse = {"name": i}
        try:
            warehouse["location"] = (warehouse_geolocation["geometry"]["location"]["lat"],
                                      warehouse_geolocation["geometry"]["location"]["lng"])
            warehouse["postal_code"] = getFirstIfExists(
                [x["long_name"] for x in warehouse_geolocation["address_components"] if "postal_code" in x["types"]])
            warehouse["city"] = getFirstIfExists(
                [x["long_name"] for x in warehouse_geolocation["address_components"] if "locality" in x["types"]])
            warehouse["province"] = getFirstIfExists(
                [x["long_name"] for x in warehouse_geolocation["address_components"] if
                 "administrative_area_level_2" in x["types"]])
            warehouse["community"] = getFirstIfExists(
                [x["long_name"] for x in warehouse_geolocation["address_components"] if
                 "administrative_area_level_1" in x["types"]])
            warehouses.append(warehouse)
        except:
            print("Fail in " + i)
    else:
        failed_to_geolocate.append(i)

# -------------- Truck float configuration -----------------------------
trucks_dataset = pd.DataFrame(
    {'name': ["euro82", "euro86", "euro90", "euro92", "jumbo", "mega", "hitch", "megahitch", "refrigerator", "warmer",
              "low_loader_platform", "open_platform"],
     'length': [1360, 1360, 1360, 1360, 1380, 1360, 1510, 1600, 1360, 1360, 1500, 1260],
     'width': [245, 245, 245, 245, 245, 245, 245, 245, 245, 245, 250, 250],
     'height': [245, 260, 270, 280, 300, 300, 295, 295, 260, 260, 370, 330],
     'volume': [82, 86, 90, 92, 96, 100, 110, 120, 86, 86, 0, 0],
     'tonnage': [22, 22, 22, 22, 22, 22, 25, 25, 20, 20, 25, 25],
     'n_wagon': [1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1],
     'refrigeration': [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]})
trucks_dataset["length"] = trucks_dataset.apply(lambda x: x.length * 10 / 1000, axis=1)
trucks_dataset["width"] = trucks_dataset.apply(lambda x: x.width * 10 / 1000, axis=1)
trucks_dataset["height"] = trucks_dataset.apply(lambda x: x.height * 10 / 1000, axis=1)
trucks_dataset["volume"] = trucks_dataset.apply(lambda x: x.length * x.width * x.height, axis=1)
trucks_dataset["tonnage"] = trucks_dataset.apply(lambda x: x.tonnage * 1000, axis=1)
trucks_dataset["dimensions"] = trucks_dataset.apply(
    lambda x: {"length": x.length, "width": x.width, "height": x.height}, axis=1)

# Lo que saca esta celda es lo que se va a meter en mongo
trucks_to_db = trucks_dataset.to_dict(orient='records')

# -------- Store common data in mongoDB ------------------------------

# Connect to database - Just important for the author
myclient = pymongo.MongoClient(mongoData["path"],
                               mongoData["username"],
                               mongoData["password"])

# Creamos la base de datos
db = myclient['SpainVRP']

# Creamos las colecciones dentro de la base de datos
warehouses_col = db['warehouses']
trucks_col = db['trucks']
packets_col = db['packets']

warehouses_col.insert_many(warehouses)
trucks_col.insert_many(trucks_to_db)
