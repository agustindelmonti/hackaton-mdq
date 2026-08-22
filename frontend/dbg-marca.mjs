import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport:{width:1600,height:1000} });
p.on("response", r=>{ if(r.url().includes("logos")) console.log("RES", r.status(), r.url()); });
await p.goto("http://localhost:5210/", { waitUntil:"domcontentloaded" });
await p.waitForSelector("input",{timeout:30000}).catch(()=>{});
await p.locator("input").first().fill("ernesto");
await p.locator('input[type="password"]').first().fill("brote-8039");
await p.keyboard.press("Enter");
await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
await p.getByRole("button",{name:/mapa de la operaci/i}).first().click();
await p.waitForSelector(".react-flow__node",{timeout:20000});
await p.waitForTimeout(2000);
await p.evaluate(()=>console.log("X"));
console.log(await p.evaluate(()=>{
  const n = document.querySelector('.react-flow__node[data-id="marca_papasud"]');
  return n ? n.outerHTML.slice(0,600) : "NO NODE " + [...document.querySelectorAll('.react-flow__node')].map(x=>x.dataset.id).join(",");
}));
await b.close();
