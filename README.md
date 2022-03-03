# IGV-S3-Presigned-URL-Session-Creator
A program written to help alleviate the difficulty of expiring S3 links, in IGV Session XMLs.. 

# Set Up
I recommend creating a virtualenv, program was build with python 3.9.7
pip install requirements.txt
aws cli must be installed, and aws configure must be run. 

You may have to modify code to match the S3 path structure of your xmls. This is currently hard-coded to work for my xmls. 

If you plan on creating .exe, which I would recommend, you'll need pyinstaller installed.

Can be done with pip install pyinstaller. 
on windows I recommend following these instructions. https://datatofish.com/executable-pyinstaller/

# Run
From terminal, or cmd prompt just run:
```
python update-existing-xml.py (xmlfile) 
```

This will generate an updated xml file in same directory. 

