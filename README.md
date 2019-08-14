# city_bikes

These scripts provide a starting point for downloading the city bike data from HSL, and making a very simple 
dashboard from that with Plotly.



## Getting started

Get all the files into your chosen directory with git:

`git clone https://github.com/tjpajala/city_bikes.git`

Make target folder for downloaded HSL data and final combined data:
`mkdir hsl_data data`

Install necessary packages with conda
`conda install pyarrow requests tqdm dash`

Change fetching time parameters in `fetch_hls_json.py`
Run fetching with:

`python -m fetch_hsl_json`

Save config file named `config.py` that has your Mapbox Access Token (for dashboard maps)
`echo "MAPBOX_ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN_HERE'" > config.py`

Start dashboard with:

`python -m dashboard`

The interactive Dash app generated from the results is available at `localhost:8050`.
