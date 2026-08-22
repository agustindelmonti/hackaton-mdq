import { chromium } from "playwright";
const W = +(process.env.W||1600), H = +(process.env.H||1000);
const b = await chromium.launch();
const p = await b.newPage({ viewport:{width:W,height:H} });
await p.goto("http://localhost:5210/", { waitUntil:"domcontentloaded" });
await p.waitForSelector("input", {timeout:30000}).catch(()=>{});
if (await p.locator("input").first().isVisible().catch(()=>false)) {
  await p.locator("input").first().fill(process.env.U||"ernesto");
  await p.locator('input[type="password"]').first().fill(process.env.P||"brote-8039");
  await p.keyboard.press("Enter");
}
await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
await p.getByRole("button",{name:/mapa de la operaci/i}).first().click();
await p.waitForSelector(".react-flow__node",{timeout:20000});
await p.waitForTimeout(2500);
const st = await p.evaluate(()=>({
  nodos: document.querySelectorAll(".react-flow__node").length,
  edges: document.querySelectorAll(".react-flow__edge").length,
  paths: [...document.querySelectorAll(".react-flow__edge-path")].map(e=>{
    const l = e.getTotalLength ? Math.round(e.getTotalLength()) : -1; return l;}),
  viewport: document.querySelector(".react-flow__viewport")?.style.transform,
}));
console.log(JSON.stringify(st));
const box = await p.locator(".react-flow").first().boundingBox();
await p.screenshot({ path:`../docs/shots/mapa-lienzo.png`, clip:{x:box.x,y:box.y-30,width:box.width,height:box.height+30} });
await b.close();
