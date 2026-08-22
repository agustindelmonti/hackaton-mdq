import { chromium } from "playwright";
const CRED={ernesto:"brote-8039",cecilia:"camara-1440",ruben:"semilla-9654",marcos:"campania-9443",dalia:"spunta-9785",nestor:"spunta-5546"};
const b = await chromium.launch();
async function entrar(ctxOpts, u){
  const p = await b.newPage(ctxOpts);
  await p.goto("http://localhost:5210/",{waitUntil:"domcontentloaded"});
  await p.waitForSelector("input",{timeout:30000}).catch(()=>{});
  if(await p.locator("input").first().isVisible().catch(()=>false)){
    await p.locator("input").first().fill(u);
    await p.locator('input[type="password"]').first().fill(CRED[u]);
    await p.keyboard.press("Enter");
  }
  await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
  await p.waitForTimeout(2500);
  return p;
}
// 1) el dueño asigna
const dueno = await entrar({viewport:{width:1600,height:1000}},"ernesto");
await dueno.getByRole("button",{name:/^Equipo$/i}).first().click();
await dueno.waitForTimeout(4000);
const btn = dueno.getByRole("button",{name:/Asignar a Néstor/i}).first();
console.log("boton asignar:", await btn.count());
await btn.click();
await dueno.waitForTimeout(2500);
console.log("toast:", await dueno.evaluate(()=>document.body.innerText.match(/Listo\. .{0,80}/)?.[0]));
// 2) Néstor lo ve en el celular
const nestor = await entrar({viewport:{width:390,height:844},isMobile:true,hasTouch:true},"nestor");
const txt = await nestor.evaluate(()=>document.body.innerText);
console.log("NESTOR VE:", /Confirmar la llegada de MOV-2026-0912/.test(txt) ? "SI la tarea" : "NO aparece");
console.log(txt.split("\n").filter(Boolean).slice(0,26).join(" | "));
await nestor.screenshot({path:"../docs/shots/nestor-tarea.png"});
await b.close();
