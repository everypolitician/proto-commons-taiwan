import json
import fiona
import fiona.crs
import fiona.transform
import logging
import sys
import pprint
import itertools

from shapely.geometry import shape, mapping
from shapely.ops import unary_union



def village_national_constituency_map(constituencies):
    m = {}
    for county in constituencies:
        for region in constituencies[county]['regions']:
            constituency_wikidata_id = (region['wikidata_item'].split('/')[-1])
            for district in region['district']:
                for villcode in region['district'][district]:
                    m[villcode]=constituency_wikidata_id
    return m




if  __name__ == "__main__":

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    constituency_json_path = "/home/will/dev/proto-commons-taiwan/scripts/national-constituencies-to-villages.json"
    villages_path = "/home/will/data/concorde_data/taiwan/source/1070129_VILLAGE/VILLAGE_MOI_1070119.shp"
    villages_out_path = "/home/will/data/concorde_data/taiwan/scratch/villages-constituencies.shp"
    #constituencies_out_path = "/home/will/dev/proto-commons-taiwan/boundaries/national-constituencies/national-constituencies.shp"
    missing_villages = "/home/will/data/concorde_data/taiwan/scratch/missing-villages-national-constituencies.txt"



    open(missing_villages, 'w', encoding='utf-8').close()

    with open(constituency_json_path, 'r') as constituencies_file:
        constituencies_json = json.load(constituencies_file)

    village_to_constituencies = village_national_constituency_map(constituencies_json)

    with fiona.open(villages_path, 'r', 
                    crs=fiona.crs.from_epsg(3824), 
                    encoding='Big5') as villages_shp:

        src_driver = villages_shp.driver
        dst_schema = villages_shp.schema.copy()
        dst_schema['properties'].update({'WIKIDATA':'str:100'})
        with fiona.open(villages_out_path, 'w', 
                        crs=fiona.crs.from_epsg(4326),
                        driver='ESRI Shapefile',
                        schema = dst_schema,
                        encoding='utf-8') as output_shp:

            for feature in villages_shp:
                try:
                    feature['geometry'] = fiona.transform.transform_geom('EPSG:3824', 'EPSG:4326',feature['geometry'])
                except Exception as e:
                    logging.exception("Error transforming feature {}".format(feature['id']))


                try: 
                    village_code = feature['properties']['VILLCODE']
                    feature['properties']['WIKIDATA'] = village_to_constituencies[village_code]
                except KeyError as e:
                    logging.exception("Error calculating attributes for village '{}'".format(feature['properties']['VILLCODE']))
                    feature['properties']['WIKIDATA'] = 'missing'               
                    with open(missing_villages, 'a', encoding='utf-8') as f:
                        f.write('\ndistrict:{}, village:{}, code:{}'.format(feature['properties']['TOWNNAME'], feature['properties']['VILLNAME'], feature['properties']['VILLCODE']))
                try:
                    output_shp.write(feature)
                except Exception as e:
                    logging.exception("Error writing feature {}".format(feature['id']))


