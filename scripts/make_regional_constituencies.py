
import fiona
import fiona.crs
import fiona.transform
import json
import pprint
import logging 
import sys
import itertools

from shapely.geometry import shape, mapping
from shapely.ops import unary_union


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def town_regional_constituency_map(constituencies):
    #takes a list of constituencies
    #returns town:constituency pairs
    map = {}
    for constituency in constituencies:
        if constituency['constituency_type'] == 'regional':
            county = constituency['county']
            towns = constituency['districts']

            if not county in map:
                map[county] = {}

            for town in towns:
                map[county][town] = constituency['constituency_label']

    return map


county_msfb_map = {'連江縣':'country:tw/county:lie',
                    '金門縣':'country:tw/county:kin',
                    '宜蘭縣':'country:tw/county:ila',
                    '彰化縣':'country:tw/county:cha',
                    '南投縣':'country:tw/county:nan',
                    '雲林縣':'country:tw/county:yun',
                    '屏東縣':'country:tw/county:pif',
                    '臺東縣':'country:tw/county:ttt',
                    '花蓮縣':'country:tw/county:hua',
                    '澎湖縣':'country:tw/county:pen',
                    '新竹市':'country:tw/city:hsz',
                    '臺北市':'country:tw/special-municipality:tpe',
                    '新北市':'country:tw/special-municipality:nwt',
                    '臺中市':'country:tw/special-municipality:txg',
                    '臺南市':'country:tw/special-municipality:tnn',
                    '桃園市':'country:tw/special-municipality:tao',
                    '苗栗縣':'country:tw/county:mia',
                    '新竹縣':'country:tw/county:hsq',
                    '嘉義縣':'country:tw/county:cyq',
                    '高雄市':'country:tw/special-municipality:khh',
                    '嘉義市':'country:tw/city:cyi',
                    '基隆市':'country:tw/city:kee'}


def get_constituency_num(constituency):
    return ''.join([s for s in constituency if s.isdigit()])


def create_attributes(constituencies_json):
    attributes = {}
    for c in constituencies_json:
        if c['constituency_type'] == 'regional':
            constituency = c['constituency_label']
            attributes[constituency] = {}
            attributes[constituency]['WIKIDATA'] = c['wikidata_item'].split('/')[-1]
            attributes[constituency]['MS_FB_PARE'] = county_msfb_map[c['county']]
            attributes[constituency]['MS_FB'] = '{}/county-constituency:{}'.format(attributes[constituency]['MS_FB_PARE'],
                                                     get_constituency_num(c['constituency_label_wiki']))
    return attributes

