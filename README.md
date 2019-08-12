# city_bikes

These scripts provide a starting point for downloading the city bike data from HSL, and making a very simple 
dashboard from that with Plotly.



## Getting started

Get all the files into your chosen directory with git:

`git clone https://github.com/tjpajala/city_bikes.git`

Make target folder for HSL data:
`mkdir hsl_data`

Change fetching time parameters in `fetch_hls_json.py`
Run fetching with:

`python -m fetch_hsl_json.py`

Start dashboard with:

`python -m dashboard.py`

The interactive Dash app generated from the results is available at `localhost:8050`.
