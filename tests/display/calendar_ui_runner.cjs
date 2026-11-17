// Executes the production calendar functions with ES2017 APIs removed and no network.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync(process.argv[2], 'utf8');
const scenario = process.argv[3];
let now = Date.parse('2026-11-15T04:00:00Z');
let sendThrows = false;
const pending = [];
const nodes = {
  'today-summary': {innerHTML:''},
  'calendar-overlay-list': {innerHTML:''},
  'calendar-overlay': {className:'calendar-overlay calendar-overlay-open'},
  eyebrow: {innerHTML:'家庭日历', title:''}
};
function ClockDate(...args) { return args.length ? Reflect.construct(Date,args) : new Date(now); }
ClockDate.now = () => now; ClockDate.parse = Date.parse; ClockDate.UTC = Date.UTC; ClockDate.prototype = Date.prototype;
function XHR() { this.readyState=0; this.status=0; this.responseText=''; this.headers={}; pending.push(this); }
XHR.prototype.open = function(method,url,async) { assert.equal(method,'GET'); assert.ok(url.startsWith('/api/calendar?')); assert.equal(async,true);this.url=url; };
XHR.prototype.send = function() { if(sendThrows) throw new Error('synthetic send failure'); };
XHR.prototype.getResponseHeader = function(name) { return this.headers[name] || null; };
XHR.prototype.reply = function(status,body,headers={}) { this.status=status;this.responseText=typeof body==='string'?body:JSON.stringify(body);this.headers=headers;this.readyState=4;this.onreadystatechange(); };
const context = vm.createContext({ Date:ClockDate,XMLHttpRequest:XHR, document:{getElementById:id=>nodes[id]||null,querySelector:s=>s==='.calendar-overlay-eyebrow'?nodes.eyebrow:null} });
vm.runInContext('String.prototype.padStart=undefined; Promise=undefined; fetch=undefined;',context);
const calendar = source.slice(source.indexOf('  var todayCalendarDate'),source.indexOf('  var todoRevision'));
const overlay = source.slice(source.indexOf('  function calendarOverlayIsOpen()'),source.indexOf('  function closeCalendarOverlay()'));
const escape = source.slice(source.indexOf('  function escapeHtml('),source.indexOf('  function formatClockTime('));
vm.runInContext(escape + calendar + overlay, context);
const run = code=>vm.runInContext(code,context);
const update = (day='2026-11-15')=>run('updateTodayCalendar('+JSON.stringify(day)+',null)');
const advance = ms=>{ now+=ms; };
const event = (title='Synthetic timed event',start='2026-11-15T09:05:00+08:00',end='2026-11-15T10:05:00+08:00',all_day=false)=>({title,start,end,all_day});
const fresh = (events=[event()],extra={})=>({events,calendar_status:{state:'fresh',stale:false,age_seconds:0,...extra}});
const prime = (events=[event()])=>{update();pending.at(-1).reply(200,fresh(events));};
const html = ()=>nodes['today-summary'].innerHTML;
const list = ()=>nodes['calendar-overlay-list'].innerHTML;
const old = ()=>{assert.ok(html().includes('旧日程'));assert.ok(nodes.eyebrow.innerHTML.includes('旧日程'));};
const expire = ()=>{advance(300001);update();};
const failing = state=>({calendar_status:{state},error:'PRIVATE_BACKEND_MESSAGE'});
const cases = {
  cold_syncing() { update();assert.ok(html().includes('日历同步中'));assert.ok(!html().includes('暂无'));pending[0].reply(503,failing('syncing'));run('renderTodaySummary("2026-11-15",null)');assert.ok(html().includes('同步中'));assert.ok(!list().includes('暂无')); },
  cold_failure_then_empty_recovery() { update();pending[0].reply(503,failing('unavailable'));assert.ok(html().includes('暂不可用'));advance(15001);update();pending[1].reply(200,fresh([]));assert.ok(html().includes('未来10天暂无事项'));assert.ok(!nodes.eyebrow.innerHTML.includes('不可用')); },
  cached_syncing() { prime();expire();old();pending.at(-1).reply(503,failing('syncing'));old();assert.ok(html().includes('Synthetic timed event'));assert.ok(list().includes('Synthetic timed event')); },
  fault_and_automatic_recovery() { prime();expire();pending.at(-1).reply(503,failing('unavailable'));old();assert.ok(html().includes('更新失败'));const count=pending.length;update();assert.equal(pending.length,count);advance(15001);run('refreshTodayCalendar()');pending.at(-1).reply(200,fresh([event('Recovered')]));assert.ok(html().includes('Recovered'));assert.ok(!html().includes('旧日程'));assert.equal(nodes.eyebrow.innerHTML,'家庭日历'); },
  transport_error() { prime();expire();pending.at(-1).onerror();old();assert.ok(html().includes('Synthetic')); },
  timeout_late_response() { prime();expire();const request=pending.at(-1);assert.equal(request.timeout,10000);request.ontimeout();old();request.reply(200,fresh([event('Late must be ignored')]));assert.ok(!html().includes('Late'));advance(15001);update();assert.equal(pending.length,3); },
  single_inflight() { for(let i=0;i<20;i++) update();assert.equal(pending.length,1);pending[0].reply(503,failing('syncing'),{'Retry-After':'5'});advance(4999);update();assert.equal(pending.length,1);advance(1);update();assert.equal(pending.length,2); },
  malformed_json() { prime();expire();pending.at(-1).reply(200,'invalid PRIVATE_BACKEND_MESSAGE');old();assert.ok(html().includes('Synthetic'));assert.ok(!html().includes('PRIVATE')); },
  invalid_events() { prime();expire();pending.at(-1).reply(200,{events:[null]});old();assert.ok(html().includes('Synthetic')); },
  stale_200() { update();pending[0].reply(200,fresh([event()],{state:'stale',stale:true,age_seconds:450}));old();advance(15001);update();pending[1].reply(200,fresh([event('Fresh')]));assert.ok(!html().includes('旧日程'));assert.ok(html().includes('Fresh')); },
  server_cache_age() { update();pending[0].reply(200,fresh([event()],{age_seconds:299}));advance(999);update();assert.equal(pending.length,1);advance(1);update();assert.equal(pending.length,2);old(); },
  eventkit_legacy_and_old_safari() { update();pending[0].reply(200,{events:[event(),event('All day','2026-11-15T00:00:00+08:00','2026-11-16T00:00:00+08:00',true)]});assert.ok(html().includes('09:05'));assert.ok(list().includes('09:05'));assert.ok(list().includes('全天'));assert.ok(!html().includes('旧日程')); },
  rollover_retains_only_overlapping_events() { prime([event('Expired all-day','2026-11-15T00:00:00+08:00','2026-11-16T00:00:00+08:00',true),event('Still active','2026-11-15T00:00:00+08:00','2026-11-17T00:00:00+08:00',true)]);advance(86400000);update('2026-11-16');pending.at(-1).reply(503,failing('unavailable'));old();assert.ok(!html().includes('Expired'));assert.ok(!list().includes('Expired'));assert.ok(html().includes('Still active'));assert.ok(list().includes('今天')); },
  late_previous_day_response() { update();update('2026-11-16');pending[0].reply(200,fresh([event('Old response','2026-11-16T00:00:00+08:00','2026-11-17T00:00:00+08:00',true)]));old();assert.equal(run('todayCalendarViewDate'),'2026-11-16');update('2026-11-16');assert.equal(pending.length,2); },
  fresh_empty() { prime([]);assert.ok(html().includes('未来10天暂无事项'));assert.ok(list().includes('未来 10 天暂无日历事项')); },
  unknown_server_state() { prime();expire();pending.at(-1).reply(200,fresh([event('Discard')],{state:'unavailable'}));old();assert.ok(!html().includes('Discard')); },
  independent_from_snapshot() { run('refreshTodayCalendar()');assert.ok(html().includes('同步中'));assert.ok(decodeURIComponent(pending[0].url).includes('2026-11-14T16:00:00.000Z'));assert.ok(source.includes('setInterval(refreshTodayCalendar, 15000)'));assert.ok(source.includes('  refreshTodayCalendar();')); },
  send_failure() { sendThrows=true;update();assert.ok(html().includes('暂不可用'));assert.equal(run('todayCalendarRequest'),null);sendThrows=false;advance(15001);update();assert.equal(pending.length,2); },
  stale_header() { update();pending[0].reply(200,{events:[event()]},{'X-Calendar-Stale':'true'});old(); },
  escaped_title_and_private_error() { prime([event('<img src=x onerror=alert(1)>')]);assert.ok(!html().includes('<img'));assert.ok(html().includes('&lt;img'));expire();pending.at(-1).reply(503,failing('unavailable'));assert.ok(!html().includes('PRIVATE'));assert.ok(!list().includes('PRIVATE')); },
  bounded_retry_hint() { update();pending[0].reply(503,failing('syncing'),{'Retry-After':'999999'});advance(29999);update();assert.equal(pending.length,1);advance(1);update();assert.equal(pending.length,2); },
  server_clock_overrides_device_drift() { now=Date.parse('2026-11-20T04:00:00Z');run('updateCalendarClock("2026-11-15","12:00:00");refreshTodayCalendar()');assert.ok(decodeURIComponent(pending[0].url).includes('2026-11-14T16:00:00.000Z'));pending[0].reply(503,failing('unavailable'));advance(86400000);run('refreshTodayCalendar()');assert.ok(decodeURIComponent(pending.at(-1).url).includes('2026-11-15T16:00:00.000Z')); },
  no_events_field_is_failure() { prime();expire();pending.at(-1).reply(200,{});old();assert.ok(html().includes('Synthetic')); }
};
assert.ok(cases[scenario], 'unknown scenario');cases[scenario]();
console.log(JSON.stringify({scenario,passed:true}));
