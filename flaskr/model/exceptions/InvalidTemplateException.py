
class InvalidTemplateException(RuntimeError) :
    """
    This custom exception is raised internally by the server when an the training
    corpus cannot be generated from the template files.
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

        return f"An exception was raised while generating the training corpus: {self.message}"
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"InvalidTemplateException({self.message})"
