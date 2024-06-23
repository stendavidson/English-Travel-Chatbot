
class SQLRequestException(Exception) :
    """
    This custom exception is raised internally by the server when an invalid
    service was requested or an invalid syntax was utilized.
    """

    def __init__(self, message)  -> None :
        """
        Initializer

        Parameters:
            message (str): The cause of the exception
        """
        
        self.message = message
        super().__init__()


    def __str__(self)  -> str :
        """
        This method displays the exception's cause.
        """

        return f"An exception was raised as a result of an invalid SQL request: {self.message}"
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"SQLRequestException({self.message})"