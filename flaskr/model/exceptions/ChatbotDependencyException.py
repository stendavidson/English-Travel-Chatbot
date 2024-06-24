
class ChatbotDependencyException(RuntimeError) :
    """
    This custom exception is raised internally by the server when an instance of
    the GoTravel chatbot cannot resolve a dependency issue.
    """

    def __init__(self)  -> None :
        """
        Initializer
        """

        super().__init__()


    def __str__(self)  -> str :
        """
        This method displays the exception's cause.
        """

        return f"Exception the chatbot could not load all of its dependencies."
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"ChatbotDependencyException()"
