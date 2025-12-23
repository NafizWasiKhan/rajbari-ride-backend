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

def calculate_fare(distance_km, base_fare=50.0, per_km_rate=20.0, per_minute_rate=2.0, duration_minutes=0):
    """
    Calculate fare based on distance and duration with configurable rates.
    """
    from decimal import Decimal
    
    # Ensure inputs are Decimal for precise currency calculation
    distance_km = Decimal(str(distance_km))
    duration_minutes = Decimal(str(duration_minutes))
    
    # Rates might be float if defaults are used, but typically Decimal from model
    base_fare = Decimal(str(base_fare))
    per_km_rate = Decimal(str(per_km_rate))
    per_minute_rate = Decimal(str(per_minute_rate))

    fare = base_fare + (distance_km * per_km_rate) + (duration_minutes * per_minute_rate)
    return round(fare, 2)

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
