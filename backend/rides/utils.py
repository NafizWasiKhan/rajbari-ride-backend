import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles.
    return c * r

def calculate_fare(distance_km, base_fare=0, per_km_rate=10, per_minute_rate=0, duration_minutes=0):
    """
    Calculate ride fare based on distance.
    Default: 10 BDT per kilometer (integer).
    User can negotiate a different fare later.
    """
    # Simple calculation: base fare + (distance * rate per km)
    # Default for Rajbari Ride: 10 BDT/km with no base fare
    fare = base_fare + (distance_km * per_km_rate)
    
    # Return as integer (round to nearest BDT)
    return int(round(fare))


def is_valid_coordinate(lat, lng):
    """Checks if coordinates are within reasonable global limits."""
    return -90 <= lat <= 90 and -180 <= lng <= 180

def is_within_bangladesh(lat, lng):
    """
    Checks if a point is within the Bangladesh national boundary.
    Using a simplified bounding box for the backend validation.
    Rough Bangladesh Bounding Box: 
    Lat: 20.50 to 26.50
    Lng: 88.00 to 92.70
    """
    return 20.50 <= lat <= 26.50 and 88.00 <= lng <= 92.70
