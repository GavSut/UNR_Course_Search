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

