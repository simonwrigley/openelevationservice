# -*- coding: utf-8 -*-

from openelevationservice.server import create_app
from openelevationservice.server.utils.logger import get_logger
from openelevationservice.server.config import SETTINGS
from openelevationservice.server.db_import.models import db

import os
import requests
import subprocess
import zipfile
from bs4 import BeautifulSoup

try:
    from io import BytesIO
except:
    from StringIO import StringIO

log = get_logger(__name__)
tiles_dir = os.path.join(os.getcwd(), 'tiles')

app = create_app()

@app.cli.command()
def download():
    """Downloads SRTM tiles to disk"""
    base_url = r'http://data.cgiar-csi.org/srtm/tiles/GeoTIFF/'
    
    # Create session for authentication
    session = requests.Session()
    session.auth = tuple(SETTINGS['srtm_parameters'].values())
    response = session.get(base_url)
    
    soup = BeautifulSoup(response.content)
    
    # First find all 'a' tags starting href with srtm*
    for link in soup.find_all('a', attrs={'href': lambda x: x.startswith('srtm')}):
        # Then load the zip data in memory
        with zipfile.ZipFile(BytesIO(session.get(base_url + link.text).content)) as zip_obj:
            # Loop through the files in the zip
            for filename in zip_obj.namelist():
                # Don't extract the readme.txt
                if filename != 'readme.txt':
                    data = zip_obj.read(filename)
                    # Write byte contents to file
                    with open(os.path.join(tiles_dir, filename), 'wb') as f:
                        f.write(data)
        
        log.debug("Downloaded file {}".format(link.text))
        

@app.cli.command()
def create():
    db.create_all()
    log.debug("Table {} was created.".format(SETTINGS['provider_parameters']['table_name']))
    
    
@app.cli.command()
def drop():
    db.drop_all()
    log.debug("Table {} was dropped.".format(SETTINGS['provider_parameters']['table_name']))
    

@app.cli.command()
def importdata(): 
    
    log.info("Starting to import data...")

    #TODO: Add logic for docker setup  
#    docker_id = subprocess.run(["sudo docker ps -a",
#                    " | grep postgis"
#                    " | awk '{print $1}'"],
#                    stdout=subprocess.PIPE)
    
    cmd_docker = 'sudo docker exec 3fe21d5b4a78 '
        
    cmd_raster = 'raster2pgsql -a -I -C -F -P -M {}/*.tif {} | sudo -u {} psql -d {}'.format(tiles_dir,
                                          pg_settings['table_name'],
                                          pg_settings['user_name'],
                                          pg_settings['db_name']
                                          )
    subprocess.run([cmd_docker, cmd_raster], 
                   stdout=subprocess.DEVNULL, 
                   stderr=subprocess.STDOUT)
    
    log.info("Imported data successfully!")
    
if __name__=='__main__':
    create()