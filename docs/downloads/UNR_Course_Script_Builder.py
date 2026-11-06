#!/usr/bin/env python3
"""UNR Course Script Builder — local Tkinter GUI; no third-party packages.

Run: python3 UNR_Course_Script_Builder.py
The generated JavaScript runs in your signed-in MyNEVADA browser tab.
"""
import argparse
from datetime import datetime
import json
import re
from pathlib import Path

SUBJECTS = {'ACC': 'Accounting', 'AE': 'Aerospace engineering', 'AGSC': 'Agricultural science', 'AM': 'American Sign Language', 'ANTH': 'Anthropology', 'ARA': 'Arabic', 'ART': 'Art', 'ATMS': 'Atmospheric science', 'BADM': 'Business administration', 'BASQ': 'Basque studies', 'BCH': 'Biochemistry', 'BIOL': 'Biology', 'BME': 'Biomedical engineering', 'BUS': 'Business', 'CEE': 'Civil & environmental engineering', 'CH': 'Core humanities', 'CHE': 'Chemical engineering', 'CHEM': 'Chemistry', 'CHI': 'Chinese', 'CMB': 'Cell & molecular biology', 'COLA': 'Liberal arts', 'COM': 'Communication', 'CPE': 'Computer engineering', 'CRJ': 'Criminal justice', 'CS': 'Computer science', 'DAN': 'Dance', 'ECON': 'Economics', 'EDSP': 'Special education', 'EDUC': 'Education', 'EE': 'Electrical engineering', 'EECB': 'Ecology, evolution & conservation biology', 'ENG': 'English', 'ENGR': 'Engineering', 'ENT': 'Entrepreneurship', 'ETS': 'Ethnic studies', 'FIN': 'Finance', 'FREN': 'French', 'GEOG': 'Geography', 'GEOL': 'Geology', 'GER': 'German', 'GRAD': 'Graduate studies', 'GRC': 'Graphic design', 'GRI': 'Gender, race & identity', 'HDFS': 'Human development & family science', 'HGPS': 'Holocaust, genocide & peace studies', 'HIST': 'History', 'HP': 'Historic preservation', 'IAFF': 'International affairs', 'IS': 'Information systems', 'ITAL': 'Italian', 'JOUR': 'Journalism', 'JPN': 'Japanese', 'KIN': 'Kinesiology', 'MATH': 'Mathematics', 'ME': 'Mechanical engineering', 'MGT': 'Management', 'MIL': 'Military science', 'MINE': 'Mining engineering', 'MKT': 'Marketing', 'MSE': 'Materials science & engineering', 'MUS': 'Music', 'MUSA': 'Music: applied', 'MUSE': 'Music: ensembles', 'NRES': 'Natural resources & environmental science', 'NURS': 'Nursing', 'NUTR': 'Nutrition', 'PAIT': 'Northern Paiute', 'PBH': 'Public health', 'PHIL': 'Philosophy', 'PHYS': 'Physics', 'PSC': 'Political science', 'PSY': 'Psychology', 'RST': 'Religious studies', 'SCM': 'Supply chain management', 'SOC': 'Sociology', 'SOTA': 'School of the arts', 'SPAN': 'Spanish', 'STAT': 'Statistics', 'THTR': 'Theatre', 'WMST': "Women's studies"}
DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
DEFAULTS = dict(useCurrentTerm=True, year=str(datetime.now().year), season='Spring', termOverride='',
    subjects=[], customSubjects='', minimumCourseNumber='', maximumCourseNumber='',
    keywords='', instructor='', component='', status='Any', filterSchedule=False,
    days=DAYS.copy(), start='08:00', end='18:00', outputFormat='csv', includeReview=True)

INSTRUCTIONS = "COURSE SEARCH STUDIO — UNR\n\n1. Select subjects (or type any MyNEVADA subject codes), course-number limits,\n   and optional title, instructor, status, component, day, or time filters.\n   By default, all course numbers are eligible and the script uses the term\n   already selected in MyNEVADA. To choose another term, turn that option off.\n\n2. Choose CSV (default), JSON, or TSV under Export. Copy the generated script\n   or save it as a .txt file. Keep the desktop app open until you paste.\n\n3. Sign in to MyNEVADA yourself and open Class Search. Select the desired term.\n   Open your browser's developer console and choose the top execution context.\n   Firefox on Mac: Command–Option–K; Windows/Linux: Ctrl–Shift–K.\n   Paste the entire generated script and press Return. Keep the tab open.\n\n4. The script uses normal class-search controls, expands sections, follows\n   recognized pages, and downloads your chosen file. Review its summary to\n   see whether every requested subject finished. If blocked, run:\n     UNRexport.download()\n   Other formats: UNRexport.downloadCSV(), UNRexport.downloadJSON(),\n   or UNRexport.downloadTSV(). Stop and save partial data: UNRexport.stop().\n\nWHAT THE FILTERS MEAN\n• All listed meetings of an individual section must fit the selected days\n  and hours. Endpoints are inclusive. Hours are campus-local, 24-hour time.\n• TBA, missing, overnight, or unrecognized schedules need review when the\n  time/day filter is on. TBA does not prove online or asynchronous delivery.\n• When time filtering is off, TBA sections can match your other criteria;\n  Schedule verified will still say No.\n• Comma-separated title keywords use ANY-match, ignoring case. Instructor\n  accepts part of a name. Blank fields mean no restriction.\n• Course numbers are numeric ranges, not a guarantee of degree applicability.\n• Component filters (LEC, LAB, etc.) select individual sections. They do not\n  verify linked lecture/lab enrollment combinations.\n• Most filters are applied after collection. Closed sections are collected\n  too, so the JSON retains the other course components for inspection.\n\nREADING THE FILE\nCSV / TSV: the first data row is Search summary, followed by one row per\nmeeting. Match distinguishes Matches selected filters from Needs review.\nThe optional needs-review checkbox affects CSV/TSV only. A header plus a\nsummary with zero matches is a valid result. PARTIAL filenames and the\nSearch completeness column identify unfinished searches. Search notes name\nunfinished subjects and any error. Start/end times use 24-hour time and\nmeeting dates use YYYY-MM-DD when recognizable.\nJSON: results.matched, results.needsReview, results.excluded, and\nresults.unparsedRows contain the audit. courses retains raw text and rows.\nThe summary and searches fields describe collection progress.\n\nLIMITATIONS AND PRIVACY\nThis independent tool supports UNR's observed MyNEVADA layout; it is not an\nofficial university service or a universal adapter for other universities.\nVerify required lecture/lab/discussion combinations, credits, prerequisites,\npermissions, and seats in MyNEVADA. Broad searches can hit university limits;\nnarrow subjects or minimum course numbers and inspect any partial export.\nNo section-detail-only credits, delivery modes, or prerequisites are inferred.\nPage layout changes may require updating the engine.\nNeither builder asks for passwords or uploads your results. The generated\nscript works in your browser session using normal search controls and does\nnot enroll you. Saved settings contain filters only. GitHub Pages serves the\nbuilder; it does not access MyNEVADA on your behalf.\n"

