__author__      = "Nandan Sharma"

from xlrd import open_workbook as open_wb
from re import sub


def num2col(n):
    """Number to Excel-style column name, e.g., 0 = A, 25 = Z, 26 = AA, 702 = AAA."""
    n = n + 1
    name = ''
    while n > 0:
        n, r = divmod (n - 1, 26)
        name = chr(r + ord('A')) + name
    return name
    

def col2num(name):
    """Excel-style column name to number, e.g., A = 0, Z = 25, AA = 26, AAA = 702."""
    n = 0
    for c in name.upper():
        n = n * 26 + 1 + ord(c) - ord('A')
    return n - 1
    
    
def create_spec_dict(file, col_key, col_val, sh_name):
    """arguments:
                    file:       .xls parameter spec file name with path
                    col_key:    .xls column for parameter key
                    col_val:    .xls column for parameter value
                    sh_name:    .xls sheet name
        returns:    
                    Returns a dictionary with parameter key and their values"""

    col_key =  col2num(col_key)
    col_val =  col2num(col_val)

    dict = {}
    workbook = open_wb(file)
    sheet = workbook.sheet_by_name(sh_name)
    row_count = sheet.nrows

    for cur_row in range(0, row_count):
            k = sheet.cell(cur_row, col_key)
            v = sheet.cell(cur_row, col_val)
            
            k = str(k)
            k = sub('^text:', '', k)
            k = sub("'","", k) # remove all single quote chars from the key name
            k = sub('"','', k) # remove all double quote chars from the key name
            k = sub(' ','', k) # remove all space chars from the key name
            k = sub('   ','', k) # remove all tab chars from the key name
        
            v = str(v)
            v = sub('^text:', '', v)
            v = sub('^number:', '', v)
            v = sub("'","", v) # remove all single quote chars from the value
            v = sub('"','', v) # remove all double quote chars from the value
            v = sub(' ','', v) # remove all space chars from the value
            v = sub('   ','', v) # remove all tab chars from the value
            try:
                v = float(v)
            except:
                pass
           
            dict[k] = v
    
    return dict


def create_t3k_list(file, prefix, col_key, col_val):
    """arguments:
                    file:       .xls parameter t3k export file name with path
                    prefix:     prefix for parameter key identification in T3000
                    col_key:    .xls column for parameter key
                    col_val:    .xls column for parameter value
        returns:    
                    list_key:   ordered list of t3k parameter keys
                    list_val:   ordered list of t3k parameter values"""

    col_key =  col2num(col_key)
    col_val =  col2num(col_val)
    
    list_key = []
    list_val = []
    
    workbook = open_wb(file)
    sheet = workbook.sheet_by_index(0)
    row_count = sheet.nrows
    
    for cur_row in range(1, row_count):
        k = sheet.cell(cur_row, col_key)
        v = sheet.cell(cur_row, col_val)
        
        k = str(k)
        k = sub('^text:', '', k)
        k = sub("'","", k) # remove all single quote chars from the key name
        k = sub('"','', k) # remove all double quote chars from the key name
        k = sub(' ','', k) # remove all space chars from the key name
        k = sub('   ','', k) # remove all tab chars from the key name    
        k = sub('^' + prefix, '', k) # remove the prefix from parameter key
        k = sub('^:', '', k) # remove the colon char used after prefix from parameter key
        k = sub(',.*$', '', k) # remove everything after the comma char, including the comma itself
        
        v = str(v)
        v = sub('^text:', '', v)
        v = sub('^number:', '', v)
        v = sub("'","", v) # remove all single quote chars from the value
        v = sub('"','', v) # remove all double quote chars from the value
        v = sub(' ','', v) # remove all space chars from the value
        v = sub('   ','', v) # remove all tab chars from the value
        try:
            v = float(v)
        except:
            pass

        list_key.append(k)
        list_val.append(v)
    
    return list_key, list_val


def update_t3k_list(dict, list_key, list_val, incl_dev_th, dev_th_pct):
    """arguments:
                    dict:           spec dictionary with parameter key and their values
                    list_key:       ordered list of t3k parameter keys
                    list_val:       ordered list of t3k parameter values
                    incl_dev_th:    boolean user input for including parameters with deviation higher than threshold
                    dev_th_pct:     float user input for deviation threshold in %
        returns:    
                    list_val_updated:           ordered list of updated t3k parameter values
                    matched_param_list:         list of t3k parameter keys which are found in the spec dictionary
                    unmatched_param_list_t3k:   list of t3k parameter keys which are not found in the spec dictionary
                    unmatched_param_list_spec:   list of spec parameter keys which are not found in the t3k parameter key list"""
    
    matched_param_list = [['ParameterKey', 'old_Value', 'new_Value', 'deviation %', 'changed in import file', 'check']]
    unmatched_param_list_t3k = [['ParameterKey', 'Value']]
    unmatched_param_list_spec = []
    list_val_updated = list_val[:]

    for idx, key in enumerate(list_key):
        if list_key[idx] in dict.keys():
            old_val = list_val[idx]
            new_val = dict[key]
            try: dev_pct = ((abs(float(old_val) - float(new_val)))*100)/max(float(old_val), 0.001)
            except: dev_pct = 'calcError'
            if old_val == new_val:
                changed = 'NO'
                check = 'OK'
            elif dev_pct == 'calcError':
                changed = 'NO'
                check = 'MISMATCH'
            elif incl_dev_th or (dev_pct < dev_th_pct):
                list_val_updated[idx] = new_val
                if dev_pct < dev_th_pct:
                    changed = 'YES'
                    check = 'DEV < THRESHOLD'
                else:
                    changed = 'YES'
                    check = 'DEV >= THRESHOLD'
            else:
                changed = 'NO'
                check = 'DEV >= THRESHOLD'
            matched_param_list.append([key, old_val, new_val, str(dev_pct), changed, check])

        if list_key[idx] not in dict.keys() and [key, list_val[idx]] not in unmatched_param_list_t3k:
            unmatched_param_list_t3k.append([key, list_val[idx]])
    
    for key in dict.keys():
        if key not in list_key:
            unmatched_param_list_spec.append([key, dict[key]])

    return list_val_updated, matched_param_list, unmatched_param_list_t3k, unmatched_param_list_spec


