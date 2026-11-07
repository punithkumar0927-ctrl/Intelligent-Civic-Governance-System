'''ai_engine/geographic_intelligence/distance_calculator.py
Distance utilities: Haversine, Vincenty, grid-based approximations.'''
import math
from typing import Optional

R_EARTH_KM = 6371.0
R_EARTH_M  = 6371000.0

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)
    return R_EARTH_KM * 2 * math.asin(math.sqrt(a))

def haversine_m(lat1, lon1, lat2, lon2) -> float:
    return haversine_km(lat1, lon1, lat2, lon2) * 1000

def vincenty_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    a_axis = 6378137.0; b_axis = 6356752.314245; f = 1/298.257223563
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1-f) * math.tan(math.radians(lat1)))
    U2 = math.atan((1-f) * math.tan(math.radians(lat2)))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sinU2, cosU2 = math.sin(U2), math.cos(U2)
    lam = L
    for _ in range(100):
        sin_lam = math.sin(lam); cos_lam = math.cos(lam)
        sin_sigma = math.sqrt((cosU2*sin_lam)**2 + (cosU1*sinU2-sinU1*cosU2*cos_lam)**2)
        if sin_sigma == 0: return 0.0
        cos_sigma = sinU1*sinU2 + cosU1*cosU2*cos_lam
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cosU1*cosU2*sin_lam / sin_sigma
        cos2_alpha = 1 - sin_alpha**2
        if cos2_alpha == 0: cos_2sigma_m = 0
        else: cos_2sigma_m = cos_sigma - 2*sinU1*sinU2/cos2_alpha
        C = f/16 * cos2_alpha * (4 + f*(4 - 3*cos2_alpha))
        lam_prev = lam
        lam = L + (1-C)*f*sin_alpha*(sigma + C*sin_sigma*(cos_2sigma_m + C*cos_sigma*(-1 + 2*cos_2sigma_m**2)))
        if abs(lam - lam_prev) < 1e-12: break
    u2 = cos2_alpha * (a_axis**2 - b_axis**2) / b_axis**2
    A_coeff = 1 + u2/16384 * (4096 + u2*(-768 + u2*(320 - 175*u2)))
    B_coeff = u2/1024 * (256 + u2*(-128 + u2*(74 - 47*u2)))
    delta_sigma = B_coeff*sin_sigma*(cos_2sigma_m + B_coeff/4*(cos_sigma*(-1+2*cos_2sigma_m**2) - B_coeff/6*cos_2sigma_m*(-3+4*sin_sigma**2)*(-3+4*cos_2sigma_m**2)))
    s = b_axis * A_coeff * (sigma - delta_sigma)
    return s / 1000.0

def grid_distance_km(lat1, lon1, lat2, lon2) -> float:
    import numpy as np
    return float(np.linalg.norm(np.array([lat1, lon1]) - np.array([lat2, lon2])) * 111.32)

def nearest_point(query_lat: float, query_lon: float,
                  points: list[tuple[float, float]], top_k: int = 5) -> list[int]:
    indexed = [(i, haversine_km(query_lat, query_lon, p[0], p[1])) for i, p in enumerate(points)]
    return [i for i, _ in sorted(indexed, key=lambda x: x[1])[:top_k]]
