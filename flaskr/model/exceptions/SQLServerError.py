
class SQLServerError(RuntimeError) :
    """
    This custom exception is raised internally by the server when an unanticipated
    error occurred while performing an database operation.
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

        return f"An unanticipated error occurred during a database operation: {self.message}"
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"SQLServerError({self.message})"

