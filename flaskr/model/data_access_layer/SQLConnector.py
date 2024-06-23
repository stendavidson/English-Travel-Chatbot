from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, DateTime, text, bindparam
from sqlalchemy.sql.expression import TextClause
from sqlalchemy.exc import StatementError, InvalidRequestError, SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError, MultipleResultsFound


from ..exceptions.InvalidORMClassException import InvalidORMClassException
from ..exceptions.SQLRequestException import SQLRequestException
from ..exceptions.SQLServerError import SQLServerError
from ..utils.validation_utils import with_type_validation


db : SQLAlchemy = SQLAlchemy()


class Weather(db.Model) :
    """
    The Weather class encapsulates all the information relating to the weather in 
    a given location at a given time.

    Parameters:
        date_time (datetime): the (starting) date and time of the 3 hour forecast window.
        location (str): The plain text location name.
        lat (float): The latitude of the location.
        lon (float): The longitude of the location.
        temp (float): The temperature in degrees Celsius.
        min_temp (float): The minimum temperature in degrees Celsius.
        max_temp (float): The maximum temperature in degrees Celsius.
        feels_temp (float): What the temperature actually feels like in degrees Celsius.
        humidity (float): The percentage % humidity.
        description (str): The plain text description of the weather.
        wind_speed (float): The wind speed in m/s.
        rain_prob (float): The probability (0.0 - 1.0) of rainfall in the 3hr window.
        visibility (int): The number of metres of visibility [0,10000]
    """

    date_time : Column = db.Column(DateTime, unique=False, nullable=False, primary_key=True)
    location : Column = db.Column(String, unique=False, nullable=False, primary_key=True)
    lat : Column = db.Column(Float, unique=False, nullable=False)
    lon : Column = db.Column(Float, unique=False, nullable=False)
    temp : Column = db.Column(Float, unique=False, nullable=True)
    min_temp : Column = db.Column(Float, unique=False, nullable=True)
    max_temp : Column = db.Column(Float, unique=False, nullable=True)
    feels_temp : Column = db.Column(Float, unique=False, nullable=True)
    humidity : Column = db.Column(Float, unique=False, nullable=True)
    description : Column = db.Column(String, unique=False, nullable=True)
    wind_speed : Column = db.Column(Float, unique=False, nullable=True)
    rain_prob : Column = db.Column(Float, unique=False, nullable=True)
    visibility : Column = db.Column(Integer, unique=False, nullable=True)


class News(db.Model) :
    """
    The News class encapsulates all the information relating to the latest News in 
    a given location within the last five days.

    Parameters:
        location (str): the plain text location name.
        date_time (datetime): the publishing date of the article.
        url (str): the url corresponding to the article.
        imgUrl (str): the url corresponding to the article image.
        title (str): the title of the news article.
        description (str): a summary of the news article.
    """
    
    location : Column = db.Column(String, unique=True, nullable=False, primary_key=True)
    date_time : Column = db.Column(DateTime, unique=False, nullable=False)
    url : Column = db.Column(String, unique=False, nullable=False)
    imgURL : Column = db.Column(String, unique=False, nullable=True)
    title : Column = db.Column(String, unique=False, nullable=False)
    description : Column = db.Column(String, unique=False, nullable=False)


