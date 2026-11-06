(() => {
  'use strict';
  const C=window.CourseSearch;
  const $=id=>document.getElementById(id);
  const selected=new Set();
  const strings=['year','season','termOverride','customSubjects','minimumCourseNumber','maximumCourseNumber','keywords','instructor','component','status','start','end'];
  const flags=['useCurrentTerm','filterSchedule','includeReview'];
  const dayNames=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  C.DAYS.forEach((d,i)=>{
    const label=document.createElement('label'),input=document.createElement('input');
    input.type='checkbox';input.value=d;input.checked=true;input.setAttribute('aria-label',dayNames[i]);
    label.append(input,document.createTextNode(dayNames[i].slice(0,3)));$('days').append(label);
  });
  function activate(name,focus=false) {
    for(const key of ['search','subjects','export']) {
      const tab=$('tab-'+key),active=key===name;
      tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;
      $('panel-'+key).hidden=!active;
      if(active&&focus)tab.focus();
    }
  }
  document.querySelectorAll('[role=tab]').forEach((tab,i,tabs)=>{
    tab.addEventListener('click',()=>activate(tab.id.slice(4)));
    tab.addEventListener('keydown',e=>{
      let target;
      if(e.key==='ArrowRight')target=(i+1)%tabs.length;
      if(e.key==='ArrowLeft')target=(i+tabs.length-1)%tabs.length;
      if(e.key==='Home')target=0;
      if(e.key==='End')target=tabs.length-1;
      if(target!==undefined){e.preventDefault();activate(tabs[target].id.slice(4),true);}
    });
  });
  function settings() {
    const s=Object.fromEntries(strings.map(k=>[k,$(k).value]));
    flags.forEach(k=>s[k]=$(k).checked);
    s.subjects=[...selected];s.days=[...$('days').querySelectorAll('input:checked')].map(e=>e.value);
    s.outputFormat=document.querySelector('[name=outputFormat]:checked').value;
    return s;
  }
  function notify(text,error=false) { $('message').textContent=text;$('message').classList.toggle('error',error); }
  function checkedConfig() {
    try{return C.validateSettings(settings());}
    catch(e){notify(e.message,true);if(!selected.size&&!$('customSubjects').value.trim())activate('subjects');return null;}
  }
  function script() {if(!checkedConfig())return null;return C.generate(settings());}
  function drawSubjects() {
    const q=$('subject-filter').value.trim().toLowerCase();$('subjects').replaceChildren();
    for(const [code,name] of Object.entries(C.SUBJECTS)) {
      if(!(code+' '+name).toLowerCase().includes(q))continue;
      const label=document.createElement('label');label.className='subject-item';
      const input=document.createElement('input');input.type='checkbox';input.value=code;input.checked=selected.has(code);
      input.addEventListener('change',()=>{input.checked?selected.add(code):selected.delete(code);refresh();});
      const text=document.createElement('span'),strong=document.createElement('strong'),small=document.createElement('small');
      strong.textContent=code;small.textContent=name;text.append(strong,small);label.append(input,text);$('subjects').append(label);
    }
    $('no-subjects').hidden=!!$('subjects').children.length;
  }
  function refresh() {
    const s=settings();
    ['year','season','termOverride'].forEach(k=>$(k).disabled=s.useCurrentTerm);
    $('availability-fields').querySelectorAll('input').forEach(e=>e.disabled=!s.filterSchedule);
    $('summary-term').textContent=s.useCurrentTerm?'Selected in MyNEVADA':s.termOverride.trim()||`${s.year} ${s.season}`;
    $('summary-level').textContent=!s.minimumCourseNumber&&!s.maximumCourseNumber?'All levels':`${s.minimumCourseNumber||'Any'} – ${s.maximumCourseNumber||'Any'}`;
    $('summary-time').textContent=s.filterSchedule?`${s.days.join(', ')||'No days'} · ${s.start}–${s.end}`:'No day or time restriction';
    $('summary-format').textContent=s.outputFormat.toUpperCase()+(s.outputFormat==='csv'?' spreadsheet':'');
    const codes=[...new Set([...selected,...s.customSubjects.toUpperCase().split(/[,\s]+/).filter(Boolean)])];
    $('subject-badge').textContent=codes.length;$('subject-count').textContent=selected.size+' selected';
    $('selected-subjects').replaceChildren();
    if(!codes.length){const p=document.createElement('p');p.textContent='Choose subjects to get started.';$('selected-subjects').append(p);}
    else for(const code of codes){const el=document.createElement('span');el.textContent=code;$('selected-subjects').append(el);}
    if($('preview-details').open){try{$('script-preview').value=C.generate(s);}catch(e){$('script-preview').value=e.message;}}
    notify('');
  }
  function applySettings(raw) {
    const s={...C.DEFAULTS,...raw};
    strings.forEach(k=>$(k).value=s[k]);flags.forEach(k=>$(k).checked=s[k]);
    selected.clear();s.subjects.forEach(code=>selected.add(code));
    $('days').querySelectorAll('input').forEach(e=>e.checked=s.days.includes(e.value));
    document.querySelectorAll('[name=outputFormat]').forEach(e=>e.checked=e.value===s.outputFormat);
    // An imported custom component remains selectable in the web version.
    if(s.component && !$('component').value){const o=new Option(s.component,s.component);$('component').add(o);$('component').value=s.component;}
    syncLevel();drawSubjects();refresh();
  }
  function syncLevel(){const pair=[$('minimumCourseNumber').value,$('maximumCourseNumber').value].join(':');$('level').value=({'':'all',':':'all','100:299':'lower','300:499':'upper','600:999':'graduate'})[pair]||'custom';}
  function download(text,name,type='text/plain;charset=utf-8') {
    const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
  }
  $('settings-form').addEventListener('submit',e=>e.preventDefault());
  $('settings-form').addEventListener('input',()=>{syncLevel();refresh();});
  $('settings-form').addEventListener('change',()=>refresh());
  $('level').addEventListener('change',()=>{
    const ranges={all:['',''],lower:['100','299'],upper:['300','499'],graduate:['600','999']};
    const pair=ranges[$('level').value];if(pair){$('minimumCourseNumber').value=pair[0];$('maximumCourseNumber').value=pair[1];}refresh();
  });
  // Select changes may also dispatch input; do not reset a preset before its change handler.
  $('level').addEventListener('input',e=>e.stopPropagation());
  $('subject-filter').addEventListener('input',drawSubjects);
  $('select-shown').addEventListener('click',()=>{$('subjects').querySelectorAll('input').forEach(e=>selected.add(e.value));drawSubjects();refresh();});
  $('clear-subjects').addEventListener('click',()=>{selected.clear();drawSubjects();refresh();});
  $('reset').addEventListener('click',()=>{$('subject-filter').value='';applySettings(C.DEFAULTS);notify('Filters reset. Choose subjects to begin.');});
  $('copy-script').addEventListener('click',async()=>{
    const code=script();if(code===null)return;
    try{await navigator.clipboard.writeText(code);notify('Copied. Paste into the top console on MyNEVADA Class Search.');}
    catch{$('preview-details').open=true;$('script-preview').value=code;$('script-preview').focus();$('script-preview').select();notify('Automatic copy is unavailable. The script is selected above; use your browser’s Copy command.');}
  });
  $('download-script').addEventListener('click',()=>{const code=script();if(code===null)return;download(code,'UNR_Course_Search.txt');notify('Script downloaded. Run it in MyNEVADA to download your course results.');});
  $('preview-details').addEventListener('toggle',()=>{if($('preview-details').open){const code=script();$('script-preview').value=code||'Choose subjects and correct the settings to preview your script.';}});
  $('save-settings').addEventListener('click',()=>{if(!checkedConfig())return;download(JSON.stringify(settings(),null,2),'UNR_search_settings.json','application/json');notify('Settings saved. They also work in the Python app.');});
  $('load-settings').addEventListener('click',()=>$('settings-file').click());
  $('settings-file').addEventListener('change',async()=>{
    const file=$('settings-file').files[0];if(!file)return;
    try{if(file.size>1000000)throw Error('Choose a small builder settings JSON, not course results.');const data=JSON.parse(await file.text());C.validateSettings(data);applySettings(data);notify('Settings loaded.');}
    catch(e){notify('Could not load settings: '+e.message,true);}finally{$('settings-file').value='';}
  });
  applySettings(C.DEFAULTS);
})();
