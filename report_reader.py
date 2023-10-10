'''
This program reads reports generated by the Intel DPC++/OneAPI compiler
and prints them in the command line.

This way you don't have to open their web application to check basic mectrics.
Opening web pages in cluster environments (which is the common development environment
when you're doing FPGA work) is a pain (zipping + downloading + opening up on your local
computer...)

The next goal is to be able to make reports easily searcheable and comparable by storing
them in a database instead of having a bunch of folder with webpages in them. This will
probably be a separate module/program.
'''

'''
Usage: report_summarizer report_path/
Report summarizer prints to the command line information regarding:
    - FPGA board target
    - Resource usage
    - Loop analysis information

Technical implementation: all of the information shown in the HTML page
are in JSON objects available inside the resources folder. So I just need
to read those.

This project is part of the effort of creating a CI/CD pipeline for FPGA designs in
the context of high performance computing research.
'''

import sys
import json
from pathlib import Path

'''
JSON structure in report_data.js:
    - 'total' lists the usage of ALUTs, REGs, RAM, DSP, and MLAB in that order
    - 'total_percent' doesn't seem to agree with the actual percentage usage
    - 'max_resources' follows the same order as 'total'
    - 'children' is huge.
'''

class Report:
    def __init__(self, reports_path):
        '''
        There's definitely room for encapsulating the logic that reads from the JSON
        I should avoid repeating myself in code
        '''
        self.reports_path = reports_path
        '''
        The report_data.js file contains information on resource usage
        '''
        resource_report = open(reports_path/"resources"/"report_data.js", "r", encoding="utf-8")
        ''' 
        Checking my understanding: There should be a way of doing this without reading 
        The entire report at once.  Some way of doing it by just passing in report
        What kind of object is returned by open()?
        '''
        s = resource_report.readline() 
        # Quick hack to just get info on resources report_data actually contains more than one JSON object
        s = s.lstrip("var areaJSON=")
        s = s[:-2]
        '''
        I don't know anything about string encoding.
        All I know is that loads is taking that string and turning
        into a python object. What is a python object?
        '''
        self.resource_obj = json.loads(s.encode('unicode_escape'))

        # skip until line 5; There's a more elegant and less order-dependent way of doing this I'm sure
        resource_report.readline()
        resource_report.readline()
        resource_report.readline()
        s = resource_report.readline()
        s = s.lstrip("var loop_attrJSON=")
        s = s[:-2]
        self.loop_attr_obj = json.loads(s.encode('unicode_escape'))
        resource_report.close()
        '''
        product_data.js contains information on the board the code is targeting 
        '''
        product_data = open(reports_path/"resources"/"product_data.js")
        s = product_data.readline()
        s = s.lstrip("var infoJSON=")
        s = s[:-2]
        self.product_data_obj = json.loads(s.encode('unicode_escape'))
        product_data.close()
        

    def print_board_info(self):
        p = self.product_data_obj['compileInfo']['nodes'][0]
        print(f"Report from {self.reports_path}:")
        print("Board and product info:")
        print("---")
        print(p['family'])
        print(p['product'])
        print(p['version'])
        print("---")

    def print_resource(label, idx, obj):
        total = obj['total'][idx]
        max_resource = obj['max_resources'][idx]
        print(f"{label : <4} {(total/max_resource) * 100:>5.2f}% ({total}/{max_resource})")

    def print_resource_usage(self):
        print(f"Resource usage:")
        print("----")
        resources = "ALUT REG RAM DSP MLAB".split()
        for idx, j in enumerate(resources):
            Report.print_resource(j, idx, self.resource_obj)
        print("----")

    def print_loop_attr(self):
        print("Loop attributes:")
        print("---")
        for i in self.loop_attr_obj['nodes']:
            print(i['name'])
            for j in i['children']:
                # I'm not sure if this goes deeper than one level. If it does then I'm going to need some recursion
                print(f"{j['name']}: II {j['ii']}")
                if j.get('children'):
                    for k in j['children']:
                        print(f"L {k['name']}: II {k['ii']}")
                        
        print("---")

reports_path = Path(sys.argv[1])
r = Report(reports_path)
r.print_board_info()
r.print_resource_usage()
r.print_loop_attr()