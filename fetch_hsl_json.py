import datetime
import requests
from tqdm import tqdm
import tarfile
import urllib
import pandas as pd
import json
import glob
import dateutil
import logging


TARGET_FOLDER = "hsl_data"
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')


def fetch_tar(year, month, target_folder=TARGET_FOLDER):

    s = datetime.datetime(year=year, month=month, day=1).strftime("%Y%m")
    url = "https://dev.hsl.fi/citybike/stations/stations_" + s + ".tar.xz"
    r = requests.get(url)


    urllib.request.urlretrieve(url,"./"+target_folder+"/"+"temp.tar.xz")

    with tarfile.open('./hsl_data/temp.tar.xz') as tar:
        # Go over each member
        for member in tqdm(iterable=tar.getmembers(), total=len(tar.getmembers()), unit="file"):
            # Extract member
            tar.extract(member=member, path="./" + target_folder + "/")


# example
# fetch_tar(2018, 9)

for month in range(8,13):
    year = 2018
    s = datetime.datetime(year=year, month=month, day=1).strftime("%Y%m")
    print(s)
    fetch_tar(year, month)

for month in range(1,7):
    year = 2019
    s = datetime.datetime(year=year, month=month, day=1).strftime("%Y%m")
    print(s)
    fetch_tar(year, month)


def fetch_2019(target_folder = TARGET_FOLDER):
    start_time = datetime.datetime.strptime("2019-06-01T00:01","%Y-%m-%dT%H:%M")
    end_time = datetime.datetime.strptime("2019-06-27T05:48","%Y-%m-%dT%H:%M")

    time = start_time

    target_filenames = []
    while time < end_time:
        target_filenames.append(time.strftime("%Y%m%dT%H%M")+"01Z.json")
        time = time + datetime.timedelta(minutes=1)

    print(len(target_filenames))
    print(target_filenames)

    for s in tqdm(target_filenames, unit="files"):
        # print(s)
        url = "https://dev.hsl.fi/citybike/stations/stations_" + s
        r = requests.get(url=url)
        target = "./" + target_folder + "/stations_" + s
        if r.status_code == 200:
            with open(target, 'wb') as outfile:
                outfile.write(r.content)
            #print("Stored " + s + "")
        else:
            print("File " + s + " not found on server, skipping.")



def get_spaces(data):
    # spaces = data.bikesAvailable + data.spacesAvailable
    # names = data.name

    #d = data.assign(space = lambda frame: (frame.bikesAvailable + frame.spacesAvailable))
    return data.groupby('name').agg({'space': min})


def json_to_csv():
    json_files = glob.glob("./hsl_data/*.json")
    data_list = []
    for curfile in tqdm(json_files[0:len(json_files)], unit="files"):
        try:
            data_list.append(pd.DataFrame(json.load(open(curfile))["result"]).assign(timestamp=dateutil.parser.parse(curfile.rsplit("_")[-1].split(".")[0]).strftime("%d/%m/%Y %H:%M:%S")))
        except json.decoder.JSONDecodeError:
            print("Invalid JSON, skipping...")
        except KeyError:
            print("Key ['result'] not in file, skipping...")
        except UnicodeDecodeError:
            print("Invalid encoding, skipping...")

    df = pd.concat(data_list)
    logging.debug("Df concat completed.")
    del data_list

    # drop stations with empty coordinates
    df = df[df.coordinates != ""]
    #coordinates to lat and long
    df[["lat","lon"]] = df.coordinates.str.split(",", expand=True)
    # round lat and long to fix errors
    df.lat = round(df.lat.astype(float), 4)
    df.lon = round(df.lon.astype(float), 4)
    df.drop(columns=["coordinates"], inplace=True)
    logging.debug("Coordinates completed.")


    # rename style column to status
    df.rename(columns = {'style': 'status'}, inplace=True)

    # transform API call times to correct timezone (US/Mountain -> Europe/Helsinki)
    # Not necessary anymore
    # server_timezone = pytz.timezone("US/Mountain")
    # helsinki_timezone = pytz.timezone("Europe/Helsinki")
    df["datetime"] = [datetime.datetime.strptime(x, "%d/%m/%Y %H:%M:%S") for x in df.timestamp]
    logging.debug("Datetime stripped.")
    #df["datetime"] = [server_timezone.localize(x).astimezone(helsinki_timezone) for x in df.datetime]
    df["date"] = [datetime.datetime.strftime(x, "%Y-%m-%d") for x in df.datetime]
    df["time"] = [datetime.datetime.strftime(x, "%H:%M") for x in df.datetime]
    logging.debug("Date and time converted.")


    #fix types
    df.name = df.name.astype(str)
    df.status = df.status.astype(str)
    df.timestamp = df.timestamp.astype(str)
    df.date = df.date.astype(str)
    df.time = df.time.astype(str)
    logging.debug("Type changes completed.")

    #rename columns
    df.rename(columns={'avl_bikes': 'bikesAvailable', 'free_slots': 'spacesAvailable',
                        'operative': 'allowDropoff', 'total_slots': 'totalSpaces',
                         'timestamp': 'Timestamp'},inplace=True)

    logging.debug("Df rename completed.")




    # reset index for feather
    df.reset_index(drop=True, inplace=True)
    logging.debug("Df reset_index completed.")

    df.to_feather('./data/fillaridata.feather')

json_to_csv()

stamps = [dateutil.parser.parse(x.rsplit("_")[-1].split(".")[0]).strftime("%d/%m/%Y %H:%M:%S") for x in json_files]
dates = [datetime.datetime.strftime(datetime.datetime.strptime(x, "%d/%m/%Y %H:%M:%S"), "%Y-%m-%d") for x in stamps]
times = [datetime.datetime.strftime(datetime.datetime.strptime(x, "%d/%m/%Y %H:%M:%S"), "%H:%M") for x in stamps]

time_parsed = pd.DataFrame({
    "stamps": stamps,
    "dates": dates,
    "times": times,
}, index=range(0,len(stamps)))

