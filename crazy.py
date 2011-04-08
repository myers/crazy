#!/usr/bin/env python

import csv, pprint, os, re
import xml.etree.ElementTree as ET

import java_utils
from collections import defaultdict

"""
oname = obfuscated name
mname = mcp name
bname = bukkit name
"""

def crazy():
    ck = ClassKeeper('../CraftBukkit/src/main/java/net/minecraft/server')
    ck.load_class_list()
    ck.load_class_tree()
    ck.load_members()
    ck.prune_methods()
    #pprint.pprint(ck.bukkit_lookup['Entity'].__dict__)
    #pprint.pprint(ck.bukkit_lookup['EntityLiving'].__dict__)
    #pprint.pprint(ck.bukkit_lookup['EntitySlime'].__dict__)
    #ck.load_fields()
    #ck.prune_fields()

    #def _visitor(clsmodel):
    #    print clsmodel

    rs = RefactorScript(ck.obf_to_bukkit_translator)
    ck.walk_tree(rs.script_for_class)
    rs.write('out.xml')
    
 
class MethodKeeper:
    def __init__(self):
        self.mcp_classes = defaultdict(dict)
        
        for row in csv.reader(open('methods.csv', 'rb')):
            if row[0] != "*":
                continue
            self.mcp_classes[row[2]][row[3]] = row[4]

    def lookup(self, mcp_name, searge_name):
        try:
            return self.mcp_classes[mcp_name][searge_name]            
        except KeyError:
            return searge_name
           
class ClassKeeper:
    def __init__(self, dirname):
        # k: bukkit name, v: ClassModel instance
        self.bukkit_lookup = {}
        # k: obf name, v: bukkit name
        self.obf_lookup = {}
        # k: mcp server name, v: bukkit name
        self.mcp_lookup = {}

        self.dirname = dirname
        
        self.mk = MethodKeeper()
    
    def obf_to_bukkit_translator(self, obf_name):
        return self.obf_lookup.get(obf_name, obf_name)
        
    def class_model_for_obf(self, obf_name):
        b_name = self.obf_lookup[obf_name]
        return self.bukkit_lookup[b_name]
        
    def load_class_tree(self):
        #k class name, v list of parent class name or None
        for root, dirs, files in os.walk(self.dirname):
            dirs.sort()
            for fn in files:
                if os.path.splitext(fn)[1] != '.java':
                    continue
                class_, superclass = java_utils.find_parent(os.path.join(root, fn))
                if not class_:
                    continue
                    
                assert class_ in self.bukkit_lookup.keys(), "%r %r" % (class_, fn,)
                clsmodel = self.bukkit_lookup[class_]
                clsmodel.set_parent(superclass)
                if superclass in self.bukkit_lookup.keys():
                    self.bukkit_lookup[superclass].subclasses.append(clsmodel)
    

        for clsmodel in self.bukkit_lookup.values():
            for interface_name in clsmodel.implements():
                interface_cls_model = self.bukkit_lookup.get(interface_name, None)
                print "I got %r" % (interface_cls_model,)
                if interface_cls_model:
                    interface_cls_model.subclasses.append(clsmodel)
                    
    def load_class_list(self):
        rr = csv.reader(open('mcp1401.csv', 'rb'))
        rr.next()
        for row in rr: 
            
            if len(row) < 7:
                # this class isn't in the server
                continue
            if not row[6]:
                continue
            self.add(ClassModel(
              bukkit_name=row[6], 
              obf_name=row[3], 
              mcp_name=row[0], 
              filepath=os.path.join(self.dirname, row[6] + '.java') 
            ))

    def load_members(self):
        res = {}
        for line in open('minecraft_server.rgs', 'r'):
            if line.startswith('.method_map'):
                start, rest = line.split(' ', 1)
                
                obf_name, end = rest.split('/', 1)
                
                try:
                    clsmodel = self.class_model_for_obf(obf_name)
                except KeyError:
                    continue
                method_sig, dest = end.rsplit(' ', 1)
                
                searge_name = dest.strip()
                method_name = self.mk.lookup(clsmodel.mcp_name, searge_name)
                clsmodel.methods[method_sig] = method_name

                
    def add(self, clsmodel):
        self.bukkit_lookup[clsmodel.bukkit_name] = clsmodel
        self.obf_lookup[clsmodel.obf_name] = clsmodel.bukkit_name
        self.mcp_lookup[clsmodel.mcp_name] = clsmodel.bukkit_name

    def prune_methods(self):
        for classmodel in self.bukkit_lookup.values():
            classmodel.prune_subclasses_methods()

    def walk_tree(self, func, currentclass=None):
        if currentclass is None:
            for clsmodel in self.bukkit_lookup.values():
                if clsmodel.is_interface:
                    self.walk_tree(func, clsmodel)
            for clsmodel in self.bukkit_lookup.values():
                if not clsmodel.superclass:
                    self.walk_tree(func, clsmodel)
            return
        func(currentclass)
        for clsmodel in currentclass.subclasses:
            self.walk_tree(func, clsmodel)


