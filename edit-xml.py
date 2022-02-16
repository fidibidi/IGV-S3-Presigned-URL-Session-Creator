#!/usr/bin/env python
from asyncio import subprocess
from fileinput import filename
from importlib.abc import ResourceReader
from random import sample
from typing import final
import xml.etree.ElementTree as ET
import subprocess as sp

import sys
import pickle

from os import path

sys.path.append(".")


def bash_command(cmd):
    return sp.Popen(cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE)


def make_bam_track(sample, url):
    track = '''    <Track attributeKey="''' + sample + ''' Coverage" autoScale="true" clazz="org.broad.igv.sam.CoverageTrack" color="175,175,175" colorScale="ContinuousColorScale;0.0;60.0;255,255,255;175,175,175" fontSize="10" id="''' + url + '''_coverage" name="''' + sample + ''' Coverage" snpThreshold="0.2" visible="true">
            <DataRange baseline="0.0" drawBaseline="true" flipAxis="false" maximum="60.0" minimum="0.0" type="LINEAR"/>
        </Track>
        <Track attributeKey="''' + sample + ''' Junctions" clazz="org.broad.igv.sam.SpliceJunctionTrack" fontSize="10" groupByStrand="false" height="60" id="''' + url + '''_junctions" name="''' + sample + ''' Junctions" visible="false"/>
        <Track attributeKey="''' + sample + '''" clazz="org.broad.igv.sam.AlignmentTrack" displayMode="EXPANDED" experimentType="THIRD_GEN" fontSize="10" id="''' + url + '''" name="''' + sample + '''" visible="false">
            <RenderOptions/>
        </Track>'''
    return track


def make_vcf_track(fileName, url):
    track = '''<Track attributeKey="''' + fileName + '''" clazz="org.broad.igv.variant.VariantTrack" displayMode="EXPANDED" featureVisibilityWindow="100000" fontSize="10" groupByStrand="false" id="''' + \
        url + '''" name="''' + fileName + \
            '''" siteColorMode="ALLELE_FREQUENCY" squishedHeight="1" visible="true"/>'''
    # track = '''<Track attributeKey="M0354.cuteSV.vcf" clazz="org.broad.igv.variant.VariantTrack" displayMode="EXPANDED" fontSize="10" groupByStrand="false" id="https://praxisgenomics-patient-res.s3.us-east-1.amazonaws.com/nanopore/rando-ONT/vcfs/cuteSV/M0354.cuteSV.vcf?X-Amz-Algorithm=AWS4-HMAC-SHA256&amp;X-Amz-Credential=AKIASEJWMTN76OTW345Z%2F20220209%2Fus-east-1%2Fs3%2Faws4_request&amp;X-Amz-Date=20220209T215802Z&amp;X-Amz-Expires=604800&amp;X-Amz-SignedHeaders=host&amp;X-Amz-Signature=8b6d2171cc291f062483089f36cf23dbc82a83c1d9a7516f0f99ce4e5abe8b06" name="M0354.cuteSV.vcf" siteColorMode="ALLELE_FREQUENCY" squishedHeight="1" visible="true"/>'''
    return track


def return_track(track_list):
    combined_tracks = ""
    for track in track_list:
        if not combined_tracks:
            combined_tracks = track
        else:
            combined_tracks = f'''{combined_tracks}
        {track}'''
    return combined_tracks


def make_panel(track_list):
    header = '''<Panel height="395" name="DataPanel" width="1311">'''
    closer = '''</Panel>'''
    final_panel = f'''{header}
    {return_track(track_list)}
    {closer}'''
    return final_panel


def make_sample_panels(samples_list):
    file_panels = []
    for file_list in samples_list:
        file_tracks = []
        for files_object in file_list:
            file_track = ""
            if files_object.type == "bam":
                file_track = make_bam_track(
                    files_object.filename, files_object.path)
            if files_object.type == "vcf":
                file_track = make_vcf_track(
                    files_object.filename, files_object.path)
            file_tracks.append(file_track)
        file_panels.append(file_tracks)
    # iterate through and combine...

    final_panels = ""
    for panel in file_panels:
        if not final_panels:
            final_panels = make_panel(panel)
        else:
            # final_panels = final_panels + "\n" + make_panel(panel)
            final_panels = f'''{final_panels}
    {make_panel(panel)}'''

    return final_panels


def make_resource(sample_dict):
    index = sample_dict.index
    index = (f'index="{index}" ' if sample_dict.index else '')

    path = sample_dict.path
    path = (f'path="{path}"' if sample_dict.path else '')

    resource = '''<Resource ''' + index + path + '''/>'''
    return resource


def make_resources(sample_list):
    final_resources = ""
    for files_list in sample_list:
        for files_object in files_list:
            resource = make_resource(files_object)
            if resource:
                if not final_resources:
                    final_resources = f'''{resource}'''
                else:
                    final_resources = f'''{final_resources}
        {resource}'''
    return final_resources



class IGVFile:
    def __init__(self, filename, path, type, index=''):
        self.filename = filename
        self.index = index
        self.path = path
        self.type = type

