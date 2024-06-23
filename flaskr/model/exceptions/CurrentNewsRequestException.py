
class CurrentNewsRequestException(Exception) :
    """
    This custom exception is raised internally by the server when it cannot retrieve
    the current news information from the current news API endpoint.
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

        return f"An exception occurred while retrieving News Data: {self.message}"
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"CurrentNewsRequestException({self.message})"
