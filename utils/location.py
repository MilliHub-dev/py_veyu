from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    # convert degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    lat = lat2 - lat1 # diff of latitudes
    lng = lon2 - lon1 # diff of longitudes

    a = (
        sin(lat / 2)**2 \
        + cos(lat1) * \
        cos(lat2) * \
        sin(lng / 2)**2
    )
    
    c = 2 * asin(sqrt(a))
    dist = 6371 * c # Radius of Earth in km * coord center
    return round(dist, 2) # return in 2 sf