class S3SamplesManager:
    def __init__(self):
        self.S3Samples = []

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

    def start(self):
        if (self.bool_prompt("Add sample?: ")):
            sampleTemp = self.S3Sample()
            sampleTemp.start()
            
            S3SampleWithFiles = sampleTemp.returnS3Sample()

            self.addS3Samples(S3SampleWithFiles)
            self.start()

    
    class S3Sample:
        def __init__(self):
            self.IGVFiles = []

        def __bool_prompt(self, message):
            val = input(message)
            if val.strip().lower() == 'y':
                return True
            elif val.strip().lower() == 'n':
                return False
            else:
                print('Error, please type y or n')
                self.__bool_prompt(message)

        def __string_prompt(self, message):
            val = input(message)
            if type(val) == str:
                return val
            else:
                self.__string_prompt("Please enter string values only.")
        
        def start(self):
            if self.__bool_prompt("Add file for sample?: "):
                self.createSampleIGVFiles()
                self.start()

        def createSampleIGVFiles(self):
            filename = self.__string_prompt("Enter filename: ")
            type = self.__string_prompt("Type (VCF, BAM): ")
            path = self.__string_prompt("Enter File URL: ")
            index = self.__string_prompt("Enter File Index URL: ")
            # sample = self.IGVFile(filename, path, type, index)
            sample = self.IGVFile()
            self.IGVFiles.append(sample)

        def returnS3Sample(self):
            return self.IGVFiles


        class IGVFile:
            def __repr__(self):
                return f'Filename: {self.filename}, Index: {self.index}, Path: {self.path}, Type: {self.type}'

            def __init__(self, filename='M0356.sorted.bam', path='https://praxisgenomics-patient-res.s3.us-east-1.amazonaws.com/nanopore/rando-ONT/bams/M0356.sorted.bam?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIASEJWMTN76OTW345Z%2F20220216%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20220216T211445Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=721f65941799c60a51d2f11d7721ff362755778414e20cd233c036c7d472156f', type='bam', index='https://praxisgenomics-patient-res.s3.us-east-1.amazonaws.com/nanopore/rando-ONT/bams/M0356.sorted.bam.bai?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIASEJWMTN76OTW345Z%2F20220216%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20220216T211449Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=920cabc890f8e13056c61552cf80753f078d7182618e3d3db9434df45355bbda'):
                self.filename = filename
                self.index = index
                self.path = path
                self.type = type


def string_main():
    if not path.exists('data.pl'):
        sampleManager = S3SamplesManager()
        sampleManager.start()
        dataFile = open('data.pl', 'ab')
        pickle.dump(sampleManager, dataFile)
        dataFile.close()
    else:
        print("DATA EXISTS")
        dataFile = open('data.pl', 'rb')
        pickleData = pickle.load(dataFile)
        sampleManager = pickleData
        dataFile.close()

    text = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<Session genome="hg38" hasGeneTrack="true" hasSequenceTrack="true" locus="chr1:237334302-237369372" nextAutoscaleGroup="2" version="8">
    <Resources>
        ''' + make_resources(sampleManager.S3Samples) + '''
    </Resources>
    ''' + make_sample_panels(sampleManager.S3Samples) + '''
    <Panel height="54" name="FeaturePanel" width="1311">
        <Track attributeKey="Reference sequence" clazz="org.broad.igv.track.SequenceTrack" fontSize="10" id="Reference sequence" name="Reference sequence" sequenceTranslationStrandValue="POSITIVE" shouldShowTranslation="false" visible="true"/>
        <Track attributeKey="Gene" clazz="org.broad.igv.track.FeatureTrack" color="0,0,178" colorScale="ContinuousColorScale;0.0;845.0;255,255,255;0,0,178" fontSize="10" groupByStrand="false" height="35" id="hg38_genes" name="Gene" visible="true"/>
    </Panel>
    <PanelLayout dividerFractions="0.2126642771804062,0.4336917562724014,0.6798088410991637,0.929510155316607"/>
    <HiddenAttributes>
        <Attribute name="DATA FILE"/>
        <Attribute name="DATA TYPE"/>
        <Attribute name="NAME"/>
    </HiddenAttributes>
</Session>'''

    fileTree = ET.ElementTree(ET.fromstring(text))
    fileTree.write('edit-xml-2.xml')


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
                indent(elem, level+1)
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
        resource.set('index', igvFile.index)
        resource.set('path', igvFile.path)

    def addPanelWithTrack(self, igvFile):
        panel = ET.Element("Panel", Panel = "300", name = "DataPanel", width = "1311")
        coverageTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename} Coverage', autoScale="true", clazz="org.broad.igv.sam.CoverageTrack", color="175,175,175", colorScale="ContinuousColorScale;0.0;60.0;255,255,255;175,175,175", fontSize="10", id=f"{igvFile.path}_coverage", name=f'{igvFile.filename} Coverage', snpThreshold="0.2", visible="true")
        datarange = ET.SubElement(coverageTrack, "DataRange", baseline="0.0", drawBaseline="true", flipAxis="false", maximum="60.0", minimum="0.0", type="LINEAR")
        
        junctionTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename} Junctions', clazz="org.broad.igv.sam.SpliceJunctionTrack", fontSize="10", groupByStrand="false", height="60", id=f"{igvFile.path}_junctions", name=f"{igvFile.filename} Junctions", visible="false")
        alignmentTrack = ET.SubElement(panel, "Track", attributeKey=f'{igvFile.filename}', clazz="org.broad.igv.sam.AlignmentTrack", displayMode="EXPANDED", experimentType="THIRD_GEN", fontSize="10", id=f"{igvFile.path}", name=f"{igvFile.filename}", visible="false")
        renderOptions = ET.SubElement(alignmentTrack, "RenderOptions")

        self.root.insert(1, panel)

    def processFile(self, igvFile):
        self.addResources(igvFile)
        self.addPanelWithTrack(igvFile)



def main():
    xmlFile = xmlManager()
    IGVFileObj = S3SamplesManager.S3Sample.IGVFile()
    xmlFile.processFile(IGVFileObj)    
    xmlFile.save()



if __name__ == "__main__":
    main()

