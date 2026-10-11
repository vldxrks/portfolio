const $=s=>document.querySelector(s),esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const EQ=["4K Projector","Whiteboard","Polycom Video","Acoustic Panels"],DN=['Today','Tomorrow','Day after tomorrow'];
let me=null,rooms=[],sel={},filt={q:'',cap:'',loc:'',eq:new Set()},reg=false,pendingHold=null;
async function api(u,o={}){const r=await fetch(u,{method:o.method||'GET',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:o.body?JSON.stringify(o.body):undefined});
const j=await r.json().catch(()=>({}));if(!r.ok)throw Object.assign(new Error(j.error||'Request failed'),{status:r.status});return j}
function toast(m,bad){const t=document.createElement('div');t.className='toast'+(bad?' bad':'');t.textContent=m;document.body.append(t);setTimeout(()=>t.remove(),3500)}
const firstFree=(r,d)=>(r.slots[d].find(s=>s.free)||{}).t||null;
function sync(){rooms.forEach(r=>{const s=sel[r.id]||(sel[r.id]={day:0,slot:null});const cur=r.slots[s.day].find(x=>x.t===s.slot);if(!cur||!cur.free)s.slot=firstFree(r,s.day)})}
async function loadRooms(){rooms=(await api('/api/rooms')).rooms;sync();render()}
function slotsHtml(r){const s=sel[r.id];return r.slots[s.day].map(x=>`<button class="slot ${x.free?'':'off'} ${s.slot===x.t?'on':''}" ${x.free?'':'disabled'} onclick="pick(${r.id},'${x.t}')">${x.t.replace('-','–')}${s.slot===x.t?' ✓':''}</button>`).join('')}
function daysHtml(r,n){return `<div class="days">${DN.slice(0,n).map((d,i)=>`<button class="${sel[r.id].day===i?'on':''}" onclick="setDay(${r.id},${i})">${d}</button>`).join('')}</div>`}
function eqHtml(r){return `<div class="eq">${r.equipment.map(e=>`<span>${esc(e)}</span>`).join('')}</div>`}
function holdLbl(r){const s=sel[r.id].slot;return s?s.replace('-','–'):''}
function featured(r){const s=sel[r.id];return `<article class="room feat"><div class="ph"><img src="${r.image}" alt="${esc(r.name)}" onerror="this.remove()">
<span class="tag dk" style="left:16px;top:16px">${esc(r.badge||r.floor)}</span>${r.tag?`<span class="tag" style="left:150px;top:16px">${esc(r.tag)}</span>`:''}<span class="st ${r.status[0]=='A'?'':'no'}" style="bottom:16px">${r.status=='Available now'?'Ready for teams':r.status}</span></div>
<div class="body"><div class="row"><div><div class="mono" style="color:var(--mute)">ROOM ID: ${r.code}</div><h3>${esc(r.name)}</h3></div><div class="big">$${r.price}<div style="font-size:16px;font-weight:400">per hour</div></div></div>
<p>${esc(r.description)}</p><div class="facts"><span>up to ${r.capacity} guests</span>${r.area?`<span>${r.area} m²</span>`:''}${r.cls?`<span>${esc(r.cls)}</span>`:''}</div>${eqHtml(r)}
<div class="tm"><div class="slots-h"><span>CHRONO-GRID TIMELINE (8:00 – 22:00)</span>${daysHtml(r,3)}</div><div class="slots">${slotsHtml(r)}</div>
<div class="sel"><span>Selected interval: <b class="mono">${s.slot?holdLbl(r)+' ('+DN[s.day]+')':'—'}</b></span><button class="btn pri" ${s.slot?'':'disabled'} onclick="hold(${r.id})">Hold slot for ${window.HOLD||15} minutes</button></div></div></div></article>`}
function card(r){const s=sel[r.id];return `<article class="room"><div class="ph"><img src="${r.image}" alt="${esc(r.name)}" onerror="this.remove()"><span class="tag" style="left:16px;top:16px">${esc(r.floor)}</span>
<span class="st ${r.status[0]=='A'?'':'no'}">${r.status}</span><span class="price">$${r.price}/h</span></div><div class="body"><div class="meta"><span>${r.code}</span><span>up to ${r.capacity}</span></div>
<h3>${esc(r.name)}</h3><p>${esc(r.description)}</p>${eqHtml(r)}<div class="slots-h"><span>Select slot:</span>${daysHtml(r,2)}</div><div class="slots">${slotsHtml(r)}</div>
<button class="btn hold" ${s.slot?'':'disabled'} onclick="hold(${r.id})">${s.slot?'Hold '+holdLbl(r):'No free slots'}</button></div></article>`}
function render(){const f=rooms.filter(r=>(!filt.q||(r.name+' '+r.description+' '+r.tag+' '+r.code).toLowerCase().includes(filt.q))&&(!filt.cap||r.capacity>=+filt.cap)&&(!filt.loc||r.floor===filt.loc)&&[...filt.eq].every(e=>r.equipment.includes(e)));
const L=$('#list');if(!f.length){L.innerHTML='<div class="empty">No rooms match the filters.</div>';return}
const top=f[0].featured?f[0]:null,rest=top?f.slice(1):f;L.innerHTML=(top?featured(top):'')+`<div class="grid">${rest.map(card).join('')}</div>`}
window.pick=(id,t)=>{sel[id].slot=t;render()};window.setDay=(id,d)=>{const r=rooms.find(x=>x.id===id);sel[id]={day:d,slot:firstFree(r,d)};render()};
window.hold=async id=>{if(!me){pendingHold=id;return openAuth()}const s=sel[id];try{await api('/api/bookings',{method:'POST',body:{room_id:id,day:s.day,slot:s.slot}});toast('Slot held. Confirm it in My Bookings before the timer ends.');
await Promise.all([loadRooms(),loadMine()]);$('#bookings').scrollIntoView()}catch(e){toast(e.message,1);loadRooms()}};
function left(x){const ms=new Date(x)-Date.now();if(ms<=0)return'expired';const s=Math.floor(ms/1000);return Math.floor(s/60)+':'+String(s%60).padStart(2,'0')}
async function loadMine(){const m=$('#mine');if(!me){$('#cnt').textContent=0;m.innerHTML='<div class="empty">Sign in to see your bookings.</div>';return}
const b=(await api('/api/bookings/mine')).bookings;$('#cnt').textContent=b.length;
m.innerHTML=b.length?b.map(x=>`<div class="bi"><div><b>${esc(x.room)}</b><span class="code">#${x.code}</span><span class="badge ${x.status=='pending'?'p':''}">${x.status=='pending'?'Pending (Hold) <span class="mono" data-exp="'+x.expires_at+'">'+left(x.expires_at)+'</span>':'Confirmed'}</span>
<div class="m"><span>${x.day}</span><span class="mono">${x.slot.replace('-','–')}</span><span>${esc(x.floor)}</span><span>$${x.amount}</span></div></div>
<div style="display:flex;gap:8px">${x.status=='pending'?`<button class="btn pri" onclick="act(${x.id},'confirm')">Confirm</button>`:''}<button class="btn" onclick="act(${x.id},'cancel')">✕ Cancel ${x.status=='pending'?'hold':'booking'}</button></div></div>`).join(''):'<div class="empty">No active bookings yet.</div>'}
window.act=async(id,a)=>{try{await api(`/api/bookings/${id}/${a}`,{method:'POST'});toast(a=='confirm'?'Booking confirmed':'Cancelled')}catch(e){toast(e.message,1)}await Promise.all([loadRooms(),loadMine()])};
function ui(){$('#authBtn').textContent=me?'Sign out':'Sign in';$('#adminLink').hidden=!(me&&me.role==='admin')}
async function loadMe(){me=(await api('/api/me')).user;ui();await loadMine()}
function openAuth(){$('#aerr').textContent='';$('#auth').showModal()}
function setReg(v){reg=v;$('#at').textContent=v?'Register':'Sign in';$('#asub').textContent=v?'Create account':'Sign in';$('#atog').textContent=v?'Have an account?':'Register';$('#nl').hidden=!v}
$('#atog').onclick=()=>setReg(!reg);
$('#af').onsubmit=async e=>{e.preventDefault();try{me=await api(reg?'/api/register':'/api/login',{method:'POST',body:{email:$('#ae').value,password:$('#ap').value,name:$('#an').value}});
$('#auth').close();ui();await loadMine();if(pendingHold){const id=pendingHold;pendingHold=null;hold(id)}}catch(x){$('#aerr').textContent=x.message}};
$('#authBtn').onclick=async()=>{if(me){await api('/api/logout',{method:'POST'});me=null;ui();loadMine()}else openAuth()};
$('#supBtn').onclick=()=>{$('#pol').hidden=true;$('#sup').showModal()};window.policy=()=>{$('#pol').hidden=false;$('#sup').showModal()};
$('#q').oninput=e=>{filt.q=e.target.value.trim().toLowerCase();render()};$('#cap').onchange=e=>{filt.cap=e.target.value;render()};$('#loc').onchange=e=>{filt.loc=e.target.value;render()};
$('#eqs').innerHTML=EQ.map(e=>`<button class="chip" data-e="${e}">${e}</button>`).join('');
$('#eqs').onclick=e=>{const b=e.target.closest('.chip');if(!b)return;const k=b.dataset.e;filt.eq.has(k)?filt.eq.delete(k):filt.eq.add(k);b.classList.toggle('on');render()};
(async()=>{await loadRooms();[...new Set(rooms.map(r=>r.floor))].forEach(f=>$('#loc').insertAdjacentHTML('beforeend',`<option>${esc(f)}</option>`));await loadMe();if(new URLSearchParams(location.search).get('login'))openAuth();
setInterval(()=>document.querySelectorAll('[data-exp]').forEach(n=>{n.textContent=left(n.dataset.exp)}),1000);setInterval(()=>{loadRooms();if(me)loadMine()},20000)})();
