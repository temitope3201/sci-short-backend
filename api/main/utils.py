from geopy.geocoders import Nominatim
import requests


geolocator = Nominatim(user_agent='geoapiExercises')


def get_location(ip_address):
   
    response = requests.get(f'http://ip-api.com/json/{ip_address}')
    data = response.json()

    if data['status'] == 'success':
        latitude = data['lat']
        longitude = data['lon']

        location = geolocator.reverse((latitude, longitude))
        return str(location)

    return 'Unknown'