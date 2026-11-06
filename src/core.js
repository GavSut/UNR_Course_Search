(function(root) {
  'use strict';
  const SUBJECTS = __SUBJECTS_JSON__;
  const DAYS = ['Mo','Tu','We','Th','Fr','Sa','Su'];
  const DEFAULTS = {
    useCurrentTerm:true, year:String(new Date().getFullYear()), season:'Spring',termOverride:'',
    subjects:[],customSubjects:'',minimumCourseNumber:'',maximumCourseNumber:'',keywords:'',
    instructor:'',component:'',status:'Any',filterSchedule:false,days:DAYS,
    start:'08:00',end:'18:00',outputFormat:'csv',includeReview:true
  };
  const TEMPLATE = __TEMPLATE_JSON__;
  function parseTime(value) {
    const m=String(value).trim().match(/^(\d{1,2}):(\d{2})$/);
    if(!m || +m[1]>23 || +m[2]>59) throw Error('Enter time as HH:MM in 24-hour format, such as 08:00 or 16:30.');
    return +m[1]*60 + +m[2];
  }
  function validateSettings(raw) {
    if(!raw || typeof raw!=='object' || Array.isArray(raw)) throw Error('Expected a saved settings object.');
    const unknown=Object.keys(raw).filter(k=>!Object.prototype.hasOwnProperty.call(DEFAULTS,k));
    if(unknown.length) throw Error('This is not a builder settings file. Import saved settings, not course results.');
    const s={...DEFAULTS,...raw};
    for(const k of ['useCurrentTerm','filterSchedule','includeReview']) if(typeof s[k]!=='boolean') throw Error('Invalid checkbox setting: '+k);
    if(!/^20\d{2}$/.test(String(s.year).trim())) throw Error('Enter a four-digit year from 2000 to 2099.');
    if(!['Spring','Summer','Fall','Winter'].includes(s.season)) throw Error('Choose a valid term.');
    const termName=s.useCurrentTerm ? '' : String(s.termOverride).trim() || `${s.year} ${s.season}`;
    if(termName.length>100) throw Error('The term label is too long.');
    if(!Array.isArray(s.subjects) || s.subjects.some(x=>typeof x!=='string')) throw Error('Subjects must be a list of codes.');
    const subjects=[...new Set([...s.subjects,...String(s.customSubjects).toUpperCase().split(/[,\s]+/)].map(s=>s.trim().toUpperCase()).filter(Boolean))];
    if(!subjects.length || subjects.some(s=>!/^[A-Z]{2,8}$/.test(s))) throw Error('Select at least one subject, or enter a code of 2–8 letters.');
    const minimum=String(s.minimumCourseNumber).trim(),maximum=String(s.maximumCourseNumber).trim();
    if([minimum,maximum].some(v=>v&&!/^\d{1,4}$/.test(v))) throw Error('Course limits must be whole numbers or blank.');
    if(minimum && maximum && +minimum>+maximum) throw Error('Minimum course number cannot exceed maximum.');
    if(!Array.isArray(s.days) || s.days.some(d=>!DAYS.includes(d))) throw Error('Invalid meeting days.');
    const start=parseTime(s.start),end=parseTime(s.end);
    if(s.filterSchedule && (start>=end || !s.days.length)) throw Error('Choose at least one day and an end time later than the start.');
    const component=String(s.component).trim().toUpperCase();
    if(component && !/^[A-Z]{2,5}$/.test(component)) throw Error('Use a component code such as LEC, LAB, DIS, or SEM.');
    if(!['Any','Open','Closed','Waitlist'].includes(s.status)) throw Error('Invalid class status.');
    if(!['csv','json','tsv'].includes(s.outputFormat)) throw Error('Choose CSV, JSON, or TSV.');
    return {useCurrentTerm:s.useCurrentTerm,termName,subjects,minimumCourseNumber:minimum,maximumCourseNumber:maximum,
      keywords:String(s.keywords).split(',').map(s=>s.trim()).filter(Boolean),instructor:String(s.instructor).trim(),component,
      status:s.status,filterSchedule:s.filterSchedule,days:[...new Set(s.days)],startMinutes:start,endMinutes:end,
      outputFormat:s.outputFormat,includeReview:s.includeReview,timeoutMs:45000,maxPageActions:250};
  }
  function generate(raw) { return TEMPLATE.replace('__CONFIG_JSON__',()=>JSON.stringify(validateSettings(raw),null,2)); }
  const api={SUBJECTS,DAYS,DEFAULTS,parseTime,validateSettings,generate};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  else root.CourseSearch=api;
})(typeof globalThis!=='undefined' ? globalThis : this);
