#!/usr/bin/env python

import csv, pprint
"""
oname = obfuscated name
mname = mcp name
bname = bukkit name
"""

def crazy():
    oname, mname = names_for_bukkit_class('Entity')
    out = methods_for_class(oname)
    methods = rename_methods(mname, out)
    pprint.pprint(methods)

def rename_methods(mname, out):
    assert len(set(out.values())) == len(out.values())
    
    rout = dict((v,k) for k, v in out.iteritems())

    res = {}    
    for row in csv.reader(open('methods.csv', 'rb')):
        if row[0] != mname:
            continue
        #skip c'tors
        if row[1] == mname:
            continue
        print row
        assert row[1] in rout.keys(), "%r %r" % (row[1], rout.keys(),)
        res[row[4]] = rout[row[1]]        
    return res

def names_for_bukkit_class(bukkit_class):
    classlist = csv.reader(open('mcp1401.csv', 'rb'))
    for row in classlist:
        if len(row) < 7:
            continue
        if row[6] == bukkit_class:
            return row[4], row[0]
    raise ArgumentError

def methods_for_class(name):
    res = {}
    for line in open('minecraft_server.rgs', 'r'):
        if line.startswith('.method_map %s/' % (name,)):
            start, end = line.split('/', 1)
            src, dest = end.rsplit(' ', 1)
            res[src] = dest.strip()
    return res

if __name__ == '__main__':
    crazy()
    