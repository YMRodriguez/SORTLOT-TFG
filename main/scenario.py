import gmaps
import googlemaps


# GCloud configuration
API_KEY = "AIzaSyCnCXg1vN3cOhY2cGPtC-tCkwbrrjUu6-Y"
gmaps.configure(api_key=API_KEY)
gmaps_services = googlemaps.Client(key = API_KEY)
