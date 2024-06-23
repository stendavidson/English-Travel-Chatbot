
from datetime import datetime, timezone, timedelta
from json import dumps
import re
from flask import Flask, Response, render_template
import numpy as np
import pandas as pd

from flaskr.model.exceptions.InvalidTemplateException import InvalidTemplateException
from flaskr.model.exceptions.SQLServerError import SQLServerError
from flaskr.model.utils.validation_utils import with_type_validation

from ..model.chatbot.GoTravelBot import GoTravelBot
from ..model.chatbot.generate_corpus import create_corpus_from_template
from ..model.data_access_layer.CurrentNewsConnector import CurrentNewsConnector
from ..model.data_access_layer.OpenWeatherConnector import OpenWeatherConnector
from ..model.data_access_layer.SQLConnector import SQLConnector, News, Weather


# Creath Exception Handlers ||
# Creath All (2) Endpoints ||


#################################################################################################
###################################### Retrieve API Keys ########################################
#################################################################################################



KEYS_FILE : str = "api_key.txt"
api_keys : list = []


# The file is read and exceptions handled
try :

    with open(KEYS_FILE, "r") as file:

        api_keys : list = file.readlines()

except FileNotFoundError :
    
    # The application exits with code 2 - file cannot be found
    print("Application dependency - api_key.txt file not found. Application exiting...")  
    exit(2)

except Exception :
    
    # The application exits with code 1 - an unspecified error
    print("An unexpected error occurred while retrieving api key. Application exiting...")
    exit(1)


# The file contents are validated
if len(api_keys) != 2 or api_keys[0] == "" or api_keys[1] == "" :

    # The application exits with windows code 13 - invalid data
    print("The api_key.txt file doesn't contain the correct number of entries or is empty. Application exiting...")
    exit(13)


# If the key file is populated retrieve keys
weather_key : str = api_keys[0].strip()
news_key : str = api_keys[1].strip()



#################################################################################################
############################### Retrieve Locations & Coordinates ################################
#################################################################################################



LOCATIONS_FILE : str = "locations.csv"
locations : list = []

# The file is read and exceptions handled
try :

    data : pd.DataFrame = pd.read_csv(LOCATIONS_FILE, delimiter=",")    
    locations = [data.to_list() for index, data in data.iterrows()]

except FileNotFoundError :
    
    # The application exits with code 2 - file could not be found
    print("Application dependency - locations.csv file not found. Application exiting...")  
    exit(2)

except pd.errors.ParserError :

    # The application exits with windows code 13 - invalid data
    print("The locations.csv file could not be parsed. Application exiting...")
    exit(13)

except Exception :
    
    # The application exits with code 1 - an unspecified error
    print("An unexpected error occurred while retrieving locations information. Application exiting...")
    exit(1)


location_names = [location[0] for location in locations]


#################################################################################################
##################################### Create Chatbot Corpus ####################################
#################################################################################################



BOT_DATABASE = "SQLite/chatterbot-database.db"

TEMPLATES : list = [
    "flaskr/model/chatbot/corpus_templates/best_day_certain_location.csv",
    "flaskr/model/chatbot/corpus_templates/current_day_best_location.csv",
    "flaskr/model/chatbot/corpus_templates/current_weather_request.csv",
    "flaskr/model/chatbot/corpus_templates/latest_news_request.csv",
    "flaskr/model/chatbot/corpus_templates/weather_forecast_request.csv"
]


def generate_training_data() -> list:
    """
    This function trains the chatbot once per application initialization.
    """
        
    training_data : pd.DataFrame = pd.DataFrame(dtype=str)
    
    for template in TEMPLATES:
    
        training_data = pd.concat(
            [
                training_data, 
                create_corpus_from_template(template, location_names)
            ]
        )

    data = training_data.values.tolist()

    return data



def generate_default_responses() -> dict:
    """
    This function retrieves the defaults
    """

    default_responses : pd.DataFrame = pd.DataFrame(dtype=str)
    
    for template in TEMPLATES:
    
        default_responses = pd.concat(
            [
                default_responses, 
                create_corpus_from_template(template, location_names)
            ]
        )

    dictionary: dict[str, str] = {text_pair[1] : text_pair[0] for text_pair in default_responses.values.tolist()}

    return dictionary


#################################################################################################
################################## Initialize Flask Application #################################
#################################################################################################



app = Flask(__name__)


# Initialize SQL Connector
sql_connector : SQLConnector = None

try :
    
    sql_connector : SQLConnector = SQLConnector(app, "../../SQLite/storage-database.db")
    sql_connector.initialize_tables()

except SQLServerError as e :

    print(f"{str(e)} Application exiting...")
    exit(1)


