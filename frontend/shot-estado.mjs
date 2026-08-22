import { chromium } from "playwright";
const U = process.env.U || "ernesto";
const P = { ernesto:"brote-8039", cecilia:"camara-1440", ruben:"semilla-9654",
            marcos:"campania-9443", dalia:"spunta-9785", nestor:"spunta-5546" }[U];
const W = +(process.env.W||1600), H = +(process.env.H||1000);
const SEC = process.env.SEC || "";
const TAG = process.env.TAG || "inicio";
const b = await chromium.launch();
const p = await b.newPage({ viewport:{width:W,height:H}, isMobile: W<600, hasTouch: W<600 });
const errs=[]; p.on("console",m=>{ if(m.type()==="error") errs.push(m.text().slice(0,200)); });
p.on("pageerror",e=>errs.push("PAGEERROR "+String(e).slice(0,300)));
await p.goto("http://localhost:5210/", { waitUntil:"domcontentloaded" });
await p.waitForSelector("input", {timeout:30000}).catch(()=>{});
const user = p.locator("input").first();
if (await user.isVisible().catch(()=>false)) {
  await user.click(); await user.fill(U);
  const pw = p.locator('input[type="password"]').first();
  await pw.click(); await pw.fill(P);
  console.log("CAMPOS:", await user.inputValue(), (await pw.inputValue()).length);
  await p.keyboard.press("Enter");
}
await p.waitForFunction(()=>!/Leyendo tu negocio|Reading your/.test(document.body.innerText), null, {timeout:60000}).catch(()=>console.log("TIMEOUT esperando app"));
await p.waitForTimeout(2500);
const nav = await p.evaluate(()=>[...document.querySelectorAll("nav button,nav a,aside button,header button")].map(b=>(b.innerText||"").replace(/\s+/g," ").trim()).filter(Boolean));
console.log("NAV:", JSON.stringify(nav));
if (SEC) {
  const btn = p.getByRole("button", { name: new RegExp(SEC,"i") }).first();
  if (await btn.count()) { await btn.click(); await p.waitForTimeout(4000); }
  else console.log("NO ENCONTRE seccion", SEC);
}
await p.screenshot({ path:`../docs/shots/${U}-${TAG}.png` });
console.log("ERRS:", JSON.stringify([...new Set(errs)].slice(0,10)));
await b.close();
