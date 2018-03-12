import csv
import json


county_msfb_map = {'連江縣': 'country:tw/county:lie',
                   '金門縣': 'country:tw/county:kin',
                   '宜蘭縣': 'country:tw/county:ila',
                   '彰化縣': 'country:tw/county:cha',
                   '南投縣': 'country:tw/county:nan',
                   '雲林縣': 'country:tw/county:yun',
                   '屏東縣': 'country:tw/county:pif',
                   '臺東縣': 'country:tw/county:ttt',
                   '花蓮縣': 'country:tw/county:hua',
                   '澎湖縣': 'country:tw/county:pen',
                   '新竹市': 'country:tw/city:hsz',
                   '臺北市': 'country:tw/special-municipality:tpe',
                   '新北市': 'country:tw/special-municipality:nwt',
                   '臺中市': 'country:tw/special-municipality:txg',
                   '臺南市': 'country:tw/special-municipality:tnn',
                   '桃園市': 'country:tw/special-municipality:tao',
                   '苗栗縣': 'country:tw/county:mia',
                   '新竹縣': 'country:tw/county:hsq',
                   '嘉義縣': 'country:tw/county:cyq',
                   '高雄市': 'country:tw/special-municipality:khh',
                   '嘉義市': 'country:tw/city:cyi',
                   '基隆市': 'country:tw/city:kee'}


def get_constituency_num(constituency):
    return ''.join([s for s in constituency if s.isdigit()])


def wiki_id(url):
    return url.split('/')[-1]


def ms_fb_id(ms_fb_pare, constituency_num):
    return '{}/county-constituency:{}'.format(ms_fb_pare,
                                              constituency_num)


def create_attributes(constituency):
    attributes = {'WIKIDATA': '',
                  'MS_FB_PARE': '',
                  'MS_FB': '',
                  'name-zh': ''}

    name = constituency['constituency_label']
    ms_fb_pare = county_msfb_map[constituency['county']]
    con_num = get_constituency_num(constituency['constituency_label_wiki'])
    ms_fb = ms_fb_id(ms_fb_pare, con_num)
    attributes['WIKIDATA'] = wiki_id(constituency['wikidata_item'])
    attributes['MS_FB_PARE'] = ms_fb_pare
    attributes['MS_FB'] = ms_fb
    attributes['name-zh'] = name
    return attributes


if __name__ == '__main__':
    constituency_json_path = '/home/will/dev/proto-commons-taiwan/scripts/county-constituencies-to-towns.json'
    aboriginal_constituencies = '/home/will/dev/proto-commons-taiwan/boundaries/county-aboriginal-constituencies/county-aboriginal-constituencies.csv'

    with open(constituency_json_path, 'r') as f:
        constituencies_json = json.load(f)

    with open(aboriginal_constituencies, 'w', encoding='utf-8') as csv_file:
        fieldnames = ['MS_FB_PARE', 'MS_FB', 'name-zh', 'WIKIDATA']
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for constituency in constituencies_json:
            if constituency['constituency_type'] == 'ethnical':
                try:
                    row = create_attributes(constituency)
                    csv_writer.writerow(row)
                except Exception as e:
                    print('failed to print row')
