__author__      = "Nandan Sharma"

from xlrd import open_workbook as open_wb
from re import sub
from copy import deepcopy


def formatCellData(x):
    x = str(x)
    x = sub('^text:', '', x)
    x = sub('^number:', '', x)
    x = sub("'","", x) # remove all single quote chars from the value
    x = sub('"','', x) # remove all double quote chars from the value
    x = sub(' ','', x) # remove all space chars from the value
    x = sub('   ','', x) # remove all tab chars from the value
      
    return x
    
    
def create_std_sch_list(stdSchFile, ap, prefix_std, prefix_prj):
    """ 1. reads stdSchFile and returns a nested list where each row of standard scheduling table is an sublist of the list.
        Header is at index 0. Index signifies FUP sequence. 

        2. replaces standard KKS prefix with project specific KKS prefix. """
    stdSchList = []
    workbook = open_wb(stdSchFile)
    sheet = workbook.sheet_by_index(0)
    row_count = sheet.nrows
    
    for cur_row in range(1, row_count):
        item1 = formatCellData(sheet.cell(cur_row, 1)) # Diagram Name
        item1 = sub("^" + prefix_std, prefix_prj, item1) # Diagram Path
        item2 = formatCellData(sheet.cell(cur_row, 2))
        item3 = formatCellData(sheet.cell(cur_row, 3))
        item4 = "TRUE"
        item5 = int(float(formatCellData(sheet.cell(cur_row, 5))))
        key = sub(".*" + ap, ap, item2 + item1)
        subList = [key, item1, item2, item3, item4, item5]
        stdSchList.append(subList)
    
    return stdSchList
    
    
def create_proj_sch_old_list(projSchFileOld, ap):
    """ 1. reads projSchFileOld and returns a nested list where each row of project specific scheduling table is an sublist of the list.
        Header is at index 0. Index signifies FUP sequence. """
    
    projSchOldList = []
    workbook = open_wb(projSchFileOld)
    sheet = workbook.sheet_by_index(0)
    row_count = sheet.nrows
    
    for cur_row in range(1, row_count):
        item1 = formatCellData(sheet.cell(cur_row, 1)) # Diagram Name
        item2 = formatCellData(sheet.cell(cur_row, 2)) # Diagram Path
        item3 = formatCellData(sheet.cell(cur_row, 3))
        item4 = "TRUE"
        item5 = int(float(formatCellData(sheet.cell(cur_row, 5))))
        key = sub(".*" + ap, ap, item2 + item1)
        subList = [key, item1, item2, item3, item4, item5, "check", "#N/A", 0]
        projSchOldList.append(subList)
        
    return projSchOldList


def create_proj_sch_new_list(stdSchList, projSchOldList):
    """ 1. reorders projSchOldList as per ordering in stdSchList.
        2. remaining items of projSchOldList are ordered in alphabetical order.
        3. returns the resultant nested list."""
    
    def sort_key_func(_item):
        for idx, ref_item in enumerate(stdSchList):
            if _item[0] == ref_item[0]:
                _item[6] = "ok"
                _item[7] = idx + 1
                return stdSchList.index(ref_item)
            else:
                continue
        return 9999999
    
    
    def index_after_sorting(projSchNewList_temp_ref, subList_chk):
        diag_path = subList_chk[2]
        # ref list is filtered out to keep items which have same diagram path as item being processed.
        projSchNewList_temp_ref = [_item for _item in projSchNewList_temp_ref if _item[2] == diag_path]
        
        if projSchNewList_temp_ref == []: return 9999999
        else:
            for idx_ref, subList_ref in enumerate(projSchNewList_temp_ref):
                temp_list1 = [subList_ref, subList_chk]
                temp_list2 = sorted(temp_list1, key = lambda x: x[0])
                if temp_list1 != temp_list2: 
                    return subList_ref[8] # returning index of subList_ref in the projSchNewList_temp_ref before list comprehension
                elif subList_ref == projSchNewList_temp_ref[-1]: # check if last subList
                    return subList_ref[8] + 1
                else:
                    continue
        

    projSchNewList_ref = sorted(projSchOldList, key = sort_key_func)
    
    projSchNewList_ok = [_item for _item in projSchNewList_ref if _item[6] == "ok"] # items matched with standard
    projSchNewList_chk = [_item for _item in projSchNewList_ref if _item[6] == "check"] # items needing further sorting
    projSchNewList_chk = sorted(projSchNewList_chk, key = lambda _item : _item[0]) # sort aphabetically
    
    projSchNewList_temp = deepcopy(projSchNewList_ok)
    
    
    for subList_chk in  projSchNewList_chk: # iterate over items needing further sorting
        
        # write index of each sublist at index7 of that subList
        for _item in projSchNewList_temp:
            _item[8] = projSchNewList_temp.index(_item)
            
        projSchNewList_temp_ref = deepcopy(projSchNewList_temp)
        
        new_index = index_after_sorting(projSchNewList_temp_ref, subList_chk)
        
        projSchNewList_temp.insert(new_index, subList_chk)
        
    projSchNewList = [_item[0:8] for _item in projSchNewList_temp]
    
    return projSchNewList
