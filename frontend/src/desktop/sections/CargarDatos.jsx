import { useRef, useState } from "react";
import { UploadCloud, Check, ArrowRight, Sparkles, Camera , TriangleAlert } from "lucide-react";
import AngelaMark from "../../components/AngelaMark";
import FacturaFlow from "../../components/FacturaFlow";
import { api } from "../../lib/api";
import { useEmpresa } from "../../lib/useEmpresa";
import { useT } from "../../lib/i18n";

// Vista del DUEÑO: cargar los archivos de SU negocio como "cartas de
// desbloqueo" (el valor primero, el trámite después). Al soltar la planilla,
// Ángela infiere el mapeo de columnas, MUESTRA QUÉ ESTÁ ROTO ADENTRO, y espera
// el OK antes de que nada entre.
//
// El .xlsx entra como .xlsx. Antes esto decía "por ahora exportalo a CSV", que
// es exactamente el paso manual que este producto viene a sacar: el lector de
// openpyxl ya estaba en el backend y sólo faltaba dejar SUBIR el archivo.
// LAS TRES PLANILLAS QUE PAPASUD YA TIENE.
// No son "datos que estaría bueno tener": son los tres archivos que hoy viven
// en la máquina de alguien y que, cargados acá, encienden cosas concretas. La
// primera es LA del brief — la planilla de stock que editan varias personas a
// la vez y que es la base de datos de facto de la empresa.
const CARTAS = [
  {
    id: "stock", destino: "stock_semilla",
    lk_titulo: "cargar.stock_titulo", lk_valor: "cargar.stock_valor", lk_como: "cargar.stock_como",
  },
  {
    id: "conteos", destino: "deposito",
    lk_titulo: "cargar.conteos_titulo", lk_valor: "cargar.conteos_valor", lk_como: "cargar.conteos_como",
  },
  {
    id: "clientes", destino: "cuenta_corriente",
    lk_titulo: "cargar.clientes_titulo", lk_valor: "cargar.clientes_valor", lk_como: "cargar.clientes_como",
  },
];


export default function CargarDatos({ user, onArchivoCargado, onPreguntar, onAbrirAngela }) {
  const t = useT();
  const { erpSimulado } = useEmpresa();
  const [fotoAbierta, setFotoAbierta] = useState(false);
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">{t("cargar.titulo")}</h1>
          <p className="mt-1 text-[0.95rem] text-tinta-suave">
            {t("cargar.sub")}
          </p>
        </div>
        {/* P18·C: la conexión ERP, visible y HONESTA — solo el demo, que la
            declara simulada; el piloto no lleva badge (su ERP es el delta real). */}
        {erpSimulado && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-linea bg-crema px-3 py-1.5 text-[0.76rem] font-medium text-tinta-suave sombra-papel">
            <span className="h-1.5 w-1.5 rounded-full bg-salvia" />
            {t("cargar.erp_badge")}
          </span>
        )}
      </header>

      <div className="flex items-start gap-4 rounded-[var(--radius-card)] border border-violeta/15 bg-violeta/[0.04] p-5">
        <AngelaMark size={38} />
        <div>
          <p className="text-[1rem] leading-snug text-tinta">
            {t("cargar.angela_intro")}
          </p>
          {/* P38·I — el mensaje transversal, en copy y sólo en copy: el
              empleado deja de cargar a mano y de hacer cursos del ERP; le pide
              a Ángela y ella se encarga, y la corrección VUELVE al sistema por
              el delta que ya existe. Sin simular una conexión viva que acá no
              está: el badge de al lado dice que el ERP es simulado. */}
          <p className="mt-2 text-[0.92rem] font-semibold leading-snug text-violeta">
            {t("cargar.erp_atras_1")}
          </p>
          <p className="mt-1 text-[0.88rem] leading-snug text-tinta-suave">
            {t("cargar.erp_atras_2")}
          </p>
        </div>
      </div>

      {/* P10: la carta REAL — foto del comprobante → Ángela la lee, la cruza y
          la carga con tu ok. Las otras cartas quedan como estaban (honestas). */}
      <div className="rounded-[var(--radius-card)] border border-violeta/25 bg-crema p-5 sombra-papel">
        <div className="flex flex-wrap items-center gap-4">
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-violeta text-crema">
            <Camera size={20} />
          </span>
          <div className="min-w-0 flex-1">
            <h3 className="font-display text-[1.1rem] font-bold leading-tight">{t("foto.carta_titulo")}</h3>
            <p className="mt-1 text-[0.88rem] leading-snug text-tinta">{t("foto.carta_valor")}</p>
          </div>
          <button onClick={() => setFotoAbierta(true)}
            className="inline-flex items-center gap-1.5 rounded-full bg-violeta px-4 py-2 text-[0.86rem] font-semibold text-crema">
            {t("foto.carta_cta")} <ArrowRight size={14} />
          </button>
        </div>
      </div>
      {fotoAbierta && (
        <FacturaFlow onCerrar={() => setFotoAbierta(false)}
          onCargado={onArchivoCargado} onPreguntar={onPreguntar}
          onAngelaAbrir={onAbrirAngela} />
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {CARTAS.map((c) => <Carta key={c.id} carta={c} usuario={user?.nombre} onArchivoCargado={onArchivoCargado} />)}
      </div>

      <CartaLibre usuario={user?.nombre} onArchivoCargado={onArchivoCargado} />
    </div>
  );
}

