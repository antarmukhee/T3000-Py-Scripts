__author__      = "Nandan Sharma"

# first use notepad++ to manually replace following occurrences in xml files:
# 1. {tagname=" + prefix_find} with {tagname=" + prefix_replace}
# 2. {tag=" + prefix_find}     with {tag=" + prefix_replace}
# 3. {nodename=" + prefix_find} with {nodename=" + prefix_replace}

# then use this script to rename folder names. Set {root_dir} to correct path before runnig the script.

import os
import re

root_dir = r"C:\Temp\old"
prefix_find = "YY_10"
prefix_replace = "10"


count = -1

while count != 0:
    count = 0
    for root, dirs, files in os.walk(root_dir, topdown = True):
        for name in dirs:
            if not name.startswith(prefix_find): continue
            pattern = prefix_find + r'(.*)'
            replacement = prefix_replace + r'\1'
            new_name = re.sub(pattern, replacement, name)
            dir_old = os.path.join(root,name)
            dir_new = os.path.join(root,new_name)
            os.rename(dir_old, dir_new)
            count += 1


        
        
        

