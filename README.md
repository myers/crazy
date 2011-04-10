# Crazy

A crazy seeming idea that's working.  Long have the tribes of Bukkit and MCP
been seprate, but now they will be rejoined!

This script, crazy.py, will create an Eclipse refactor script that will
instruct Eclipse how to rename all the methods in the CraftBukkit project
using the names the MCP project uses for their server deobfuscation.  This
will allow folks that want to dig deeper into the minecraft server code to
do so without risking obfuscation madness.

## To run

from a command line run 

python crazy.py

it will put out a file called out.xml

load up CraftBukkit in eclipse.  

Add the missing classes from mc-dev.

fix the bugs in the missing classes.

Ask the bukkit team again why they don't commit the code that produces
minecraft_server-xx.jar

Go to the Refactor menu. Pick "Apply Script..."

find out.xml.  

Apply.  This will take about 20 minutes.

Many fields and some methods, but that's usually where the Bukkit guys have
already renamed something.

enjoy.