// Campo libre: cualquier archivo + qué es. Si es CSV de productos, va a la zona
// de revisión (staging). Si no, lo guarda en la memoria del negocio.
function CartaLibre({ usuario, onArchivoCargado }) {
  const t = useT();
  const ref = useRef(null);
  const [file, setFile] = useState(null);
  const [desc, setDesc] = useState("");
  const [confirm, setConfirm] = useState(null);

  const enviar = async () => {
    if (!file) return;
    const n = file.name.toLowerCase();
    if (n.endsWith(".csv")) {
      const texto = await file.text();
      await api.stagingCrear(desc || file.name, texto);
      onArchivoCargado?.();  // va a "Datos pendientes"
      return;
    }
    if (n.endsWith(".xlsx") || n.endsWith(".xlsm") || n.endsWith(".xls")) {
      try {
        const info = await api.importPreviewArchivo(file, "stock_semilla", usuario);
        await api.stagingCrear(desc || file.name, info.csv);
        onArchivoCargado?.();
        return;
      } catch { /* si el Excel no se puede leer, sigue el camino de siempre */ }
    }
    const r = await api.cargarOtro(file.name, desc, usuario);
    setConfirm(r.mensaje);
    setFile(null); setDesc("");
  };

  return (
    <div className="rounded-[var(--radius-card)] border border-dashed border-linea bg-papel-hondo/30 p-5">
      <h3 className="font-display text-[1.1rem] font-bold">{t("cargar.otro_titulo")}</h3>
      <p className="mt-1 text-[0.88rem] text-tinta-suave">
        {t("cargar.otro_sub")}
      </p>
      {confirm ? (
        <div className="mt-3 flex items-start gap-2.5 rounded-xl border border-salvia/30 bg-salvia/[0.07] p-3">
          <AngelaMark size={26} /><p className="text-[0.88rem] text-tinta">{confirm}</p>
        </div>
      ) : (
        <div className="mt-3 grid gap-3 sm:grid-cols-[auto_1fr_auto] sm:items-center">
          <button onClick={() => ref.current?.click()} className="inline-flex items-center gap-2 rounded-full border border-linea bg-crema px-4 py-2 text-[0.85rem] font-semibold text-tinta-suave hover:text-tinta">
            <UploadCloud size={16} /> {file?.name || t("cargar.elegir_archivo")}
            <input ref={ref} type="file" className="hidden" onChange={(e) => setFile(e.target.files?.[0])} />
          </button>
          <input value={desc} onChange={(e) => setDesc(e.target.value)}
            placeholder={t("cargar.otro_ph")}
            className="rounded-full border border-linea bg-crema px-4 py-2 text-[0.85rem] outline-none focus:border-violeta/40" />
          <button onClick={enviar} disabled={!file}
            className="rounded-full bg-violeta px-4 py-2 text-[0.85rem] font-semibold text-crema disabled:opacity-40">
            {t("cargar.darselo")}
          </button>
        </div>
      )}
    </div>
  );
}

