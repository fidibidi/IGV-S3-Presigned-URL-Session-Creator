#!/usr/bin/env python
import sys
from os import path
import json
from json import JSONEncoder

from asyncio import subprocess
from fileinput import filename
from importlib.abc import ResourceReader
from random import sample
from typing import final


import logging
import xml.etree.ElementTree as ET
import subprocess as sp
import boto3 as b3
from botocore.exceptions import ClientError
import pickle


sys.path.append(".")


def bash_command(cmd):
    return sp.Popen(cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE)

def string_prompt(message):
    val = input(message)
    if type(val) == str:
        return val
    else:
        string_prompt("Please enter string values only.")

def bool_prompt(message):
    val = input(message)
    if val.strip().lower() == 'y':
        return True
    elif val.strip().lower() == 'n':
        return False
    else:
        print('Error, please type y or n')
        bool_prompt(message)

class S3SamplesManagerEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class S3SamplesManager:
    def __init__(self, saveFile='data.pl'):
        self.S3Samples = []
        self.saveFile = saveFile

    def bool_prompt(self, message):
        val = input(message)
        if val.strip().lower() == 'y':
            return True
        elif val.strip().lower() == 'n':
            return False
        else:
            print('Error, please type y or n')
            self.bool_prompt(message)

    def addS3Samples(self, s3Sample):
        self.S3Samples.append(s3Sample)

    def start(self, s3Client):
        if (self.bool_prompt("Add sample? (y/n):\n")):
            s3SampleObj = self.S3Sample()
            s3SampleObj.start(s3Client)
            
            S3SampleWithFiles = s3SampleObj.returnS3Sample()

            self.addS3Samples(S3SampleWithFiles)
            self.start(s3Client)

    def convertToJSON(self):
        tempJSON = json.dumps(self.S3Samples, ensure_ascii=False, indent=4)
        print(tempJSON)

    class S3Sample:

        def __init__(self):
            self.IGVFiles = []            

        def __string_prompt(self, message):
            val = input(message)
            if type(val) == str:
                return val
            else:
                self.__string_prompt("Please enter string values only.\n")

        def __bool_prompt(self, message):
            val = input(message)
            if val.strip().lower() == 'y':
                return True
            elif val.strip().lower() == 'n':
                return False
            else:
                print('Error, please type y or n')
                self.__bool_prompt(message)
        
        def saveIGVFile(self, igvFile):
            self.IGVFiles.append(igvFile)
        
        def start(self, s3Client):
            if self.__bool_prompt("Add file for sample? (y/n):\n"):
                type = self.__string_prompt("Type (VCF, BAM):\n")
                filename = self.__string_prompt("Enter filename:\n")
                print("Enter File URL: ")
                print("(ex. s3://praxisgenomics-patient-res/novaseq/CA0402/RES123121/e0e4956a-ad90-4cdf-9451-685aff26293f/$SAMPLE.bam)")
                url = self.__string_prompt("")
                indexUrl = self.__string_prompt("Enter File Index URL: ")

                path = self.createPresign(url, s3Client) 
                index = self.createPresign(indexUrl, s3Client) if indexUrl else ""
                sampleIGVFile = self.IGVFile(filename=filename, url=url, indexUrl=indexUrl, path=path, index=index, type=type)
                
                self.saveIGVFile(sampleIGVFile)
                self.start(s3Client)

        def createPresign(self, link, s3Client):
            if link:
                link = link.split('/',3)
                bucket = link[2]
                key = link[3]

                try:
                    response = s3Client.generate_presigned_url('get_object', Params={'Bucket': bucket,'Key': key},ExpiresIn=600)
                except ClientError as e:
                    logging.error(e)
                    return ""

                return response
            else:
                logging.warning("createPresign: No link was passed.")
                return ""

        def updateLinks(self, s3Client):
            for IGVFileObj in self.IGVFiles:
                IGVFileObj.path = self.createPresign(IGVFileObj.url, s3Client)
                if IGVFileObj.indexUrl:
                    IGVFileObj.index = self.createPresign(IGVFileObj.indexUrl, s3Client)

        def returnS3Sample(self):
            return self


        class IGVFile:
            def __repr__(self):
                return f'Filename: {self.filename}, Index: {self.index}, Path: {self.path}, Type: {self.type}, URL: {self.url}, Index URL: {self.indexUrl}'

            def __init__(self, filename='', url='', indexUrl='', path='', index='', type=''):
                self.filename = filename
                self.index = index
                self.path = path
                self.type = type
                self.url = url
                self.indexUrl = indexUrl

            def importJSON(self, JSONObject):
                self.filename = JSONObject["filename"]
                self.type = JSONObject["type"]
                self.url = JSONObject["url"]
                self.indexUrl = JSONObject["indexUrl"]


