const {JSDOM,VirtualConsole}=require('jsdom');
const fs=require('fs'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'../../frontend/heimdall_console.html'),'utf8');
const wait=()=>new Promise(r=>setTimeout(r,25));
const stamp=new Date().toISOString();
const records={'/sources':[{source_id:1,source_name:'Test source <img src=x onerror=alert(1)>',reliability_score:.8}],'/threat-events':[{event_id:1,timestamp:stamp,source_id:1,object_class:'person',confidence_score:.95,camera_id:'CAM-1',status:'Pending'},{event_id:2,timestamp:stamp,object_class:'car',confidence_score:.6,camera_id:'CAM-1',status:'Pending'}],'/alert-logs':[{alert_id:1,event_id:1,alert_time:stamp,alert_level:'Critical',message:'Test <script>bad()</script>',acknowledged:false}],'/camera-states':[{state_id:1,camera_id:'CAM-1',timestamp:stamp,mode:'Active',fps:30,resolution:'1920x1080'}],'/system-logs':[{log_id:1,log_time:stamp,module:'vision',message:'record created <img src=x>'}]};
async function boot(data=records){
 const errors=[],calls=[],pins=[];let failure=null;const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(e.type!=='css-parsing')errors.push(e.message)});
 const chain=()=>new Proxy({}, {get:(o,k)=>k==='then'?undefined:(...args)=>{if(k==='panTo')pins.push(args);return chain()}});
 const dom=new JSDOM(html,{url:'http://localhost:8501',runScripts:'dangerously',virtualConsole:vc,beforeParse(w){
  w.Headers=Headers;w.AbortController=AbortController;
  w.L={map:()=>chain(),tileLayer:()=>chain(),control:{zoom:()=>chain()},layerGroup:()=>chain(),circle:()=>chain(),circleMarker:(...args)=>{pins.push(args);return chain()},polyline:()=>chain(),latLngBounds:()=>chain()};
  w.fetch=async(url,opts)=>{const path=String(url).replace('__HEIMDALL_API_URL__','');calls.push({path,opts});if(failure && path===failure.path && failure.status==='network')throw new TypeError('Failed to fetch');if(failure && path===failure.path)return{ok:false,status:failure.status,json:async()=>({})};return {ok:true,status:200,json:async()=>path==='/auth/login'?{access_token:'test-token'}:path==='/auth/me'?{is_active:true,username:'tester'}:structuredClone(data[path]||[])};};
 }});
 const w=dom.window,d=w.document;
 async function login(){d.getElementById('authUsername').value='tester';d.getElementById('authPassword').value='test-password-123';d.getElementById('loginForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await wait();}
 return {dom,w,d,errors,calls,pins,login,fail:(path,status)=>failure={path,status},recover:()=>failure=null,close:()=>w.close()};
}
(async()=>{
 let passed=0;async function test(name,fn){await fn();console.log('PASS',name);passed++;}
 await test('login loads real records and preserves shell',async()=>{const t=await boot();try{await t.login();assert.equal(t.d.querySelector('#authGate').hidden,true);assert.match(t.d.querySelector('#coreApiRecords').textContent,/2 events · 1 alerts · 1 camera states/);assert.equal(t.d.querySelectorAll('#viewOps main').length,1);assert.match(t.d.querySelector('#queue').textContent,/Detected object: car/);assert.match(t.d.querySelector('#threatPanel').textContent,/Test <script>/);assert.equal(t.errors.length,0,t.errors.join('\n'));}finally{t.close()}});
 await test('unlocated records do not produce map markers and details open',async()=>{const t=await boot();try{await t.login();t.d.querySelector('#queue .alert').click();assert.match(t.d.querySelector('#dSub').textContent,/Location not provided/);assert.equal(t.pins.length,0);assert.equal(t.errors.length,0);}finally{t.close()}});
 await test('API text is escaped in feed, details and sources',async()=>{const t=await boot();try{await t.login();assert.equal(t.d.querySelectorAll('#app img,#app script').length,0);t.d.querySelector('[data-t="drawer"]').click();assert.equal(t.d.querySelectorAll('#drawer img,#drawer script').length,0);assert.match(t.d.querySelector('#drawer').textContent,/Test <script>/);}finally{t.close()}});
 await test('camera panel uses real states without claiming video',async()=>{const t=await boot();try{await t.login();assert.equal(t.d.querySelectorAll('.cam').length,1);assert.match(t.d.querySelector('#camGrid').textContent,/30 FPS/);assert.match(t.d.querySelector('#camGrid').textContent,/NO VIDEO STREAM/);t.d.querySelector('[data-cam]').click();assert.equal(t.errors.length,0);}finally{t.close()}});
 await test('unsupported writes disabled and no legacy requests',async()=>{const t=await boot();try{await t.login();assert.ok(t.d.querySelector('#dAck').disabled);assert.ok(t.d.querySelector('#camAll').disabled);assert.ok(t.calls.every(c=>!c.path.startsWith('/api/')));assert.ok(t.calls.filter(c=>c.path!=='/auth/login').every(c=>(c.opts.headers.get?.('Authorization')||c.opts.headers.Authorization)==='Bearer test-token'));}finally{t.close()}});
 await test('empty API has no fake data or NaN analytics',async()=>{const t=await boot({});try{await t.login();assert.equal(t.d.querySelectorAll('.alert,.cam').length,0);assert.match(t.d.querySelector('#coreApiRecords').textContent,/0 events/);assert.ok(!t.d.querySelector('#triageStats').textContent.includes('NaN'));assert.equal(t.errors.length,0,t.errors.join('\n'));}finally{t.close()}});
 await test('refresh replaces snapshot without duplicate events',async()=>{const t=await boot();try{await t.login();t.d.querySelector('#demoBtn').click();await wait();assert.equal(t.d.querySelectorAll('#queue .alert').length,1);assert.equal(t.d.querySelectorAll('.cam').length,1);}finally{t.close()}});
 await test('logout clears backend data and sign-in works again',async()=>{const t=await boot();try{await t.login();t.d.querySelector('#logoutButton').click();assert.equal(t.d.querySelector('#authGate').hidden,false);assert.equal(t.d.querySelectorAll('.alert,.cam').length,0);await t.login();assert.equal(t.d.querySelector('#authGate').hidden,true);assert.match(t.d.querySelector('#coreApiRecords').textContent,/2 events/);assert.equal(t.errors.length,0);}finally{t.close()}});
 await test('expired session returns to login',async()=>{const t=await boot();try{await t.login();t.fail('/auth/me',401);t.d.querySelector('#demoBtn').click();await wait();assert.equal(t.d.querySelector('#authGate').hidden,false);assert.match(t.d.querySelector('#authMessage').textContent,/expired/);}finally{t.close()}});
 await test('API failure labels retained snapshot stale',async()=>{const t=await boot();try{await t.login();t.fail('/threat-events',500);t.d.querySelector('#demoBtn').click();await wait();assert.match(t.d.querySelector('#coreApiStatus').textContent,/stale/);assert.match(t.d.querySelector('#modeLabel').textContent,/UNAVAILABLE/);}finally{t.close()}});
 await test('pause suppresses record loading; resume reloads',async()=>{const t=await boot();try{await t.login();t.d.querySelector('#liveBtn').click();const n=t.calls.length;t.d.querySelector('#demoBtn').click();await wait();assert.equal(t.calls.length,n);t.d.querySelector('#liveBtn').click();await wait();assert.ok(t.calls.length>n);}finally{t.close()}});
 await test('scheduled poll updates records after five seconds',async()=>{const t=await boot();try{await t.login();const n=t.calls.filter(c=>c.path==='/threat-events').length;await new Promise(r=>setTimeout(r,5300));assert.ok(t.calls.filter(c=>c.path==='/threat-events').length>n);}finally{t.close()}});
 await test('late responses cannot repopulate signed-out dashboard',async()=>{const t=await boot();try{await t.login();const base=t.w.fetch;let release;t.w.fetch=async(url,opts)=>{if(String(url).endsWith('/threat-events'))await new Promise(r=>release=r);return base(url,opts);};t.d.querySelector('#demoBtn').click();await wait();t.d.querySelector('#logoutButton').click();release();await wait();assert.equal(t.d.querySelector('#authGate').hidden,false);assert.equal(t.d.querySelectorAll('.alert,.cam').length,0);assert.equal(t.d.querySelector('#coreApiStatus').textContent,'Signed out');}finally{t.close()}});

 await test('signed-out page makes no API requests',async()=>{const t=await boot();try{await wait();assert.equal(t.calls.length,0);assert.ok(t.d.body.classList.contains('auth-locked'));}finally{t.close()}});
 await test('invalid password keeps dashboard locked and clears password',async()=>{const t=await boot();try{t.fail('/auth/login',401);await t.login();assert.ok(t.d.body.classList.contains('auth-locked'));assert.match(t.d.querySelector('#authMessage').textContent,/Invalid credentials/);assert.equal(t.d.querySelector('#authPassword').value,'');assert.equal(t.d.querySelector('#loginButton').disabled,false);assert.ok(!t.calls.some(c=>c.path==='/threat-events'));}finally{t.close()}});
 await test('registration creates account without signing in',async()=>{const t=await boot();try{t.d.querySelector('#authUsername').value='newuser';t.d.querySelector('#authPassword').value='test-password-123';t.d.querySelector('#registerButton').click();await wait();const c=t.calls.find(c=>c.path==='/auth/register');assert.equal(c.opts.method,'POST');assert.equal(JSON.parse(c.opts.body).username,'newuser');assert.match(t.d.querySelector('#authMessage').textContent,/Account created/);assert.ok(t.d.body.classList.contains('auth-locked'));assert.equal(t.d.querySelector('#authPassword').value,'');}finally{t.close()}});
 await test('duplicate registration shows readable conflict',async()=>{const t=await boot();try{t.fail('/auth/register',409);t.d.querySelector('#authUsername').value='tester';t.d.querySelector('#authPassword').value='test-password-123';t.d.querySelector('#registerButton').click();await wait();assert.match(t.d.querySelector('#authMessage').textContent,/already taken/);assert.ok(t.d.body.classList.contains('auth-locked'));}finally{t.close()}});
 for(const [status,message] of [[404,/could not be found/],[409,/conflicts with the current record/]]){
 await test(`HTTP ${status} shows readable error and retains records`,async()=>{const t=await boot();try{await t.login();const before=t.d.querySelector('#queue').textContent;t.fail('/threat-events',status);t.d.querySelector('#demoBtn').click();await wait();assert.match(t.d.querySelector('#coreApiRecords').textContent,message);assert.equal(t.d.querySelector('#queue').textContent,before);assert.equal(t.d.querySelector('#authGate').hidden,true);}finally{t.close()}});
 }
 await test('network failure recovers on next scheduled poll',async()=>{const t=await boot();try{await t.login();t.fail('/threat-events','network');t.d.querySelector('#demoBtn').click();await wait();assert.match(t.d.querySelector('#coreApiRecords').textContent,/Cannot reach the backend/);assert.match(t.d.querySelector('#coreApiStatus').textContent,/stale/);t.recover();await new Promise(r=>setTimeout(r,5300));assert.match(t.d.querySelector('#coreApiStatus').textContent,/Connected/);assert.match(t.d.querySelector('#coreApiRecords').textContent,/2 events/);}finally{t.close()}});
 await test('feature flags hide unsupported actions including rendered buttons',async()=>{const t=await boot();try{await t.login();for(const selector of ['#ackAll','#feedClear','#dAck','#dEsc','#dDismiss','#camAll','#queue .acts button:nth-child(1)','#queue .acts button:nth-child(2)','#queue .acts button:nth-child(3)','#camGrid button[title="Camera hardware controls are not connected"]']){const el=t.d.querySelector(selector);assert.ok(el,selector+' exists');assert.equal(t.w.getComputedStyle(el).display,'none',selector+' hidden');}const details=t.d.querySelector('[data-t="drawer"]');assert.notEqual(t.w.getComputedStyle(details).display,'none');details.click();assert.match(t.d.querySelector('#drawer').textContent,/Test <script>/);}finally{t.close()}});
 await test('tokens are not stored in localStorage or sessionStorage',async()=>{const t=await boot();try{await t.login();assert.equal(t.w.localStorage.length,0);assert.equal(t.w.sessionStorage.length,0);}finally{t.close()}});

 await test('ACK uses alert ID and persists across refresh and relogin',async()=>{
  const data=structuredClone(records);data['/alert-logs'][0].alert_id=77;
  const t=await boot(data);try{
   const base=t.w.fetch;t.w.fetch=async(url,opts)=>{
    if(opts?.method==='PATCH'){
     assert.ok(String(url).endsWith('/alert-logs/77'));
     assert.equal(opts.headers.Authorization,'Bearer test-token');
     assert.deepEqual(JSON.parse(opts.body),{acknowledged:true});
     data['/alert-logs'][0].acknowledged=true;
     return {ok:true,status:200,json:async()=>structuredClone(data['/alert-logs'][0])};
    }return base(url,opts);
   };
   await t.login();t.d.querySelector('[data-t="drawer"]').click();
   t.d.querySelector('[data-ack-alert="77"]').click();await wait();
   assert.match(t.d.querySelector('#toasts').textContent,/acknowledged and saved/);
   assert.equal(data['/threat-events'][0].status,'Pending');
   t.d.querySelector('#demoBtn').click();await wait();
   assert.equal(t.d.querySelector('[data-ack-alert="77"]').textContent,'Acknowledged');
   t.d.querySelector('#logoutButton').click();await t.login();
   t.d.querySelector('[data-t="drawer"]').click();
   assert.ok(t.d.querySelector('[data-ack-alert="77"]').disabled);
   assert.equal(t.errors.length,0,t.errors.join('\n'));
  }finally{t.close()}
 });
 for(const status of [401,404,409,500]){
  await test(`ACK HTTP ${status} never shows false success`,async()=>{
   const t=await boot();try{
    await t.login();t.fail('/alert-logs/1',status);
    t.d.querySelector('[data-t="drawer"]').click();t.d.querySelector('[data-ack-alert]').click();await wait();
    assert.doesNotMatch(t.d.querySelector('#toasts').textContent,/acknowledged and saved/);
    if(status===401)assert.equal(t.d.querySelector('#authGate').hidden,false);
    else {assert.equal(t.d.querySelector('[data-ack-alert]').textContent,'Acknowledge');assert.ok(t.d.querySelector('#toasts').textContent.length>0);}
   }finally{t.close()}
  });
 }
 await test('ACK blocks duplicate clicks and ignores response after logout',async()=>{
  const t=await boot();try{
   await t.login();const base=t.w.fetch;let release,count=0;
   t.w.fetch=async(url,opts)=>{if(opts?.method==='PATCH'){count++;await new Promise(r=>release=r);return{ok:true,status:200,json:async()=>({...records['/alert-logs'][0],acknowledged:true})};}return base(url,opts)};
   t.d.querySelector('[data-t="drawer"]').click();const button=t.d.querySelector('[data-ack-alert]');button.click();button.click();
   assert.equal(count,1);assert.equal(t.d.querySelector('[data-ack-alert]').textContent,'Saving…');
   t.d.querySelector('#logoutButton').click();release();await wait();
   assert.equal(t.d.querySelector('#authGate').hidden,false);assert.equal(t.d.querySelector('#alertActions').textContent,'');assert.equal(t.d.querySelector('#toasts').textContent,'');
  }finally{t.close()}
 });
 await test('ACK updates only chosen alert in event with multiple alerts',async()=>{
  const data=structuredClone(records);data['/alert-logs'].push({...data['/alert-logs'][0],alert_id:8});
  const t=await boot(data);try{
   const base=t.w.fetch;t.w.fetch=async(url,opts)=>{if(opts?.method==='PATCH'){data['/alert-logs'][1].acknowledged=true;return{ok:true,status:200,json:async()=>structuredClone(data['/alert-logs'][1])};}return base(url,opts)};
   await t.login();t.d.querySelector('[data-t="drawer"]').click();t.d.querySelector('[data-ack-alert="8"]').click();await wait();
   assert.equal(t.d.querySelector('[data-ack-alert="8"]').textContent,'Acknowledged');assert.equal(t.d.querySelector('[data-ack-alert="1"]').textContent,'Acknowledge');
  }finally{t.close()}
 });
 await test('read started before ACK cannot overwrite confirmed result',async()=>{
  const data=structuredClone(records),t=await boot(data);try{
   await t.login();t.d.querySelector('[data-t="drawer"]').click();
   const base=t.w.fetch;let release,hold=true;
   t.w.fetch=async(url,opts)=>{
    if(opts?.method==='PATCH'){data['/alert-logs'][0].acknowledged=true;return{ok:true,status:200,json:async()=>structuredClone(data['/alert-logs'][0])};}
    if(String(url).endsWith('/alert-logs')&&hold){hold=false;const old=structuredClone(data['/alert-logs']);await new Promise(r=>release=r);return{ok:true,status:200,json:async()=>old};}
    return base(url,opts);
   };
   t.d.querySelector('#demoBtn').click();await wait();t.d.querySelector('[data-ack-alert]').click();await wait();release();await wait();
   assert.equal(t.d.querySelector('[data-ack-alert]').textContent,'Acknowledged');assert.equal(t.errors.length,0);
  }finally{t.close()}
 });

 await test('threat status PATCH uses event ID and preserves alert acknowledgment',async()=>{
  const data=structuredClone(records);data['/alert-logs'][0].alert_id=77;data['/alert-logs'][0].acknowledged=true;
  const t=await boot(data);try{
   const base=t.w.fetch;t.w.fetch=async(url,opts)=>{if(opts?.method==='PATCH'){
    assert.ok(String(url).endsWith('/threat-events/1'));assert.equal(opts.headers.Authorization,'Bearer test-token');
    const body=JSON.parse(opts.body);assert.deepEqual(Object.keys(body),['status']);
    data['/threat-events'][0].status=body.status;return{ok:true,status:200,json:async()=>structuredClone(data['/threat-events'][0])};
   }return base(url,opts)};
   await t.login();t.d.querySelector('[data-t="drawer"]').click();
   assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Pending/);
   t.d.querySelector('[data-threat-status="Resolved"]').click();await wait();
   assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Resolved/);
   assert.equal(t.d.querySelector('[data-ack-alert="77"]').textContent,'Acknowledged');
   t.d.querySelector('#demoBtn').click();await wait();assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Resolved/);
   t.d.querySelector('#logoutButton').click();await t.login();t.d.querySelector('[data-t="drawer"]').click();
   assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Resolved/);
   t.d.querySelector('[data-threat-status="Pending"]').click();await wait();
   assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Pending/);assert.equal(data['/alert-logs'][0].acknowledged,true);
   assert.equal(t.errors.length,0,t.errors.join('\n'));
  }finally{t.close()}
 });
 for(const status of [401,404,409,500])await test(`threat status HTTP ${status} never shows false success`,async()=>{
  const t=await boot();try{await t.login();t.fail('/threat-events/1',status);t.d.querySelector('[data-t="drawer"]').click();
   t.d.querySelector('[data-threat-status="Resolved"]').click();await wait();assert.doesNotMatch(t.d.querySelector('#toasts').textContent,/status saved/);
   if(status===401)assert.equal(t.d.querySelector('#authGate').hidden,false);
   else assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Pending/);
  }finally{t.close()}
 });
 await test('threat write blocks duplicate and concurrent ACK, ignores late logout response',async()=>{
  const t=await boot();try{await t.login();const base=t.w.fetch;let release,count=0;
   t.w.fetch=async(url,opts)=>{if(opts?.method==='PATCH'){count++;await new Promise(r=>release=r);return{ok:true,status:200,json:async()=>({...records['/threat-events'][0],status:'Resolved'})};}return base(url,opts)};
   t.d.querySelector('[data-t="drawer"]').click();const button=t.d.querySelector('[data-threat-status="Resolved"]');button.click();button.click();
   assert.equal(t.d.querySelector('[data-ack-alert]').disabled,true);t.d.querySelector('[data-ack-alert]').click();assert.equal(count,1);
   t.d.querySelector('#logoutButton').click();release();await wait();assert.equal(t.d.querySelector('#threatActions').textContent,'');assert.equal(t.d.querySelector('#toasts').textContent,'');
  }finally{t.close()}
 });
 await test('stale reads cannot undo confirmed threat status',async()=>{
  const data=structuredClone(records),t=await boot(data);try{
   await t.login();t.d.querySelector('[data-t="drawer"]').click();const base=t.w.fetch;let release,hold=true;
   t.w.fetch=async(url,opts)=>{
    if(opts?.method==='PATCH'){data['/threat-events'][0].status='Resolved';return{ok:true,status:200,json:async()=>structuredClone(data['/threat-events'][0])};}
    if(String(url).endsWith('/threat-events')&&hold){hold=false;const old=structuredClone(data['/threat-events']);await new Promise(r=>release=r);return{ok:true,status:200,json:async()=>old};}return base(url,opts);
   };
   t.d.querySelector('#demoBtn').click();await wait();t.d.querySelector('[data-threat-status="Resolved"]').click();await wait();release();await wait();
   assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Resolved/);assert.equal(data['/alert-logs'][0].acknowledged,false);
  }finally{t.close()}
 });
 await test('invalid threat response never shows success',async()=>{
  const t=await boot();try{await t.login();const base=t.w.fetch;t.w.fetch=async(url,opts)=>opts?.method==='PATCH'?{ok:true,status:200,json:async()=>({event_id:999,status:'Resolved'})}:base(url,opts);
   t.d.querySelector('[data-t="drawer"]').click();t.d.querySelector('[data-threat-status="Resolved"]').click();await wait();
   assert.doesNotMatch(t.d.querySelector('#toasts').textContent,/status saved/);assert.match(t.d.querySelector('#currentThreatStatus').textContent,/Pending/);
  }finally{t.close()}
 });

 console.log(`${passed} tests passed`);
})().catch(e=>{console.error(e);process.exitCode=1});
