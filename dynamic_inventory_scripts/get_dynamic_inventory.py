#!/usr/bin/python

import sys
import json

if '--list' in sys.argv:
    invin = {}

    invin['group2'] = {}

    invin['group2']['hosts'] = ['192.168.0.1', '192.168.0.2', '192.168.0.3']

    invin['group2']['vars'] = {}
    invin['group2']['vars']['dns_nameservers'] = ['8.8.8.8', '8.8.4.4']

    invin['group1'] = {}

    invin['group1']['hosts'] = ['192.168.0.1','192.168.0.2','192.168.0.3']

    invin['group1']['vars'] = {}
    invin['group1']['vars']['dns_nameservers'] = ['8.8.8.8', '8.8.4.4']

    invin['_meta'] = {}
    invin['_meta']['hostvars'] = {}
    invin['_meta']['hostvars']['192.168.0.1'] = {'data': 'haha'}

    x = json.dumps(invin, indent=2, sort_keys=True)
    print(x)