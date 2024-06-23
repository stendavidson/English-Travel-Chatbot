from typing import Any, Callable

from ..exceptions.ValidationException import ValidationException


def with_type_validation(*types)  -> None :
    """
    This function enables the underlying decorator function to be 
    parameterized.

    Parameters:
        *types (list[type]): the types corresponding to the wrapped functions
        input parameters types.
    """

    def decorator(func : Callable) -> Callable :
        """
        This is the decorator function itself

        Parameters:
            func (Callable): The function being wrapped by the decorator.
        """

        def wrapper(*args, **kwargs) -> Any :
            """
            This function peforms input type validation on the wrapped function.

            Parameters:
                *args (Any): The wrapped functions inputs
                **kwargs (Any): The wrapped functions keyword inputs
            """

            inputs = list(args) + list(kwargs.values())


            # The decorator must have the correct number of arguments - input
            # validation is handled.
            if len(inputs) != len(types) :

                raise ValidationException()
            
            
            for i in range(len(types)):
                
                # The decorator only takes "type" objects - input validation is
                # handled.
                if not isinstance(types[i], type) :

                    raise TypeError("All inputs must be \"type\" objects")

                # The decorator validates the wrapped functions inputs
                if not isinstance(inputs[i], types[i]) :

                    raise TypeError(f"Invalid input type \"{inputs[i].__class__.__name__}\" "\
                                    f"for function {func.__name__}, \"{types[i].__class__.__name__}\" was expected.")
        
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator



            



