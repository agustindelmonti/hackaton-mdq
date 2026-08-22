// Pasada de UI: mide los blancos táctiles y el contraste del texto chico.
import { chromium } from "playwright";
const CRED={ernesto:"brote-8039",cecilia:"camara-1440",ruben:"semilla-9654",marcos:"campania-9443",dalia:"spunta-9785",nestor:"spunta-5546"};
const U=process.env.U||"marcos", W=+(process.env.W||390), H=+(process.env.H||844);
const b=await chromium.launch();
const p=await b.newPage({viewport:{width:W,height:H},isMobile:W<600,hasTouch:W<600});
await p.goto("http://localhost:5210/",{waitUntil:"domcontentloaded"});
await p.waitForSelector("input",{timeout:30000}).catch(()=>{});
await p.locator("input").first().fill(U);
await p.locator('input[type="password"]').first().fill(CRED[U]);
await p.keyboard.press("Enter");
await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
await p.waitForTimeout(3500);
const r = await p.evaluate(()=>{
  const chicos=[], flojos=[];
  const lum=(c)=>{const m=c.match(/[\d.]+/g)||[0,0,0];const f=m.slice(0,3).map(v=>{v=v/255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4);});return .2126*f[0]+.7152*f[1]+.0722*f[2];};
  const fondoDe=(el)=>{let e=el;while(e){const bg=getComputedStyle(e).backgroundColor;const m=bg&&bg.match(/[\d.]+/g);const a=m&&m.length>3?parseFloat(m[3]):1;if(bg&&a>=0.5)return bg;e=e.parentElement;}return "rgb(255,255,255)";};
  for (const el of document.querySelectorAll("button,a[href],input,select,textarea,[role=button]")) {
    const r=el.getBoundingClientRect();
    if (r.width===0||r.height===0) continue;
    if (r.height < 44 || r.width < 44) chicos.push({t:(el.innerText||el.getAttribute("aria-label")||el.tagName).replace(/\s+/g," ").slice(0,42), w:Math.round(r.width), h:Math.round(r.height)});
  }
  for (const el of document.querySelectorAll("p,span,dd,dt,li,h1,h2,h3,label")) {
    if (!el.innerText || el.children.length) continue;
    const cs=getComputedStyle(el); const px=parseFloat(cs.fontSize);
    const L1=lum(cs.color), L2=lum(fondoDe(el));
    const cr=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const min = px>=18.66 || (px>=14 && cs.fontWeight>=700) ? 3 : 4.5;
    if (cr < min) flojos.push({t:el.innerText.replace(/\s+/g," ").slice(0,40), px:Math.round(px*10)/10, cr:Math.round(cr*100)/100});
  }
  return {chicos, flojos:flojos.slice(0,20), totalFlojos:flojos.length};
});
console.log("BLANCOS <44px:", r.chicos.length);
for (const c of r.chicos.slice(0,14)) console.log("  ", c.w+"x"+c.h, "|", c.t);
console.log("CONTRASTE bajo:", r.totalFlojos);
for (const f of r.flojos.slice(0,12)) console.log("  ", f.cr, f.px+"px", "|", f.t);
await b.close();