class ClassModel:
    def __init__(self, bukkit_name, obf_name, mcp_name, filepath):
        self.bukkit_name = bukkit_name
        self.obf_name = obf_name
        self.mcp_name = mcp_name
        self.filepath = filepath
        
        self.superclass = None

        # this is also implmentors if this is a interface
        self.subclasses = []
    
        self._is_interface = None    
        # k: obf signature, v: mcp name
        self.methods = {}
        
        #self.fields = {}

    @property
    def is_interface(self):
        if self._is_interface is None:
            if "interface %s" % (self.bukkit_name,) in self.java_file():
                self._is_interface = True
            else:
                self._is_interface = False
            if self.bukkit_name == 'IInventory':
                assert self._is_interface
        return self._is_interface
        
    def set_parent(self, parent_b_name):
        self.superclass = parent_b_name        

    def remove_method(self, method_sig):
        if self.methods.has_key(method_sig):
            print "removing %r %r" % (method_sig, self.methods[method_sig],)
            self.methods.pop(method_sig)
        self.remove_method_in_subclasses(method_sig)
    
    def remove_method_in_subclasses(self, method_sig):
        for subclass in self.subclasses:
            subclass.remove_method(method_sig)

    def prune_subclasses_methods(self):
        for method_sig in self.methods.keys():
            self.remove_method_in_subclasses(method_sig)
            

    def implements(self):
        match = re.search(r'implements (.+){', self.java_file())
        if not match:
            return []
        print match.group(1)
        return [ii.strip() for ii in match.group(1).split(',')]\
        
    def java_file(self):
        return open(self.filepath, 'r').read()

    def __repr__(self):
        return "ClassModel(%r, %r, %r, %r)" % (self.bukkit_name, self.obf_name, self.mcp_name, len(self.subclasses))

class RefactorScript:
    def __init__(self, obf_to_bukkit_translator):
        self.root = ET.Element("session", version="1.0")
        self.obf_to_bukkit_translator = obf_to_bukkit_translator
   
    def script_for_class(self, clsmodel):
        for old_sig, new_name in clsmodel.methods.items():
            old_method_name = old_sig.split(" ")[0]
            if old_method_name == new_name:
                continue
            el = ET.SubElement(self.root, "refactoring", 
              comment="", 
              delegate="false",
              deprecate="false",
              description="Rename method %r to %r" % (old_sig, new_name,),
              flags="589830",
              id="org.eclipse.jdt.ui.rename.method",
              input="/src\/main\/java<net.minecraft.server{%s.java[%s" % (clsmodel.bukkit_name, self.eclipse_sig(clsmodel.bukkit_name, old_sig),),
              name=new_name,
              project="CraftBukkit",
              references="true",
              version="1.0")

    def write(self, path):        
        tree = ET.ElementTree(self.root)
        tree.write(path)

    def eclipse_sig(self, class_name, old_sig):
        # http://www.retrologic.com/rg-docs-grammar.html
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
            #print args
            classname, args = args[1:].split(';', 1)
            classname = classname.split('/')[-1]
            res.append('~Q%s%s;' % (''.join(array), self.obf_to_bukkit_translator(classname),))
        #print old_sig
        #pprint.pprint(res)
        return ''.join(res)

if __name__ == '__main__':
    crazy()
    