# The bot is trained at application start up
try :

    # Application context is used to reduct thread related errors
    with app.app_context() :

        app.data = generate_default_responses()
        app.bot = GoTravelBot(BOT_DATABASE, app.data)
        
        # The bot is only trained once
        if not app.bot.trained :

            print("Please wait while the chatbot is trained...")
            
            app.bot.train(generate_training_data())

            print("Training Complete")

except InvalidTemplateException as e :

    print(f"{str(e)} Application exiting...")





#################################################################################################
###################################### Flask Error Handlers #####################################
#################################################################################################




#################################################################################################
################################### Endpoint Utility Functions ##################################
#################################################################################################



def update_weather_data() -> None :
    """
    This utility function enables a bulk update of the weather data stored for later
    use.
    """

    weather_connector : OpenWeatherConnector = OpenWeatherConnector(api_key=weather_key)

    weather_data : list[Weather] = np.array(weather_connector.bulk_weather_request(locations=locations)).flatten().tolist()

    sql_connector.bulk_save(Weather, weather_data)



def update_news_data() -> None :
    """
    This utility function enables a bulk update of the news data stored for later
    use.
    """

    news_connector : CurrentNewsConnector = CurrentNewsConnector(api_key=news_key)

    news_data : list[News] = [news for news in news_connector.bulk_news_request(locations=location_names) if news]

    sql_connector.bulk_save(News, news_data)



@with_type_validation(str)
def find_best_day(location : str) -> Weather :
    """
    This utility function provides a simple mechanism by which the "ideal" time
    to visit a given location is provided

    Parameters:
        location (str): the location to be searched
    """

    # If data is out of date update it
    if not date_check_weather() :
        update_weather_data()

    outcome : Weather | None = None

    forecast : list[Weather] = sql_connector.bulk_orm_query(Weather, 
                                """
                                SELECT * FROM weather 
                                WHERE feels_temp < 30 
                                AND wind_speed <= 8
                                AND visibility > 4000
                                AND location = :location
                                ORDER BY rain_prob ASC, feels_temp DESC, visibility DESC, wind_speed DESC
                                """,
                                {"location" : location})
    
    # Filter outcomes - to times between 6am and 6pm
    for weather in forecast :

        weather.date_time = datetime.strptime(weather.date_time, "%Y-%m-%d %H:%M:%S.000000").replace(tzinfo=timezone.utc)

        if weather.date_time.hour >= 6 and weather.date_time.hour <= 18 :
            outcome = weather
            break

    return outcome



def find_best_location() -> Weather :
    """
    This utility function provides a simple mechanism by which the "ideal" location
    to visit on a given day.
    """

    # If data is out of date update it
    if not date_check_weather() :
        update_weather_data()

    date_time_1 : datetime = datetime.now(timezone.utc).replace(hour=6)
    date_time_2 : datetime = datetime.now(timezone.utc).replace(hour=18)

    weather : Weather = sql_connector.orm_query(Weather, 
                        """
                        SELECT * FROM weather 
                        WHERE feels_temp < 30 
                        AND wind_speed <= 8
                        AND visibility > 4000
                        AND date_time BETWEEN :date_time_1 AND :date_time_2
                        ORDER BY rain_prob ASC, feels_temp DESC, visibility DESC, wind_speed DESC
                        LIMIT 1
                        """,
                        {
                            "date_time_1" : date_time_1,
                            "date_time_2" : date_time_2,
                        })

    # Fix datetime
    if weather :
        weather.date_time = datetime.strptime(weather.date_time, "%Y-%m-%d %H:%M:%S.000000").replace(tzinfo=timezone.utc)

    return weather


@with_type_validation(str)
def get_current_weather(location : str) -> Weather :
    """
    This utility function provides a simple mechanism by which the current 
    weather can be retrieved for a given location.

    Parameters:
        location (str): the location to retrieve the current weather data for.
    """

    # If data is out of date update it
    if not date_check_weather() :
        update_weather_data()

    date_time : datetime = datetime.now(timezone.utc)

    weather : Weather = sql_connector.orm_query(Weather, 
                        """
                        SELECT * FROM weather
                        WHERE location = :location
                        AND date_time >= :date_time
                        ORDER BY date_time ASC
                        LIMIT 1
                        """,
                        {
                            "location" : location,
                            "date_time" : date_time
                        })
    
    # Fix datetime
    if weather :
        weather.date_time = datetime.strptime(weather.date_time, "%Y-%m-%d %H:%M:%S.000000").replace(tzinfo=timezone.utc)

    return weather


