# Use this script to update T3000_AF_db_dict.json. First T3000_AF_db.csv would need to be updated.

__author__      = "Nandan Sharma"

import csv
import sys
from os import path
import json

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    application_path = path.dirname(path.realpath(sys.executable))
elif __file__:
    application_path = path.dirname(__file__)

dict = {}
  
T3000_AF_db_csv = path.join(application_path, 'T3000_AF_db.csv')
T3000_AF_db_dict_file = path.join(application_path, 'T3000_AF_db_dict.json')

with open(T3000_AF_db_csv, 'r', encoding='utf-8') as file:
    csvreader = csv.reader(file)
    for idx, line in enumerate(csvreader):
        if idx == 0: continue
        else:
            if line[0] not in dict.keys():
                nested_dict1 = {line[2]: line[3]}
                nested_dict2 = {line[3]: line[4]}
                dict.update({line[0]: [line[1], nested_dict1, nested_dict2]})
            else:
                nested_dict1.update({line[2]: line[3]})
                nested_dict2.update({line[3]: line[4]})
                
                
if T3000_AF_db_dict_file != None:
        with open(T3000_AF_db_dict_file, 'w', encoding='utf-8') as fileobj:
            fileobj.write(json.dumps(dict, indent = 4))

