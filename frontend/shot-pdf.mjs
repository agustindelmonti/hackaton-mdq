import { chromium } from "playwright";
import fs from "fs";
const b = await chromium.launch();
const ctx = await b.newContext({ viewport:{width:1600,height:1000}, acceptDownloads:true });
const p = await ctx.newPage();
p.on("pageerror",e=>console.log("PAGEERROR", String(e).slice(0,200)));
await p.goto("http://localhost:5210/",{waitUntil:"domcontentloaded"});
await p.waitForSelector("input",{timeout:30000}).catch(()=>{});
await p.locator("input").first().fill("cecilia");
await p.locator('input[type="password"]').first().fill("camara-1440");
await p.keyboard.press("Enter");
await p.waitForFunction(()=>!/Leyendo tu negocio/.test(document.body.innerText),null,{timeout:60000}).catch(()=>{});
await p.waitForTimeout(2500);
await p.getByRole("button",{name:/Exportaci/i}).first().click();
await p.waitForTimeout(4500);
await p.getByRole("button",{name:/" + (process.env.DOC || "Factura proforma") + "/i}).first().click().catch(()=>{});
await p.locator("text=" + (process.env.DOC || "Factura proforma") + "").first().click().catch(()=>{});
await p.waitForTimeout(2500);
await p.screenshot({path:"../docs/shots/cecilia-exportacion.png"});
const [dl] = await Promise.all([
  p.waitForEvent("download", {timeout:30000}),
  p.getByRole("button",{name:/Descargar|PDF/i}).first().click(),
]);
const out = "../docs/shots/" + dl.suggestedFilename();
await dl.saveAs(out);
console.log("PDF:", out, fs.statSync(out).size, "bytes");
await b.close();
