import os
import logging
import asyncio
from typing import List, Dict, Any

import googlemaps

logger = logging.getLogger(__name__)

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))


async def get_nearby_hospitals(
    lat: float,
    lng: float,
    radius: int = 5000,
    max_results: int = 15,
) -> List[Dict[str, Any]]:
    """
    Find nearby hospitals using Google Places API.
    Runs blocking gmaps calls in a thread so FastAPI event loop is not blocked.
    """
    try:
        location = (lat, lng)
        logger.info(f"Searching for hospitals near ({lat}, {lng})")

        places_result = await asyncio.to_thread(
            gmaps.places_nearby,
            location=location,
            radius=radius,
            type="hospital",
            keyword="hospital clinic medical",
        )

        hospitals: List[Dict[str, Any]] = []

        for place in places_result.get("results", [])[:max_results]:
            try:
                hospital_data: Dict[str, Any] = {
                    "name": place.get("name", "Unknown"),
                    "location": {
                        "lat": place["geometry"]["location"]["lat"],
                        "lng": place["geometry"]["location"]["lng"],
                    },
                    "rating": place.get("rating"),
                    "address": place.get("vicinity", "Address not available"),
                    # Phone is not provided by places_nearby; would require a separate place details call
                    "phone": None,
                    "types": place.get("types", []),
                    "open_now": place.get("opening_hours", {}).get("open_now"),
                    "place_id": place.get("place_id"),
                }

                hospitals.append(hospital_data)

            except Exception as inner_e:
                logger.warning(f"Error processing place: {inner_e}")
                continue

        logger.info(f"Found {len(hospitals)} hospitals")

        # Sort by rating (highest first, treat None as 0)
        hospitals.sort(
            key=lambda x: x["rating"] if x.get("rating") is not None else 0,
            reverse=True,
        )

        return hospitals

    except Exception as e:
        logger.error(f"Error fetching hospitals: {e}")
        return []


async def get_place_details(place_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a place from Google Places API.
    """
    try:
        details = await asyncio.to_thread(gmaps.place, place_id=place_id)
        result = details.get("result", {})

        return {
            "name": result.get("name"),
            "address": result.get("formatted_address"),
            "phone": result.get("formatted_phone_number"),
            "website": result.get("website"),
            "hours": result.get("opening_hours", {}).get("weekday_text"),
            "rating": result.get("rating"),
            "reviews": result.get("reviews", [])[:3],
        }

    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
        return {}
