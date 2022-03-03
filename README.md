# IGV-S3-Presigned-URL-Session-Creator
A program written to help alleviate the difficulty of expiring S3 links, in IGV Session XMLs.. 

Currently there are three variations:
update-existing-xml.py - This script takes an xml file, looks at all resources, and if they are links, it will try to update them accordingly. 
update-existing-xml-gui.py - Same as above, but with a tkinter interface. 
create-xml.py - This will walk you through creating an xml from scratch. Will save JSON file of xml data, and can regenerate xmls based on these JSON files. Not super well tested as of 3/3/22.

# Set Up
I recommend creating a virtualenv, program was build with python 3.9.7
pip install requirements.txt
aws cli must be installed, and aws configure must be run. 

You may have to modify code to match the S3 path structure of your xmls. This is currently hard-coded to work for my xmls. 


## Additional Set Up
If you plan on creating .exe, which I would recommend, you'll need pyinstaller installed.

Can be done with pip install pyinstaller. 
on windows I recommend following these instructions. https://datatofish.com/executable-pyinstaller/

```
pyinstaller --onefile update-existing-xml.py
```

You can then just drag the file you want updated onto the .exe, making a very simple app to use. 

# Run

From terminal, or cmd prompt just run:
```
python update-existing-xml.py (xmlfile) 
```

This will generate an updated xml file in same directory. 