@with_type_validation(str)
def get_weather_forecast(location : str) -> list :
    """
    This utility function provides a simple mechanism by which the weather 
    forecast can be retrieved for a given location. It returns the weather
    data for each day at 12:00 noon.

    Parameters:
        location (str): the location to retrieve the weather forecast for
    """

    # If data is out of date update it
    if not date_check_weather() :
        update_weather_data()

    forecast : list[Weather] = sql_connector.bulk_orm_query(Weather, 
                        """
                        SELECT * FROM weather
                        WHERE location = :location
                        ORDER BY date_time ASC
                        """,
                        {
                            "location" : location
                        })

    # Fix dates
    for weather in forecast :
        weather.date_time = datetime.strptime(weather.date_time, "%Y-%m-%d %H:%M:%S.000000").replace(tzinfo=timezone.utc)

    forecast = [weather for weather in forecast if weather.date_time.hour == 12]

    return forecast


@with_type_validation(str)
def get_current_news(location : str) -> list :
    """
    This utility function provides a simple mechanism by which the latest
    news for given location can be retrieved.

    Parameters:
        location (str): the location to retrieve the news for
    """

    # If data is out of date update it
    if not date_check_news() :
        update_news_data()

    news : News = sql_connector.orm_query(News, 
                        """
                        SELECT * FROM news
                        WHERE location = :location
                        LIMIT 1
                        """,
                        {
                            "location" : location
                        })
    
    return news



def date_check_news() -> bool:
    """
    This function verifies whether the news data in the database needs to be
    updated. Returns true if everything is up-to-date (within 5 days old)
    """
    
    news : News  = sql_connector.orm_query(News, 
                        """
                        SELECT * FROM news
                        ORDER BY date_time ASC
                        LIMIT 1
                        """, {})
    
    uptodate : bool = False

    if news :
        date_time : datetime = (datetime.now(timezone.utc) - timedelta(days=5))
        news_date_time : datetime = datetime.strptime(news.date_time, "%Y-%m-%d %H:%M:%S.000000").replace(tzinfo=timezone.utc)
        uptodate = date_time < news_date_time

    return uptodate



def date_check_weather() -> bool:
    """
    This function verifies whether the weather data in the database needs to be
    updated. Returns true if everything is up-to-date (within 1 days old)
    """
    
    weather : Weather  = sql_connector.orm_query(Weather, 
                        """
                        SELECT * FROM weather
                        ORDER BY date_time ASC
                        LIMIT 1
                        """, {})
    
    uptodate : bool = False

    if weather :

        date_time : datetime = datetime.now(timezone.utc)
        weather_date_time : datetime = datetime.strptime(weather.date_time, "%Y-%m-%d %H:%M:%S.000000").replace(tzinfo=timezone.utc)
        uptodate = date_time.day == weather_date_time.day

    return uptodate



#################################################################################################
################################## Template Population Functions ################################
#################################################################################################


@with_type_validation(str)
def current_weather_response(response : str) -> Response :
    """
    This function returns a json encoded HTTP response containing
    the chat bot's populated response - the current weather at a
    specified location.

    Parameters:
        response (str): The chat bot's response
    """

    
    output : str = None
    location_match : list | None = re.findall(r"\{(.+?)\}", response)
    weather : Weather = None
    
    if len(location_match) == 3 :

        weather : Weather = get_current_weather(location_match[1])

    # Create response or default response
    if weather :

        output = re.sub(r"\{weather_description\}", weather.description, response)
        output = re.sub(r"\{temp\}", str(weather.temp), output)
        output = re.sub(r"\{|\}", "", output)

    elif location_match :

        output = f"Sorry weather data could not be retrieved for {location_match.group(1)}."

    else :

        output = "Sorry something went wrong..."

    return Response(dumps({"Go Travel Bot" : output}), status=200)


@with_type_validation(str)
def weather_forecast_response(response : str) -> Response :
    """
    This function returns a json encoded HTTP response containing
    the chat bot's populated response - the weather forecast for
    a given location.

    Parameters:
        response (str): The chat bot's response
    """

    output : str = response
    location_match : re.Match[str] | None = re.search(r"\{(.+?)\}", response)
    list_match : re.Match[str] | None = re.search(r"\[(.+?)\]", response)
    forecast : list[Weather] = []
    template : str | None = None

    if location_match and list_match :

        forecast : list[Weather] = get_weather_forecast(location_match.group(1))
        template : str = list_match.group(0)

    # Create response or default response
    if len(forecast) > 0 :

        for weather in forecast :
            temp : str = re.sub(r"\{weekday\}", weather.date_time.strftime("%A"), template)
            temp = re.sub(r"\{description\}", weather.description, temp)
            temp = re.sub(r"\{temp\}", str(weather.temp), temp)
            output += f"\n{temp}"
        
        output = re.sub(list_match.group(1), "", output)
        output = re.sub(r"\[|\]", "", output)
        output = re.sub(r"\{|\}", "", output)

    elif location_match and list_match :

        output = f"Sorry the weather forecast couldn't be retrieved for {location_match.group(1)}."

    else :

        raise InvalidTemplateException("Sorry something went wrong while populating the response.")


    return Response(dumps({"Go Travel Bot" : output}), status=200)



