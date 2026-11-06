// Pure scheduling logic, shared by the browser UI and Node tests.
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ScheduleEngine=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
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


const DAYS=['Mo','Tu','We','Th','Fr','Sa','Su'];
const NAMES=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
const text=v=>String(v??'').trim();
const unique=a=>[...new Set(a)];
const clock=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
function time(s){const m=text(s).match(/^(\d{1,2}):(\d{2})\s*([AP]M)?$/i);if(!m||+m[2]>59)return null;let h=+m[1];if(m[3]){if(h<1||h>12)return null;h=h%12+(/PM/i.test(m[3])?12:0);}else if(h>23)return null;return h*60+(+m[2]);}
function date(s){s=text(s);const m=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);if(m)s=`${m[3]}-${m[1].padStart(2,'0')}-${m[2].padStart(2,'0')}`;if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return '';const d=new Date(s+'T00:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===s?s:'';}
function addDays(s,n){const d=new Date(s+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10);}
function weekday(s){return (new Date(s+'T00:00:00Z').getUTCDay()+6)%7;}
function monday(s){return addDays(s,-weekday(s));}
function parseDays(s){if(Array.isArray(s))return unique(s.filter(d=>DAYS.includes(d)));s=text(s);if(!s)return [];let rest=s.toLowerCase();const out=[];for(let i=0;i<7;i++){const re=new RegExp(NAMES[i].toLowerCase()+'|'+NAMES[i].slice(0,3).toLowerCase(),'g');if(re.test(rest)){out.push(DAYS[i]);rest=rest.replace(re,'');}}rest=rest.replace(/[\s,;/|]+/g,'');if(rest){const tokens=rest.match(/mo|tu|we|th|fr|sa|su/g)||[];if(tokens.join('')!==rest)return [];out.push(...tokens.map(d=>DAYS.find(x=>x.toLowerCase()===d)));}return unique(out).sort((a,b)=>DAYS.indexOf(a)-DAYS.indexOf(b));}
function splitDates(s){const a=text(s).split(/\s+[-–—]\s+/);return [date(a[0]),date(a[1])];}
function validMeeting(m){return m.days.length>0&&Number.isFinite(m.start)&&Number.isFinite(m.end)&&m.start>=0&&m.end<=1440&&m.end>m.start;}
function normalizeMeeting(raw){const days=parseDays(raw.days),start=typeof raw.start==='number'?raw.start:time(raw.start),end=typeof raw.end==='number'?raw.end:time(raw.end);const m={days,start,end,startDate:date(raw.startDate),endDate:date(raw.endDate),room:text(raw.room),instructor:text(raw.instructor),raw:text(raw.raw)};m.known=validMeeting(m)&&raw.known!==false;return m;}
function rawMeetings(r){const p=parseMeeting(r.daysTimes),[startDate,endDate]=splitDates(r.dates);const common={startDate,endDate,room:text(r.room),instructor:text(r.instructor),raw:text(r.daysTimes)};const good=p.meetings.filter(validMeeting).map(m=>({...common,...m,known:true}));if(!p.known)good.push({...common,days:[],start:null,end:null,known:false});return good;}
function normalizedSection(s){const term=text(s.term)||'Unspecified term',subject=text(s.subject).toUpperCase(),number=text(s.number);if(!/^[A-Z][A-Z0-9&]{1,11}$/.test(subject)||!/^\d{1,4}[A-Z]?$/i.test(number))throw Error('A section has an invalid subject or course number.');const classNumber=text(s.classNumber),section=text(s.section);if(!classNumber&&!section)throw Error('A section is missing its class number and section identifier.');const courseKey=`${term}|${subject}|${number}`;return {id:`${courseKey}|${classNumber||section}`,courseKey,term,subject,number,title:text(s.title)||`${subject} ${number}`,classNumber,section,component:text(s.component).toUpperCase()||((section.match(/-([A-Z]+)/)||[])[1]||'OTHER'),status:/^wait\s*list(?:ed)?$/i.test(text(s.status))?'Waitlist':/^open$/i.test(text(s.status))?'Open':/^closed$/i.test(text(s.status))?'Closed':text(s.status)||'Unknown',meetings:(Array.isArray(s.meetings)?s.meetings:[]).map(normalizeMeeting),notes:(Array.isArray(s.notes)?s.notes:[s.notes]).map(text).filter(Boolean),source:text(s.source),captured:text(s.captured)};}
function mergeSections(list){const map=new Map();for(const raw of list){const s=normalizedSection(raw);if(!map.has(s.id))map.set(s.id,s);else{const old=map.get(s.id);old.meetings.push(...s.meetings);old.notes=unique([...old.notes,...s.notes]);}}for(const s of map.values())s.meetings=[...new Map(s.meetings.map(m=>[JSON.stringify(m),m])).values()];return [...map.values()];}
function parseDelimited(input,delimiter){const rows=[];let row=[],cell='',quoted=false;input=input.replace(/^\uFEFF/,'');for(let i=0;i<input.length;i++){const c=input[i];if(c==='"'){if(quoted&&input[i+1]==='"'){cell+='"';i++;}else if(quoted)quoted=false;else if(cell==='')quoted=true;else cell+=c;}else if(c===delimiter&&!quoted){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&input[i+1]==='\n')i++;row.push(cell);if(row.some(v=>v.trim()))rows.push(row);row=[];cell='';}else cell+=c;}if(quoted)throw Error('This file has an unfinished quoted field. Re-export the CSV or TSV.');row.push(cell);if(row.some(v=>v.trim()))rows.push(row);return rows;}
function importData(input,filename='results.json'){
 const info={name:filename,term:'',captured:'',notes:[],partial:false,skipped:0};let sections=[];
 if(/\.json$/i.test(filename)||/^\s*[\[{]/.test(input)){
  let data;try{data=JSON.parse(input);}catch{throw Error('This is not valid JSON. Upload the downloaded results file.');}
  if(data?.format==='course-studio-schedules-v1')return {backup:validateState(data.state)};
  if(!data||!Array.isArray(data.courses))throw Error('Choose a Course Search Studio results JSON, CSV, or TSV—not search settings.');
  info.term=text(data.term)||'Unspecified term';info.captured=text(data.finished||data.started);info.partial=data.status==='partial'||(data.searches||[]).some(s=>s.status==='incomplete');
  if(data.error)info.notes.push(text(data.error));
  const unfinished=(data.searches||[]).filter(s=>!['no_results','reached_end_of_recognized_results'].includes(s.status)).map(s=>s.subject);if(unfinished.length)info.notes.push('Unfinished subjects: '+unfinished.join(', '));
  const results=buildMatches(data.courses,{keywords:[],instructor:'',component:'',status:'Any',filterSchedule:false});info.skipped=results.unparsedRows.length;
  for(const s of results.matched){const h=s.heading.match(/^[A-Z0-9&]+\s+(\d+[A-Z]?)\s*[-–—:]\s*(.*)$/i);if(!h){info.skipped++;continue;}sections.push({term:info.term,subject:s.subject,number:h[1],title:h[2],classNumber:s.classNumber,section:s.section,component:s.component,status:s.status,meetings:s.meetingRows.flatMap(rawMeetings),notes:s.notes,source:filename,captured:info.captured});}
  info.notes.push('JSON includes all collected sections, including those excluded by your original search filters.');
 }else{
  const rows=parseDelimited(input,/\.tsv$/i.test(filename)?'\t':','),header=(rows.shift()||[]).map(v=>v.trim());
  for(const h of ['Subject','Course number','Course title','Class number','Section'])if(!header.includes(h))throw Error(`Missing “${h}” column. Use a CSV or TSV downloaded by Course Search Studio.`);
  for(const r of rows){const x=Object.fromEntries(header.map((h,i)=>[h,r[i]||'']));if(x['Record type']&&x['Record type']!=='Section'){if(x['Record type']==='Search summary'){info.notes.push(x['Search notes']);info.partial ||= /partial|incomplete/i.test(x['Search completeness']);}continue;}
   if(!x.Subject||!x['Course number']){info.skipped++;continue;}
   const raw=x['Meeting time as listed'],common={startDate:x['First meeting date'],endDate:x['Last meeting date'],room:x.Room,instructor:x.Instructor,raw};
   let meetings;if(x.Days&&x['Start time']&&x['End time'])meetings=[normalizeMeeting({...common,days:parseDays(x.Days),start:time(x['Start time']),end:time(x['End time'])})];else meetings=rawMeetings({daysTimes:raw,dates:[x['First meeting date'],x['Last meeting date']].join(' - '),room:x.Room,instructor:x.Instructor});
   sections.push({term:x.Term,subject:x.Subject,number:x['Course number'],title:x['Course title'],classNumber:x['Class number'],section:x.Section,component:x.Component,status:x['Class status'],meetings,notes:[x.Notes],source:filename,captured:x['Collected at']});info.partial ||= /partial|incomplete/i.test(x['Search completeness']);info.captured ||= x['Collected at'];info.term ||= x.Term;
  }
  info.notes.push('CSV/TSV contains only sections included in that export; omitted sections cannot be recovered here.');
 }
 sections=mergeSections(sections);info.notes=unique(info.notes.filter(Boolean));if(!sections.length)throw Error('No usable sections were found. Your current schedules have not changed.');return {sections,info};
}
function effectiveDates(m,plan={}){return [date(m.startDate)||date(plan.startDate),date(m.endDate)||date(plan.endDate)];}
function sharedDates(a,b,day,plan){const [as,ae]=effectiveDates(a,plan),[bs,be]=effectiveDates(b,plan);if(!as||!ae||!bs||!be||as>ae||bs>be)return {overlap:true,unknown:true};const start=as>bs?as:bs,end=ae<be?ae:be;if(start>end)return {overlap:false,unknown:false};const first=addDays(start,(DAYS.indexOf(day)-weekday(start)+7)%7);return {overlap:first<=end,unknown:false};}
function collision(a,b,buffer=0,plan={}){if(!validMeeting(a)||!validMeeting(b))return null;const actual=a.start<b.end&&b.start<a.end;if(!actual&&!(a.start<b.end+buffer&&b.start<a.end+buffer))return null;const dates=a.days.filter(d=>b.days.includes(d)).map(day=>({day,...sharedDates(a,b,day,plan)})).filter(x=>x.overlap);return dates.length?{days:dates.map(x=>x.day),bufferOnly:!actual,dateUnknown:dates.some(x=>x.unknown)}:null;}
function eventsFor(sections,plan){return [...sections.filter(s=>plan.selected.includes(s.id)).flatMap(s=>s.meetings.map(m=>({...m,owner:s.id,courseKey:s.courseKey,label:`${s.subject} ${s.number}`,title:s.title,component:s.component,classNumber:s.classNumber,kind:'course'}))),...(plan.blocks||[]).map(b=>({...b,owner:b.id,courseKey:b.id,title:b.label,kind:'block'}))];}
function analyze(sections,plan){const events=eventsFor(sections,plan),conflicts=[],seen=new Set();for(let i=0;i<events.length;i++)for(let j=i+1;j<events.length;j++){const a=events[i],b=events[j];if(a.owner===b.owner)continue;const c=collision(a,b,plan.buffer||0,plan);if(c){const key=[a.owner,b.owner].sort().join('|')+'|'+c.days.join(',')+'|'+c.bufferOnly;if(!seen.has(key)){seen.add(key);conflicts.push({a:a.owner,b:b.owner,aLabel:a.label,bLabel:b.label,...c});}}}
 const chosen=sections.filter(s=>plan.selected.includes(s.id)),courses=unique(chosen.map(s=>s.courseKey));
 const unknown=chosen.filter(s=>!s.meetings.length||s.meetings.some(m=>!m.known)).map(s=>s.id);
 const missingDates=unique(events.filter(m=>{const [a,b]=effectiveDates(m,plan);return !a||!b||a>b;}).map(m=>m.owner));
 let credits=0,level700=0,unknownCredits=0;
 const components=[];for(const key of courses){const ss=chosen.filter(s=>s.courseKey===key),meta=plan.courseMeta?.[key]||{},v=meta.credits;if(typeof v==='number'&&Number.isFinite(v)){credits+=v;if(parseInt(ss[0].number)>=700&&parseInt(ss[0].number)<800)level700+=v;}else unknownCredits++;
  const available=unique(sections.filter(s=>s.courseKey===key).map(s=>s.component)),selected=unique(ss.map(s=>s.component));
  if(available.length>1&&!meta.componentsVerified)components.push({courseKey:key,label:`${ss[0].subject} ${ss[0].number}`,missing:available.filter(c=>!selected.includes(c))});
 }
 return {events,conflicts,unknown,missingDates,credits,level700,unknownCredits,components,courses: courses.length,sections:chosen.length};}
function candidateConflicts(s,sections,plan){const selected=sections.filter(x=>plan.selected.includes(x.id)&&!(x.courseKey===s.courseKey&&x.component===s.component));const others=eventsFor(selected,{...plan,selected:selected.map(x=>x.id)});return s.meetings.some(a=>others.some(b=>collision(a,b,plan.buffer||0,plan)));}
function filterSections(sections,filters,plan,favorites=[]){const q=text(filters.q).toLowerCase().split(/\s+/).filter(Boolean);return sections.filter(s=>{
 if(s.term!==plan.term)return false;
 const hay=[s.subject,s.number,s.title,s.classNumber,s.section,...s.meetings.map(m=>m.instructor)].join(' ').toLowerCase();if(!q.every(x=>hay.includes(x)))return false;
 if(filters.subject&&s.subject!==filters.subject)return false;
 if(filters.min!==''&&filters.min!=null&&parseInt(s.number)<+filters.min)return false;if(filters.max!==''&&filters.max!=null&&parseInt(s.number)>+filters.max)return false;
 if(filters.instructor&&!s.meetings.some(m=>m.instructor.toLowerCase().includes(filters.instructor.toLowerCase())))return false;
 if(filters.status&&s.status.toLowerCase()!==filters.status.toLowerCase())return false;if(filters.component&&s.component!==filters.component)return false;
 if(filters.starred&&!favorites.includes(s.courseKey))return false;
 if(filters.hideResearch&&/dissertation|thesis|independent study|individual study|comprehensive exam|graduate advisement|special problems|research rotation/i.test(s.title))return false;
 if(filters.known&&(!s.meetings.length||s.meetings.some(m=>!m.known)))return false;
 if(filters.availability){if(!s.meetings.length||s.meetings.some(m=>!m.known||m.days.some(d=>!filters.days.includes(d))||m.start<filters.start||m.end>filters.end))return false;}
 if(filters.noConflicts&&candidateConflicts(s,sections,plan))return false;return true;
 });}
function weekEvents(events,week,plan){return events.flatMap(m=>{if(!m.known)return [];const [start,end]=effectiveDates(m,plan);return m.days.flatMap(day=>{const on=addDays(week,DAYS.indexOf(day));if(start&&on<start||end&&on>end)return [];return [{...m,day,on}];});});}
function layoutDay(events){const sorted=events.map(x=>({...x})).sort((a,b)=>a.start-b.start||a.end-b.end);let group=[],end=-1;function finish(){const used=[];for(const e of group){let col=used.findIndex(t=>t<=e.start);if(col<0)col=used.length;used[col]=e.end;e.column=col;}for(const e of group)e.columns=used.length;group=[];}
 for(const e of sorted){if(e.start>=end&&group.length)finish();group.push(e);end=Math.max(group.length===1?-1:end,e.end);}if(group.length)finish();return sorted;}
function csv(rows){const cell=x=>{let s=text(x);if(/^[=+@-]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};return '\uFEFF'+rows.map(r=>r.map(cell).join(',')).join('\r\n');}
function exportCSV(sections,plan){const rows=[['Plan','Term','Course','Title','Class number','Section','Component','Status snapshot','Days','Start','End','First date','Last date','Room','Instructor','Course credits (count once per course)','Notes']];for(const s of sections.filter(s=>plan.selected.includes(s.id)))for(const m of s.meetings.length?s.meetings:[{}])rows.push([plan.name,plan.term,`${s.subject} ${s.number}`,s.title,s.classNumber,s.section,s.component,s.status,(m.days||[]).join(' '),m.known?clock(m.start):'TBA',m.known?clock(m.end):'',...effectiveDates(m,plan),m.room,m.instructor,plan.courseMeta?.[s.courseKey]?.credits??'',plan.courseMeta?.[s.courseKey]?.notes||'']);for(const b of plan.blocks)rows.push([plan.name,plan.term,'Personal block',b.label,'','','','',''+b.days.join(' '),clock(b.start),clock(b.end),...effectiveDates(b,plan),'','','','']);return csv(rows);}
function ics(sections,plan){const out=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Course Search Studio//Schedule Builder//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:'+escapeICS(plan.name),'X-WR-TIMEZONE:America/Los_Angeles',
 'BEGIN:VTIMEZONE','TZID:America/Los_Angeles','BEGIN:DAYLIGHT','DTSTART:19700308T020000','RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU','TZOFFSETFROM:-0800','TZOFFSETTO:-0700','TZNAME:PDT','END:DAYLIGHT','BEGIN:STANDARD','DTSTART:19701101T020000','RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU','TZOFFSETFROM:-0700','TZOFFSETTO:-0800','TZNAME:PST','END:STANDARD','END:VTIMEZONE'];let count=0,skipped=0;const stamp=new Date().toISOString().replace(/[-:]/g,'').split('.')[0]+'Z';
 for(const m of eventsFor(sections,plan)){let [start,end]=effectiveDates(m,plan);if(!m.known||!start||!end||start>end){skipped++;continue;}for(const day of m.days){const first=addDays(start,(DAYS.indexOf(day)-weekday(start)+7)%7);if(first>end)continue;const occurrences=Math.floor((+new Date(end+'T00:00:00Z')-+new Date(first+'T00:00:00Z'))/604800000)+1;const dt=(d,t)=>d.replace(/-/g,'')+'T'+clock(t).replace(':','')+'00';out.push('BEGIN:VEVENT',`UID:${encodeURIComponent(plan.id+'-'+m.owner+'-'+count+'-'+day)}@course-studio.local`,'DTSTAMP:'+stamp,'DTSTART;TZID=America/Los_Angeles:'+dt(first,m.start),'DTEND;TZID=America/Los_Angeles:'+dt(first,m.end),`RRULE:FREQ=WEEKLY;COUNT=${occurrences};BYDAY=${day.toUpperCase()}`,'SUMMARY:'+escapeICS(m.label+' '+(m.component||'')+' — '+m.title),'LOCATION:'+escapeICS(m.room||''),'DESCRIPTION:'+escapeICS([m.instructor,m.classNumber?'Class '+m.classNumber:'','Planning copy; verify enrollment and holidays.'].filter(Boolean).join('\n')),'END:VEVENT');count++;}}
 out.push('END:VCALENDAR');return {text:out.map(foldICS).join('\r\n')+'\r\n',count,skipped};}
function escapeICS(s){return text(s).replace(/\\/g,'\\\\').replace(/\r?\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');}
function foldICS(s){let result='',line='',bytes=0;for(const c of s){const n=new TextEncoder().encode(c).length;if(bytes+n>73){result+=line+'\r\n';line=' ';bytes=1;}line+=c;bytes+=n;}return result+line;}
// Enumerate time-compatible proposals, never assert registration component compatibility.
function combinations(sections,plan,courseKeys,options={}){
 const keys=unique(courseKeys),groups=[],empty=[];if(!keys.length||keys.length>8)throw Error('Choose between one and eight starred courses.');
 const candidates=sections.filter(s=>s.term===plan.term);
 for(const key of keys){const all=candidates.filter(s=>s.courseKey===key);if(!all.length){empty.push(key);continue;}
  for(const component of unique(all.map(s=>s.component))){const pool=all.filter(s=>s.component===component&&(!options.openOnly||/^open$/i.test(s.status))&&s.meetings.length&&s.meetings.every(m=>m.known&&effectiveDates(m,plan).every(Boolean)&&effectiveDates(m,plan)[0]<=effectiveDates(m,plan)[1]));if(!pool.length)empty.push(all[0].subject+' '+all[0].number+' '+component);else groups.push(pool);}
 }
 if(empty.length)return {results:[],empty,visited:0,truncated:false};
 groups.sort((a,b)=>a.length-b.length);const results=[],maxResults=12,maxNodes=50000;let visited=0,truncated=false;
 function search(index,selected,events){if(visited>=maxNodes||results.length>=maxResults){truncated=true;return;}if(index===groups.length){results.push(selected);return;}
  for(const s of groups[index]){if(visited>=maxNodes||results.length>=maxResults){truncated=true;break;}visited++;if(s.meetings.some(a=>events.some(b=>collision(a,b,plan.buffer||0,plan))))continue;search(index+1,[...selected,s.id],[...events,...s.meetings]);}
 }
 search(0,[],(plan.blocks||[]));return {results,empty,visited,truncated};
}
function newPlan(term,name='Schedule A'){return {id:'p-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8),name,term,selected:[],blocks:[],courseMeta:{},buffer:0,startDate:'',endDate:''};}
function validateState(raw){if(!raw||!Array.isArray(raw.sections)||!Array.isArray(raw.plans)||raw.sections.length>30000||raw.plans.length>60)throw Error('Invalid schedule backup.');const sections=mergeSections(raw.sections),ids=new Set(sections.map(s=>s.id)),plans=raw.plans.map((p,i)=>{const n=newPlan(text(p.term),text(p.name)||`Schedule ${i+1}`);n.id=text(p.id)||n.id;n.selected=unique((Array.isArray(p.selected)?p.selected:[]).filter(id=>ids.has(id)&&sections.find(s=>s.id===id)?.term===n.term));n.startDate=date(p.startDate);n.endDate=date(p.endDate);n.buffer=Math.max(0,Math.min(60,+p.buffer||0));n.blocks=(Array.isArray(p.blocks)?p.blocks:[]).slice(0,200).map((b,j)=>({...normalizeMeeting(b),id:text(b.id)||'b-'+j,label:text(b.label)||'Personal block',known:true})).filter(validMeeting);for(const [key,v] of Object.entries(p.courseMeta||{})){if(sections.some(s=>s.courseKey===key))n.courseMeta[key]={credits:typeof v?.credits==='number'&&v.credits>=0&&v.credits<=99?v.credits:null,notes:text(v?.notes),componentsVerified:v?.componentsVerified===true};}return n;});if(new Set(plans.map(p=>p.id)).size!==plans.length)throw Error('Duplicate schedule IDs in backup.');return {sections,plans,active:plans.some(p=>p.id===raw.active)?raw.active:plans[0]?.id||'',favorites:unique((Array.isArray(raw.favorites)?raw.favorites:[]).filter(k=>sections.some(s=>s.courseKey===k))),imports:(Array.isArray(raw.imports)?raw.imports:[]).slice(-30).map(x=>({name:text(x.name),partial:!!x.partial,captured:text(x.captured),notes:(Array.isArray(x.notes)?x.notes:[]).map(text),skipped:+x.skipped||0})),version:1};}
return {DAYS,NAMES,text,unique,clock,time,date,addDays,weekday,monday,parseDays,normalizeMeeting,mergeSections,importData,parseDelimited,effectiveDates,collision,analyze,candidateConflicts,filterSections,eventsFor,weekEvents,layoutDay,exportCSV,ics,combinations,newPlan,validateState};
});
