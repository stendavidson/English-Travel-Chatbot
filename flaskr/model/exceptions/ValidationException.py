
class ValidationException(RuntimeError) :
    """
    This custom exception is raised internally by the server when the validation
    utility decorator has an incorrect number of types.
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

        return f"An exception occurred performing parameter validation: an "\
                "incorrect number of \"type\" arguments were entered."
    

    def __repr__(self) -> str :
        """
        This method displays the object's intialization specification as a string.
        """

        return f"ValidationException()"
