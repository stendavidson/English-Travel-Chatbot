import pandas as pd

from ..exceptions.InvalidTemplateException import InvalidTemplateException



def create_corpus_from_template(csv_file : str, locations : list, num_templates : int = None) -> pd.DataFrame:
    """
    This function generates training corpus for the GoTravelBot class.

    Parameters:
        csv_file (str): The file path to the corpus template
        locations (list): The locations to substitute into the template.
        num_templates (int): The number of templates to load
    """

    # Input validation
    if not isinstance(csv_file, str) :

        raise TypeError(f"Invalid input type \"{csv_file.__class__.__name__}\" "\
                        f"for function create_corpus_from_template, \"str\" was expected.")

    elif not isinstance(locations, list) :

        raise TypeError(f"Invalid input type \"{locations.__class__.__name__}\" "\
                        f"for function create_corpus_from_template, \"list\" was expected.")
    
    elif not isinstance(num_templates, int) and not num_templates == None :

        raise TypeError(f"Invalid input type \"{num_templates.__class__.__name__}\" "\
                        f"for function create_corpus_from_template, \"int\" was expected.")


    corpus : pd.DataFrame | None = None
    
    # Exception handling
    try:

        corpus = pd.read_csv(csv_file, delimiter=",", names=["input", "response"], header=None, dtype=str, nrows=num_templates)

    except FileNotFoundError :
        raise FileNotFoundError(f"The csv template could not be found at this location: {csv_file}")
    except pd.errors.ParserError :
        raise InvalidTemplateException("the file could not be parsed")
    except pd.errors.EmptyDataError :
        raise InvalidTemplateException("the file didn't contain any corpus")
    except Exception :
        raise InvalidTemplateException("an unknown error was raised while generating the template")

    # Clean up input templates
    corpus.dropna()
    corpus["input"] = corpus["input"].str.strip().str.replace("  ", " ")
    corpus["response"] = corpus["response"].str.strip().str.replace("  ", " ")
    corpus.drop_duplicates("input", inplace=True)

    # Create conversation pairs for all locations
    for location in locations :
        
        corpus[f"input-{location}"] = corpus["input"].str.replace("{location}", location, regex=False)
        corpus[f"response-{location}"] = corpus["response"].str.replace("output-location", location, regex=False)

    corpus = corpus.drop(columns=["input", "response"])

    conversations : pd.DataFrame = pd.DataFrame()

    conversations["input"] = pd.concat([corpus[i] for i in corpus.columns if "input" in i])
    conversations["response"] = pd.concat([corpus[i] for i in corpus.columns if "response" in i])

    return conversations