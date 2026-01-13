from typing import Optional, Tuple
from geopy.geocoders import Nominatim
import logging
import time
import random
import hashlib

logger = logging.getLogger(__name__)

# City-level coordinates with city bounds (lat/lon variations)
GEOCODING_CACHE: dict[str, Tuple[float, float]] = {
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050),
    "madrid": (40.4168, -3.7038),
    "barcelona": (41.3851, 2.1734),
    "amsterdam": (52.3676, 4.9041),
    "lisbon": (38.7223, -9.1393),
    "milan": (45.4642, 9.1900),
    "rome": (41.9028, 12.4964),
    "vienna": (48.2082, 16.3738),
    "prague": (50.0755, 14.4378),
    "warsaw": (52.2297, 21.0122),
    "budapest": (47.4979, 19.0402),
    "athens": (37.9838, 23.7275),
    "istanbul": (41.0082, 28.9784),
    "sofia": (42.6977, 23.3219),
}

# City bounds for jittering (lat_variance, lon_variance in degrees)
# These are approximate city extents to scatter workshops realistically
CITY_BOUNDS: dict[str, Tuple[float, float]] = {
    "london": (0.15, 0.25),
    "paris": (0.1, 0.15),
    "berlin": (0.12, 0.15),
    "madrid": (0.08, 0.12),
    "barcelona": (0.08, 0.12),
    "amsterdam": (0.08, 0.12),
    "lisbon": (0.08, 0.12),
    "rome": (0.06, 0.08),
    "vienna": (0.08, 0.1),
    "prague": (0.08, 0.1),
    "warsaw": (0.12, 0.15),
    "budapest": (0.08, 0.1),
    "athens": (0.08, 0.1),
    "istanbul": (0.15, 0.25),
    "sofia": (0.1, 0.12),
}

# Cache for workshop-level geocoding (location + city)
WORKSHOP_GEOCODING_CACHE: dict[str, Tuple[float, float]] = {}

# Initialize geocoder (Nominatim - free, no API key needed)
geolocator = Nominatim(user_agent="dance-app-recommender")


def get_city_coordinates(city_name: str) -> Optional[Tuple[float, float]]:
    """Get lat/lon coordinates for a city. Tries cache first, then Nominatim API."""
    city_lower = city_name.lower().strip()

    # Check cache first
    if city_lower in GEOCODING_CACHE:
        return GEOCODING_CACHE[city_lower]

    # Try API if not cached
    try:
        location = geolocator.geocode(city_name + ", Europe")
        if location:
            coords = (location.latitude, location.longitude)
            GEOCODING_CACHE[city_lower] = coords  # Cache for future use
            return coords
    except Exception as e:
        logger.warning(f"Geocoding failed for {city_name}: {e}")

    return None


def _jitter_coordinates(lat: float, lon: float, location: str, city: str) -> Tuple[float, float]:
    """
    Add deterministic jitter to coordinates based on location + city hash.
    This ensures the same location always gets the same offset (deterministic but varied).
    """
    # Get city bounds
    bounds = CITY_BOUNDS.get(city.lower(), (0.1, 0.1))
    lat_variance, lon_variance = bounds

    # Create a hash from location + city to get deterministic random values
    hash_input = f"{location.lower().strip()}|{city.lower().strip()}"
    hash_obj = hashlib.md5(hash_input.encode())
    hash_bytes = hash_obj.digest()

    # Convert hash bytes to deterministic random values between -1 and 1
    lat_offset = ((hash_bytes[0] / 255.0) * 2 - 1) * lat_variance
    lon_offset = ((hash_bytes[1] / 255.0) * 2 - 1) * lon_variance

    return (lat + lat_offset, lon + lon_offset)


def get_workshop_coordinates(location: str, city: str) -> Optional[Tuple[float, float]]:
    """
    Get precise coordinates for a workshop by:
    1. Trying street-level geocoding (location + city)
    2. If that fails, use city coordinates with deterministic jitter

    This ensures workshops in the same city show at different points on the map.
    Results are cached to avoid repeated API calls.
    """
    # Create cache key
    cache_key = f"{location.lower().strip()}|{city.lower().strip()}"

    # Check workshop cache first
    if cache_key in WORKSHOP_GEOCODING_CACHE:
        return WORKSHOP_GEOCODING_CACHE[cache_key]

    # Try street-level geocoding with full address
    try:
        full_address = f"{location}, {city}, Europe"
        location_obj = geolocator.geocode(full_address, timeout=5)

        if location_obj:
            coords = (location_obj.latitude, location_obj.longitude)
            WORKSHOP_GEOCODING_CACHE[cache_key] = coords
            logger.info(f"✅ Street-level geocoded: {location}, {city} -> {coords}")
            time.sleep(0.1)  # Be nice to Nominatim API
            return coords
    except Exception as e:
        logger.debug(f"Street-level geocoding failed for {location}, {city}: {e}")

    # Fallback: Use city coordinates with jitter
    city_coords = get_city_coordinates(city)
    if city_coords:
        jittered = _jitter_coordinates(city_coords[0], city_coords[1], location, city)
        WORKSHOP_GEOCODING_CACHE[cache_key] = jittered
        logger.info(f"⚠️  Using city coords with jitter: {location}, {city} -> {jittered}")
        return jittered

    return None


def geocode_workshop(city: str) -> Optional[dict]:
    """Geocode a workshop location. Returns dict with lat/lon or None if city not found."""
    coords = get_city_coordinates(city)
    if coords:
        return {"lat": coords[0], "lon": coords[1]}
    return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    from math import radians, cos, sin, asin, sqrt

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

