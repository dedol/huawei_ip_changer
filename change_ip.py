import time
from huawei_modem import Modem

host = '192.168.8.1'
username = 'admin'
password = ''

def change_ip():
    api = Modem(host, username, password)
    while (not api.check_ip()):
        api.switch_mobile(0)
        time.sleep(5)
        api.switch_mobile(1)

if __name__ == '__main__':
	change_ip()
