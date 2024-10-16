#!/usr/bin/env python
import os,sys

import logging
import xml.etree.ElementTree as ET
import boto3 as b3
import datetime

from botocore.exceptions import ClientError

class IGVFile:
    def __repr__(self):
        return f'(Sample: {self.sample}, Filename: {self.filename}, Index: {self.index}, Path: {self.path}, Type: {self.type}, URL: {self.url}, Index URL: {self.indexUrl}, OldURL: {self.oldUrl}, OldIndUrl: {self.oldIndexUrl})'

    def __init__(self, sample='', filename='', url=False, indexUrl='', path='', index='', type='', oldUrl='', oldIndexUrl=''):
        self.filename = filename
        self.index = index
        self.path = path
        self.type = type
        self.url = url
        self.indexUrl = indexUrl
        self.oldUrl = oldUrl
        self.oldIndexUrl = oldIndexUrl
        self.sample = sample

def splitTSSUrl(url):
    splitUrl = url.split("/",3)
    bucket = splitUrl[2].split(".")[0]
    key = splitUrl[3].split("?")[0]
    sampleName = key.split("/")[-1]
    s3Key = f's3://{bucket}/{key}'
    return sampleName, s3Key

def createPresign(link):
    if link:
        link = link.split('/',3)
        bucket = link[2]
        key = link[3]

        try:
            response = s3Client.generate_presigned_url('get_object', Params={'Bucket': bucket,'Key': key},ExpiresIn=604800)
        except ClientError as e:
            logging.error(e)
            return ""

        return response
    else:
        logging.warning("createPresign: No link was passed.")
        return ""

def extractInfoFromResource(resource):
    IGVSampleData = IGVFile()
    existingKeys = resource.keys()
    if "path" in existingKeys:
        if 'https://' in resource.get('path'):
            url = resource.get('path')
            IGVSampleData.oldUrl = url
            sampleName, s3Key = splitTSSUrl(url)
            IGVSampleData.filename = sampleName
            IGVSampleData.sample = IGVSampleData.filename.split('.')[0]
            IGVSampleData.url = s3Key
            IGVSampleData.path = createPresign(s3Key)
            resource.set('path', IGVSampleData.path)
    if "index" in existingKeys:
        if 'https://' in resource.get('index'):
            indexUrl = resource.get('index')
            IGVSampleData.oldIndexUrl = indexUrl
            sampleName, s3Key = splitTSSUrl(indexUrl)
            IGVSampleData.indexUrl = s3Key
            IGVSampleData.index = createPresign(s3Key)
            resource.set('index', IGVSampleData.index)

    if not IGVSampleData.url:
        IGVSampleData = False

    return IGVSampleData

def replaceOldLinks(xmlFile, IGVSample):
    for track in xmlFile.findall('.//Track'):
        if track.attrib['id'] == IGVSample.oldUrl:
            track.set('id', IGVSample.path)
        if track.attrib['id'] == f'{IGVSample.oldUrl}_junctions':
            track.set('id', f'{IGVSample.path}_junctions')
        if track.attrib['id'] == f'{IGVSample.oldUrl}_coverage':
            track.set('id', f'{IGVSample.path}_coverage')

s3Client = b3.client('s3')

class xmlManager:
    def __init__(self, xmlToParse, fileName, dirPath):
        self.mainTree = ET.parse(xmlToParse)
        self.root = self.mainTree.getroot()
        self.fileName = fileName
        self.dirPath = dirPath 

    def backup(self):
        self.mainTree.write(os.path.join(self.dirPath,f'{self.fileName}.original.xml'))

    def save(self):
        date = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        newName = self.fileName.split('.')[0]
        finalName = self.fileName
        if (newName):
            finalName = newName
        self.mainTree.write(os.path.join(self.dirPath,f'{finalName}.regen-{date}.dragen.xml'))
        logging.info("Successfully Saved")

def main():
    xmlFile = sys.argv[1]
    fileName = os.path.basename(xmlFile)
    dirPath = os.path.dirname(xmlFile)
    xmlFileManager = xmlManager(xmlFile, fileName, dirPath)
      
    for resources in xmlFileManager.root.findall('Resources'):
        for resource in resources.findall('Resource'):
            IGVFileObj = extractInfoFromResource(resource)
            if IGVFileObj:
                replaceOldLinks(xmlFileManager.mainTree, IGVFileObj)
    
    xmlFileManager.save()


if __name__ == "__main__":
    main()