def parse_time(value):
    match = re.fullmatch(r'(\d{1,2}):(\d{2})', str(value).strip())
    if not match or int(match[1]) > 23 or int(match[2]) > 59:
        raise ValueError('Enter time as HH:MM in 24-hour format, such as 08:00 or 16:30.')
    return int(match[1]) * 60 + int(match[2])

def validate_settings(raw):
    if not isinstance(raw, dict):
        raise ValueError('Expected a saved settings object.')
    if set(raw)-set(DEFAULTS):
        raise ValueError('Import saved settings, not exported course results.')
    settings = dict(DEFAULTS)
    settings.update(raw)
    for key in ('useCurrentTerm', 'filterSchedule', 'includeReview'):
        if not isinstance(settings[key], bool):
            raise ValueError('Invalid checkbox setting: '+key)
    if not isinstance(settings['subjects'], list) or any(not isinstance(s, str) for s in settings['subjects']):
        raise ValueError('Subjects must be a list of codes.')
    if not isinstance(settings['days'], list):
        raise ValueError('Invalid meeting days.')
    if not re.fullmatch(r'20\d{2}', str(settings['year']).strip()):
        raise ValueError('Enter a four-digit year from 2000 to 2099.')
    if settings['season'] not in ('Spring','Summer','Fall','Winter'):
        raise ValueError('Choose Spring, Summer, Fall, or Winter.')
    term = str(settings['termOverride']).strip() or f"{settings['year']} {settings['season']}"
    if settings['useCurrentTerm']: term = ''
    if len(term) > 100:
        raise ValueError('The term label is too long.')
    subjects = list(dict.fromkeys(list(settings['subjects']) +
        re.split(r'[,\s]+', str(settings['customSubjects']).strip().upper())))
    subjects = list(dict.fromkeys(s.strip().upper() for s in subjects if s.strip()))
    if not subjects or any(not re.fullmatch(r'[A-Z]{2,8}', s) for s in subjects):
        raise ValueError('Select at least one subject. Custom subject codes must be 2–8 letters.')
    minimum, maximum = (str(settings[k]).strip() for k in ('minimumCourseNumber','maximumCourseNumber'))
    if any(v and not re.fullmatch(r'\d{1,4}', v) for v in (minimum, maximum)):
        raise ValueError('Course limits must be whole numbers or blank.')
    if minimum and maximum and int(minimum) > int(maximum):
        raise ValueError('Minimum course number cannot exceed maximum.')
    start, end = parse_time(settings['start']), parse_time(settings['end'])
    if not isinstance(settings['filterSchedule'], bool):
        raise ValueError('Schedule filtering must be true or false.')
    if settings['filterSchedule'] and (start >= end or not settings['days']):
        raise ValueError('For schedule filtering, choose at least one day and an end time later than the start.')
    if any(d not in DAYS for d in settings['days']):
        raise ValueError('Invalid day code in settings.')
    component = str(settings['component']).strip().upper()
    if component and not re.fullmatch(r'[A-Z]{2,5}', component):
        raise ValueError('Use a component code such as LEC, LAB, DIS, or SEM; blank means any.')
    if settings['status'] not in ('Any','Open','Closed','Waitlist'):
        raise ValueError('Invalid section status.')
    if settings['outputFormat'] not in ('csv','json','tsv'):
        raise ValueError('Choose CSV, JSON, or TSV.')
    return dict(useCurrentTerm=settings['useCurrentTerm'],termName=term, subjects=subjects, minimumCourseNumber=minimum,
        maximumCourseNumber=maximum, keywords=[k.strip() for k in str(settings['keywords']).split(',') if k.strip()],
        instructor=str(settings['instructor']).strip(), component=component,
        status=settings['status'], filterSchedule=settings['filterSchedule'],
        days=list(dict.fromkeys(settings['days'])), startMinutes=start, endMinutes=end,
        outputFormat=settings['outputFormat'],includeReview=settings['includeReview'],timeoutMs=45000, maxPageActions=250)

def generate_script(settings):
    config = validate_settings(settings)
    # JSON encoding prevents text entered in the GUI from becoming JS code.
    return JS_TEMPLATE.replace('__CONFIG_JSON__', json.dumps(config, indent=2, ensure_ascii=True))

