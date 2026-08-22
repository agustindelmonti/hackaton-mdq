import { chromium } from "playwright";
const U=process.env.U||"ernesto";
const P={ernesto:"brote-8039",cecilia:"camara-1440",ruben:"semilla-9654",marcos:"campania-9443",dalia:"spunta-9785",nestor:"spunta-5546"}[U];
const W=+(process.env.W||1600),H=+(process.env.H||1000);
const b=await chromium.launch();
const p=await b.newPage({viewport:{width:W,height:H}});
await p.goto("http://localhost:5210/",{waitUntil:"domcontentloaded"});
await p.waitForSelector("input",{timeout:30000}).catch(()=>{});
if(await p.locator("input").first().isVisible().catch(()=>false)){
  await p.locator("input").first().fill(U);
  await p.locator('input[type="password"]').first().fill(P);
  await p.keyboard.press("Enter");
}
await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
await p.waitForTimeout(2500);
if(process.env.SEC){ const btn=p.getByRole("button",{name:new RegExp(process.env.SEC,"i")}).first(); if(await btn.count()){await btn.click(); await p.waitForTimeout(4000);} }
const y=+(process.env.Y||900);
await p.mouse.move(Math.floor(+(process.env.W||1600)/2), Math.floor(+(process.env.H||1000)/2));
await p.mouse.wheel(0, y);
await p.waitForTimeout(1200);
await p.screenshot({path:`../docs/shots/${U}-${process.env.TAG||"scroll"}.png`});
await b.close();
