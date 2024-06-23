
class InvalidORMClassException(ValueError) :
    """
    This custom exception is raised internally by the server when an invalid ORM
    class is retrieved.
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

        return f"An invalid ORM class was selected, only Weather and News are valid ORM classes."
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"InvalidORMClassException()"
