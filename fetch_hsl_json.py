import datetime
import requests
from tqdm import tqdm
import tarfile
import io
import pandas as pd
import json
import os
import urllib

TARGET_FOLDER = "hsl_data"


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


def json_to_csv():
    import os
    import pandas as pd
    import json
    import itertools
    import glob
    #json_files = os.listdir("./hsl_data")
    #json_files = [f for f in os.listdir('./hsl_data') if re.match('.json', f)]
    json_files = glob.glob("./hsl_data/*.json")
    df = pd.DataFrame()
    data_list = []
    for curfile in tqdm(json_files[0:len(json_files)], unit="files"):
        try:
            data_list.append(json.load(open(curfile))["result"])
        except json.decoder.JSONDecodeError:
            print("Invalid JSON, skipping...")
        except KeyError:
            print("Key ['result'] not in file, skipping...")
        except UnicodeDecodeError:
            print("Invalid encoding, skipping...")
        #tmp = pd.read_json("./hsl_data/"+file)
        #with open("./hsl_data/"+curfile, 'r') as f:
            #tmp = pd.read_json(json.dumps(json.load(f)["result"]), orient="records")
        #df=df.append(tmp)
    d = list(itertools.chain.from_iterable(data_list))
    df = pd.DataFrame(d)
    df.to_csv('./data/fillaridata.csv')

json_to_csv()