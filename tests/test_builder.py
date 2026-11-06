import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'UNR_Course_Script_Builder.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BuilderTests(unittest.TestCase):
    def test_defaults(self):
        c=b.validate_settings({'subjects':['ENG']})
        self.assertTrue(c['useCurrentTerm']);self.assertEqual(c['minimumCourseNumber'],'')
        self.assertEqual(c['outputFormat'],'csv');self.assertEqual(b.DEFAULTS['subjects'],[])

    def test_invalid_settings(self):
        for updates in [{'subjects':[]},{'subjects':'ENG'},{'year':'27'},
            {'minimumCourseNumber':'x'},{'minimumCourseNumber':'800','maximumCourseNumber':'600'},
            {'start':'25:00'},{'filterSchedule':True,'start':'16:00','end':'08:00'},
            {'filterSchedule':True,'days':[]},{'customSubjects':'CS;alert(1)'},
            {'status':'Available'},{'outputFormat':'xml'},{'courses':[]}]:
            with self.subTest(updates=updates),self.assertRaises(ValueError):
                b.validate_settings({'subjects':['ENG'],**updates})

    def test_web_and_desktop_config_equivalence(self):
        cases=[{'subjects':['ENG']},{'subjects':['NURS','CS'],'minimumCourseNumber':'100','maximumCourseNumber':'499'},
            {'subjects':['ART'],'useCurrentTerm':False,'termOverride':'Fall 2028','outputFormat':'tsv'},
            {'subjects':['CS'],'customSubjects':'cs, ENG','keywords':'art, design','instructor':'Smith',
             'component':'lab','status':'Open','filterSchedule':True,'days':['Mo','We'],'start':'12:00','end':'18:00','outputFormat':'json','includeReview':False}]
        for settings in cases:
            node="const C=require('./docs/assets/core.js');process.stdout.write(JSON.stringify(C.validateSettings(JSON.parse(process.argv[1]))));"
            out=subprocess.run(['node','-e',node,json.dumps(settings)],cwd=ROOT,check=True,text=True,capture_output=True)
            self.assertEqual(b.validate_settings(settings),json.loads(out.stdout))

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'settings.json').write_text(json.dumps({'subjects':['ENG'],'outputFormat':'csv'}))
            subprocess.run(['python3',str(ROOT/'UNR_Course_Script_Builder.py'),'--generate',str(p/'settings.json'),'--output',str(p/'output.js')],check=True,capture_output=True)
            subprocess.run(['node','--check',str(p/'output.js')],check=True,capture_output=True)
            self.assertNotIn('__CONFIG_JSON__',(p/'output.js').read_text())

    def test_export_roundtrip_in_standard_csv_reader(self):
        import csv,io
        node="const fs=require('fs');eval(fs.readFileSync('src/exports.js','utf8'));process.stdout.write(serializeTable([['Title','Notes'],['A, B','two\\n\"lines\"']]));"
        out=subprocess.run(['node','-e',node],cwd=ROOT,check=True,text=True,capture_output=True)
        self.assertEqual(list(csv.reader(io.StringIO(out.stdout.lstrip('\ufeff')))),[['Title','Notes'],['A, B','two\n"lines"']])

if __name__=='__main__':unittest.main(verbosity=2)
