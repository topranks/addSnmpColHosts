#!/usr/bin/python3

# Adds hosts to SNMPCollector from a list in file passed in.

import os
import requests
import json
import sys
import time
import argparse

def begin():
    parser = argparse.ArgumentParser(description='SNMP Collector Device Adder')
    parser.add_argument('-s', '--server', help ='IP or hostname of SNMPCollector Server', required=True)
    parser.add_argument('-t', '--tcpport', help='TCP Port of SNMP Collector HTTP endpoint (default 8090)', type=int, default=8090)
    parser.add_argument('-u', '--username', help='SNMP Collector web interface username', type=str, required=True)
    parser.add_argument('-p', '--password', help='SNMP Collector web interface password', type=str, required=True)
    parser.add_argument('-f', '--filename', help='File with list of hostnames or IP addresses to add', type=str, default="devices.txt")
    parser.add_argument('-c', '--community', help='SNMP Community to use when polling devices', type=str, default="public")
    parser.add_argument('-i', '--influx', help='Influx DB Server name as configured in SNMP Collector', type=str, required=True)
    parser.add_argument('-m', '--measurementgroup', help='Measurement Group to add to devices', type=str, default="")
    args = parser.parse_args()

    # Log on to server and get cookie:
    cookies=snmpColLogin(args.server, args.tcpport, args.username, args.password)

    # Add hosts defined in file:
    addSnmpColHosts(args, cookies)
   
def addSnmpColHosts(args, cookies):
    f = open(args.filename, 'r')
    for device in f:
        # Remove trailing return from line:
        if '\n' == device[-1]:
            device = device[:-1]

        # Device data to insert into SNMP Col:
        deviceData = {
            "ID": device,
            "Host": device,
            "Port": 161,
            "Retries": 5,
            "Timeout": 20,
            "Active": True,
            "SnmpVersion": "2c",
            "DisableBulk": False,
            "Community": args.community,
            "MaxRepetitions": 50,
            "Freq": 5,
            "UpdateFltFreq": 5,
            "ConcurrentGather": True,
            "OutDB": args.influx,
            "LogLevel": "error",
            "SnmpDebug": False,
            "DeviceTagName": "hostname",
            "DeviceTagValue": "id",
            "ExtraTags": [""],
            "MeasurementGroups": None,
            "MeasFilters": None,
            "Description": ""
        }

        if args.measurementgroup != "":
            deviceData['MeasurementGroups'] = []
            deviceData['MeasurementGroups'].append(args.measurementgroup)

        addSnmpColElement(deviceData, args.server, args.tcpport, cookies, "snmpdevice")
 

def snmpColLogin(server, port, username, password):
    # Logs in to SNMP collector, returns request module 'cookies' object
    url="http://{0}:{1}/login".format(server, port)
    creds = {"username": username, "password": password}
    headers = {'Content-Type':'application/json'}
    
    r = requests.post(url, json=creds, headers=headers)
    if r.status_code == 200:
        return r.cookies
    else:
        print("Error logging on to server, return code {0}\n".format(r.status_code))
        sys.exit(1)


def addSnmpColElement(data, server, port, cookies, elementType):
    headers = {'Content-Type':'application/json'}
    # Check if the element already exists:
    exists=checkSnmpColElementExists(data['ID'], server, port, cookies, elementType)

    # Add or ammend element:
    print("Adding device {0}.".format(data['ID']))
    if(exists):
        url="http://{0}:{1}/api/cfg/{2}/{3}".format(server, port, elementType, data['ID'])
        r = requests.put(url, json=data, headers=headers, cookies=cookies)
    else:
        url="http://{0}:{1}/api/cfg/{2}".format(server, port, elementType)
        r = requests.post(url, json=data, headers=headers, cookies=cookies)

    if(r.status_code==200):
        time.sleep(0.2)
    else:
        print("Somethng went wrong adding device {0}, status code: {1} .".format(data['ID']), r.status_code)
        print(r.json)
        print(r.text)
        sys.exit(1)



def checkSnmpColElementExists(elementName, server, port, cookies, elementType):
    headers = {'Content-Type':'application/json'}

    url="http://{0}:{1}/api/cfg/{2}/{3}".format(server, port, elementType, elementName)
    r = requests.get(url, headers=headers, cookies=cookies)
    if r.status_code==200:
        return 1
    else:
        return 0


if __name__=="__main__":
    begin()

