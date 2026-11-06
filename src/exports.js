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