class SQLConnector:
    """
    This class handles the initialization and communication with an SQLite
    ORM database using SQLAlchemy.
    """

    @with_type_validation(object, Flask, str)
    def __init__(self, app : Flask, path : str)  -> None:
        """
        Constructor method

        Parameters:
            app (Flask): an instance of a Flask application
            path (str): the relative path to create the SQL database at
        """

        # Flask app, context and SQLAlchemy configuration is set.
        self.app : Flask = app
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{path}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.db : SQLAlchemy = db
        self.db.init_app(self.app)

    
    def initialize_tables(self)  -> None:
        """
        The tables in the database are initialized if they are not already created.
        """
        
        # Exception Handling
        try :

            with self.app.app_context():
                self.db.create_all()
            
        # An unknown error occurred.    
        except SQLAlchemyError as e :

            raise SQLServerError("An error occurred while initializing tables.") from e


    @with_type_validation(object, type, list)
    def bulk_save(self, type : type, objects : list) -> None:
        """
        This function saves a list of ORM objects as rows in the SQLite database.

        Parameters:
            type (type): The ORM class type.
            objects (list[Weather] | list[News]): The object to be saved.
        """

        # Input ORM Class type validation
        if type != Weather and type != News:
            raise InvalidORMClassException()

        # Input validation ORM Class must be Weather or News
        for obj in objects:
            if not isinstance(obj, type):
                raise InvalidORMClassException() 
                

        with self.app.app_context():

            # SQL Exception Handling
            try:
                
                self.db.session.query(type).delete()
                self.db.session.bulk_save_objects(objects)
                self.db.session.commit()
            
            # The SQL statement is invalid
            except StatementError as e :
                
                # Cleanup
                self.db.session.rollback()

                raise SQLRequestException("An SQL syntax error occurred.") from e
            
            # The request made was rejected by the server
            except InvalidRequestError as e :

                # Cleanup
                self.db.session.rollback()

                raise SQLRequestException("An invalid SQL INSERT or UPDATE request was made.") from e
            
            # The SQL statement is invalid
            except StaleDataError as e :

                # Cleanup
                self.db.session.rollback()

                raise SQLServerError("A database concurrency issue caused an error.") from e
            
            # An unknown error occurred.    
            except SQLAlchemyError as e :

                # Cleanup
                self.db.session.rollback()

                raise SQLServerError("An unspecified SQLAlchemy error occurred during an INSERT or UPDATE request.") from e


    @with_type_validation(object, type, str, dict)
    def orm_query(self, type : type, query : str, substitutions : dict)  -> object :
        """
        This function can retrieve a single point of Weather or News data using an SQL query.

        Parameters:
            type (type): ORM class type - valid values "Weather", "News" (see static keywords)
            query (str): a written sql query
            substitutions (dict[str, Any]): the values to be injected into the query

        Returns:
            Weather | News : an ORM object created from the tables in the database.
        """

        result : Weather | News | None = None # type: ignore

        # Input ORM Class type validation
        if type != Weather and type != News:
            raise InvalidORMClassException()
        

        with self.app.app_context():

            # SQL Exception Handling
            try:

                result = self.db.session.query(type).from_statement(text(query)).params(**substitutions).one_or_none()

            # The SQL statement is invalid
            except StatementError as e :
                raise SQLRequestException("An SQL syntax error occurred.") from e
            # The request made was rejected by the server
            except MultipleResultsFound as e :
                raise SQLRequestException("This query returned multiple results, please utilize bulk method.") from e
            # The request made was rejected by the server
            except InvalidRequestError as e :
                raise SQLRequestException("An invalid SQL query was made.") from e
            # An unknown error occurred.    
            except SQLAlchemyError as e :
                raise SQLServerError("An unspecified SQLAlchemy error occurred during a query.") from e

        return result
    

    @with_type_validation(object, type, str, dict)
    def bulk_orm_query(self, type : type, query : str, substitutions : dict) -> list :
        """
        This function can retrieve a set of Weather or News data using an SQL query.

        Parameters:
            type (type): ORM class type - valid values "Weather", "News" (see static keywords)
            query (str): a written sql query
            substitutions (dict[str, Any]): the values to be injected into the query

        Returns:
            list[Weather] | list[News]: a list of ORM objects defined from the tables in the
            database.
        """

        results : list = []

        # Input ORM Class type validation
        if type != Weather and type != News:
            raise InvalidORMClassException()
        
        
        with self.app.app_context():

            # SQL Exception Handling
            try:

                results = self.db.session.query(type).from_statement(text(query)).params(**substitutions).all()
            
            # The SQL statement is invalid
            except StatementError as e :
                raise SQLRequestException("An SQL syntax error occurred.") from e
            # The request made was rejected by the server
            except InvalidRequestError as e :
                raise SQLRequestException("An invalid SQL query was made.") from e
            # An unknown error occurred.    
            except SQLAlchemyError as e :
                raise SQLServerError("An unspecified SQLAlchemy error occurred during a query.") from e

        return results


