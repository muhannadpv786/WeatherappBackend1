from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from typing import Optional
import logging
from opentelemetry import trace
from otel_setup import setup_otel

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env variables
load_dotenv()

# FastAPI instance
app = FastAPI()

# Add OpenTelemetry
setup_otel(app)
tracer = trace.get_tracer(__name__)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate API key
if not os.getenv("OPENWEATHER_API_KEY"):
    raise RuntimeError("OPENWEATHER_API_KEY not set")

class LocationInput(BaseModel):
    city_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None

@app.post("/weather")
async def get_weather(location: LocationInput):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    logger.info(f"Fetching weather for {location.city_name or f'lat={location.lat}, lon={location.lon}'}")

    if location.lat and location.lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={location.lat}&lon={location.lon}&appid={api_key}&units=metric"
    else:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location.city_name}&appid={api_key}&units=metric"

    with tracer.start_as_current_span("call-weather-api"):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            weather_data = response.json()

            if not isinstance(weather_data, dict):
                raise HTTPException(status_code=502, detail="Invalid response from weather API")

            if weather_data.get("cod") != 200:
                raise HTTPException(
                    status_code=400,
                    detail=weather_data.get("message", "Unknown error from weather API")
                )

            return {
                "city": weather_data.get("name"),
                "country": weather_data.get("sys", {}).get("country"),
                "temperature": weather_data.get("main", {}).get("temp"),
                "feels_like": weather_data.get("main", {}).get("feels_like"),
                "humidity": weather_data.get("main", {}).get("humidity"),
                "wind_speed": weather_data.get("wind", {}).get("speed"),
                "weather": weather_data.get("weather", [{}])[0].get("description"),
                "icon": weather_data.get("weather", [{}])[0].get("icon"),
                "coordinates": weather_data.get("coord"),
                "timestamp": weather_data.get("dt")
            }

        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="Weather API request timed out")
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Weather API request failed: {str(e)}"
            )

@app.get("/weather")
async def get_weather_get(city_name: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    logger.info(f"Fetching weather for {city_name}")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"

    with tracer.start_as_current_span("call-weather-api"):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            weather_data = response.json()

            if not isinstance(weather_data, dict):
                raise HTTPException(status_code=502, detail="Invalid response from weather API")

            if weather_data.get("cod") != 200:
                raise HTTPException(
                    status_code=400,
                    detail=weather_data.get("message", "Unknown error from weather API")
                )

            return {
                "city": weather_data.get("name"),
                "country": weather_data.get("sys", {}).get("country"),
                "temperature": weather_data.get("main", {}).get("temp"),
                "feels_like": weather_data.get("main", {}).get("feels_like"),
                "humidity": weather_data.get("main", {}).get("humidity"),
                "wind_speed": weather_data.get("wind", {}).get("speed"),
                "weather": weather_data.get("weather", [{}])[0].get("description"),
                "icon": weather_data.get("weather", [{}])[0].get("icon"),
                "coordinates": weather_data.get("coord"),
                "timestamp": weather_data.get("dt")
            }

        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="Weather API request timed out")
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Weather API request failed: {str(e)}"
            )

@app.get("/health")
async def health_check():
    logger.info("Health check route hit")
    return {"status": "Ok", "message": "Weather API is running smoothly!"}
