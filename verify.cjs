// 浏览器验收（离线）：node verify.cjs [生成器.html] [catalog.json]
// 需要 Playwright；默认用系统 Edge（PW_CHANNEL=chrome 可改用 Chrome）。PLAYWRIGHT_PATH 可指向已有的 playwright 模块目录。
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const {pathToFileURL}=require('url'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=__dirname,htmlFile=path.resolve(process.argv[2]||path.join(root,'封面生成器.html')),catalogFile=path.resolve(process.argv[3]||path.join(root,'catalog.json'));
const catalog=JSON.parse(fs.readFileSync(catalogFile,'utf8')).series,outDir=path.dirname(htmlFile);
const legacyReference=path.join(root,'backups/claude-original.html');// 本地历史版本，仓库里没有时跳过逐像素对照
function jpgSize(b){assert.equal(b.toString('hex',0,3),'ffd8ff','不是 JPG');for(let i=2;i<b.length;){const m=b[i+1],len=b.readUInt16BE(i+2);if(m>=0xc0&&m<=0xc3)return[b.readUInt16BE(i+7),b.readUInt16BE(i+5)];i+=2+len}throw Error('JPG 无尺寸')}
(async()=>{const browser=await chromium.launch({channel:process.env.PW_CHANNEL||'msedge',headless:true});try{
 const context=await browser.newContext({acceptDownloads:true,offline:true,viewport:{width:1280,height:900}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const out=path.join(outDir,'validation');fs.mkdirSync(out,{recursive:true});
 const t0=Date.now();await page.goto(pathToFileURL(htmlFile).href);
 const ready=()=>page.waitForFunction(()=>[...document.querySelectorAll('.panel:not([hidden]) .cover')].every(x=>x.getAttribute('aria-disabled')==='false'));
 await ready();const firstPageMs=Date.now()-t0;
 assert.equal(await page.locator('nav [role=tab]').count(),catalog.length);assert.equal(await page.evaluate(()=>scrollY),0,'打开时不应自动滚动');
 const exports=[];
 for(const s of catalog){
  const panel=page.locator('#panel-'+s.id),input=panel.locator('input'),minus=panel.locator('.stepper button').first(),plus=panel.locator('.stepper button').last();
  await page.locator('[data-page="'+s.id+'"]').click();await ready();
  // 编号器：三位数步进、上下限
  await input.fill('5');await plus.click();assert.equal(await input.inputValue(),'006');await minus.click();await minus.click();assert.equal(await input.inputValue(),'004');
  await input.fill('999');await plus.click();assert.equal(await input.inputValue(),'1000');await input.fill('0');await minus.click();assert.equal(await input.inputValue(),'000');
  await input.fill('9999');await plus.click();assert.equal(await input.inputValue(),'9999');await ready();
  // 分页：每页最多 4 行，entries[0] 在第一页第一行
  const pages=Math.ceil(s.entries.length/4);
  for(let pg=0;pg<pages;pg++){
   const rows=await panel.locator('.row').evaluateAll(xs=>xs.map(r=>r.dataset.entry));assert.deepEqual(rows,s.entries.slice(pg*4,pg*4+4).map(e=>e.id),'第'+(pg+1)+'页行顺序');
   const heights=await panel.locator('.row').evaluateAll(xs=>xs.map(r=>[...r.querySelectorAll('.cover')].map(c=>c.getBoundingClientRect().height)));heights.forEach(h=>assert(h.every(x=>Math.abs(x-h[0])<1),'同行等高'));
   for(const link of await panel.locator('.cover').all()){
    const id=await link.getAttribute('data-id'),pending=page.waitForEvent('download');await link.click();const dl=await pending,name=dl.suggestedFilename();
    assert(name.endsWith('-#9999.jpg'),name);const file=path.join(out,name);await dl.saveAs(file);const [w,h]=jpgSize(fs.readFileSync(file));assert.equal(w,id.endsWith('16x9')?1920:1440);assert.equal(h,1080);exports.push({id,file:name,width:w,height:h});
    await ready();
   }
   if(pg<pages-1){await panel.locator('.pager button').last().click();await ready()}
  }
  assert.equal(await panel.locator('.pager').isHidden(),pages<2);
 }
 // 两个系列编号互相独立，刷新后各自保留
 const [a,b]=catalog;
 await page.locator('[data-page="'+a.id+'"]').click();await page.locator('#panel-'+a.id+' input').fill('12');await ready();
 await page.locator('[data-page="'+b.id+'"]').click();await page.locator('#panel-'+b.id+' input').fill('34');await ready();
 assert((await page.locator('#panel-'+b.id+' canvas').first().getAttribute('aria-label')).endsWith('#034'));
 await page.reload();await ready();assert.equal(await page.locator('#panel-'+a.id+' input').inputValue(),'012');assert.equal(await page.locator('#panel-'+b.id+' input').inputValue(),'034');
 // 快速输入、连点不串号
 const inp=page.locator('#panel-'+b.id+' input');for(const raw of ['１２３','a7b','','9999','21'])await inp.fill(raw);await ready();assert((await page.locator('#panel-'+b.id+' canvas').first().getAttribute('aria-label')).endsWith('#021'));
 for(let i=0;i<7;i++)await page.locator('#panel-'+b.id+' .stepper button').last().click();await ready();assert((await page.locator('#panel-'+b.id+' canvas').first().getAttribute('aria-label')).endsWith('#028'));
 // 回到顶部
 await page.locator('[data-page="'+a.id+'"]').click();await ready();await page.setViewportSize({width:1280,height:360});await page.mouse.move(600,300);await page.mouse.wheel(0,800);await page.waitForFunction(()=>document.getElementById('toTop').classList.contains('show'));await page.locator('#toTop').click();await page.waitForFunction(()=>scrollY===0);await page.setViewportSize({width:1280,height:900});
 for(const s of catalog){await page.locator('[data-page="'+s.id+'"]').click();await ready();await page.screenshot({path:path.join(out,s.id+'-预览.png')})}
 // 历史款 A–F 与最早的独立编辑器逐像素一致（仅本机有历史备份时）
 let equivalent=0;
 if(fs.existsSync(legacyReference)){
  const old=await context.newPage();await old.goto(pathToFileURL(legacyReference).href);await old.evaluate(()=>document.fonts.ready);
  for(const s of catalog)for(const e of s.entries.filter(e=>e.renderer==='legacy'))for(const ratio of ['16:9','4:3']){
   const original=await old.evaluate(({k,r})=>renderPNG(k,r,'002'),{k:e.legacyKey,r:ratio});
   const current=await page.evaluate(({s,id,r})=>window.__studio.renderFull(s,id,r,'002'),{s:s.id,id:e.id,r:ratio});
   assert.equal(current,original,'旧款渲染改变 '+e.id+' '+ratio);equivalent++}
  await old.close();
 }
 // 手机宽度不横向溢出
 await page.setViewportSize({width:390,height:844});for(const s of catalog){await page.locator('[data-page="'+s.id+'"]').click();await ready();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(out,s.id+'-手机预览.png')})}
 assert.deepEqual(errors,[]);
 const report={passed:true,checkedAt:new Date().toISOString(),offline:true,firstPageMs,legacyPixelEquivalent:equivalent,JPG:exports,stepper3Digit:true,independentNumbers:true,maxRowsPerPage:4,backToTop:true,mobileNoOverflow:true,errors};
 fs.writeFileSync(path.join(out,'验证结果.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:true,firstPageMs,jpg:exports.length,legacyPixelEquivalent:equivalent,errors}));
}finally{await browser.close()}})().catch(e=>{console.error(String(e.stack||e).slice(0,2000));process.exitCode=1});
