# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import copy
from rasa_sdk.events import AllSlotsReset, SlotSet
import random
from datetime import datetime
CRENDENTIAL = {"x-rapidapi-host":"imdb8.p.rapidapi.com", "x-rapidapi-key":"f639d442b8mshd9c9379c543422dp176783jsn41fd5948fe2a"}

class SearchMovieByActor(Action):

    def name(self) -> Text:
        return "action_search_movie_by_actor"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        url = "https://imdb8.p.rapidapi.com/auto-complete"
        if tracker.get_intent_of_latest_message() == "affirm":
            actor = tracker.get_slot('PERSON')
        else:
            actor = tracker.latest_message["text"]
        # actor = tracker.latest_message['entities'][0]['value']
        querystring = {"q":actor}
        print(querystring)
        headers = CRENDENTIAL
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        if "d" not in response:
            dispatcher.utter_message(text = "There is something wrong with my system. Could you please repeat the command from begining")
            return []
        for i in range(len(response['d'])):
            ids = response['d'][i]['id']
            if "nm" in ids:
                break
            if i == (len(response['d'])-1) and "nm" not in ids:
                dispatcher.utter_message(text="We cannot find the information. Sorry for my rusty skills")
                return []
        if ids == None:
            dispatcher.utter_message(text="We cannot find the information. Sorry for my rusty skills")
            return []
        querystring = {"nconst":ids}
        url = "https://imdb8.p.rapidapi.com/actors/get-known-for"
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        films = []
        message = actor + " is well known for: "
        for i in response:
            films.append(i["title"]["title"])
            message += i["title"]["title"]
            message +=", "

        dispatcher.utter_message(text=message)
        return []

class SearchMovieInfo(Action):

    def name(self) -> Text:
        return "action_search_movie_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_intent_of_latest_message() == "affirm":
            title = tracker.get_slot('movie_title')
        else:
            title = tracker.latest_message["text"]
        act = tracker.get_slot('act')
        url = "https://imdb8.p.rapidapi.com/auto-complete"
        querystring = {"q":title}
        headers = CRENDENTIAL
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        for i in range(len(response['d'])):
            ids = response['d'][i]['id']
            if "tt" in ids:
                break
            if i == (len(response['d'])-1) and "tt" not in ids:
                dispatcher.utter_message(text="We cannot find the information. Sorry for my rusty skills")
                return []
        if ids == None:
             dispatcher.utter_message(text="We cannot find the information. Sorry for my rusty skills")
             return []
        url = "https://imdb8.p.rapidapi.com/title/get-full-credits"
        querystring = {"tconst": ids}
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        # dispatcher.utter_message(text = tracker.latest_message["text"])
        if "direct" in act:
            message = "It is " + response["crew"]["director"][0]["name"] + "."
            if len(response["crew"]["director"]) > 1:
                message += "The movie is also directed by "
                for i in range(1,len(response["crew"]["director"])):
                    message += response["crew"]["director"][i]["name"]
            dispatcher.utter_message(text=message)
            return []
        elif "act" in act:
            message = "The movie stars "
            for i in range(3):
                message += response["cast"][i]["name"]
                message+= ","
            dispatcher.utter_message(text=message)
            return []
        elif "release" in act:
            message = " The movie is released in " + str(response["base"]["year"])
            dispatcher.utter_message(text = message)
            return []
        elif "plot" in act:
            sub_url = "https://imdb8.p.rapidapi.com/title/get-overview-details"
            sub_querry = {"tconst":ids}
            sub_response = requests.request("GET", sub_url, headers=headers, params=sub_querry).json()
            message = sub_response["plotSummary"]["text"]
            dispatcher.utter_message(text = message)
            return []
        elif "rating" in act:
            sub_url = "https://imdb8.p.rapidapi.com/title/get-ratings"
            sub_querry = {"tconst": ids}
            sub_response = requests.request("GET", sub_url, headers=headers, params= sub_querry).json()
            message = "Rating of " + title + " is: " + str(sub_response["rating"])
            dispatcher.utter_message(text = message)
            return []
        else:
            message = "Information about movie \n"
            message += "Movie is directed by " + response["crew"]["director"][0]["name"] + "."
            message += "Starring in movie is" + response["cast"][0]["name"] + "."
            dispatcher.utter_message(text = message)
            return []

        return []

class ActionRecommendation(Action):

    def name(self) -> Text:
        return "action_recommendation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        headers = CRENDENTIAL
        if tracker.get_intent_of_latest_message() == "affirm":
            genre = tracker.get_slot("genre")
        else:
            genre = tracker.latest_message["text"]
        url = "https://imdb8.p.rapidapi.com/title/get-popular-movies-by-genre"
        querystring = {"genre":genre}
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        rd_number = random.randint(0,100)
        ids = response[rd_number].rsplit('/',2)[1]
        url = "https://imdb8.p.rapidapi.com/title/get-details"
        querystring = {"tconst":ids}
        response = requests.request("GET", url, headers=headers, params=querystring).json()
        title = response["title"]

        dispatcher.utter_message(text="Let's try {} today. Hope you will like that".format(title))
        return []

class ActionVerifyPerson(Action):

    def name(self) -> Text:
        return "action_verify_person"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        verify = tracker.get_slot("PERSON")
        dispatcher.utter_message(text="You mean, {}, right?".format(verify))
        return []

class ActionVerifyTitle(Action):

    def name(self) -> Text:
        return "action_verify_title"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        txt = tracker.latest_message["text"]
        if "act" in txt or "star" in txt:
            slots = "act"
        elif "direct" in txt:
            slots = "direct"
        elif "release" in txt or "when" in txt:
            slots = "release"
        elif "plot" in txt or "summary" in txt:
            slots = "plot"
        elif "rating" in txt or "rate" in txt or "score" in txt or "imdb" in txt:
            slots = "rating"
        else:
            slots = "None"

        verify = tracker.get_slot('movie_title')
        dispatcher.utter_message(text="You mean, {}, right?".format(verify))
        return [SlotSet("act", slots)]

class ActionVerifyGenre(Action):

    def name(self) -> Text:
        return "action_verify_genre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # txt = tracker.latest_message["text"]
        verify = tracker.get_slot('genre')
        dispatcher.utter_message(text="You mean, {}, right?".format(verify))

        return []


class ActionTellTime(Action):

    def name(self) -> Text:
        return "action_tell_time"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        time = datetime.now()
        time = time.strftime("%H:%M")
        dispatcher.utter_message(text="It's {}".format(time))

        return []

class ActionTellWeatherDefault(Action):

    def name(self) -> Text:
        return "action_tell_weather_default"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        url = "https://weatherapi-com.p.rapidapi.com/current.json"
        headers = {
    'x-rapidapi-host': "weatherapi-com.p.rapidapi.com",
    'x-rapidapi-key': "f639d442b8mshd9c9379c543422dp176783jsn41fd5948fe2a"
    }
        if tracker.get_intent_of_latest_message() == "weather":
            slots = "Trento"
        else:
            slots = tracker.get_slot("city") 
        querystring = {"q":slots}
        response = requests.request("GET", url, headers=headers, params=querystring).json()

        if "error" in response:
            dispatcher.utter_message(text = "Sorry but location not found")
            return []

        temper = response["current"]["temp_c"]
        real_temper = response["current"]["feelslike_c"]
        condition = response["current"]["condition"]["text"]
        dispatcher.utter_message(text="The current temperature in {} is {} but it's actually feels like {}. The weather is {}. \n For others city, please repeat the command along with the city name".format(slots,temper, real_temper, condition))

        return []


