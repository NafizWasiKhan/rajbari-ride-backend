from django.contrib.auth.models import User
from .utils import calculate_distance

def find_nearest_driver(ride):
    """
    Finds the nearest online driver who hasn't rejected this ride.
    """
    pickup_lat = float(ride.pickup_lat)
    pickup_lng = float(ride.pickup_lng)
    
    # Filter drivers
    drivers = User.objects.filter(
        profile__role='DRIVER',
        profile__is_online=True,
        profile__current_lat__isnull=False,
        profile__current_lng__isnull=False
    ).exclude(rejected_rides=ride) # Exclude drivers who rejected this ride
    
    nearest_driver = None
    min_dist = float('inf')
    
    for driver in drivers:
        dist = calculate_distance(
            pickup_lat, pickup_lng, 
            float(driver.profile.current_lat), 
            float(driver.profile.current_lng)
        )
        if dist < min_dist:
            min_dist = dist
            nearest_driver = driver
            
    return nearest_driver
