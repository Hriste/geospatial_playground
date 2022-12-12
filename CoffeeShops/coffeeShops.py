'''
Coffee Shops of San Francisco
Data downloaded from my google maps list of Coffee shops I like or want to try from Google Takeout 

Christina Paolicelli
'''

import pandas as pd
import geopandas as gpd
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import zipfile
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

FIRST_RUN = False 

def getShopLocation(url, browser) -> str:
    if browser is None:
        return ''

    sleep(2)
    try: 
        browser.get(url)
        address = WebDriverWait(browser, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-item-id=\"address\"]")))
        #address = browser.find_element(By.CSS_SELECTOR, "[data-item-id=\"address\"]")
        print(f'Address: {address.text}')
        return address.text
    except:
        print('Failed :(')
        return ''

def WebScrape(df) -> None:
    # Now we need to webscrape to get the location from the links
    # Following this tutorial (https://medium.com/swlh/scraping-google-maps-using-selenium-3cec08eb6a92)

    # Create the Web driver options
    #  Can't run headless for Safari :(
    browser = webdriver.Safari()

    df['address'] = df['URL'].apply(lambda x: getShopLocation(x, browser))
    browser.quit()

    # Save to file so I can just load the second time :) 
    df.to_csv("addresses.csv")

if FIRST_RUN:
    # Read CSV of coffee shops in & Webscrape for addresses - this takes some time
    # so we save it off and only do this the first time
    df = pd.read_csv('CoffeeShops.csv')
    WebScrape(df)

df_addresses = pd.read_csv('addresses.csv')

# CLEANUP
df_addresses['address'] = df_addresses['address'].apply(lambda x: str(x).strip())
df_addresses = df_addresses[df_addresses['address'].str.contains('San Francisco')]

# Now onto Mapping!

# Following this tutorial for shapefile (https://medium.com/@sindhu.ravikumar/visualizing-spatial-data-with-geopandas-and-contextily-10e9b8e71e49)
# Get Shapefile with ! wget https://www2.census.gov/geo/tiger/TIGER2017//ROADS/tl_2017_06075_roads.zip

# Unzip on First Run
if FIRST_RUN:
    with zipfile.ZipFile('tl_2017_06075_roads.zip', 'r') as zip_ref:
        zip_ref.extractall('shapefiles')

# Import Shapefile as GeoPandas Data Frame 
geo_df = gpd.read_file('shapefiles/tl_2017_06075_roads.shp')

# Initialize the plot 
fig, ax = plt.subplots(figsize=(10,10))
geo_df.plot(ax=ax, alpha=0.2)
ax.set_axis_off()

# OK Now let's plot some coffee shops!
geo_df = geo_df.to_crs(epsg=3857)

# Get Coffee Shop locations from address by geocoding 
# Geocoding based on https://cduvallet.github.io/posts/2020/02/road-trip-map
geolocator = Nominatim(user_agent="homes", timeout=10)
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
df_addresses['location'] = df_addresses['address'].apply(geocode)
#df_addresses.to_csv("location.csv")

df_location = df_addresses#pd.read_csv('location.csv')
df_location = df_location.dropna(subset=['location'])
df_location['latitude'] = df_location['location'].apply(lambda x: x.latitude)
df_location['longitude'] = df_location['location'].apply(lambda x: x.longitude)
df_location['geometry'] = gpd.points_from_xy(df_location['longitude'], df_location['latitude'])
gdf = gpd.GeoDataFrame(df_location)

gdf.plot(ax=ax, marker='.', markersize=150)

# Save 
fig.tight_layout()
plt.title('San Francisco Coffee Shops')
plt.savefig('sf_coffee.png')
