#!/usr/bin/python
from jsonrpclib import Server
import json
import ssl
from netaddr import *
import subprocess
import os
import multiprocessing
from pprint import pprint

#CREDS
user = "admin"
passwd = "Arista"
ssl._create_default_https_context = ssl._create_unverified_context

#Define IP range(s)
iprange = '192.168.255.0/24'
netblock = IPNetwork(iprange)

def pinger( job_q, results_q ):
    DEVNULL = open(os.devnull,'w')
    while True:
        ip = job_q.get()
        if ip is None: break

        try:
            subprocess.check_call(['ping','-c1',ip],
                                  stdout=DEVNULL)
            results_q.put(ip)
        except:
            pass

def main():
    endpoint_list = []
    pool_size = int(netblock.size)

    jobs = multiprocessing.Queue()
    results = multiprocessing.Queue()

    pool = [ multiprocessing.Process(target=pinger, args=(jobs,results))
             for i in range(pool_size) ]

    for p in pool:
        p.start()

    for host in netblock:
        jobs.put(str(host))

    for p in pool:
        jobs.put(None)

    for p in pool:
        p.join()

    while not results.empty():
        ip = results.get()
        endpoint_list.append(ip)

    listofendpoints = []
    for live_endpoint in endpoint_list:
        try:
          #SESSION SETUP FOR eAPI TO DEVICE
          url = "https://%s:%s@%s/command-api" % (user, passwd, str(live_endpoint))
          ss = Server(url)

          #CONNECT TO DEVICE
          hostname = ss.runCmds( 1, ['enable', 'show hostname' ])[1]['hostname']
          version = ss.runCmds( 1, ['enable', 'show version' ])[1]
          modelnumber = version['modelName']
          serial = version['serialNumber']
          jsonlist = {hostname: [modelnumber, serial]}
          listofendpoints.append(jsonlist)
        except:
          print 'Failure to connect to -- '+live_endpoint
    pprint(listofendpoints)

if __name__ == "__main__":
  main()
