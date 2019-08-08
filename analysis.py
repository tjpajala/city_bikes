import pandas as pd

desired_width = 640
pd.set_option('display.width', desired_width)
pd.set_option('display.max_columns', 10)

DATA_FOLDER = './data'
SOURCE_FILENAME = 'fillaridata.feather'
# load data


def load_and_clean_data(data_folder=DATA_FOLDER, filename=SOURCE_FILENAME):
    data = pd.read_feather(data_folder + '/' + filename)

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