class xmlManager:
    def __init__(self):
        self.mainTree = ET.parse('xml-template.xml')
        self.root = self.mainTree.getroot()

    def indent(self, elem, level=0):
        i = "\n" + level*"\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def save(self, output='test.xml'):
        self.indent(self.root)
        self.mainTree.write(output)

    def addResources(self, igvFile):
        resources = self.mainTree.find('Resources')

        resource = ET.SubElement(resources, 'Resource')
        if igvFile.index: 
            resource.set('index', igvFile.index)
        resource.set('path', igvFile.path)

    def addPanelWithBamTrack(self, igvFile, panel):
        coverageTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename} Coverage', autoScale="true", clazz="org.broad.igv.sam.CoverageTrack", color="175,175,175", colorScale="ContinuousColorScale;0.0;60.0;255,255,255;175,175,175", fontSize="10", id=f"{igvFile.path}_coverage", name=f'{igvFile.filename} Coverage', snpThreshold="0.2", visible="true")
        datarange = ET.SubElement(coverageTrack, "DataRange", baseline="0.0", drawBaseline="true", flipAxis="false", maximum="60.0", minimum="0.0", type="LINEAR")
        
        junctionTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename} Junctions', clazz="org.broad.igv.sam.SpliceJunctionTrack", fontSize="10", groupByStrand="false", height="60", id=f"{igvFile.path}_junctions", name=f"{igvFile.filename} Junctions", visible="false")
        alignmentTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename}', clazz="org.broad.igv.sam.AlignmentTrack", displayMode="EXPANDED", experimentType="THIRD_GEN", fontSize="10", id=f"{igvFile.path}", name=f"{igvFile.filename}", visible="false")
        renderOptions = ET.SubElement(alignmentTrack, "RenderOptions")

    def addPanelWithBedgraphTrack(self, igvFile, panel):
        bedgraphTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename}', autoScale="false", clazz="org.broad.igv.sam.DataSourceTrack", fontSize="10", id=f"{igvFile.path}", name=f'{igvFile.filename}', rendere="SCATTER_PLOT", visible="true", windowFunction="none")
        datarange = ET.SubElement(bedgraphTrack, "DataRange", baseline="0.0", drawBaseline="true", flipAxis="false", maximum="1.0", minimum="0.0", type="LINEAR")
        


    def addPanelWithVcfTrack(self, igvFile, panel):
        vcfTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename}', clazz="org.broad.igv.variant.VariantTrack", displayMode="COLLAPSED", fontSize="10", groupByStrand="false", id=f'{igvFile.path}', name=f'{igvFile.filename}', siteColorMode="ALLELE_FREQUENCY", squishedHeight="1", visible="true")

    def processFile(self, igvFile):
        self.addResources(igvFile)
        if igvFile.type == "bam":
            self.addPanelWithBamTrack(igvFile)
        elif igvFile.type == "vcf":
            self.addPanelWithVcfTrack(igvFile)
        elif igvFile.type == "bedgraph":
            self.addPanelWithBedgraphTrack(igvFile)
        

    def processFiles(self, S3Sample, panelID):
        panel = ET.Element("Panel", Panel="300", name=f"{panelID}", width="1311")
        for igvFileObj in S3Sample.IGVFiles:
            self.addResources(igvFileObj)
            if igvFileObj.type == "bam":
                self.addPanelWithBamTrack(igvFileObj, panel)
            elif igvFileObj.type == "vcf":
                self.addPanelWithVcfTrack(igvFileObj, panel)

        self.root.insert(1, panel)

    def processSampleManagerSamples(self, sampleManager):

        PanelInd = 1
        for S3Sample in sampleManager.S3Samples:
            if S3Sample == sampleManager.S3Samples[-1]:
                panelID = "DataPanel"
            else:
                panelID = f'Panel{PanelInd}'
            self.processFiles(S3Sample, panelID)
            PanelInd += 1
    
    def processJSONSamples(self, JSONData):
        pass

