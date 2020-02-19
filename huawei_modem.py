import json
import time
import base64
import hashlib
import binascii
import requests
import xmltodict

class Modem:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session_id = None
        self.tokens = []
        self.ip_list = []
        with open('ip_list.txt', 'r', encoding='utf-8') as file:
            for line in file:
                self.ip_list.append(line.split("\n")[0])

    @property
    def token(self):
        if not self.tokens:
            self.login()
        return self.tokens.pop()

    def __b64_sha256(self, data):
        s256 = hashlib.sha256()
        s256.update(data.encode('utf-8'))
        dg = s256.digest()
        hs256 = binascii.hexlify(dg)
        return base64.urlsafe_b64encode(hs256).decode('utf-8', 'ignore')

    def login(self):
        url = 'http://{}/api/webserver/SesTokInfo'.format(self.host)
        headers = {"X-Requested-With": "XMLHttpRequest"}
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code != 200:
            r.raise_for_status()
        result = xmltodict.parse(r.text)
        self.session_id = result['response']['SesInfo'].split("=")[1]
        token = result['response']['TokInfo']

        url = 'http://{}/api/user/login'.format(self.host)
        password_value = self.__b64_sha256(self.username + self.__b64_sha256(self.password) + token)
        xml_data = (
            '<?xml version:"1.0" encoding="UTF-8"?>'
            '<request>'
                '<Username>{}</Username>'
                '<Password>{}</Password>'
                '<password_type>4</password_type>'
            '</request>'
        ).format(self.username, password_value)
        headers['__RequestVerificationToken'] = token
        cookies = {'SessionID': self.session_id}
        r = requests.post(url, data=xml_data, headers=headers, cookies=cookies)
        if '__RequestVerificationToken' in r.headers:
            toks = [x for x in r.headers['__RequestVerificationToken'].split("#") if x != '']
            if len(toks) > 1:
                self.tokens = toks[2:]
            elif len(toks) == 1:
                self.tokens.append(toks[0])
        if 'SessionID' in r.cookies:
            self.session_id = r.cookies['SessionID']
        if r.status_code != 200:
            r.raise_for_status()
        result = xmltodict.parse(r.text)
        response = result['response']
        if response == "OK":
            return True
        return False

    def mobile_status(self):
        url = "http://{}/api/dialup/mobile-dataswitch".format(self.host)
        headers = {}
        headers['__RequestVerificationToken'] = self.token
        headers['X-Requested-With'] = 'XMLHttpRequest'
        cookies = {'SessionID': self.session_id}
        r = requests.get(url, headers=headers, cookies=cookies)
        if r.status_code != 200:
            r.raise_for_status()
        result = xmltodict.parse(r.text)
        response = result['response']['dataswitch']
        return bool(int(response))

    def switch_mobile(self, action):
        url = "http://{}/api/dialup/mobile-dataswitch".format(self.host)
        headers = {}
        headers['__RequestVerificationToken'] = self.token
        headers['X-Requested-With'] = 'XMLHttpRequest'
        cookies = {'SessionID': self.session_id}
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<request>'
            '<dataswitch>{}</dataswitch>'
            '</request>'
        ).format(action)
        r = requests.post(url, data=data, headers=headers, cookies=cookies)
        if r.status_code != 200: 
            r.raise_for_status()
        result = xmltodict.parse(r.text)
        response = result['response']
        return response

    def check_ip(self):
        if not self.mobile_status():
            self.switch_mobile(1)
        ip = None
        for i in range(30):
            try:
                ip = requests.get("http://ip-api.com/json").json()['query']
                break
            except:
                time.sleep(1)
        if ip is None:
            print('Cant get ip address. Check your connection!')
            return True
        if ip in self.ip_list:
            print(f"{ip} already used")
            return False
        else:
            with open('ip_list.txt', 'a') as file:
                file.write(ip + "\n")
            self.ip_list.append(ip)
            print(ip)
            return True