from threading import Lock
from typing import Callable

from ..utils.validation_utils import with_type_validation


class ThreadingContext :
    """
        This class creates simple threading context and allows any given
        function to operate in a thread safe way.
    """

    def __init__(self)  -> None :
        """
        Initializer
        """

        self.lock : Lock = Lock()
        """
        A mutex lock on the shared_list to allow function returns to be stored in a
        thread safe manner.
        """

        self.exception_lock : Lock = Lock()
        """
        A mutex lock on the exceptions list to allow exceptions to be stored in a
        thread safe manner.
        """

        self.exceptions : list = []
        """
        A simple shared exceptions list to store exceptions thrown outside the thread
        context.
        """

    @with_type_validation(object, list)
    def with_threading_context(self, shared_list : list) -> Callable :
        """
            This function allows the underlying decorator to be parameterized.

            Parameters:
                shared_list (list): the shared list to be populated by the thread.
            """

        def decorator(func : Callable) -> Callable :
            """
            This is the decorator function

            Parameters:
                func (function): the function to be wrapped
            """
            
            def wrapper(*args, **kwargs) -> None :
                """
                This function wraps the function that is being decorated.

                Parameters:
                    *args (list): a list of parameters
                    **kwargs (dict): a dictionary of named parameters
                """
                
                # Generic exception handling catches all exceptions to re-throw
                try :
                    
                    # The shared list is written to in a thread safe manner
                    with self.lock :
                        
                        shared_list.append(func(*args, **kwargs))

                except Exception as e :
                    
                    # The shared exception list is written to in a thread safe manner
                    with self.exception_lock :
                        self.exceptions.append(e)
                
            return wrapper
        
        return decorator