def launch_gui():
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        from tkinter.scrolledtext import ScrolledText
    except ImportError as exc:
        raise SystemExit('This app needs Python with Tkinter. Install a Tk-enabled Python 3 distribution, then run again.') from exc

    class App:
        def __init__(self, root):
            self.root = root
            root.title('Course Search Studio — UNR')
            root.geometry('980x770')
            root.minsize(820, 680)
            style = ttk.Style(root)
            if 'clam' in style.theme_names(): style.theme_use('clam')
            style.configure('TLabel', padding=2)
            style.configure('TButton', padding=(9,6))
            main = ttk.Frame(root, padding=16)
            main.pack(fill='both', expand=True)
            ttk.Label(main,text='Course Search Studio',font=('TkDefaultFont',19,'bold')).pack(anchor='w')
            ttk.Label(main,text='For any UNR student. Choose classes around your interests and availability.').pack(anchor='w',pady=(0,12))
            book = self.book = ttk.Notebook(main)
            book.pack(fill='both',expand=True)
            self.search_outer, self.search = self.scrollable_form(book, tk, ttk)
            self.subject_outer, self.subject_tab = self.scrollable_form(book, tk, ttk)
            self.export_tab = ttk.Frame(book,padding=16)
            self.preview_tab = ttk.Frame(book,padding=10)
            help_tab = ttk.Frame(book,padding=10)
            for frame,title in ((self.search_outer,'Search settings'),(self.subject_outer,'Subjects'),(self.export_tab,'Export'),(self.preview_tab,'Console script'),(help_tab,'How to run')):
                book.add(frame,text=title)
            self.vars = {k:(tk.BooleanVar(value=v) if isinstance(v,bool) else tk.StringVar(value=v))
                         for k,v in DEFAULTS.items() if k not in ('subjects','days')}
            self.subject_vars = {s:tk.BooleanVar(value=False) for s in SUBJECTS}
            self.day_vars = {d:tk.BooleanVar(value=True) for d in DAYS}
            self.make_search(ttk)
            self.make_subjects(ttk)
            self.make_export(ttk)
            self.preview = ScrolledText(self.preview_tab,wrap='none',font=('Courier',10),undo=False)
            self.preview.pack(fill='both',expand=True)
            self.preview.configure(state='disabled')
            help_text = ScrolledText(help_tab,wrap='word',font=('TkDefaultFont',11))
            help_text.pack(fill='both',expand=True)
            help_text.insert('1.0',INSTRUCTIONS); help_text.configure(state='disabled')
            buttons = ttk.Frame(main); buttons.pack(fill='x',pady=(12,4))
            for label,func in [('Preview',self.preview_script),('Copy console script',self.copy_script),('Save script…',self.save_script)]:
                ttk.Button(buttons,text=label,command=func).pack(side='left',padx=(0,6))
            ttk.Button(buttons,text='Load settings…',command=self.load_settings).pack(side='right')
            ttk.Button(buttons,text='Save settings…',command=self.save_settings).pack(side='right',padx=6)
            self.status = tk.StringVar(value='Ready. Select subjects to begin. Defaults: selected MyNEVADA term, all course levels, CSV.')
            ttk.Label(main,textvariable=self.status,wraplength=900).pack(anchor='w',pady=(4,0))

        def scrollable_form(self, parent, tk, ttk):
            outer=ttk.Frame(parent)
            canvas=tk.Canvas(outer,highlightthickness=0)
            bar=ttk.Scrollbar(outer,orient='vertical',command=canvas.yview)
            bar.pack(side='right',fill='y'); canvas.pack(side='left',fill='both',expand=True)
            canvas.configure(yscrollcommand=bar.set)
            inner=ttk.Frame(canvas,padding=16)
            window_id=canvas.create_window((0,0),window=inner,anchor='nw')
            inner.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.bind('<Configure>',lambda event:canvas.itemconfigure(window_id,width=event.width))
            return outer,inner

        def make_search(self, ttk):
            f=self.search
            f.columnconfigure(1,weight=1)
            term=ttk.Frame(f); term.grid(row=0,column=0,columnspan=2,sticky='ew',pady=5)
            ttk.Checkbutton(term,text='Use the term selected in MyNEVADA',variable=self.vars['useCurrentTerm']).pack(side='top',anchor='w',pady=(0,8))
            ttk.Label(term,text='Year').pack(side='left')
            ttk.Entry(term,textvariable=self.vars['year'],width=7).pack(side='left',padx=(4,14))
            ttk.Label(term,text='Term').pack(side='left')
            ttk.Combobox(term,textvariable=self.vars['season'],values=('Spring','Summer','Fall','Winter'),state='readonly',width=12).pack(side='left',padx=4)
            self.field(f,1,'Exact term label (optional)','termOverride','Used when the checkbox above is off. Must match an available term label.')
            numbers=ttk.Frame(f); numbers.grid(row=2,column=0,columnspan=2,sticky='ew',pady=9)
            for label,key in [('Minimum course number','minimumCourseNumber'),('Maximum','maximumCourseNumber')]:
                ttk.Label(numbers,text=label).pack(side='left')
                ttk.Entry(numbers,textvariable=self.vars[key],width=8).pack(side='left',padx=(5,18))
            ttk.Label(numbers,text='Blank = no limit').pack(side='left')
            self.field(f,3,'Title keywords (any match)','keywords','Example: ecology, water, statistical — leave blank for all titles.')
            self.field(f,4,'Instructor contains','instructor','Optional name or part of a name.')
            options=ttk.Frame(f); options.grid(row=5,column=0,columnspan=2,sticky='ew',pady=10)
            ttk.Label(options,text='Status').pack(side='left')
            ttk.Combobox(options,textvariable=self.vars['status'],values=('Any','Open','Closed','Waitlist'),state='readonly',width=12).pack(side='left',padx=(4,20))
            ttk.Label(options,text='Component').pack(side='left')
            ttk.Combobox(options,textvariable=self.vars['component'],values=('','LEC','LAB','DIS','SEM','IND','FLD','PRA'),width=10).pack(side='left',padx=4)
            ttk.Label(options,text='Blank = any').pack(side='left')
            schedule=ttk.LabelFrame(f,text='Meeting days and times',padding=12)
            schedule.grid(row=6,column=0,columnspan=2,sticky='ew',pady=8)
            ttk.Checkbutton(schedule,text='Require every listed meeting to fit these days and hours',variable=self.vars['filterSchedule']).pack(anchor='w')
            days=ttk.Frame(schedule); days.pack(anchor='w',pady=8)
            for d,label in zip(DAYS,['Mon','Tue','Wed','Thu','Fri','Sat','Sun']):
                ttk.Checkbutton(days,text=label,variable=self.day_vars[d]).pack(side='left',padx=(0,12))
            times=ttk.Frame(schedule); times.pack(anchor='w')
            for label,key in [('Start no earlier than','start'),('End no later than','end')]:
                ttk.Label(times,text=label).pack(side='left')
                ttk.Entry(times,textvariable=self.vars[key],width=7).pack(side='left',padx=(5,16))
            ttk.Label(schedule,text='24-hour campus-local time. TBA / unknown times go to “needs review”.',wraplength=740).pack(anchor='w',pady=(8,0))
            ttk.Label(f,text='Matches are individual sections. Required lecture/lab combinations, credits,\nprerequisites, and enrollment permissions still need checking in MyNEVADA.',wraplength=760).grid(row=7,column=0,columnspan=2,sticky='w',pady=8)

        def field(self,parent,row,label,key,hint):
            from tkinter import ttk
            ttk.Label(parent,text=label).grid(row=row,column=0,sticky='nw',padx=(0,12),pady=5)
            box=ttk.Frame(parent); box.grid(row=row,column=1,sticky='ew',pady=5)
            ttk.Entry(box,textvariable=self.vars[key]).pack(fill='x')
            ttk.Label(box,text=hint,wraplength=580).pack(anchor='w')

        def make_subjects(self,ttk):
            import tkinter as tk
            f=self.subject_tab
            ttk.Label(f,text='Common subjects across majors. Add any other MyNEVADA subject code below.').pack(anchor='w')
            self.subject_filter=tk.StringVar()
            search=ttk.Entry(f,textvariable=self.subject_filter)
            search.pack(fill='x',pady=(8,0))
            ttk.Label(f,text='Filter by name or code; hidden selections are retained.').pack(anchor='w')
            buttons=ttk.Frame(f); buttons.pack(anchor='w',pady=8)
            ttk.Button(buttons,text='Select shown',command=self.select_shown).pack(side='left',padx=(0,6))
            ttk.Button(buttons,text='Clear selections',command=lambda:self.select_subjects([])).pack(side='left')
            self.subject_count=tk.StringVar()
            ttk.Label(buttons,textvariable=self.subject_count).pack(side='left',padx=12)
            ttk.Label(f,text='Additional subject codes (comma-separated)').pack(anchor='w',pady=(6,2))
            ttk.Entry(f,textvariable=self.vars['customSubjects']).pack(fill='x')
            ttk.Label(f,text='These suggestions are not a live offering list. Use MyNEVADA to confirm codes.').pack(anchor='w',pady=6)
            self.subject_grid=ttk.Frame(f); self.subject_grid.pack(fill='x',pady=8)
            self.subject_filter.trace_add('write',lambda *args:self.draw_subjects())
            for v in self.subject_vars.values(): v.trace_add('write',lambda *args:self.update_subject_count())
            self.draw_subjects()

        def update_subject_count(self):
            self.subject_count.set(str(sum(v.get() for v in self.subject_vars.values()))+' selected')

        def draw_subjects(self):
            from tkinter import ttk
            for child in self.subject_grid.winfo_children(): child.destroy()
            term=self.subject_filter.get().lower()
            self.shown_subjects=[s for s,name in SUBJECTS.items() if term in (s+' '+name).lower()]
            for i,code in enumerate(self.shown_subjects):
                ttk.Checkbutton(self.subject_grid,text=f'{code} — {SUBJECTS[code]}',variable=self.subject_vars[code]).grid(row=i//2,column=i%2,sticky='w',padx=(0,16),pady=5)
            self.update_subject_count()

        def select_shown(self):
            for s in self.shown_subjects: self.subject_vars[s].set(True)

        def make_export(self,ttk):
            f=self.export_tab
            ttk.Label(f,text='Automatic result download',font=('TkDefaultFont',14,'bold')).pack(anchor='w',pady=(0,12))
            for value,label in [('csv','CSV — readable spreadsheet (default)'),('json','JSON — full results and search audit'),('tsv','TSV — tab-separated spreadsheet')]:
                ttk.Radiobutton(f,text=label,variable=self.vars['outputFormat'],value=value).pack(anchor='w',pady=6)
            ttk.Checkbutton(f,text='Include needs-review sections in CSV / TSV',variable=self.vars['includeReview']).pack(anchor='w',pady=16)
            ttk.Label(f,text='CSV and TSV start with a Search summary row, then one row per meeting.\nColumns include course, section, instructor, days, start/end times, room,\nstatus, and any reason for review. Partial searches are clearly labeled.\n\nJSON always contains raw courses, matches, excluded sections, and search logs.\nTBA does not establish that a class is asynchronous or online.\n\nAfter a search, request another format in the browser console:\nUNRexport.downloadCSV()\nUNRexport.downloadJSON()\nUNRexport.downloadTSV()',wraplength=740).pack(anchor='w')

        def select_subjects(self,subjects):
            for s,var in self.subject_vars.items(): var.set(s in subjects)

        def settings(self):
            data={k:v.get() for k,v in self.vars.items()}
            data['subjects']=[s for s,v in self.subject_vars.items() if v.get()]
            data['days']=[d for d,v in self.day_vars.items() if v.get()]
            return data

        def script(self):
            try: return generate_script(self.settings())
            except (ValueError,TypeError) as exc:
                messagebox.showerror('Check your settings',str(exc),parent=self.root)
                return None

        def preview_script(self):
            code=self.script()
            if code is None: return
            self.preview.configure(state='normal'); self.preview.delete('1.0','end')
            self.preview.insert('1.0',code); self.preview.configure(state='disabled')
            self.book.select(self.preview_tab)
            self.status.set('Preview refreshed from the current settings. Copy and Save also regenerate it.')

        def copy_script(self):
            code=self.script()
            if code is None: return
            self.root.clipboard_clear(); self.root.clipboard_append(code); self.root.update()
            self.status.set('Copied. Keep this window open until you paste into the browser’s top console context.')

        def save_script(self):
            code=self.script()
            if code is None: return
            config=validate_settings(self.settings())
            basename='UNR_'+re.sub(r'[^A-Za-z0-9]+','_',config['termName'] or 'selected_term')+'_Search.txt'
            path=filedialog.asksaveasfilename(parent=self.root,initialfile=basename,defaultextension='.txt',filetypes=[('Console script text','*.txt'),('JavaScript','*.js')])
            if path:
                try: Path(path).write_text(code,encoding='utf-8')
                except OSError as exc: messagebox.showerror('Could not save',str(exc),parent=self.root); return
                self.status.set('Saved script: '+path)

        def save_settings(self):
            if self.script() is None: return
            path=filedialog.asksaveasfilename(parent=self.root,initialfile='UNR_search_settings.json',defaultextension='.json',filetypes=[('JSON settings','*.json')])
            if path:
                try: Path(path).write_text(json.dumps(self.settings(),indent=2),encoding='utf-8')
                except OSError as exc: messagebox.showerror('Could not save',str(exc),parent=self.root); return
                self.status.set('Saved settings: '+path)

        def load_settings(self):
            path=filedialog.askopenfilename(parent=self.root,filetypes=[('JSON settings','*.json')])
            if not path: return
            try:
                data=json.loads(Path(path).read_text(encoding='utf-8'))
                if not isinstance(data,dict): raise ValueError('Expected a settings object.')
                if set(data)-set(DEFAULTS): raise ValueError('This is not a builder settings file. Load a saved settings JSON, not exported course results.')
                merged=dict(DEFAULTS); merged.update(data); validate_settings(merged)
                for k,var in self.vars.items(): var.set(merged[k])
                self.select_subjects(merged['subjects'])
                for d,var in self.day_vars.items(): var.set(d in merged['days'])
                # Keep any non-built-in subjects when loading hand-edited settings.
                extra=[s for s in merged['subjects'] if s not in SUBJECTS]
                if extra: self.vars['customSubjects'].set(', '.join([merged['customSubjects'],*extra]).strip(', '))
                self.status.set('Loaded settings: '+path)
            except (OSError,ValueError,TypeError,KeyError) as exc:
                messagebox.showerror('Could not load settings',str(exc),parent=self.root)

    try: root=tk.Tk()
    except tk.TclError as exc:
        raise SystemExit('Cannot open a desktop window. Run this file on your Mac/PC with a graphical session and Tk-enabled Python.') from exc
    App(root)
    root.mainloop()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate',metavar='SETTINGS.json',help='Generate a script without opening the GUI')
    parser.add_argument('--output',default='UNR_Custom_Search.txt',help='Output path for --generate')
    args=parser.parse_args()
    if args.generate:
        try:
            settings=json.loads(Path(args.generate).read_text(encoding='utf-8'))
            Path(args.output).write_text(generate_script(settings),encoding='utf-8')
        except (ValueError,TypeError,OSError) as exc: parser.error(str(exc))
        print(args.output)
    else: launch_gui()


# Generated from the shared browser engine by scripts/build.py.
JS_TEMPLATE = r'''

/* MyNEVADA custom course search, generated by UNR Course Script Builder.
 * Sign in, open Class Search, then paste into the top browser console context.
 * Uses the normal search interface only. Keep the tab open.
 * Stop: UNRexport.stop()  JSON: UNRexport.download()  CSV: UNRexport.downloadCSV()
 * CSV is the default; JSON preserves raw results and TSV is also available.
 * Time matching requires every listed meeting to fit. TBA is kept separately.
 * Linked lecture/lab requirements, credits and enrollment eligibility need review.
 */
(async () => {
  'use strict';
  const CONFIG = __CONFIG_JSON__;
  let resolvedTerm = null;
  if (!/(^|\.)unr\.edu$/i.test(window.location.hostname)) throw Error('Run this script on MyNEVADA at UNR, not on the builder website.');
  if (window !== window.top) throw Error('Select the top console context, then rerun.');
  if (window.UNRexport?.running) throw Error('An exporter is already running.');
  const output = {
    format: 'UNR-student-course-export-v2', started: new Date().toISOString(),
    term: CONFIG.termName, subjectsRequested: CONFIG.subjects,
    minimumCourseNumber: CONFIG.minimumCourseNumber,
    includeClosedClasses: true, filters: CONFIG, searches: [], courses: [],
    limitations: ['Displayed search results only; detail-only prerequisites, units, and linked-section rules may require separate review.',
      'Matches are individual sections, not verified lecture/lab enrollment combinations. TBA does not prove asynchronous delivery.',
      'End-of-pages is based on recognized UI controls, not independent confirmation of the university database.']
  };
// Conservative section matching. No guesses about TBA or linked components.
function parseMeeting(value) {
  const text = String(value || '').trim();
  const re = /((?:(?:Mo|Tu|We|Th|Fr|Sa|Su)\s*)+)\s+(\d{1,2}:\d{2}\s*[AP]M)\s*[-–—]\s*(\d{1,2}:\d{2}\s*[AP]M)/gi;
  const matches = [...text.matchAll(re)];
  const residue = text.replace(re, '').replace(/[\s|;,]+/g, '');
  const minutes = t => {
    const m = t.match(/^(\d{1,2}):(\d{2})\s*([AP])M$/i);
    if (!m || +m[1] < 1 || +m[1] > 12 || +m[2] > 59) return NaN;
    return (+m[1] % 12) * 60 + +m[2] + (/p/i.test(m[3]) ? 720 : 0);
  };
  const canonical = {mo:'Mo',tu:'Tu',we:'We',th:'Th',fr:'Fr',sa:'Sa',su:'Su'};
  const meetings = matches.map(m => ({
    days: m[1].match(/Mo|Tu|We|Th|Fr|Sa|Su/gi).map(d => canonical[d.toLowerCase()]),
    start: minutes(m[2]), end: minutes(m[3]), raw: m[0]
  }));
  return {meetings, known: meetings.length > 0 && !residue &&
    meetings.every(m => Number.isFinite(m.start) && Number.isFinite(m.end) && m.end > m.start)};
}

function buildMatches(courses, config) {
  const sections = new Map(), unparsed = [];
  for (const course of courses) {
    let previous = null;
    for (const row of course.rows || []) {
      if (/^Class$/i.test(String(row[0] || '').trim())) { previous = null; continue; }
      if (/^\d{4,8}$/.test(String(row[0] || '').trim()) && row.length >= 7) {
        const classNumber = row[0].trim();
        const key = course.subject + ':' + classNumber;
        if (!sections.has(key)) sections.set(key, {
          subject: course.subject, heading: course.heading, classNumber,
          section: row[1], meetingRows: [], notes: [],
          component: (row[1].match(/-([A-Z]+)/) || [,''])[1]
        });
        previous = sections.get(key);
        const meeting = {daysTimes:row[2], room:row[3], instructor:row[4], dates:row[5], status:row[6]};
        if (!previous.meetingRows.some(m => JSON.stringify(m) === JSON.stringify(meeting))) previous.meetingRows.push(meeting);
      } else if (previous && !String(row[0] || '').trim() && row.length >= 6 && row.slice(2,6).some(Boolean)) {
        const meeting = {daysTimes:row[2] || '',room:row[3] || '',instructor:row[4] || '',dates:row[5] || '',status:row[6] || ''};
        if (!previous.meetingRows.some(m => JSON.stringify(m) === JSON.stringify(meeting))) previous.meetingRows.push(meeting);
      } else if (previous && /Notes:/i.test(row.join(' '))) {
        const note = row.join(' ').trim();
        if (!previous.notes.includes(note)) previous.notes.push(note);
      } else if (row.length >= 6 && row.slice(2,6).some(Boolean)) {
        // Unknown data layout is retained for review, never silently called a match.
        unparsed.push({heading:course.heading,row});
      }
    }
  }
  const matched = [], needsReview = [], excluded = [];
  for (const section of sections.values()) {
    const reasons = [], uncertain = [];
    const n = +(section.heading.match(/^[A-Z]+\s+(\d+)/) || [,'NaN'])[1];
    if (!Number.isFinite(n)) uncertain.push('Unrecognized course number');
    else if ((config.minimumCourseNumber && n < +config.minimumCourseNumber) ||
             (config.maximumCourseNumber && n > +config.maximumCourseNumber)) reasons.push('Course number outside selected range');
    const title = section.heading.toLowerCase();
    if (config.keywords.length && !config.keywords.some(k => title.includes(k.toLowerCase()))) reasons.push('No title keyword match');
    if (config.instructor && !section.meetingRows.some(m => m.instructor.toLowerCase().includes(config.instructor.toLowerCase()))) reasons.push('Instructor does not match');
    if (config.component && section.component !== config.component) reasons.push('Component does not match');
    const statuses = [...new Set(section.meetingRows.map(m => m.status.trim()).filter(Boolean))];
    section.status = statuses.join(' / ');
    if (config.status !== 'Any') {
      const recognized = statuses.map(s => /^open$/i.test(s) ? 'Open' : /^closed$/i.test(s) ? 'Closed' : /^wait\s*list(?:ed)?$/i.test(s) ? 'Waitlist' : 'Unknown');
      if (!recognized.length || recognized.includes('Unknown')) uncertain.push('Status cannot be verified');
      if (recognized.some(s => s !== 'Unknown' && s !== config.status)) reasons.push('Status does not match');
    }
    const parsed = section.meetingRows.map(m => parseMeeting(m.daysTimes));
    section.scheduleVerified = parsed.length > 0 && parsed.every(p => p.known);
    if (config.filterSchedule) {
      if (!section.scheduleVerified) uncertain.push('TBA, missing, overnight, or unrecognized meeting schedule');
      for (const p of parsed) for (const m of p.meetings) {
        if (m.days.some(d => !config.days.includes(d))) reasons.push('Meets on an excluded day');
        if (m.start < config.startMinutes || m.end > config.endMinutes) reasons.push('Meeting extends outside selected hours');
      }
    }
    section.reasons = [...new Set(reasons.length ? [...reasons,...uncertain] : uncertain)];
    section.matchStatus = reasons.length ? 'excluded' : uncertain.length ? 'needs_review' : 'matched';
    (reasons.length ? excluded : uncertain.length ? needsReview : matched).push(section);
  }
  return {matched, needsReview, excluded, unparsedRows:unparsed, totalSections:sections.size};
}


function exportTable(output, config) {
  const columns = ['Record type','Match','Subject','Course number','Course title','Class number',
    'Section','Component','Class status','Days','Start time','End time','Meeting time as listed',
    'Room','Instructor','First meeting date','Last meeting date','Schedule verified','Notes',
    'Term','Search completeness','Search notes','Collected at'];
  const results = output.results;
  const complete = output.status === 'finished';
  const done = (output.searches || []).filter(s => ['no_results','reached_end_of_recognized_results'].includes(s.status)).map(s=>s.subject);
  const requested = output.subjectsRequested || [];
  const unfinished = requested.filter(s=>!done.includes(s));
  const status = complete ? 'Finished recognized pages' : 'PARTIAL — search incomplete';
  const searchNotes = `${done.length}/${requested.length} subject searches finished. Requested: ${requested.join(', ')}.` +
    (unfinished.length ? ` Unfinished: ${unfinished.join(', ')}.` : '') + (output.error ? ` ${output.error}` : '') +
    (results.unparsedRows.length ? ` ${results.unparsedRows.length} unrecognized result rows: inspect JSON.` : '');
  const rows = [columns];
  const record = fields => columns.map(c => fields[c] ?? '');
  const common = {'Term':output.term,'Search completeness':status,'Search notes':searchNotes,'Collected at':output.finished || output.started};
  rows.push(record({...common,'Record type':'Search summary',Notes:
    `${results.matched.length} matching sections; ${results.needsReview.length} need review; ${results.excluded.length} excluded. `+
    `Time filter ${config.filterSchedule ? 'on' : 'off'}. `+
    (config.includeReview ? 'Needs-review sections included below. ' : 'Needs-review sections omitted from table; download JSON to inspect them. ')+
    'Matches are individual sections. Verify required lecture/lab combinations, credits, prerequisites and seats in MyNEVADA.'}));
  const names={Mo:'Monday',Tu:'Tuesday',We:'Wednesday',Th:'Thursday',Fr:'Friday',Sa:'Saturday',Su:'Sunday'};
  const clock = m => String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
  const isoDate = value => {
    const m = String(value || '').match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    return m ? `${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}` : value || '';
  };
  const sections=[...results.matched,...(config.includeReview ? results.needsReview : [])]
    .sort((a,b)=>a.heading.localeCompare(b.heading,undefined,{numeric:true}) || a.classNumber.localeCompare(b.classNumber));
  for (const s of sections) for (const raw of s.meetingRows) {
    const parsed=parseMeeting(raw.daysTimes);
    const blocks=parsed.known ? parsed.meetings : [null];
    const dates=raw.dates.split(/\s+[-–—]\s+/);
    const heading=s.heading.match(/^[A-Z]{2,8}\s+(\d+[A-Z]?)\s*[-–—:]\s*(.*)$/);
    for (const m of blocks) rows.push(record({...common,'Record type':'Section',
      'Match':s.matchStatus === 'matched' ? 'Matches selected filters' : 'Needs review',
      'Subject':s.subject,'Course number':heading?.[1] || '', 'Course title':heading?.[2] || s.heading,
      'Class number':s.classNumber,'Section':s.section.replace(/\s+/g,' ').trim(),'Component':s.component,
      'Class status':s.status,'Days':m ? m.days.map(d=>names[d]).join(', ') : '',
      'Start time':m ? clock(m.start) : '', 'End time':m ? clock(m.end) : '',
      'Meeting time as listed':raw.daysTimes,'Room':raw.room,'Instructor':raw.instructor,
      'First meeting date':isoDate(dates[0]),'Last meeting date':isoDate(dates[1]),
      'Schedule verified':s.scheduleVerified ? 'Yes' : 'No',
      'Notes':[...s.reasons,...s.notes].join('; ')}));
  }
  return rows;
}

function serializeTable(rows, separator=',') {
  // Quote every field, preserve Unicode, and neutralize spreadsheet formulas.
  const cell = value => {
    let s=String(value ?? '');
    if (/^\s*[=+@-]/.test(s) || /^[\t\r]/.test(s)) s="'"+s;
    return '"'+s.replace(/"/g,'""')+'"';
  };
  return '\uFEFF'+rows.map(row=>row.map(cell).join(separator)).join('\r\n');
}

  let stopped = false;
  const courseKeys = new Set();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const visible = e => !!e && e.getClientRects().length > 0 && e.ownerDocument.defaultView.getComputedStyle(e).visibility !== 'hidden';
  const label = e => [e.innerText, e.value, e.title, e.getAttribute('aria-label'),
    ...Array.from(e.querySelectorAll('img'), i => i.alt)].filter(Boolean).join(' ').replace(/\s+/g, ' ').trim();
  function documents(w = window, out = []) {
    try {
      out.push(w.document);
      for (const f of w.document.querySelectorAll('iframe,frame')) documents(f.contentWindow, out);
    } catch (_) { /* Inaccessible frames are not bypassed. */ }
    return out;
  }
  const groups = d => Array.from(d.querySelectorAll('a[id^="SSR_CLSRSLT_WRK_GROUPBOX2$"]')).filter(visible);
  function doc() {
    const ds = documents();
    return ds.find(d => groups(d).length) || ds.find(d => visible(d.getElementById('SSR_CLSRCH_WRK_SUBJECT$0')))
      || ds.find(d => d.defaultView?.name === 'TargetContent');
  }
  const byId = id => doc()?.getElementById(id);
  function refreshMatches() {
    output.results = buildMatches(output.courses, CONFIG);
    output.summary = {matched:output.results.matched.length,
      needsReview:output.results.needsReview.length, excluded:output.results.excluded.length,
      totalSections:output.results.totalSections, unparsedRows:output.results.unparsedRows.length};
  }
  const basename = () => 'UNR_' + (output.term || 'selected_term').replace(/[^a-z0-9]+/gi, '_') + (output.status === 'finished' ? '' : '_PARTIAL');
  function download(format = CONFIG.outputFormat) {
    refreshMatches();
    if (!['csv','tsv','json'].includes(format)) throw Error('Use csv, tsv, or json.');
    const content = format === 'json' ? JSON.stringify(output, null, 2) : serializeTable(exportTable(output, CONFIG), format === 'tsv' ? '\t' : ',');
    const mime = {csv:'text/csv',tsv:'text/tab-separated-values',json:'application/json'}[format];
    const blob = new Blob([content], {type:mime+';charset=utf-8'});
    const url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url; a.download=basename()+'_courses.'+format;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),60000);
  }
  window.UNRexport = {running:true,data:output,stop:()=>{stopped=true;},download,
    downloadCSV:()=>download('csv'),downloadJSON:()=>download('json'),downloadTSV:()=>download('tsv')};
  function check() { if (stopped) throw Error('Stopped by user'); }
  let emptySearch = false;
  const confirmedSearchPrompts = new WeakSet();
  const isLargeSearchPrompt = text => /your search will return over\s+\d+\s+classes,?\s+would you like to continue\?/i.test(text.replace(/\s+/g, ' '));
  async function acceptLargeSearchPrompt() {
    // Only accept the exact class-search warning shown in the supplied screenshot.
    // Do not accept other dialogs (registration, account changes, errors, etc.).
    for (const d of documents()) {
      const candidates = Array.from(d.querySelectorAll('button,input[type="button"],input[type="submit"],a,[role="button"]'))
        .filter(e => visible(e) && !e.disabled && e.getAttribute('aria-disabled') !== 'true' &&
          /^(?:OK|&OK)$/i.test((e.value || e.innerText || e.getAttribute('aria-label') || '').trim()));
      for (const button of candidates) {
        if (confirmedSearchPrompts.has(button)) continue;
        let container = button.parentElement;
        while (container) {
          const text = container.innerText || '';
          if (isLargeSearchPrompt(text) || /(?:search returned no results|no classes found that meet your search criteria)/i.test(text)) {
            // Require one OK button in the warning's shared container.
            if (candidates.filter(e => container.contains(e)).length !== 1) break;
            confirmedSearchPrompts.add(button);
            if (!isLargeSearchPrompt(text)) emptySearch = true;
            console.log('[UNR exporter] Acknowledging class-search message.');
            button.click();
            await sleep(1000);
            return true;
          }
          container = container.parentElement;
        }
      }
    }
    return false;
  }
  async function waitFor(predicate, description) {
    const start = Date.now(); let stableSince = 0, lastSignature = null;
    while (Date.now() - start < CONFIG.timeoutMs) {
      check();
      if (await acceptLargeSearchPrompt()) { stableSince = 0; continue; }
      if (predicate()) {
        const signature = resultSignature();
        if (signature !== lastSignature) { stableSince = 0; lastSignature = signature; }
        stableSince ||= Date.now();
        if (Date.now() - stableSince > 1200) return;
      } else stableSince = 0;
      await sleep(250);
    }
    throw Error('Timed out: ' + description + '. Partial data saved. Inspect the page for a message.');
  }
  function resultSignature() {
    return groups(doc() || document).map(a => {
      const n = a.id.split('$').pop();
      return doc().getElementById('win0divSSR_CLSRSLT_WRK_GROUPBOX2$' + n)?.innerText || label(a);
    }).join('\n');
  }
  async function clickAndWait(element, predicate, description) {
    if (!element || !visible(element) || element.disabled || element.getAttribute('aria-disabled') === 'true')
      throw Error('Control unavailable: ' + description);
    check(); element.click();
    await waitFor(predicate, description);
    await sleep(500);
  }
  async function setField(id, value) {
    let e = byId(id);
    if (!e) throw Error('Missing search field: ' + id);
    if (e.value === value) return;
    e.value = value;
    e.dispatchEvent(new e.ownerDocument.defaultView.Event('input', {bubbles:true}));
    e.dispatchEvent(new e.ownerDocument.defaultView.Event('change', {bubbles:true}));
    await sleep(500);
    await waitFor(() => byId(id)?.value === value, 'set ' + id);
  }
  async function form() {
    if (visible(byId('SSR_CLSRCH_WRK_SUBJECT$0')) && !groups(doc()).length) return;
    await clickAndWait(byId('CLASS_SRCH_WRK2_SSR_PB_MODIFY'),
      () => visible(byId('SSR_CLSRCH_WRK_SUBJECT$0')) && !groups(doc()).length, 'Modify Search');
  }
  function noResults() { return emptySearch || /no classes found|no results found|search returned no results/i.test(doc()?.body?.innerText || ''); }
  function capMessage() {
    // Match an actual returned-result error, not help text such as 'narrow your search'.
    const text = doc()?.body?.innerText || '';
    const match = text.match(/(?:your search|the search|search results|this search)\s+(?:has\s+)?(?:returned|retrieved|exceeded)\s+(?:more than|over|the maximum)[^\n]{0,180}|(?:search results|number of classes returned)\s+exceed(?:s|ed)?[^\n]{0,180}/i);
    return match ? match[0] : '';
  }
  function capped() { return !!capMessage(); }
  async function prepare(subject) {
    await form();
    const termId = 'CLASS_SRCH_WRK2_STRM$35$';
    const termSelect = byId(termId);
    if (!termSelect?.options) throw Error('Term selector not found. Open Class Search first.');
    // Use the selected term or match a live label; never infer term codes.
    const normalize = value => value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim().split(/\s+/).sort().join(' ');
    let chosen;
    if (CONFIG.useCurrentTerm) {
      resolvedTerm ??= termSelect.value;
      chosen = [...termSelect.options].find(o => o.value === resolvedTerm && !o.disabled && o.value);
      if (!chosen) throw Error('Choose a term in MyNEVADA before running the script.');
      if (termSelect.value !== resolvedTerm) throw Error('Selected term changed during the search. Rerun on the desired term.');
    } else {
      const options=[...termSelect.options].filter(o=>normalize(o.text)===normalize(CONFIG.termName) && !o.disabled && o.value);
      if (options.length !== 1) throw Error('Requested term is not uniquely available: '+CONFIG.termName+
        '. Available terms: '+[...termSelect.options].map(o=>o.text).join(', '));
      chosen=options[0]; resolvedTerm=chosen.value;
      if (termSelect.value !== resolvedTerm) await setField(termId,resolvedTerm);
      if (byId(termId)?.value !== resolvedTerm) throw Error('Term verification failed.');
    }
    output.resolvedTermCode=resolvedTerm; output.term=chosen.text.trim();
    if (byId('CLASS_SRCH_WRK2_INSTITUTION$31$')?.value !== 'UNR01')
      throw Error('Institution must be University of Nevada, Reno.');
    // Clear all text criteria within the class-search fields, not personal fields.
    for (const e of Array.from(doc().querySelectorAll('input[type="text"][id^="SSR_CLSRCH_WRK_"]')))
      if (e.value) await setField(e.id, '');
    for (const stem of ['ACAD_CAREER$2','INSTRUCTION_MODE$4','SSR_COMPONENT$11','SESSION_CODE$12','LOCATION$13','CRSE_ATTR$14','CRSE_ATTR_VALUE$14'])
      await setField('SSR_CLSRCH_WRK_' + stem, '');
    for (const old of Array.from(doc().querySelectorAll('input[type="checkbox"][id^="SSR_CLSRCH_WRK_"]'))) {
      const e = byId(old.id);
      if (e?.checked) { e.click(); await sleep(500); }
    }
    await setField('SSR_CLSRCH_WRK_SUBJECT$0', subject);
    await setField('SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$1', CONFIG.minimumCourseNumber ? 'G' : 'E');
    await setField('SSR_CLSRCH_WRK_CATALOG_NBR$1', CONFIG.minimumCourseNumber);
    if (byId('SSR_CLSRCH_WRK_SSR_OPEN_ONLY$3')?.checked) throw Error('Open-only filter is still selected.');
    if (byId('SSR_CLSRCH_WRK_SUBJECT$0')?.value.trim() !== subject) throw Error('Subject verification failed.');
  }
  async function expand() {
    for (let i = 0; i < 300; i++) {
      const a = groups(doc()).find(e => e.getAttribute('aria-expanded') === 'false' || /\bexpand section\b/i.test(label(e)));
      if (!a) return;
      const id = a.id;
      await clickAndWait(a, () => {
        const e = byId(id);
        return e && (e.getAttribute('aria-expanded') === 'true' || /\bcollapse section\b/i.test(label(e)));
      }, 'expand course');
    }
    throw Error('Expansion limit reached.');
  }
  function courseHeading(a) {
    const clean = value => (value || '').replace(/Collapsible section/gi, '')
      .replace(/^(?:collapse|expand) section\s+/i, '').trim();
    for (const value of [a.innerText, a.getAttribute('aria-label'), a.title, a.textContent]) {
      const heading = clean(value);
      if (/^[A-Z]{2,8}\s+\d{3}/.test(heading)) return heading;
    }
    throw Error('Could not read course heading: ' + a.id);
  }
  function harvest(subject) {
    for (const a of groups(doc())) {
      const n = a.id.split('$').pop();
      const box = byId('win0divSSR_CLSRSLT_WRK_GROUPBOX2$' + n) || byId('ACE_SSR_CLSRSLT_WRK_GROUPBOX2$' + n);
      if (!box) throw Error('Course container not found.');
      const heading = courseHeading(a);
      if (!new RegExp('^' + subject + '\\s+\\d').test(heading)) throw Error('Unexpected subject in results: ' + heading);
      const text = box.innerText.trim();
      const key = subject + '\n' + text;
      if (courseKeys.has(key)) continue;
      courseKeys.add(key);
      const statuses = Array.from(box.querySelectorAll('img[alt]'), i => i.alt).filter(s => /open|closed|wait/i.test(s));
      // Preserve complete course text and table rows; repeated meeting rows are intentional.
      const rows = Array.from(box.querySelectorAll('tr')).filter(tr => !tr.querySelector('table'))
        .map(tr => Array.from(tr.cells, td => {
          const icons = Array.from(td.querySelectorAll('img[alt]'), i => i.alt).filter(Boolean);
          return [td.innerText.trim(), ...icons].filter(Boolean).join(' | ');
        })).filter(r => r.some(Boolean));
      output.courses.push({subject, heading, text, statuses, rows});
    }
  }
  function pagers() {
    // Only results-grid controls, never general navigation or registration buttons.
    return Array.from(doc().querySelectorAll('a,button,input[type="button"]')).filter(e =>
      visible(e) && /SSR_CLSRSLT|SSR_CLSRCH_MTG/.test(e.id) &&
      !/SELECT|ENRL|CART/i.test(e.id) &&
      /\b(?:next|view all)\b/i.test(label(e)));
  }
  function enabled(e) {
    return !e.disabled && e.getAttribute('aria-disabled') !== 'true' &&
      !/disabled/i.test(e.className) && (e.tagName !== 'A' || e.hasAttribute('href') || e.hasAttribute('onclick'));
  }
  try {
    for (const subject of CONFIG.subjects) {
      check();
      const report = {subject, status:'running', snapshots:0};
      output.searches.push(report);
      console.log('[UNR exporter] Searching ' + subject + ' (' + (CONFIG.subjects.indexOf(subject)+1) + '/' + CONFIG.subjects.length + ')');
      emptySearch = false;
      await prepare(subject);
      await clickAndWait(byId('CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH'),
        () => groups(doc() || document).length > 0 || noResults() || capped(), 'search ' + subject);
      if (noResults() && !groups(doc() || document).length) { report.status = 'no_results'; continue; }
      if (!groups(doc()).length) throw Error('No course groups loaded. ' + capMessage());
      const visited = new Set();
      for (let step = 0; ; step++) {
        if (step >= CONFIG.maxPageActions) throw Error('Pagination action limit reached.');
        await expand();
        harvest(subject); report.snapshots++;
        if (capped()) throw Error('Result limit for ' + subject + ': ' + capMessage());
        const signature = resultSignature();
        if (visited.has(signature)) throw Error('Repeated results page detected for ' + subject);
        visited.add(signature);
        const candidates = pagers().filter(enabled);
        const next = candidates.find(e => /view all/i.test(label(e))) || candidates[0];
        if (!next) {
          const unknown = Array.from(doc().querySelectorAll('a,button,input[type="button"]')).filter(e =>
            visible(e) && enabled(e) && /\bnext\b|\bview all\b/i.test(label(e)));
          if (unknown.length) throw Error('Unrecognized pagination control. Stopping rather than skipping pages.');
          report.status = 'reached_end_of_recognized_results';
          break;
        }
        await clickAndWait(next, () => resultSignature() !== signature, 'next results page');
      }
      report.courseSnapshots = output.courses.filter(c => c.subject === subject).length;
    }
    output.status = 'finished';
  } catch (e) {
    output.status = 'partial'; output.error = e.message;
    output.diagnostics = documents().map(d => ({
      frame: d.defaultView?.name || 'top',
      courseGroups: groups(d).length,
      visibleSearchForm: visible(d.getElementById('SSR_CLSRCH_WRK_SUBJECT$0')),
      headings: groups(d).map(a => { try { return courseHeading(a); } catch (_) { return a.id; } })
    }));
    const active = output.searches.find(r => r.status === 'running');
    if (active) { active.status = 'incomplete'; active.reason = e.message; }
    console.error('[UNR exporter]', e.message);
  } finally {
    output.finished = new Date().toISOString();
    window.UNRexport.running = false;
    refreshMatches();
    console.table(output.searches);
    console.table(output.summary);
    console.table(output.results.matched.map(s => ({course:s.heading,classNumber:s.classNumber,section:s.section,meetings:s.meetingRows.map(m=>m.daysTimes).join('; ')})));
    if (output.results.needsReview.length) console.warn('[UNR exporter] Some sections need schedule/status review. See Needs review rows, or run UNRexport.downloadJSON() for the full audit.');
    download();
    console.log('[UNR exporter] Downloaded ' + output.status + ' export. If blocked, run UNRexport.download().');
  }
})();


'''

if __name__ == '__main__': main()
