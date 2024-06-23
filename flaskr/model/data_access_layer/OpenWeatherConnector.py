from datetime import datetime, timezone
from threading import Thread
from requests import Response, get
from requests.exceptions import RequestException, JSONDecodeError

from .SQLConnector import Weather
from ..exceptions.OpenWeatherRequestException import OpenWeatherRequestException
from ..utils.threading_utils import ThreadingContext
from ..utils.validation_utils import with_type_validation


class OpenWeatherConnector :
    """
    This class establishes a connection to the OpenWeather API to
    extract Weather data in 5 Day blocks across multiple locations.
    """

    API_URL : str = "http://api.openweathermap.org/data/2.5/forecast"
    """
    This (static) class constant defines the api endpoint being accessed.
    """

    @with_type_validation(object, str)
    def __init__(self, api_key : str) -> None:
        """
        Initializer

        Parameters:
            api_key (str) : The api key for the OpenWeather API
        """
        self.api_key : str = api_key

    @with_type_validation(object, str, float, float)
    def request_weather(self, location : str, lat : float, lon : float) -> Weather:
        """
        This function provides a simple method by which weather data can
        be retrieved for a 5 day period for a given location.

        Parameters:
            location (str) : The plain text name of the location.
            lat (float) : The latitude of the location.
            lon (float) : The longitude of the location.
        """            

        # Input validation is performed to range check the coordinates.
        if lat < -90 or lat > 90 and lat < -180 and lat > 180:
            raise ValueError(f"Invalid latitude and longitude values: ({lat},{lon}).")

        forecast : list[Weather] | None = []
        
        try :

            forecast_data : Response = get(OpenWeatherConnector.API_URL, params={
                "lat" : lat, 
                "lon" : lon, 
                "appid" : self.api_key,
                "units" : "metric",
                "lang" : "en"
            })

            forecast_json : dict = forecast_data.json()

            for weather in forecast_json["list"]:

                date_time : datetime = datetime.fromtimestamp(weather["dt"], timezone.utc)

                if date_time.hour >= 6 and date_time.hour <= 18 :

                    forecast.append(Weather(
                        date_time=date_time,
                        location=location,
                        lat=lat,
                        lon=lon,
                        temp=weather["main"].get("temp", None) ,
                        min_temp=weather["main"].get("temp_min", None),
                        max_temp=weather["main"].get("temp_max", None),
                        feels_temp=weather["main"].get("feels_like", None),
                        humidity=weather["main"].get("humidity", None),
                        description=weather.get("weather", [dict()])[0].get("description", None),
                        wind_speed=weather.get("wind", None).get("speed", None),
                        rain_prob=weather.get("pop", None),
                        visibility=weather.get("visibility", None)
                    ))

        except KeyError as e:

            raise OpenWeatherRequestException("The response body did not"\
                                              " contain valid data.") from e

        except JSONDecodeError as e:

            raise OpenWeatherRequestException("An unexpected response was"\
                                              " returned by the endpoint it.") from e

        except RequestException as e:

            raise OpenWeatherRequestException("Something went wrong whilst"\
                                              " connecting to the API endpoint.") from e
        
        return forecast
        
    @with_type_validation(object, list)
    def bulk_weather_request(self, locations : list) -> list :
        """
        This function performs a multi-threaded request for weather forecasts 
        at a list of locations.

        Parameters:
            locations (list[list[str, float, float]]): A list of location names
            to search.
        """

        context : ThreadingContext = ThreadingContext()

        forecasts : list[list[Weather]] = []


        @context.with_threading_context(forecasts)
        def thread_request(location : str, lat : float, lon : float) -> None:
            """
            This function converts the weather forecaset request into a threadable
            function.

            Parameters:
                location (str): the location to search for weather forecast data from.
            """

            return self.request_weather(location, lat, lon)
            

        threads : list[Thread] = []

        # Threads are intialized
        for location in locations :
            threads.append(Thread(target=thread_request, args=(location))) 
            threads[threads.__len__()-1].start()

        # Threads are joined to the main thread.
        for thread in threads:
            thread.join()

        # The threading context provides access to exceptions thrown inside the 
        # threading context.
        for exception in context.exceptions :
            raise exception

        return forecasts