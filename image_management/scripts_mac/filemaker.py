import configparser
import os
import requests
import base64
import getpass
from progress import Progress


class FilemakerAPI:
    
    def __init__(self, base_url, database, layout):
        home_directory = os.path.expanduser("~")
        config_dir = os.path.join(home_directory, ".fm_credentials")
        self.config_file_path = os.path.join(config_dir, "config.ini")
        self.base_url = base_url.replace(" ", "%20")
        self.database = database.replace(" ", "%20")
        self.layout = layout.replace(" ", "%20")
        self.token = None
        self.found_count = 0
        self.total_record_count = 0
        self.returned_count = 0


        # Check if the config file exists
        if not os.path.exists(self.config_file_path):
            os.makedirs(config_dir, exist_ok=True)
            self._get_credentials_from_user()
        else:
            config = configparser.ConfigParser()
            config.read(self.config_file_path)

            if not config.has_section("default"):
                self._get_credentials_from_user()

            try:
                self._username = config.get("default", "username")
                self._password = config.get("default", "password")
                self.authenticate()
            except:
                print("Invalid FileMaker Credentials.")
                os.remove(self.config_file_path)
                self._get_credentials_from_user()

        self.authenticate()

    def _get_credentials_from_user(self):
        self._username = None
        self._password = None
        # Prompt the user for credentials
        while not self._username:
            self._username = input("Enter your username: ")
            if not self._username:
                print("Username required.")
        while not self._password:
            self._password = getpass.getpass("Enter your password: ")
            if not self._password:
                print("Password Required.")

        self._write_credentials_to_file()

    def _write_credentials_to_file(self):

        # Write credentials to the config file
        config = configparser.ConfigParser()
        config.add_section("default")
        config.set("default", "username", self._username)
        config.set("default", "password", self._password)

        with open(self.config_file_path, "w") as config_file:
            config.write(config_file)
        self.authenticate()
    def authenticate(self):
        auth_url = f"{self.base_url}/fmi/data/vLatest/databases/{self.database}/sessions"

        auth_payload = {
            "fmDataSource": [
                {
                    "database": self.database,
                    "username": self._username,
                    "password": self._password
                }
            ]
        }
        credentials = base64.urlsafe_b64encode(f"{self._username}:{self._password}".encode()).decode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}"
        }
        
        response = requests.post(auth_url, json=auth_payload, headers=headers)
        
        if response.status_code == 200:
            self.token = response.json().get('response').get('token')
        else:
            print("Invalid FileMaker Credentials.")
            os.remove(self.config_file_path)
            self._get_credentials_from_user()

    def session_close(self):
        if not self.token:
            raise Exception("No active session to close.")

        close_url = f"{self.base_url}/fmi/data/vLatest/databases/{self.database}/sessions/{self.token}"
        headers = {
            "Authorization": f"Bearer {self.token}",
        }

        response = requests.delete(close_url, headers=headers)

        if response.status_code == 200:
            self.token = None
            return 0
        else:
            raise Exception(f"Failed to close session: {response.text}")


    def find_records(self, criteria, offset, limit):
        if not self.token:
            raise Exception("Authentication required. Call authenticate() first.")

        find_url = f"{self.base_url}/fmi/data/vLatest/databases/{self.database}/layouts/{self.layout}/_find"
        headers = {
            "-X": "GET",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "--conect-timeout": "2",
            "-d":"{}"
        }

        find_payload = {
            "query": [{field: value} for field, value in criteria.items()],
            "offset":offset,
            "limit":limit
        }
        response = requests.post(find_url, headers=headers, json=find_payload)
        if response.status_code == 200:
            found_records = response.json()
            self.found_count = found_records.get('response').get('dataInfo').get('foundCount')
            self.total_record_count = found_records.get('response').get('dataInfo').get('totalRecordCount')
            self.returned_count = found_records.get('response').get('dataInfo').get('returnedCount')
            return found_records
        
        else:
            raise Exception(f"Failed to find records: {response.text}")
            
    def update_records(self, record_id, update_data):
        if not self.token:
            raise Exception("Authentication required. Call authenticate() first.")
        headers = {
            "-X":"PATCH",
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "-d":"{}"
        }
        try:
            update_payload = {
                        "fieldData": update_data,
                    }
        except Exception as e:
            print(f"failed to update record id: {record_id}")
        update_response = requests.patch(f"{self.base_url}/fmi/data/vLatest/databases/{self.database}/layouts/{self.layout}/records/{record_id}", headers=headers, json=update_payload)
        return update_response.text
