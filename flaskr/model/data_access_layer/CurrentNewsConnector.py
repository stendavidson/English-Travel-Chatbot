from datetime import datetime, timezone, timedelta
from threading import Thread
from requests import Response, get
from requests.exceptions import RequestException, JSONDecodeError

from .SQLConnector import News
from ..exceptions.CurrentNewsRequestException import CurrentNewsRequestException
from ..utils.threading_utils import ThreadingContext
from ..utils.validation_utils import with_type_validation


class CurrentNewsConnector :
    """
    This class establishes a connection to the Currents API to extract the latest 
    News data.
    """

    API_URL : str = "https://api.currentsapi.services/v1/search"
    """
    This (static) class constant defines the api endpoint being accessed.
    """

    @with_type_validation(object, str)
    def __init__(self, api_key) -> None:
        """
        Initializer

        Parameters:
            api_key (str) : The api key for the OpenWeather API
        """
        self.api_key : str = api_key


    @with_type_validation(object, str)
    def request_news(self, location : str) -> News:
        """
        This function provides a simple method by which the latest news articles for
        a given location can be retrieved.

        Parameters:
            location (str) : The location for which the news is retrieved.
        """

        news : News | None = None
        
        try :

            news_data : Response = get(CurrentNewsConnector.API_URL, params={
                "language" : "en",
                "type" : 1,
                "country" : "GB",
                "limit" : 1,
                "page_size" : 1,
                "start_date" : (
                                datetime.now(timezone.utc) - timedelta(days=5)\
                               ).strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                "keywords" : location,
                "apiKey" : self.api_key
            })

            article : list[dict] = news_data.json()["news"]
            
            # A news article is only created if an article was returned
            if len(article) > 0:

                news = News(
                    location=location,
                    date_time=datetime.strptime(article[0]["published"], "%Y-%m-%d %H:%M:%S %z"), 
                    url=article[0]["url"],
                    imgURL=article[0].get("image", None),
                    title=article[0]["title"],
                    description=article[0]["description"]
                )

        except KeyError as e:

            raise CurrentNewsRequestException("The response body did not contain"\
                                              " valid data.") from e

        except JSONDecodeError as e:

            raise CurrentNewsRequestException("An unexpected response was returned"\
                                              " by the endpoint it.") from e

        except RequestException as e:

            raise CurrentNewsRequestException("Something went wrong whilst " \
                                              "connecting to the API endpoint.") from e
        
        return news
    

    @with_type_validation(object, list)
    def bulk_news_request(self, locations : list) -> list :
        """
        This function performs a multi-threaded request for current news at a list
        of locations.

        Parameters:
            locations (list[str]): A list of location names to search.
        """

        context : ThreadingContext = ThreadingContext()

        news_articles : list[News] = []


        @context.with_threading_context(news_articles)
        def thread_request(location : str) -> None:
            """
            This function converts the news request into a threadable function.

            Parameters:
                location (str): the location to search for news from.
            """

            return self.request_news(location)


        threads : list[Thread] = []

        # Threads are intialized
        for location in locations :

            # the args Thread parameter unpacks the tuple too far which causes problems for
            # further *args unpacking inside a nested function - this is resolved by placing
            # string parameters within a secondary tuple.
            threads.append(Thread(target=thread_request, args=(tuple([location])))) 
            threads[threads.__len__()-1].start()

        # Threads are joined to the main thread.
        for thread in threads:
            thread.join()

        # The threading context provides access to exceptions thrown inside the 
        # threading context.
        for exception in context.exceptions :
            raise exception

        return news_articles



        