def main():
    xmlFile = xmlManager()
    s3Client = b3.client('s3')

    if bool_prompt("Create new IGV session? (y/n):\n"):
        pickleFileName = string_prompt("Please enter a filename that you wish to store data too:\n")
        sampleManager = S3SamplesManager(pickleFileName)
        
        if bool_prompt("Manual Entry? (y/n):\n"):
            sampleManager.start(s3Client)
            
            dataFile = open(pickleFileName, 'ab')
            pickle.dump(sampleManager, dataFile)
            dataFile.close()
    
            xmlFile.processSampleManagerSamples(sampleManager)   
            xmlFile.save()

        elif bool_prompt("Auto Entry? (y/n):\n"):
            exit()


    elif bool_prompt("Load existing IGV session? (y/n):\n"):
        pickleFileName = string_prompt("Enter data filename:\n")
        if bool_prompt("Would you like to regenerate this session? (y/n)\n"):
            
            dataFile = open(pickleFileName, 'rb')
            pickleData = pickle.load(dataFile)
            dataFile.close()

            sampleManager = pickleData
        
            for S3Sample in sampleManager.S3Samples:
                S3Sample.updateLinks(s3Client)
            
            dataFile = open(pickleFileName, 'wb')
            pickle.dump(sampleManager, dataFile)
            dataFile.close()

            xmlFile.processSampleManagerSamples(sampleManager)
            xmlFile.save()

def test():
    xmlFile = xmlManager()
    s3Client = b3.client('s3')
    s3SamplesManager = S3SamplesManager()
    with open('test-2.json') as f:
        data = json.load(f)
        for key, S3sample in data.items():
            S3SampleGroup = S3SamplesManager.S3Sample()
            for fileObj in S3sample:
                igvFile = S3SamplesManager.S3Sample.IGVFile()
                igvFile.importJSON(fileObj)
                S3SampleGroup.saveIGVFile(igvFile)
            S3SampleGroup.updateLinks(s3Client)
            s3SamplesManager.addS3Samples(S3SampleGroup)
    
    # s3SamplesManager.convertToJSON()
    # print(S3SamplesManagerEncoder().encode(s3SamplesManager))
    projectJSON = json.dumps(s3SamplesManager, indent=4, cls=S3SamplesManagerEncoder)
    print(projectJSON)

    with open('saved.json', "w") as f:
        json.dump(s3SamplesManager.S3Samples, f, ensure_ascii=False, indent=4, cls=S3SamplesManagerEncoder)
        
    # xmlFile.processSampleManagerSamples(s3SamplesManager)
    # xmlFile.save()

def savedjsonttest():
    xmlFile = xmlManager()
    s3Client = b3.client('s3')
    s3SamplesManager = S3SamplesManager()
    with open('saved.json') as f:
        data = json.load(f)
        for S3Wrapper in data:
            for key,S3SamplesGroup in S3Wrapper.items():
                S3SampleGroup = S3SamplesManager.S3Sample()
                for s3File in S3SamplesGroup:
                    igvFile = S3SamplesManager.S3Sample.IGVFile()
                    igvFile.importJSON(s3File)
                    S3SampleGroup.saveIGVFile(igvFile)
                S3SampleGroup.updateLinks(s3Client)
                s3SamplesManager.addS3Samples(S3SampleGroup)
                    


    # projectJSON = json.dumps(s3SamplesManager, indent=4, cls=S3SamplesManagerEncoder)
    # print(projectJSON)

    with open('saved2.json', "w") as f:
        json.dump(s3SamplesManager.S3Samples, f, ensure_ascii=False, indent=4, cls=S3SamplesManagerEncoder)
        
    xmlFile.processSampleManagerSamples(s3SamplesManager)
    xmlFile.save()


if __name__ == "__main__":
    savedjsonttest()
    # test()
    # main()

