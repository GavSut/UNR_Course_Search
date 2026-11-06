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

SUBJECTS = __SUBJECTS_JSON__
DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
DEFAULTS = dict(useCurrentTerm=True, year=str(datetime.now().year), season='Spring', termOverride='',
    subjects=[], customSubjects='', minimumCourseNumber='', maximumCourseNumber='',
    keywords='', instructor='', component='', status='Any', filterSchedule=False,
    days=DAYS.copy(), start='08:00', end='18:00', outputFormat='csv', includeReview=True)

INSTRUCTIONS = __INSTRUCTIONS_REPR__

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
JS_TEMPLATE = __TEMPLATE_REPR__

if __name__ == '__main__': main()
