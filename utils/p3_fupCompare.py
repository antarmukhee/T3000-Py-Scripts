# caution: the script will not catch changes in output port of compound components.

__author__      = "Nandan Sharma"

import xmltodict
import json
import deepdiff
import os
import re
from openpyxl import Workbook as openpyxl_wb
import pprint

def xml_to_dict_conv(input_file, designation_fup, ignore_inp_sig_desig, T3000_AF_db_dict):

    with open(input_file, 'r', encoding='utf-8') as fileobj:
        xml_fup = fileobj.read()
        dict_fup = xmltodict.parse(xml_fup)
        

    dict_fup = dict_fup['ImportIc']
    dict_fup.pop('Sequence', None)
    dict_fup.pop('context', None)
    dict_fup.pop('ScheduleBefore', None)
    
    # ignore run time container attributes
    dict_fup.pop('@afc', None)
    dict_fup.pop('@afcName', None)
    dict_fup.pop('@afcTargetType', None)
    dict_fup.pop('@afcTargetName', None)
    
    dict_fup.update({"@designation": designation_fup})
        
    afi_dict = {}
    try:
        if isinstance(dict_fup["afi"], list): # check that the number of AFs is more than one
            afi_list = dict_fup["afi"]
            afi_dict = {afi_list[idx]["name"]["@tag"] + "|" + afi_list[idx]["name"].get("@item", "") + "@typeId:" + afi_list[idx]["@typeId"]: item for idx, item in enumerate(afi_list)}
        if isinstance(dict_fup["afi"], dict): # check that the number of AFs is equal to one
            afi_dict_1 = dict_fup["afi"]
            afi_dict_key = afi_dict_1["name"]["@tag"] + "|" + afi_dict_1["name"].get("@item", "") + "@typeId:" + afi_dict_1["@typeId"]
            afi_dict[afi_dict_key] = afi_dict_1  
    except KeyError: pass # KeyError means "no AFs defined in the diagram". Dictionary <afi_dict> remains empty
    
    
    com_dict = {}
    try:
        if isinstance(dict_fup["compound"], list): # check that the number of Compounds is more than one
            com_list = dict_fup["compound"]
            com_dict = {com_list[idx]["name"]["@tag"] + "|" + com_list[idx]["name"].get("@item", "") + "@typeName:" + com_list[idx]["@macrodefname"]: item for idx, item in enumerate(com_list)}
        if isinstance(dict_fup["compound"], dict): # check that the number of Compounds is equal to one
            com_dict_1 = dict_fup["compound"]
            com_dict_key = com_dict_1["name"]["@tag"] + "|" + com_dict_1["name"].get("@item", "") + "@typeName:" + com_dict_1["@macrodefname"]
            com_dict[com_dict_key] = com_dict_1
    except KeyError: pass # KeyError means "no Compounds defined in the diagram". Dictionary <com_dict> remains empty
    
    
    afi_plus_com_dict = afi_dict | com_dict # merging two dicts
    

    for af in afi_dict.values():
        
        af.pop("@description", None)
        af.pop("@x", None)
        af.pop("@y", None)
        af.pop("@sourceId")
        af.pop("@cmd")
        
        typeId = af["@typeId"]
        
        if af.get("context", None) != None:
            af_context_key = af.get("context").get("key", None)
            af_context_val = af.get("context").get("value", None)
        else:
            af_context_key = None
            af_context_val = None
                  
        afi_port_list = af["port"]
        try:
            db_port_dict = T3000_AF_db_dict[typeId][1]
            afi_port_dict = {db_port_dict.get(afi_port_list[idx]["portIdentifier"]["portId"], afi_port_list[idx]["portIdentifier"]["portId"]): item for idx, item in enumerate(afi_port_list)}  
        except KeyError: afi_port_dict = {afi_port_list[idx]["portIdentifier"]["portId"]: item for idx, item in enumerate(afi_port_list)}
        
        for port_key, port_val in afi_port_dict.items():
        
            try: portType = T3000_AF_db_dict[typeId][2][port_key]
            except KeyError: portType = None
            
            port_val.pop("@isvisible", None)
            port_val.pop("@parVisible", None)
            port_val.pop("context", None)
            port_val.pop("@cmd")
            
            if af_context_key != None:
                port_id = port_val["portIdentifier"]["portId"]
                try: port_val.update({"@parameterKey" : af_context_val[af_context_key.index("@" + port_id)]})
                except ValueError: pass
                
            try:
                port_val_archive_range = port_val["variation"]["range"]
                try: port_val.update({"@rangeLow" : port_val_archive_range["@min"]})
                except KeyError: pass
                try: port_val.update({"@rangeHigh" : port_val_archive_range["@max"]})
                except KeyError: pass
                try: port_val.update({"@deltaPercent" : port_val_archive_range["@percent"]})
                except KeyError: pass
                try: port_val.update({"@EU" : port_val_archive_range["@engUnit"]})
                except KeyError: pass
            except KeyError: pass
            
            port_val.pop("variation", None)
                
            port_conn = port_val.get("connection", None)
            if port_conn != None:
                try:
                    for _value in afi_plus_com_dict.values():
                        if port_conn["name"] == _value["name"]:
                            typeId_port_conn = _value["@typeId"]
                            break
                            
                    db_port_dict_conn = T3000_AF_db_dict[typeId_port_conn][1]
                    port_conn_val = port_conn["name"]["@tag"] + "|" + port_conn["name"].get("@item", "") + "@portName:" + db_port_dict_conn[port_conn["portIdentifier"]["portId"]]
                    
                except KeyError:
                    try: port_conn_val = port_conn["name"]["@tag"] + "|" + port_conn["name"].get("@item", "") + "@portName:" + port_conn["portIdentifier"]["portName"]
                    except KeyError: port_conn_val = port_conn["name"]["@tag"] + "|" + port_conn["name"].get("@item", "") + "@portId:" + port_conn["portIdentifier"]["portId"]
                port_val["connection"] = port_conn_val
                
            port_sig = port_val.get("sigdef", None)
            if port_sig != None:
                sigdef_list = []
                try: sigdef_list.append(port_sig["@tagname"])
                except KeyError: pass
                try: sigdef_list.append(port_sig["@item"])
                except KeyError: pass
                try: sigdef_list.append(port_sig["@signal"])
                except KeyError: pass
                try: sigdef_list.append(port_sig["@internalName"])
                except KeyError: pass
                
                port_desig = port_sig.get("@designation", "")
                
                try: ignore_out_sig_desig = port_desig == af["@designation"]
                except KeyError: ignore_out_sig_desig = False
                    
                portTypeIsI = portType == 'I'
                portTypeIsO = portType == 'O'
                portTypeIsNotFound = portType == None
                
                if portTypeIsO and not ignore_out_sig_desig or portTypeIsNotFound: port_sig_val = "|".join(sigdef_list) + "@designation:" + port_desig
                elif portTypeIsO and ignore_out_sig_desig: port_sig_val = "|".join(sigdef_list)
                elif portTypeIsI and not ignore_inp_sig_desig: port_sig_val = "|".join(sigdef_list) + "@designation:" + port_desig
                elif portTypeIsI and ignore_inp_sig_desig: port_sig_val = "|".join(sigdef_list)
                
                port_val["sigdef"] = port_sig_val
                
        af["port"] = afi_port_dict
        
        af.pop("context", None)
        
        try:
            if af.get("@designation", "") == dict_fup["@designation"]: af.pop("@designation")
        except KeyError: pass
        
    dict_fup["afi"] = afi_dict
    
    
    for com in com_dict.values():
        
        com.pop("@description", None)
        com.pop("@x", None)
        com.pop("@y", None)
        com.pop("@sourceId")
        com.pop("@cmd")
        
        typeId = com["@typeId"] + '_' + com["@serial"]
        
        if com.get("context", None) != None:
            com_context_key = com.get("context").get("key", None)
            com_context_val = com.get("context").get("value", None)
        else:
            com_context_key = None
            com_context_val = None
                  
        com_port_list = com["port"]
       
        com_port_dict = {com_port_list[idx]["portIdentifier"]["portName"]: item for idx, item in enumerate(com_port_list)}
        
        for port_key, port_val in com_port_dict.items():
            
            try: portType = T3000_AF_db_dict[typeId][2][port_key]
            except KeyError: portType = None
        
            port_val.pop("@isvisible", None)
            port_val.pop("@parVisible", None)
            port_val.pop("context", None)
            port_val.pop("@cmd")
            
            if com_context_key != None:
                # getting port_id corresponding to the port_name
                try:
                    key_list = list(T3000_AF_db_dict[typeId][1].keys())
                    val_list = list(T3000_AF_db_dict[typeId][1].values())
                    port_id = key_list[val_list.index(port_key)]
                    port_val.update({"@parameterKey" : com_context_val[com_context_key.index("@" + port_id)]})
                except (ValueError, KeyError): pass
                
            try:
                port_val_archive_range = port_val["variation"]["range"]
                try: port_val.update({"@rangeLow" : port_val_archive_range["@min"]})
                except KeyError: pass
                try: port_val.update({"@rangeHigh" : port_val_archive_range["@max"]})
                except KeyError: pass
                try: port_val.update({"@deltaPercent" : port_val_archive_range["@percent"]})
                except KeyError: pass
                try: port_val.update({"@EU" : port_val_archive_range["@engUnit"]})
                except KeyError: pass
            except KeyError: pass
            
            port_val.pop("variation", None)
                
            port_conn = port_val.get("connection", None)
            if port_conn != None:
                try:
                    for _value in afi_plus_com_dict.values():
                        if port_conn["name"] == _value["name"]:
                            typeId_port_conn = _value["@typeId"]
                            break
                            
                    db_port_dict_conn = T3000_AF_db_dict[typeId_port_conn][1]
                    port_conn_val = port_conn["name"]["@tag"] + "|" + port_conn["name"].get("@item", "") + "@portName:" + db_port_dict_conn[port_conn["portIdentifier"]["portId"]]
                    
                except KeyError:
                    try: port_conn_val = port_conn["name"]["@tag"] + "|" + port_conn["name"].get("@item", "") + "@portName:" + port_conn["portIdentifier"]["portName"]
                    except KeyError: port_conn_val = port_conn["name"]["@tag"] + "|" + port_conn["name"].get("@item", "") + "@portId:" + port_conn["portIdentifier"]["portId"]
                port_val["connection"] = port_conn_val
                
            port_sig = port_val.get("sigdef", None)
            if port_sig != None:
                sigdef_list = []
                try: sigdef_list.append(port_sig["@tagname"])
                except KeyError: pass
                try: sigdef_list.append(port_sig["@item"])
                except KeyError: pass
                try: sigdef_list.append(port_sig["@signal"])
                except KeyError: pass
                try: sigdef_list.append(port_sig["@internalName"])
                except KeyError: pass
                
                port_desig = port_sig.get("@designation", "")
                ignore_out_sig_desig = port_desig == com["@designation"]
                portTypeIsI = portType == 'I'
                portTypeIsO = portType == 'O'
                portTypeIsNotFound = portType == None
                
                if portTypeIsO and not ignore_out_sig_desig or portTypeIsNotFound: port_sig_val = "|".join(sigdef_list) + "@designation:" + port_desig
                elif portTypeIsO and ignore_out_sig_desig: port_sig_val = "|".join(sigdef_list)
                elif portTypeIsI and not ignore_inp_sig_desig: port_sig_val = "|".join(sigdef_list) + "@designation:" + port_desig
                elif portTypeIsI and ignore_inp_sig_desig: port_sig_val = "|".join(sigdef_list)
                
                port_val["sigdef"] = port_sig_val
                
        com["port"] = com_port_dict
        
        com.pop("context", None)
        
        if com.get("@designation", "") == dict_fup["@designation"]: com.pop("@designation")
    
    dict_fup["compound"] = com_dict
    
    return dict_fup
    
    
