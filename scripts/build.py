#!/usr/bin/env python3
"""Build both distributable interfaces from the shared browser engine."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def build():
    subjects=json.loads((ROOT/'data/subjects.json').read_text())
    instructions=(ROOT/'data/instructions.txt').read_text()
    template=(ROOT/'src/browser-template.js').read_text()
    template=template.replace('__MATCHING_JS__',(ROOT/'src/matching.js').read_text())
    template=template.replace('__EXPORTS_JS__',(ROOT/'src/exports.js').read_text())
    desktop=(ROOT/'src/desktop.py').read_text().replace('__SUBJECTS_JSON__',repr(subjects))
    desktop=desktop.replace('__INSTRUCTIONS_REPR__',repr(instructions)).replace('__TEMPLATE_REPR__',repr(template))
    # Keep the generated engine readable for inspection.
    if "'''" not in template:
        desktop=desktop.replace('JS_TEMPLATE = '+repr(template), "JS_TEMPLATE = r'''\n"+template+"\n'''")
    core=(ROOT/'src/core.js').read_text().replace('__SUBJECTS_JSON__',json.dumps(subjects,ensure_ascii=True))
    core=core.replace('__TEMPLATE_JSON__',json.dumps(template,ensure_ascii=True))
    for path in [ROOT/'UNR_Course_Script_Builder.py',ROOT/'docs/downloads/UNR_Course_Script_Builder.py']:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(desktop,encoding='utf-8')
    (ROOT/'docs/assets/core.js').write_text(core,encoding='utf-8')
    (ROOT/'docs/downloads/INSTRUCTIONS.txt').write_text(instructions,encoding='utf-8')
    schedule=(ROOT/'src/schedule-engine.js').read_text().replace('/*__MATCHING__*/',(ROOT/'src/matching.js').read_text())
    (ROOT/'docs/assets/schedule-engine.js').write_text(schedule,encoding='utf-8')
    (ROOT/'docs/.nojekyll').touch()
    print('Built standalone Python app and GitHub Pages assets.')

if __name__=='__main__': build()