@with_type_validation(str)
def best_day_response(response : str) -> Response :
    """
    This function returns a json encoded HTTP response containing
    the chat bot's populated response - the best day to visit a 
    a given location.

    Parameters:
        response (str): The chat bot's response
    """

    output : str = None
    location_match : re.Match[str] | None  = re.search(r"\{(.+?)\}", response)
    weather : Weather | None = None

    if location_match :   
        weather : Weather = find_best_day(location_match.group(1))

    # Create response or default response
    if weather :

        output = re.sub(r"\{day\}", weather.date_time.strftime("%A"), response)
        output = re.sub(r"\{time\}", weather.date_time.strftime("%I:00 %p"), output)
        output = re.sub(r"\{|\}", "", output)

    elif location_match :

        output =  f"Sorry, conditions are too poor for travelling to {location_match.group(1)} "\
                        "for the next few days."
        
    else :

        raise InvalidTemplateException("Sorry something went wrong while populating the response.")

    return Response(dumps({"Go Travel Bot" : output}), status=200)



@with_type_validation(str)
def best_location_response(response : str) -> Response :
    """
    This function returns a json encoded HTTP response containing
    the chat bot's populated response - the best location to visit 
    today.

    Parameters:
        response (str): The chat bot's response
    """

    output : str = None
    weather : Weather = find_best_location()

    # Create response or default response
    if weather :

        output = re.sub(r"\{unknown-location\}", weather.location, response)

    else :

        output = "Sorry, either it is too late in the day or conditions are to poor "\
                 "to travel today."

    return Response(dumps({"Go Travel Bot" : output}), status=200)



@with_type_validation(str)
def current_news_response(response : str) -> Response :
    """
    This function returns a json encoded HTTP response containing
    the chat bot's populated response - the latest news from a given
    location.

    Parameters:
        response (str): The chat bot's response
    """

    output : str = None
    location_match : re.Match[str] | None = re.search(r"\{(.+?)\}", response)
    news : News | None = None

    if location_match :

        news : News = get_current_news(location_match.group(1))

    # Create response or default response
    if news :    

        output = re.sub(r"\{title\}", news.title, response)
        output = re.sub(r"\{|\}", "", output)

    elif location_match :

        output = f"Sorry I couldn't retrieve the latest news for {location_match.group(1)}, maybe ask "\
                  "about somewhere else."
        
    else :

        raise InvalidTemplateException("Sorry something went wrong while populating the response.")

    return Response(dumps({"Go Travel Bot" : output}), status=200)



#################################################################################################
#################################### Flask Endpoint Functions ###################################
#################################################################################################



@app.route("/data/update", methods=["POST"])
def update() -> Response :
    """
    This endpoint forces the database to refresh.

    Parameters:
        user_input (str): The user's plain text input.
    """

    update_news_data()
    update_news_data()

    return Response(status=204)





@app.route("/chat/<user_input>", methods=["GET"])
def chatbot(user_input : str) -> Response :
    """
    This endpoint is the api endpoint to the GoTravel Chat Bot.

    Parameters:
        user_input (str): The user's plain text input.
    """
    
    # Get response from chatbot
    app.bot = GoTravelBot(BOT_DATABASE, app.data)
    response : str = app.bot.get_response(user_input)
    
    # Determine the template type
    match : re.Match[str] | None = re.search(r"#(.)#", response)
    code : int = 0

    if match :

        code = match.group(1)
        response = re.sub(r"#.# ", "", response, count=2)

    http_response : Response = None

    # Populate response templates
    if code == "1" :
        
        http_response = current_weather_response(response)

    elif code == "2" :

        http_response = weather_forecast_response(response)

    elif code == "3" :

        http_response = best_day_response(response)
        
    elif code == "4" :

        http_response = best_location_response(response)

    elif code == "5" :

        http_response = current_news_response(response)

    else :

        http_response = Response(dumps({"Go Travel Bot" : response}), status=200)

    # Set Headers
    http_response.access_control_allow_origin = "*"
    http_response.content_language = "en"
    http_response.content_type = "application/json"

    return http_response



if __name__ == "__main__" :

    app.run("localhost", "80")