function Carta({ carta, usuario, onArchivoCargado }) {
  const t = useT();
  const ref = useRef(null);
  const [drag, setDrag] = useState(false);
  const [preview, setPreview] = useState(null);
  const [aviso, setAviso] = useState(null);
  const [enviando, setEnviando] = useState(false);

  // EL EXCEL ENTRA COMO EXCEL. Antes esto pedía "exportalo a CSV primero", que
  // es exactamente el paso manual que este producto viene a sacar: el lector de
  // openpyxl ya estaba en el backend y sólo faltaba dejar SUBIR el archivo.
  const tomar = async (file) => {
    if (!file) return;
    setAviso(null);
    const nombre = file.name.toLowerCase();
    const esExcel = nombre.endsWith(".xlsx") || nombre.endsWith(".xlsm") || nombre.endsWith(".xls");
    if (esExcel) {
      try {
        const info = await api.importPreviewArchivo(file, carta.destino, usuario);
        setPreview({ ...info, nombre: file.name, texto: info.csv });
      } catch {
        setAviso(t("cargar.aviso_excel_error", { nombre: file.name }));
      }
      return;
    }
    if (!nombre.endsWith(".csv")) {
      setAviso(t("cargar.aviso_no_csv", { nombre: file.name }));
      return;
    }
    const r = new FileReader();
    r.onload = async (e) => {
      const texto = String(e.target.result || "");
      try {
        const info = await api.importPreview(texto, carta.destino, usuario);
        // B6: el texto queda en el estado — el preview ahora TIENE confirmación.
        setPreview({ ...info, nombre: file.name, texto });
      } catch {
        setAviso(t("cargar.aviso_error"));
      }
    };
    r.readAsText(file);
  };

  // B6: cerrar el flujo — soltar → preview → CONFIRMAR → el mismo pipeline
  // que el campo libre (staging → "Datos pendientes"). Antes el preview verde
  // moría en un "próximamente" sin botón.
  const confirmar = async () => {
    if (!preview?.texto || enviando) return;
    setEnviando(true);
    try {
      await api.stagingCrear(`${t(carta.lk_titulo)} · ${preview.nombre}`, preview.texto);
      setPreview(null);
      onArchivoCargado?.();  // va a "Datos pendientes"
    } catch {
      setAviso(t("cargar.aviso_error"));
      setPreview(null);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="flex flex-col rounded-[var(--radius-card)] border border-linea bg-crema p-5 sombra-papel">
      <h3 className="font-display text-[1.1rem] font-bold leading-tight">{t(carta.lk_titulo)}</h3>
      <p className="mt-2 flex-1 text-[0.88rem] leading-snug text-tinta">{t(carta.lk_valor)}</p>

      {preview ? (
        <div className="mt-4 rounded-xl border border-salvia/30 bg-salvia/[0.06] p-3">
          <p className="flex items-center gap-1.5 text-[0.84rem] font-semibold text-salvia">
            <Sparkles size={14} /> {t("cargar.leyo", { nombre: carta.nombre || preview.nombre })}
          </p>
          <p className="mt-1 text-[0.8rem] text-tinta-suave">
            {t("cargar.filas_columnas", { filas: preview.total_filas, cols: preview.mapeados })}
          </p>
          <div className="mt-2 space-y-1">
            {Object.entries(preview.mapeo).filter(([, v]) => v).map(([campo, header]) => (
              <div key={campo} className="flex items-center gap-1.5 text-[0.8rem]">
                <span className="text-tinta-suave">{header}</span>
                <ArrowRight size={11} className="text-tinta-suave" />
                <span className="font-semibold text-tinta">{campo}</span>
              </div>
            ))}
          </div>
          {preview.sin_mapear?.length > 0 && (
            <p className="mt-2 text-[0.76rem] text-tinta-suave">{t("cargar.sin_reconocer", { lista: preview.sin_mapear.join(", ") })}</p>
          )}

          {/* LO QUE ESTÁ ROTO ADENTRO. Estructurar la planilla es la mitad del
              trabajo; la otra mitad es decir qué tiene mal — y con el número de
              fila del Excel, que es como lo ve el que la cargó. */}
          {preview.problemas?.length > 0 && (
            <div className="mt-3 rounded-lg border border-oro/35 bg-oro/[0.07] p-2.5">
              <p className="flex items-center gap-1.5 text-[0.82rem] font-semibold text-oro-tinta">
                <TriangleAlert size={13} /> {t("cargar.roto_titulo")}
              </p>
              <ul className="mt-1.5 space-y-1.5">
                {preview.problemas.map((x) => (
                  <li key={x.clase + x.titulo} className="text-[0.79rem] leading-snug">
                    <span className="font-semibold">{x.cantidad} · {x.titulo}</span>
                    <span className="text-tinta-suave"> — {x.detalle}</span>
                    <span className="block text-[0.72rem] text-tinta-suave">
                      {t("cargar.roto_filas", { filas: x.filas.join(", ") })}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-1.5 text-[0.74rem] text-tinta-suave">{t("cargar.roto_nota")}</p>
            </div>
          )}
          <p className="mt-2 text-[0.78rem] text-tinta-suave">{t("cargar.confirma")}</p>
          <div className="mt-2.5 flex flex-wrap gap-2">
            <button onClick={confirmar} disabled={enviando}
              className="rounded-full bg-violeta px-4 py-1.5 text-[0.82rem] font-semibold text-crema disabled:opacity-50">
              {t("cargar.confirmar_cta")}
            </button>
            <button onClick={() => setPreview(null)} disabled={enviando}
              className="rounded-full border border-linea bg-crema px-3.5 py-1.5 text-[0.82rem] font-semibold text-tinta-suave">
              {t("cargar.cancelar_cta")}
            </button>
          </div>
        </div>
      ) : aviso ? (
        <div className="mt-4 rounded-xl border border-oro/30 bg-oro/[0.08] p-3 text-[0.82rem] text-tinta">{aviso}</div>
      ) : (
        <>
          <p className="mt-3 text-[0.78rem] text-tinta-suave">{t(carta.lk_como)}</p>
          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => { e.preventDefault(); setDrag(false); tomar(e.dataTransfer.files?.[0]); }}
            onClick={() => ref.current?.click()}
            className={`mt-2 grid cursor-pointer place-items-center rounded-xl border-2 border-dashed p-5 text-center transition-colors ${drag ? "border-violeta bg-violeta/5" : "border-linea"}`}
          >
            <input ref={ref} type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={(e) => tomar(e.target.files?.[0])} />
            <UploadCloud size={22} className="text-tinta-suave" />
            <p className="mt-1.5 inline-flex items-center gap-1 text-[0.84rem] font-semibold text-violeta">
              {t("cargar.cargar_dato")} <ArrowRight size={14} />
            </p>
          </div>
        </>
      )}
    </div>
  );
}
