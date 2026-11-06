const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const C=require('../docs/assets/core.js');
const ctx=vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(root,'src/matching.js'),'utf8')+'\n'+fs.readFileSync(path.join(root,'src/exports.js'),'utf8'),ctx);
const build=(courses,config)=>ctx.buildMatches(courses,config);
const cfg=(extra={})=>C.validateSettings({subjects:['TEST'],...extra});
const row=(time,number='12345',status='Open',name='A Teacher')=>[number,'1001-LEC',time,'Room 101',name,'01/19/2027 - 05/04/2027',status];
const course=(rows,heading='TEST 201 - Example course')=>[{subject:'TEST',heading,rows}];
const output=(results,status='finished')=>({results,status,term:'2027 Spring',started:'2026-11-05T00:00:00Z',finished:'2026-11-05T00:01:00Z',subjectsRequested:['TEST'],searches:status==='finished'?[{subject:'TEST',status:'reached_end_of_recognized_results'}]:[]});

test('student-neutral defaults and syntax for all formats',()=>{
  assert.equal(C.DEFAULTS.minimumCourseNumber,'');assert.equal(C.DEFAULTS.useCurrentTerm,true);
  assert.equal(C.DEFAULTS.outputFormat,'csv');assert.equal(C.DEFAULTS.subjects.length,0);
  assert.throws(()=>C.generate({}),/subject/i);
  for(const f of ['csv','json','tsv']) {
    const code=C.generate({subjects:['ENG'],outputFormat:f});new vm.Script(code);
    assert(!code.includes('__CONFIG_JSON__'));assert(!code.includes('__MATCHING_JS__'));
  }
});
test('untrusted settings remain string values, not executable code',()=>{
  const keyword='$& $` $\' ";globalThis.pwned=true;//';
  const code=C.generate({subjects:['ENG'],keywords:keyword});
  new vm.Script(code);
  const config=JSON.parse(code.split('const CONFIG = ')[1].split(';\n  let resolvedTerm')[0]);
  assert.equal(config.keywords[0],keyword);
});
test('every meeting must fit, including continuation rows and mixed TBA',()=>{
  const c=cfg({filterSchedule:true,days:['Mo','We'],start:'09:00',end:'17:00'});
  assert.equal(build(course([row('Mo 9:00AM - 10:00AM')]),c).matched.length,1);
  assert.equal(build(course([row('Mo 9:00AM - 10:00AM'),row('Fr 9:00AM - 10:00AM')]),c).excluded.length,1);
  assert.equal(build(course([row('Mo 9:00AM - 10:00AM'),row('TBA')]),c).needsReview.length,1);
  assert.equal(build(course([row('Mo 9:00AM - 10:00AM'),row('We 6:00PM - 7:00PM','')]),c).excluded.length,1);
  assert.equal(build(course([row('Mo 9:00AM - 10:00AM\nWe 4:00PM - 5:00PM')]),c).matched.length,1);
});
test('TBA, noon, midnight and unrecognized text are handled conservatively',()=>{
  assert.equal(ctx.parseMeeting('Mo 12:00AM - 1:00AM').meetings[0].start,0);
  assert.equal(ctx.parseMeeting('Mo 12:00PM - 1:00PM').meetings[0].start,720);
  for(const t of ['TBA','Mo 13:00PM - 2:00PM','Mo 11:00PM - 1:00AM','Mo 1:00PM - 2:00PM\nTBA'])assert.equal(ctx.parseMeeting(t).known,false);
  const s=build(course([row('TBA')]),cfg()).matched[0];assert.equal(s.scheduleVerified,false);
});
test('deduplication, keyword OR, course bounds and status',()=>{
  const rows=[row('Mo 9:00AM - 10:00AM'),row('Mo 9:00AM - 10:00AM')];
  assert.equal(build(course(rows),cfg()).matched[0].meetingRows.length,1);
  assert.equal(build(course(rows),cfg({keywords:'music, example'})).matched.length,1);
  assert.equal(build(course(rows),cfg({minimumCourseNumber:'300'})).excluded.length,1);
  assert.equal(build(course(rows),cfg({maximumCourseNumber:'200'})).excluded.length,1);
  assert.equal(build(course(rows),cfg({component:'LAB'})).excluded.length,1);
  assert.equal(build(course([row('TBA','12345','Closed')]),cfg({status:'Open'})).excluded.length,1);
  assert.equal(build(course([row('TBA','12345','Unrecognized')]),cfg({status:'Open'})).needsReview.length,1);
});
test('readable export has summary, normalized columns and one row per meeting',()=>{
  const c=cfg(),result=build(course([row('Mo 9:00AM - 10:00AM\nWe 4:00PM - 5:00PM')]),c);
  const table=ctx.exportTable(output(result),c),columns=table[0];
  assert.equal(table.length,4);assert.equal(table[1][0],'Search summary');
  assert.equal(table[2][columns.indexOf('Days')],'Monday');
  assert.equal(table[3][columns.indexOf('Start time')],'16:00');
  assert.equal(table[2][columns.indexOf('First meeting date')],'2027-01-19');
  assert.equal(table[2][columns.indexOf('Course number')],'201');
});
test('empty partial exports explicitly describe failure and unfinished subjects',()=>{
  const o=output(build([],cfg()),'partial');o.error='Timed out';
  const table=ctx.exportTable(o,cfg()),header=table[0];
  assert.equal(table.length,2);
  assert.match(table[1][header.indexOf('Search completeness')],/PARTIAL/);
  assert.match(table[1][header.indexOf('Search notes')],/Unfinished: TEST.*Timed out/);
});
test('review toggle changes table rows but preserves JSON results',()=>{
  const c=cfg({filterSchedule:true}),r=build(course([row('TBA')]),c);
  assert.equal(ctx.exportTable(output(r),c).length,3);
  assert.equal(ctx.exportTable(output(r),{...c,includeReview:false}).length,2);
  assert.equal(r.needsReview.length,1);
});
test('CSV and TSV quote multiline values and neutralize formula cells',()=>{
  const csv=ctx.serializeTable([['Header','Notes'],['  =SUM(1,2)','two\n"lines", here']]);
  assert(csv.startsWith('\uFEFF'));assert(csv.includes('"\'  =SUM(1,2)"'));
  assert(csv.includes('"two\n""lines"", here"'));
  const tsv=ctx.serializeTable([['A','B'],['1','2']],'\t');assert(tsv.includes('"A"\t"B"'));
});
