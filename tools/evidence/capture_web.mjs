import { chromium, devices } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
const dir = 'preuves/web'; await mkdir(dir, { recursive: true });
const report={date:new Date().toISOString(),screens:[],checks:[]};
const browser=await chromium.launch({headless:true});
try {
 const desktop=await browser.newContext({viewport:{width:1440,height:900}});
 for(const [route,file] of [['/','accueil.png'],['/programme','programme.png'],['/recherche','recherche.png'],['/ma-reservation','suivi.png'],['/login','connexion.png']]){
  const page=await desktop.newPage();
  try {
   const response=await page.goto('https://cooperative-opal.vercel.app'+route,{waitUntil:'domcontentloaded',timeout:90000});
   await page.waitForTimeout(4000);
   const text=(await page.locator('body').innerText()).trim();
   const ok=response?.status()<400 && text.length>40;
   if(ok){await page.screenshot({path:dir+'/'+file,fullPage:true});report.screens.push({route,file,status:response.status()});}
   report.checks.push({route,status:response?.status(),ok,excerpt:text.slice(0,180)});
  }catch(e){report.checks.push({route,ok:false,error:String(e)});}
  await page.close();
 }
 await desktop.close();
 const mobile=await browser.newContext({...devices['iPhone 13']});
 const p=await mobile.newPage();
 try {const response=await p.goto('https://cooperative-opal.vercel.app/',{waitUntil:'domcontentloaded',timeout:90000});await p.waitForTimeout(4000);await p.screenshot({path:dir+'/responsive_iphone.png',fullPage:true});report.screens.push({route:'/',file:'responsive_iphone.png',status:response?.status(),note:'Site web responsive, pas Flutter'});}
 catch(e){report.checks.push({route:'responsive',ok:false,error:String(e)});}
 await p.close();await mobile.close();
 const api=await browser.newContext();
 try {const r=await api.request.get('https://cooperative-api-3yuz.onrender.com/openapi.json',{timeout:120000});report.checks.push({route:'OpenAPI FastAPI',status:r.status(),ok:r.ok()});}
 catch(e){report.checks.push({route:'OpenAPI FastAPI',ok:false,error:String(e)});}
 await api.close();
}finally{await browser.close();await writeFile(dir+'/rapport.json',JSON.stringify(report,null,2));}