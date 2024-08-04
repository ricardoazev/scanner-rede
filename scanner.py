from multiprocessing import Process, Manager
from os import devnull, popen
from threading import Thread
from subprocess import Popen, PIPE, STDOUT
from tabulate import tabulate
from termcolor import colored
import requests
import time

class ThreadFastScanIP(Thread):

    def __init__(self, gateway, range_start, range_end, parent=None):
        super(ThreadFastScanIP, self).__init__(parent)
        self.range_start = range_start
        self.range_end = range_end
        self.working_thread = True
        self.on_ips = []
        self.gatewayNT = gateway[:len(gateway) - len(gateway.split('.').pop())]

    def run(self):
        self.jobs = []
        self.manager = Manager()
        self.on_ips = self.manager.dict()
        for count in range(self.range_start, self.range_end):
            ip = '%s{0}'.format(count) % (self.gatewayNT)
            if not self.working_thread:
                break
            p = Process(target=self.working, args=(ip, self.on_ips))
            self.jobs.append(p)
            p.start()

        for proc in self.jobs:
            proc.join()
            proc.terminate()

    def working(self, ip, lista):
        with open(devnull, 'wb') as limbo:
            result = Popen(['ping', '-c', '1', '-n', '-w', '1', ip],
                           stdout=limbo, stderr=limbo).wait()
            if not result:
                mac_address = self.get_mac(ip)
                if mac_address is None:
                    lista[ip] = {'mac': '', 'vendors': ''}
                else:
                    vendor = self.resolve_mac(mac_address)
                    lista[ip] = {'mac': mac_address, 'vendors': vendor}

    def get_mac(self, host):
        fields = popen('grep "%s" /proc/net/arp' % host).read().split()
        if len(fields) == 6 and fields[3] != '00:00:00:00:00:00':
            return fields[3]
        return None

    def resolve_mac(self, mac):
        MAC_URL = 'https://api.macvendors.com/%s'
        try:
            time.sleep(1)  # Intervalo de 1 segundo entre requisições
            r = requests.get(MAC_URL % mac)
            r.raise_for_status()  # Levanta um HTTPError para respostas de erro (4xx e 5xx)
            vendor = r.text.strip()
            if vendor:
                return colored(vendor, 'green')
            else:
                return colored('Unknown Vendor', 'red')
        except requests.exceptions.RequestException as e:
            # print(f"HTTP request failed: {e}")
            return colored('Unknown Vendor', 'red')

    def getOutput(self):
        return self.on_ips

    def showoutput_table(self):
        keys = self.on_ips.keys()
        values = self.on_ips.values()

        data = {
            'IP': keys,
            'MAC': [v['mac'] for v in values],
            'VENDORS': [v['vendors'] for v in values]
        }

        print(tabulate(data, headers='keys'))

if __name__ == '__main__':
    thread_scan = ThreadFastScanIP('192.168.0.1', 0, 255)
    thread_scan.start()
    thread_scan.join()
   # thread_scan.showoutput_table()


print("                _________                                                                                ___          ____  ___")
print("               /   _____/ ____ _____    ____   ____   ___________       ___________  ______   ____      /  / ___  __ /_   | \  V.1")
print("  ______       \_____  \_/ ___\>__  \  /    \ /    \_/ __ \_  __ \      \____ \__  \ \____ \_/ __ \    /  /  \  \/ /  |   |  \  \     ______")
print(" /_____/       /        \  \___ / __ \|   |  \   |  \  ___/|  | \/      |  |_> > __ \|  |_> >  ___/   (  (    \   /   |   |   )  )   /_____/   ")
print("              /_______  /\___  >____  /___|  /___|  /\___  >__|     /\  |   __(____  /   __/ \___  >   \  \    \_/ /\ |___|  /  /              ")
print("                      \/     \/     \/     \/     \/     \/         \/  |__|       \/|__|        \/     \__\       \/       /__/               ")

thread_scan.showoutput_table()
