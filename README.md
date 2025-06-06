# England Tourist Chatbot
 
## Author
Sten Healey

## About
This flask based web service creates a simple chatbot API endpoint for tourists and travellers in England. It integrate with [Open Weather API](https://openweathermap.org/api) and [Current API](https://currentsapi.services/en), these services provide the chatbot with weather and news information and assist in populating the chatbot's responses. 

To improve performance and cost scalability data from the two external API endpints is regularly cached in an SQLite database rather than retrieving all data upon each request.

## Pre-requisites

Please ensure you have [Python 3.7 64 bit](https://www.python.org/ftp/python/3.7.9/python-3.7.9-amd64.exe) installed and either added to PATH or set as the default python interpreter for your virtual environment. Steps to add python to PATH can be found here: [Add Python to Path](https://realpython.com/add-python-to-path/).

API Keys:
1. Please create an [Open Weather API](https://openweathermap.org/api) Key
2. Please create a [Current API](https://currentsapi.services/en) Key
3. Please create a file in the root of your project folder `C:\..\..\GoTravelBot>` called `api_key.text`.
4. Please add the API keys in their respective order.

## How to run
Once all the pre-requisites are installed or setup please navigate to your project folder `C:\..\..\GoTravelBot>` and execute the following commands:

> [!NOTE]
> You will need to execute these as administrator - I encountered some difficulties with permissions.

1. Donwload the python modules:

```console
pip install -r requirements.txt
```

2. Run the python application:

```console
python -m flaskr.controller.app
```

3. Navigate to the [Go Travel Bot Example Site](http://localhost/index)

4. Try some generic greetings or some more complex examples:

>- What is the weather like in Cumbria today?
>- When would you recommend visiting Oxford?
>- Has anything happened recently in Norwich?
>- What is the weather forecast for Cambridge?
>- What is the best tourist destination to visit today?

If it provides a suggestion just copy and paste it into the chatbot.
