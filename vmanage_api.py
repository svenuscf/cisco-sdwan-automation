import requests
import json
import urllib3
urllib3.disable_warnings()

class VManage:
    def __init__(self, host, username, password):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.base_url = f"{self.host}/dataservice"   # ✅ define base_url here
        self.session = requests.Session()
        self.jsessionid = None
        self.token = None
        self.login()

    def login(self):
        url = f"{self.host}/j_security_check"
        data = {"j_username": self.username, "j_password": self.password}

        r = self.session.post(url, data=data, verify=False)
        if r.status_code != 200 or "JSESSIONID" not in self.session.cookies:
            raise Exception("Login failed")

        self.jsessionid = self.session.cookies.get("JSESSIONID")

        # XSRF token (some deployments may not have)
        token_url = f"{self.base_url}/client/token"
        r = self.session.get(token_url, verify=False)
        if r.status_code == 200:
            self.token = r.text

    def get(self, path):
        headers = {"Accept": "application/json"}
        if self.token:
            headers["X-XSRF-TOKEN"] = self.token

        url = f"{self.base_url}/{path.lstrip('/')}"
        r = self.session.get(url, headers=headers, verify=False)
        r.raise_for_status()
        return r.json()

    def put(self, endpoint, payload):
        """Send a PUT request to vManage and return the JSON or text response."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-XSRF-TOKEN"] = self.token

        # endpoint should start with /v1/...
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        r = self.session.put(url, json=payload, headers=headers, verify=False)

        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error: {err}")

        try:
            return r.json()
        except Exception:
            return r.text
