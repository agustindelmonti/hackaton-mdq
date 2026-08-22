import { chromium } from "playwright";
const b = await chromium.launch();
const p = await b.newPage({ viewport:{width:1600,height:1000} });
p.on("console", m=>{ if(m.text().startsWith("DBG")) console.log(m.text()); });
await p.goto("http://localhost:5210/", { waitUntil:"domcontentloaded" });
await p.waitForSelector("input",{timeout:30000}).catch(()=>{});
await p.locator("input").first().fill("ernesto");
await p.locator('input[type="password"]').first().fill("brote-8039");
await p.keyboard.press("Enter");
await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
await p.getByRole("button",{name:/mapa de la operaci/i}).first().click();
await p.waitForSelector(".react-flow__node",{timeout:20000});
await p.waitForTimeout(2000);
console.log(await p.evaluate(async ()=>{
  const m = await import("/src/lib/useEmpresa.js");
  return "mod keys " + Object.keys(m).join(",");
}));
await b.close();
