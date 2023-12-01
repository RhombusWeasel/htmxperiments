import configparser
import requests
import json
from utils.logger import Logger

conf = configparser.ConfigParser()
conf.read('config.ini')

class MemoryClient:
    def __init__(self, base_url):
        self.logger = Logger('MemoryClient', log_level=Logger.WARN)
        self.logger.info(f'Initializing MemoryClient with base_url: {base_url}')
        self.base_url = base_url
        self.username = conf['memory']['username']
        self.password = conf['memory']['password']
        self.login()

    def _request(self, method, endpoint, data=None, jsn=None, retry=True):
        try:
            url = f'{self.base_url}{endpoint}'
            headers = {'Content-Type': 'application/json'}
            self.logger.info(f'Making request: {method} {endpoint}')
            if not endpoint == '/login' and self.token:
                headers['Authorization'] = f'Bearer {self.token}'

            response = requests.request(method, url, headers=headers, data=data, json=jsn, cookies=self.token)
            response.raise_for_status()
            response_json = response.json()

            if not response_json:
                self.logger.warning(f'No information was found in the response to {endpoint} {jsn and json.dumps(jsn) or ""}')
                return {'message': 'No information was found.'}
            else:
                self.logger.debug(response_json)
                return response_json

        except requests.exceptions.HTTPError as e:
            if retry and e.response.status_code == 401:
                self.logger.info('Token expired. Logging in again.')
                try:
                    self.login()
                    return self._request(method, endpoint, data, jsn, retry=False)
                except Exception as e:
                    self.logger.error(f'Error making request: {e}')
                    return None


    def login(self):
        data = {'username': self.username, 'password': self.password}
        url = f'{self.base_url}/login'
        headers = {'Content-Type': 'application/json'}
        self.token = requests.request('POST', url, headers=headers, json=data).cookies

    def make_repository(self, repository_name):
        data = {'repository_name': repository_name}
        self.logger.info(f"Creating repository '{repository_name}'.")
        return self._request('POST', '/create_repository', jsn=data)

    def create_repository(self, repository_name):
        repositories = self.view_repositories()
        if repositories:
            for repo in repositories:
                if repo == repository_name:
                    self.logger.info(f"Repository '{repository_name}' already exists.")
                    return True

        self.make_repository(repository_name)
        return True

    def view_repositories(self):
        data = self._request('GET', '/view_repositories')
        if not data:
            return False
        self.logger.info(data['repositories'])
        return data['repositories']

    def fetch_repository(self, repository_name):
        data = {'repository_name': repository_name}
        return self._request('POST', '/fetch_repository', jsn=data)

    def delete_repository(self, repository_name):
        data = {'repository_name': repository_name}
        return self._request('POST', '/delete_repository', jsn=data)

    def add_text(self, repository_name, text):
        self.create_repository(repository_name)
        data = {'repository_name': repository_name, 'text': text}
        self.logger.info(f"Adding text to repository '{repository_name}': {text}")
        return self._request('POST', '/add', jsn=data)
    
    def add_text_if_unique(self, repository_name, text, threshold=0):
        self.create_repository(repository_name)
        search_results = self.search(repository_name, text)
        found = False
        if search_results:
            for result in search_results:
                if result['distance'] < threshold:
                    self.logger.info(f"Text already exists in repository '{repository_name}' with a distance below the threshold.")
                    found = True
                    break
        if not found:
            self.add_text(repository_name, text)
        return not found

    def search(self, repository_name, query, k=2):
        data = {'repository_name': repository_name, 'query': query, 'k': k}
        resp =  self._request('POST', '/search', jsn=data)
        if not resp:
            return False
        r_data = []
        for i in range(len(resp['distances'][0])):
            r_data.append({
                'distance': resp['distances'][0][i],
                'uuid': resp['neighbors'][0][i],
                'text': resp['texts'][i]
            })
        return r_data

    def delete_entry(self, repository_name, entry_id):
        data = {'repository_name': repository_name, 'entry_id': entry_id}
        return self._request('POST', '/delete_entry', jsn=data)

    def modify_entry(self, repository_name, entry_id, new_text):
        data = {
            'repository_name': repository_name,
            'entry_id': entry_id,
            'new_text': new_text
        }
        return self._request('POST', '/modify_entry', jsn=data)