if __name__ == '__main__':


    districts_path = '/home/will/data/concorde_data/taiwan/source/1061225TOWN_MOI/TOWN_MOI_1061225.shp'
    output_towns_shp_path = '/home/will/data/concorde_data/taiwan/ouput/towns-county-constituencies.shp'
    missing_towns = '/home/will/data/concorde_data/taiwan/ouput/missing-towns.txt'
    constituency_path = '/home/will/dev/proto-commons-taiwan/scripts/county-constituencies-to-towns.json'
    output_constituency_shp_path = '/home/will/dev/proto-commons-taiwan/boundaries/county-regional-constituencies/county-regional-constituencies.shp'

    with open(missing_towns, 'w', encoding='utf-8') as f:
        f.write('county,town')

    with open(constituency_path, 'r') as f:
        constituencies_json = json.load(f)

    towns_to_constituencies = town_regional_constituency_map(constituencies_json)
    attributes = create_attributes(constituencies_json)

    with fiona.open(districts_path, 'r', 
                crs=fiona.crs.from_epsg(3824),
                encoding='Big5') as districts_shp:

        src_driver = districts_shp.driver
        dst_schema = districts_shp.schema.copy()
        dst_schema['properties'].update({'CONSTIT_ID':'str:100'})

        with fiona.open(output_towns_shp_path, 'w', 
                    crs=fiona.crs.from_epsg(4326),
                    driver='ESRI Shapefile',
                    schema = dst_schema,
                    encoding='utf-8') as output_shp:


            for feature in districts_shp:
                try:
                    feature['geometry'] = fiona.transform.transform_geom('EPSG:3824', 'EPSG:4326',feature['geometry'])
                except Exception as e:
                    logging.exception("Error transforming feature {}".format(feature['id']))


                try: 
                    district = feature['properties']['TOWNNAME']
                    county = feature['properties']['COUNTYNAME']
                    feature['properties']['CONSTIT_ID'] = towns_to_constituencies[county][district]
                    #print('\t\t\tproperrties are: ',str(feature['properties']))
                except KeyError as e:
                    logging.exception("Error calculating attributes for feature {}".format(feature['id']))
                    feature['properties']['CONSTIT_ID'] = 'missing'               
                    with open(missing_towns, 'a', encoding='utf-8') as f:
                        f.write('\n{},{}'.format(feature['properties']['COUNTYNAME'], feature['properties']['TOWNNAME']))

                try:
                    output_shp.write(feature)
                except Exception as e:
                    logging.exception("Error writing feature {}".format(feature['id']))


    with fiona.open(output_towns_shp_path, 'r') as towns_shp:
        src_driver = towns_shp.driver
        dst_schema = towns_shp.schema.copy()
        dst_schema['properties'] = {'COUNTYID':'str',
                                    'COUNTYCODE':'str',
                                    'COUNTYNAME':'str',
                                    'COUNTYNAME':'str',
                                    'CONSTIT_ID':'str',
                                    'WIKIDATA':'str',
                                    'MS_FB':'str',
                                    'MS_FB_PARE':'str'}
        with fiona.open(output_constituency_shp_path, 'w',
                                        crs=fiona.crs.from_epsg(4326),
                                        driver='ESRI Shapefile',
                                        schema = dst_schema,
                                        encoding='utf-8') as constituencies_shp:

            feat_sorted = sorted(towns_shp, key=lambda k: k['properties']['CONSTIT_ID'])

            for key, group in itertools.groupby(feat_sorted, key=lambda x:x['properties']['CONSTIT_ID']):
                properties_list, geoms = zip(*[(feature['properties'],shape(feature['geometry'])) for feature in group])

                old_properties = properties_list[0]
                new_properties = {}
                new_properties['COUNTYID'] = old_properties['COUNTYID']
                new_properties['COUNTYCODE'] = old_properties['COUNTYCODE']
                new_properties['COUNTYNAME'] = old_properties['COUNTYNAME']
                new_properties['COUNTYNAME'] = old_properties['COUNTYNAME']
                new_properties['CONSTIT_ID'] = old_properties['CONSTIT_ID']
                try:
                    new_properties['WIKIDATA'] = attributes[new_properties['CONSTIT_ID']]['WIKIDATA']
                    new_properties['MS_FB'] = attributes[new_properties['CONSTIT_ID']]['MS_FB']
                    new_properties['MS_FB_PARE'] = attributes[new_properties['CONSTIT_ID']]['MS_FB_PARE']
                except KeyError as e:
                    logging.exception(e)
                    new_properties['WIKIDATA'] = 'missing'
                    new_properties['MS_FB'] = 'missing'
                    new_properties['MS_FB_PARE'] = 'missing'
                geom = mapping(unary_union(geoms))

                constituencies_shp.write({'geometry': geom, 'properties': new_properties})




    #             def dissolve_by_attribute(input_path,output_path,attrib):
    # #based on https://gis.stackexchange.com/questions/149959/dissolving-polygons-based-on-attributes-with-python-shapely-fiona
    # with fiona.open(input_path) as input:
    #     meta = input.meta
    #     with fiona.open(output_path, 'w', meta) as output:
    #         # groupby clusters consecutive elements of an iterable which have the same key so you must first sort the features by the 'STATEFP' field
    #         e = sorted(input, key=lambda k: k['properties'][attrib])
    #         # group by the 'STATEFP' field 
    #         for key, group in itertools.groupby(e, key=lambda x:x['properties'][attrib]):
    #             properties, geom = zip(*[(feature['properties'],shape(feature['geometry'])) for feature in group])
    #             # write the feature, computing the unary_union of the elements in the group with the properties of the first element in the group
    #             output.write({'geometry': mapping(unary_union(geom)), 'properties': properties[0]})
