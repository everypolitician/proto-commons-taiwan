import json
import fiona
import fiona.crs
import fiona.transform
import logging
import sys
import pprint


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

constituency_path = "./constituency_mapping.json"
villages_path = "../source/1070129_VILLAGE/VILLAGE_MOI_1070119.shp"
constituency_out_path = "./constituency_build.shp"



open('./missing-villages.txt', 'w', encoding='utf-8').close()

village_constituency_map = {}

with open(constituency_path, 'r') as constituencies_file:

    constituencies_json = json.load(constituencies_file)
    for county in constituencies_json:
        for region in constituencies_json[county]['regions']:
            constituency_code = county+str(region['constituency'])
            for district in region['district']:
                village_constituency_map[district] = {}
                for village in region['district'][district]:
                    village_constituency_map[district][village]=constituency_code


pprint.pprint(village_constituency_map)

with fiona.open(villages_path, 'r', 
                crs=fiona.crs.from_epsg(3824), 
                encoding='Big5') as villages_shp:

    src_driver = villages_shp.driver
    dst_schema = villages_shp.schema.copy()
    dst_schema['properties'].update({'constit_id':'str:100'})
    #print('schema is: ',dst_schema)
    with fiona.open(constituency_out_path, 'w', 
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
                district = feature['properties']['TOWNNAME']
                village = feature['properties']['VILLNAME']
                feature['properties']['constit_id'] = village_constituency_map[district][village]
                #print('\t\t\tproperrties are: ',str(feature['properties']))
            except KeyError as e:
                logging.exception("Error calculating attributes for feature {}".format(feature['id']))
                feature['properties']['constit_id'] = 'missing'               
                with open('./missing-villages.txt', 'a', encoding='utf-8') as f:
                    f.write('\ndistrict:{}, village:{}'.format(feature['properties']['TOWNNAME'], feature['properties']['VILLNAME']))

            #Write feature to output shapefile
            #print('\t\t\twriting feature {}'.format(feature['id']))
            try:
                output_shp.write(feature)
            except Exception as e:
                logging.exception("Error writing feature {}".format(feature['id']))