def xml_to_dict_conv_dir(input_dir, ignore_inp_sig_desig, T3000_AF_db_dict):

    dict_fup_all = {}
    key_prefix = os.path.basename(input_dir)

    for root, dirs, files in os.walk(input_dir, topdown = True):

        for file in files:

            if file == "icdiagram.xml":
                
                file_fup_node = os.path.join(root, 'node.xml')
                with open(file_fup_node, 'r', encoding='utf-8') as fileobj:
                    xml_fup_node = fileobj.read()
                    dict_fup_node = xmltodict.parse(xml_fup_node)
                try: designation_fup = dict_fup_node['ImportNode']['context']['value'][dict_fup_node['ImportNode']['context']['key'].index('§Designation')]
                except ValueError: designation_fup = ""
                
                file_fup = os.path.join(root, file)
                dict_fup = xml_to_dict_conv(file_fup, designation_fup, ignore_inp_sig_desig, T3000_AF_db_dict)
                
                key = os.path.join(root)
                # print(key)
                key = re.sub(fr'^.*?({key_prefix})', key_prefix, key, count=1)
                # print(key)
                key = re.sub('@IC', '', key)
                # print(key)
                dict_fup_all[key] = dict_fup

    return dict_fup_all
    
    
def diff_fup_dir(xml_dir_old, xml_dir_new, ignore_inp_sig_desig, xl_diff_file, T3000_AF_db_dict, json_old_file = None, json_new_file = None):

    print("Processing old files.")
    dict_fup_old = xml_to_dict_conv_dir(xml_dir_old, ignore_inp_sig_desig, T3000_AF_db_dict)
    print("Processing new files.")
    dict_fup_new = xml_to_dict_conv_dir(xml_dir_new, ignore_inp_sig_desig, T3000_AF_db_dict)
    
    print("Generating difference.")
    diff = dict(deepdiff.DeepDiff(dict_fup_old, dict_fup_new))

    for k, v in diff.items():
        if type(v) == deepdiff.model.PrettyOrderedSet:
            diff[k] = list(v)
            
    list_added = diff.get('dictionary_item_added', [])
    list_removed = diff.get('dictionary_item_removed', [])
    dict_changed = diff.get('values_changed', {})
    
    result_header = ['Diag path', 'Diag name', 'Diag attr', 'Tag name', 'AF type', 'AF attr', 'Port name', 'Port attr', '', 'Change remark', 'Old value', 'New value']
    result_row_len = len(result_header)
    list_result_diff = []
    
    for item in list_added:
        sub_list = re.findall('(?<=\[\').*?(?=\'\])', item)
        diagList = sub_list[0].split('\\')
        diagName = diagList[-1]
        diagList.pop(-1)
        diagPath = ('\\').join(diagList)
        try: diagAttr = sub_list[1]
        except IndexError: diagAttr = '→'
        try: tagList = sub_list[2].split('@')
        except IndexError: tagList = []
        try: tagName = tagList[0]
        except IndexError: tagName = '→'
        try: afType = tagList[1]
        except IndexError: afType = '→'
        try: afAttr = sub_list[3]
        except IndexError: afAttr = '→'
        try: portName = sub_list[4]
        except IndexError: portName = '→'
        try: portAttr = sub_list[5]
        except IndexError: portAttr = '→'
        chgRemark = 'new'
       
        list_result_diff.append([diagPath, diagName, diagAttr, tagName, afType, afAttr, portName, portAttr, '→', chgRemark, '', ''])
        
    for item in list_removed:
        sub_list = re.findall('(?<=\[\').*?(?=\'\])', item)
        diagList = sub_list[0].split('\\')
        diagName = diagList[-1]
        diagList.pop(-1)
        diagPath = ('\\').join(diagList)
        try: diagAttr = sub_list[1]
        except IndexError: diagAttr = '→'
        try: tagList = sub_list[2].split('@')
        except IndexError: tagList = []
        try: tagName = tagList[0]
        except IndexError: tagName = '→'
        try: afType = tagList[1]
        except IndexError: afType = '→'
        try: afAttr = sub_list[3]
        except IndexError: afAttr = '→'
        try: portName = sub_list[4]
        except IndexError: portName = '→'
        try: portAttr = sub_list[5]
        except IndexError: portAttr = '→'
        chgRemark = '$'
        
        list_result_diff.append([diagPath, diagName, diagAttr, tagName, afType, afAttr, portName, portAttr, '→', chgRemark, '', ''])
    
    for key, value in dict_changed.items():
        sub_list = re.findall('(?<=\[\').*?(?=\'\])', key)
        diagList = sub_list[0].split('\\')
        diagName = diagList[-1]
        diagList.pop(-1)
        diagPath = ('\\').join(diagList)
        try: diagAttr = sub_list[1]
        except IndexError: diagAttr = '→'
        try: tagList = sub_list[2].split('@')
        except IndexError: tagList = []
        try: tagName = tagList[0]
        except IndexError: tagName = '→'
        try: afType = tagList[1]
        except IndexError: afType = '→'
        try: afAttr = sub_list[3]
        except IndexError: afAttr = '→'
        try: portName = sub_list[4]
        except IndexError: portName = '→'
        try: portAttr = sub_list[5]
        except IndexError: portAttr = '→'
        chgRemark = 'mod'
        oldVal = value['old_value']
        newVal = value['new_value']
        
        list_result_diff.append([diagPath, diagName, diagAttr, tagName, afType, afAttr, portName, portAttr, '→', chgRemark, oldVal, newVal])
        
    for sub_list in list_result_diff:
        if sub_list[4].startswith("typeId:"):
            try: sub_list[4] = "typeName:" + T3000_AF_db_dict[sub_list[4].split(':')[1]][0]
            except KeyError: pass
        
    list_result_diff = sorted(list_result_diff, key = lambda x: (x[1], x[3], x[5], x[6], x[7]))
    list_result_diff = [result_header] + list_result_diff
    
    print("Writing results.")
        
    wb = openpyxl_wb() # create workbook object.
    ws = wb.active # create worksheet object.
    for row in list_result_diff:
        ws.append(row) # adds values to cells, each list is a new row.
    wb.save(xl_diff_file) # save to excel file.
        
    if json_old_file != None:
        with open(json_old_file, 'w', encoding='utf-8') as fileobj:
            fileobj.write(json.dumps(dict_fup_old, indent = 4))
    
    if json_new_file != None:
        with open(json_new_file, 'w', encoding='utf-8') as fileobj:
            fileobj.write(json.dumps(dict_fup_new, indent = 4))
           
    return list_result_diff