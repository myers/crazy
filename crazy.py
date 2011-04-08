#!/usr/bin/env python

import csv, pprint
import xml.etree.ElementTree as ET

"""
oname = obfuscated name
mname = mcp name
bname = bukkit name
"""

def crazy():
    b_class = 'Entity'
    oname, mname = names_for_bukkit_class(b_class)
    out = methods_for_class(oname)
    #pprint.pprint(out)
    methods = rename_methods(mname, out)
    #pprint.pprint(methods)
    refactor_xml(b_class, methods)

def refactor_xml(b_class, methods):
    root = ET.Element("session", version="1.0")
    for new_name, old_sig in methods.items():
        el = ET.SubElement(root, "refactoring", 
          comment="", 
          delegate="false",
          deprecate="false",
          description="Rename method '%s'" % (old_sig,),
          flags="589830",
          id="org.eclipse.jdt.ui.rename.method",
          input="/src\/main\/java<net.minecraft.server{%s.java[%s" % (b_class, eclipse_sig(b_class, old_sig),),
          name=new_name,
          project="CraftBukkit",
          references="true",
          version="1.0")
        
    tree = ET.ElementTree(root)
    #txt = ET.tostring(tree)
    #open('out.xml', 'wb').write(minidom.parseString(txt).toprettyxml())
    tree.write("out.xml")

def eclipse_sig(class_name, old_sig):
    # from something like a (Lfg;F)
    # to Entity~a~QEntity;~I
    
    # int i, float f, double d, boolean b, short s, long l, char c, byte byte0
    # ~I~F~D~Z~S~J~C~B
    # type  | retro | eclipse
    # int   | I     | I 
    # float | F     | F 
    # double| D     | D
    # byte  | B     | B
    # short | S     | S
    # long  | J     | J
    # bool  | Z     | Z
    # char  | C     | C
    # void  | V
    # class | L<cls>;  | Q<cls>;
    
    method_name, rest = old_sig.split(' ', 1)
    args, rest = rest.split(')', 1)
    args = args[1:]
    
    res = [class_name, "~", method_name]
    while len(args):
        array = []
        while args[0] == '[':
            array.append('[')
            args = args[1:]
        if args[0] in ('I', 'F', 'D', 'B', 'S', 'J', 'Z', 'C'):
            res.append('~%s%s' % (''.join(array), args[0],))
            args = args[1:]
            continue
        assert args[0] == 'L', "%r %r" % (args, old_sig,)
        assert ';' in args
        classname, args = args[1:].split(';')
        res.append('~Q%s%s;' % (''.join(array), b_name_for_obfuscated_class(classname),))
    print old_sig
    pprint.pprint(res)
    return ''.join(res)
    
def rename_methods(mname, out):
    assert len(set(out.values())) == len(out.values())
    
    rout = dict((v,k) for k, v in out.iteritems())

    res = {}    
    for row in csv.reader(open('methods.csv', 'rb')):
        if row[0] != "*":
            continue
        if row[2] != mname:
            continue
        #skip c'tors
        if row[3] == mname:
            continue
        # some methods are only on the client
        #if row[1] not in rout.keys():
        #    continue
        print row
        res[row[4]] = rout[row[3]]        
    return res

def names_for_bukkit_class(bukkit_class):
    classlist = csv.reader(open('mcp1401.csv', 'rb'))
    for row in classlist:
        if len(row) < 7:
            continue
        if row[6] == bukkit_class:
            return row[4], row[0]
    raise ArgumentError

def b_name_for_obfuscated_class(o_class):
    classlist = csv.reader(open('mcp1401.csv', 'rb'))
    for row in classlist:
        if len(row) < 7:
            continue
        if row[4] == o_class:
            return row[6]
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
    