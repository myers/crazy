#!/usr/bin/env python

import os, re
from collections import defaultdict

def class_tree(dir):
    #k class name, v list of parent class name or None
    ret = defaultdict(list)
    for root, dirs, files in os.walk(dir):
        dirs.sort()
        for fn in files:
            if os.path.splitext(fn)[1] != '.java':
                continue
            class_, superclass = find_parent(os.path.join(root, fn))
            if class_:
                ret[superclass].append(class_)
    return ret
                
def find_parent(javasource):
    content = open(javasource, 'rb').read()
    match = re.search(r'class\s+(\w+)\s+extends\s+(\w+)', content, re.MULTILINE)
    if not match:
        return None, None
    return match.groups()

if __name__ == '__main__':
    import sys
    class_tree(sys.argv[1])
    