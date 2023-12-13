#Rachel Farzan
#12/10/23
#CMSC 508

import requests

#This function confirms that the hw8.qmd can connect to this file
def hello_from_utils():
    return "Hello from utils (the newest one)"

#This function takes in an API link, and calls it. It ensures that the API call can be made (and prints an error if not), and returns the results of the call.
def api_call(link):
    data = None
    response = requests.get(link)
    if response.status_code == 200:
        # Request was successful
        data = response.json()  ## Returns the json response as a python dictionary
    else:
        print("Request failed with status code:", response.status_code)
    return data

#This function takes in and end point and a query, and it calls the API by combining the two parameters. It uses api_call to return the results of the call.
def api_query(end_point, query):
    return api_call(end_point + query)