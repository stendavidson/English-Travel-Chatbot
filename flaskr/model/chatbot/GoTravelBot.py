from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
from chatterbot.response_selection import get_first_response
from chatterbot.comparisons import SpacySimilarity
import pandas as pd
from spacy.cli.download import download
from spacy.util import load_model
import os

from ..exceptions.ChatbotDependencyException import ChatbotDependencyException
from ..exceptions.UntrainedChatbotException import UntrainedChatbotException
from ..utils.validation_utils import with_type_validation



os.environ["CHATTERBOT_SHOW_TRAINING_PROGRESS"] = "False"

class GoTravelBot :
    """
    This class encapsulates the chatbot functionality that is desired for the
    GoTravel website.
    """

    @with_type_validation(object, str, dict)
    def __init__(self, database_path : str, recommendations : dict)  -> None:
        """
        Initializer

        Parameters:
            database_path (str): The path to the SQLite database.
        """

        # Dependency resolution - spacy no longer uses model name shortcuts
        try :

            try :
                load_model(name="en")
            except OSError :
                download("en")

        except Exception :
            
            raise ChatbotDependencyException()

        # The ChatBot is created
        self.bot : ChatBot = ChatBot(
            "GoTravel Bot",
            logic_adapters=[
                {
                    "import_path" : "flaskr.model.chatbot.CustomBestMatch.CustomBestMatch",
                    "statement_comparison_function" : SpacySimilarity,
                    "response_selection_method" : get_first_response,
                    "maximum_similarity_threshold" : 0.9
                }
            ],
            storage_adapter = "chatterbot.storage.SQLStorageAdapter",
            database_uri = f"sqlite:///{database_path}",
            read_only=False,
            show_training_progress=False
        )
        
        # This indicates whether the bot is already trained or not
        self.trained : bool = self.bot.storage.count() > 0

        # A list of recommendation pairs is stored
        self.recommendations = recommendations


    @with_type_validation(object, list)
    def train(self, training_data : list) -> None :
        """
        This method trains the chatterbot using the input training data

        Parameters:
            training_data (list): An input list of conversation inputs vs responses
        """

        # The model is pre-trained on a corpus of english greetings this is to
        # facilitate simple initial interactions.
        base_trainer = ChatterBotCorpusTrainer(self.bot)
        base_trainer.train("chatterbot.corpus.english.greetings")

        # The model is then trained on a corpus of business related prompts to handle
        # a broader intersection of requests.
        for converation in training_data :

            ListTrainer(self.bot).train(converation)

        self.trained = True


    @with_type_validation(object, str)
    def get_response(self, input_text : str) -> str :
        
        # This function should not be used prior to training.
        if not self.trained :

            raise UntrainedChatbotException()

        response : Statement = None # type: ignore

        attempts : int = 3

        output : str = "Not quite sure what you are asking can you try asking something else?"

        # Sometimes SQL threading errors cause low confidence responses
        while attempts > 0 :

            response = self.bot.get_response(input_text)

            output = response.text

            if response.confidence < 0.9 :
                attempts = attempts - 1
            else :
                attempts = -1

        # If the bot isn't confident then return suggestion
        if attempts == 0 :
            
            # If a suggestion doesn't exist return a default
            try :

                if response.confidence > 0.7 :
                    output = f"Hi, did you intend to ask: {self.recommendations[output]}"
                else :
                    output = "Not quite sure what you are asking can you try asking something else?"

            except KeyError :
                output = "Not quite sure what you are asking can you try asking something else?"
                
        return output

                    



        