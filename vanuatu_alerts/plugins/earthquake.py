import math
from datetime import datetime, timedelta
from dataclasses import dataclass
from vanuatu_alerts import config
from vanuatu_alerts.plugins.base import BasePlugin
from loguru import logger
import requests


@dataclass
class Earthquake:
    id: str
    geometry: any
    magnitude: float
    place: str
    url: str

    @property
    def latitude(self):
        return self.geometry["coordinates"][0]

    @property
    def longitude(self):
        return self.geometry["coordinates"][1]


class EarthquakePlugin(BasePlugin):
    def __init__(self):
        super().__init__("Earthquakes", 30)
        self.known_earthquakes = []

    def run(self) -> str | None:
        data = self.fetch()
        earthquakes = self.parse_earthquakes(data)
        if not earthquakes:
            logger.debug("No earthquakes were found")
            return None
        for item in earthquakes:
            logger.debug(f"Found earthquake {item.id}")
            if item.id in self.known_earthquakes:
                logger.debug("Skipping - known earthquake")
                continue
            try:
                if self.felt_earthquake(item):
                    logger.info(f"Earthquake {item.id} was felt")
                    return f"Earthquake felt!\nMag {item.magnitude}\nNear {item.place}.\nRead more at {item.url}"
                else:
                    logger.debug("Skipping - earthquake not felt")
            except Exception as e:
                raise e
            finally:
                self.known_earthquakes.append(item.id)

    def parse_earthquakes(self, data: any) -> list[Earthquake] | None:
        earthquake_count = data["metadata"]["count"]
        if earthquake_count == 0:
            return None
        earthquakes = []
        for item in data["features"]:
            earthquake = Earthquake(
                id=item["id"],
                geometry=item["geometry"],
                magnitude=item["properties"]["mag"],
                place=item["properties"]["place"],
                # tsunami=item["properties"]["tsunami"],
                url=item["properties"]["url"],
            )
            earthquakes.append(earthquake)
        return earthquakes

    def fetch(self):
        # docs at https://earthquake.usgs.gov/fdsnws/event/1/#parameters
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        updatedafter = datetime.utcnow() - timedelta(days=1)
        params = dict(
            format="geojson",
            updatedafter=updatedafter,
            latitude=config.COORDS_HOME[0],
            longitude=config.COORDS_HOME[1],
            maxradiuskm=1000,
        )
        resp = requests.get(url, params=params)
        return resp.json()

    def felt_earthquake(self, earthquake: Earthquake) -> bool:
        # lat = earthquake.geometry.coordinates[0]
        # lon = earthquake.geometry.coordinates[1]
        distance = self.haversine(
            config.COORDS_HOME[0],
            config.COORDS_HOME[1],
            earthquake.latitude,
            earthquake.longitude,
        )
        radius = self.felt_radius(earthquake.magnitude)
        return distance <= radius

    def haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371  # Radius of the Earth in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    def felt_radius(self, magnitude: float) -> float:
        # formulas is based on the intensity decay of seismic waves as they travel away from the epicenter.
        # increase last value to 1.5 or 1.8 to reduce false positives or only alert for larger earthquakes.
        return 10 ** (0.5 * magnitude - 1.3)
