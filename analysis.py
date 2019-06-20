import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
desired_width = 640
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', 10)

DATA_FOLDER = './data'
SOURCE_FILENAME = 'fillaridata.csv'
# load data


def load_and_clean_data(data_folder=DATA_FOLDER, filename=SOURCE_FILENAME):
    data = pd.read_csv(data_folder + '/' + filename)

    # round lat and long to fix errors
    data.lat = round(data.lat, 4)
    data.lon = round(data.lon, 4)

    # transform API call times to correct timezone (US/Mountain -> Europe/Helsinki)
    server_timezone = pytz.timezone("US/Mountain")
    helsinki_timezone = pytz.timezone("Europe/Helsinki")
    data["datetime"] = [datetime.strptime(x, "%d/%m/%Y %H:%M:%S") for x in data.date]
    data["datetime"] = [server_timezone.localize(x).astimezone(helsinki_timezone) for x in data.datetime]
    data.date = [datetime.strftime(x, "%d/%m/%Y") for x in data.datetime]
    data["time"] = [datetime.strftime(x, "%H:%M") for x in data.datetime]

    # drop ghost bike locations
    data = data[data.lat > 60]

    # ensure that bikesAvailable is at least 0
    data["bikesAvailable"]=data.bikesAvailable.clip(lower=0)
    return data


def aggregate_data(data, groupby="name"):
    # calculate aggregate data
    agg_data = data.groupby(groupby).agg({
        'allowDropoff': lambda x: x.mode()[0],
        'bikesAvailable': 'mean',
        'lat': lambda x: x.mode()[0],
        'lon': lambda x: x.mode()[0],
        'name': lambda x: x.mode()[0],
    })

    # add std of bikes available
    agg_data.rename(columns = {'bikesAvailable': 'bikesAvailable_mean'}, inplace=True)
    agg_data["bikesAvailable_std"] = data.groupby(groupby)[['bikesAvailable']].std()
    return agg_data


data = load_and_clean_data(DATA_FOLDER, SOURCE_FILENAME)
agg_data = aggregate_data(data)