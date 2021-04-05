#################################
##### Name: Tong Xu
##### Uniqname: xutong
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets  # file that contains your API key

URL = 'https://www.nps.gov/index.htm'
base_url = 'https://www.nps.gov'
CACHE_FILE_NAME = 'project2.json'
CACHE_DICT = {}
API_KEY = secrets.API_KEY


class NationalSite:
    """
    a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    """

    def __init__(self, category, name, address, zipcode, phone, url=None):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone.strip('\n')
        self.url = url

    def info(self):
        return self.name + ' (' + self.category + '): ' + self.address + ' ' + self.zipcode


def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except FileNotFoundError:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def build_state_url_dict():
    """
    Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    """
    global CACHE_DICT, base_url
    state_dict = {}
    url = base_url + '/index.htm'
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    state_parent = soup.find('ul', class_="dropdown-menu SearchBar-keywordSearch")
    state_ls = state_parent.find_all('li', recursive=False)
    for statei in state_ls:
        state_link_tag = statei.find('a')
        state_path = state_link_tag['href']
        state_name = statei.get_text().lower()
        state_dict[state_name] = base_url + state_path
    return state_dict


def make_url_request_using_cache(url, cache):
    if url in cache.keys():  # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]


def get_site_instance(site_url):
    """
    Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    """
    global CACHE_DICT
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    parent = soup.find('div', class_='Hero-titleContainer clearfix')
    name = parent.find('a', class_='Hero-title').get_text()

    category = parent.find('div', class_='Hero-designationContainer')\
                     .find('span', class_='Hero-designation').get_text().strip()

    footer_parent = soup.find('div', class_='ParkFooter')

    zip_code = footer_parent.find('p', class_='adr')\
                            .find('span', class_='postal-code').get_text().strip()

    address = footer_parent.find('p', class_='adr')\
                           .find('span', itemprop='addressLocality').get_text() + ', ' + footer_parent\
                           .find('p', class_='adr').find('span', itemprop='addressRegion').get_text()

    phone = footer_parent.find('span', class_='tel').get_text()

    instance = NationalSite(category, name, address, zip_code, phone)

    return instance


def get_sites_for_state(url):
    """
    Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    site_list: list
        The list of national site instances
    """
    global CACHE_DICT, base_url
    
    CACHE_DICT = load_cache()
    url_text = make_url_request_using_cache(url, CACHE_DICT)
    site_soup = BeautifulSoup(url_text, 'html.parser')
    parent = site_soup.find('div', id="parkListResults")
    names = parent.find_all('h3')

    site_list = []
    for name in names:
        tag = name.find('a')
        path = tag['href']
        url = base_url + path + 'index.htm'

        sitei = get_site_instance(url)
        site_instance = NationalSite(sitei.category, sitei.name, sitei.address, sitei.zipcode, sitei.phone, url)
        site_list.append(site_instance)

    return site_list


def make_request_with_cache_api(url, site_object):
    """
    Make request. If cache exits, use cache, otherwise request.

    Parameters
    ----------
    url: string
        The URL for the API endpoint

    site_object:
        a site instance


    Returns
    -------
    the results of the query, a dict.
    """
    cache_file = load_cache()
    params = {'key': API_KEY, 'origin': site_object.zipcode, 'radius': 10, 'maxMatches': 10,
              'ambiguities': 'ignore', 'outFormat': 'json'}

    if site_object.name in cache_file:
        print('Using cache')
        return cache_file[site_object.name]
    else:
        print("Fetching")
        response = requests.get(url, params).json()
        cache_file[site_object.name] = response
        save_cache(cache_file)
        return cache_file[site_object.name]


def get_nearby_places(site_object):
    """
    Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    """
    url = 'http://www.mapquestapi.com/search/v2/radius'
    nearby_dict = make_request_with_cache_api(url, site_object)
    return nearby_dict


class NearbyPlace:
    def __init__(self, name, category, street_address, city_name):
        self.name = name
        self.category = category
        self.street_address = street_address
        self.city_name = city_name

    def info(self):
        return self.name + ' (' + self.category + '): ' + self.street_address + ', ' + self.city_name


def make_nearby_instance_list(nearby_dict):
    """
    make the nearby dictionary into instance

    Parameter:
    ------------
    nearby_dict: a dictionary contain the nearby information

    Return:
    -----------
    list of nearby place instances
    """

    nearby_instance_list = []

    for member in nearby_dict['searchResults']:
        nearby_name = member['name']

        try:
            nearby_category = member['fields']["group_sic_code_name"].strip()
            if nearby_category == '':
                nearby_category = 'no category'
        except:
            nearby_category = member['fields']["group_sic_code_name_ext"].strip()

        try:
            nearby_street_address = member['fields']['address'].strip()
            if nearby_street_address == '':
                nearby_street_address = 'no address'
        except:
            nearby_street_address = 'no address'

        try:
            nearby_city_name = member['fields']['city'].strip()
            if nearby_city_name == '':
                nearby_city_name = 'no city'
        except:
            nearby_city_name = 'no city'

        nearby_instance = NearbyPlace(nearby_name, nearby_category, nearby_street_address, nearby_city_name)
        nearby_instance_list.append(nearby_instance)

    return nearby_instance_list


if __name__ == "__main__":
    states_dict = build_state_url_dict()
    x = 0
    while True:
        state = input('Enter a state name (e.g. Michigan, michigan) or "exit"\n:').lower()

        if state == 'exit':
            break
        elif state in states_dict.keys():
            state_url = states_dict[state]
            sites_list = get_sites_for_state(state_url)
        else:
            print('[Error] Enter proper state name \n')
            continue

        print('-' * 50)
        print("List of national sites in", state.lower())
        print('-' * 50)
        for i, site in enumerate(sites_list):
            print('[', i+1, '] ', site.info())

        while True:
            nearby_instance_list = []
            option = input('Choose the number for detail search or "exit" or "back"\n:').lower()
            if option == "back":
                break

            if option == "exit":
                x = 1
                break
            elif option.isnumeric():
                if int(option) <= len(sites_list) and option.isnumeric():
                    park_instance = get_site_instance(sites_list[int(option) - 1].url)
                    site_name = park_instance.name
                    nearbyplace = get_nearby_places(park_instance)
                    nearby_instance_list = make_nearby_instance_list(nearbyplace)
                    print('-' * 50)
                    print('Places near', site_name.strip())
                    print('-' * 50)
                    for nearby_place in nearby_instance_list:
                        print("-", nearby_place.info())
                    continue
                else:
                    print("[Error] Invalid input \n")
                    print('-' * 50)
            else:
                print("[Error] Invalid input \n")
                print('-' * 50)
                continue

        if x == 1:
            break
