import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import warnings

# Silencia o aviso do pandas sobre formatos de data mistos (a conversão continua a mesma)
warnings.filterwarnings("ignore", message="Could not infer format", category=UserWarning)

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("America/Fortaleza")
except Exception:  # fallback caso o fuso não esteja disponível
    _TZ = None

st.set_page_config(page_title="Análise de Operações SCENA", page_icon="🛫", layout="wide")


# =====================================================================
# 🎨 CAMADA VISUAL (somente apresentação – não altera a lógica)
# =====================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root{
  --pista:#13233A;      /* azul pista */
  --pista-2:#1D3352;
  --ambar:#F2B705;      /* âmbar dos painéis de voo */
  --concreto:#E9EDF1;   /* pátio */
  --tinta:#1B2430;
  --neblina:#5E6B7A;
  --sinal:#C8322B;      /* violação */
  --taxi:#1F8A5B;       /* ok */
}

.stApp, .stApp p, .stApp li, .stApp label, .stMarkdown { font-family:'IBM Plex Sans', system-ui, sans-serif; }
.block-container{ padding-top:1.6rem; max-width:1280px; }

/* ---------- HERO: painel de informações de voo ---------- */
.scena-hero{
  background:var(--pista);
  border-radius:14px;
  padding:34px 34px 26px;
  margin-bottom:30px;
  position:relative;
  overflow:hidden;
}
.scena-hero::after{            /* faixa de eixo de pista */
  content:""; position:absolute; left:0; right:0; bottom:0; height:6px;
  background:repeating-linear-gradient(90deg,var(--ambar) 0 38px,transparent 38px 64px);
  opacity:.85;
}
.scena-board{ display:flex; flex-wrap:wrap; gap:14px 22px; }
.scena-word{ display:inline-flex; gap:4px; white-space:nowrap; }
.flap{
  display:inline-flex; align-items:center; justify-content:center;
  width:1.02em; height:1.34em;
  font-family:'Barlow Condensed', sans-serif; font-weight:600;
  font-size:clamp(26px,4.1vw,50px); line-height:1;
  color:var(--ambar);
  background:linear-gradient(180deg,#0E1A2C 0 49%,#0A1422 51% 100%);
  border-radius:5px;
  box-shadow:inset 0 -1px 0 rgba(255,255,255,.04);
  position:relative;
  animation:flip .55s cubic-bezier(.3,.7,.2,1) both;
}
.flap::before{ content:""; position:absolute; left:0; right:0; top:50%; height:1px; background:rgba(0,0,0,.55); }
@keyframes flip{ 0%{transform:rotateX(90deg); opacity:0;} 100%{transform:rotateX(0); opacity:1;} }
@media (prefers-reduced-motion: reduce){ .flap{ animation:none; } }
.scena-sub{ color:#C9D3DF !important; font-size:15px; margin:20px 0 4px; max-width:70ch; }

/* ---------- Área de upload ---------- */
.up-titulo{ font-size:17px; color:var(--tinta); margin:4px 0 2px; }
.up-titulo strong{ color:var(--sinal); }
.up-nota{ color:var(--neblina); font-size:14.5px; margin:0 0 8px; }
[data-testid="stFileUploaderDropzone"]{
  border:1.5px dashed var(--pista-2) !important;
  border-radius:12px !important;
}
[data-testid="stDownloadButton"] button{
  background:var(--ambar) !important; color:var(--pista) !important;
  border:none !important; font-weight:600 !important; border-radius:8px !important;
}
[data-testid="stDownloadButton"] button:hover{ filter:brightness(.95); }
[data-testid="stDownloadButton"] button:focus-visible{ outline:3px solid var(--pista-2) !important; outline-offset:2px; }

/* ---------- Comprovante de leitura ---------- */
.recibo{
  border-left:5px solid var(--ambar);
  background:rgba(242,183,5,.08);
  border-radius:0 10px 10px 0;
  padding:14px 18px; margin:10px 0 6px;
}
.recibo h4{ font-family:'Barlow Condensed',sans-serif; font-size:21px; margin:0 0 4px; color:inherit; }
.recibo p{ margin:0; font-size:14px; }

/* ---------- Cabeçalho de bloco (Chegada / Saída) ---------- */
.bloco{
  display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;
  background:var(--pista); color:#fff;
  border-radius:12px; padding:16px 22px; margin:36px 0 18px;
}
.bloco .nome{ font-family:'Barlow Condensed',sans-serif; font-size:30px; font-weight:600; color:#fff; }
.bloco .nome span{ color:var(--ambar); margin-right:10px; }
.bloco .total{ font-size:15px; color:#C9D3DF; }
.bloco .total b{ color:var(--ambar); font-family:'Barlow Condensed',sans-serif; font-size:28px; margin-right:6px; }

/* ---------- Painéis ---------- */
.painel{ display:flex; align-items:baseline; gap:12px; margin:28px 0 8px;
         border-bottom:2px solid var(--pista-2); padding-bottom:6px; }
.painel .n{ font-family:'Barlow Condensed',sans-serif; font-size:15px; font-weight:700;
            background:var(--pista-2); color:var(--ambar); padding:2px 10px; border-radius:4px; }
.painel .t{ font-family:'Barlow Condensed',sans-serif; font-size:25px; font-weight:600; }

.check{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin:18px 0 6px; }
.check .t{ font-size:16px; font-weight:600; }
.badge{ font-family:'Barlow Condensed',sans-serif; font-size:17px; font-weight:700;
        min-width:44px; text-align:center; padding:1px 12px; border-radius:20px; color:#fff; }
.badge.ok{ background:var(--taxi); }
.badge.viol{ background:var(--sinal); }

.ok-msg{ color:var(--taxi); font-size:14.5px; margin:2px 0 4px; }
.ok-msg::before{ content:"✓ "; font-weight:700; }
.alerta{ color:var(--sinal); font-weight:600; font-size:14.5px; margin:2px 0 6px; }
.info-box{ border:1.5px solid var(--pista-2); border-radius:10px; padding:12px 16px; font-size:15px; }
.info-box strong span{ color:var(--sinal); }

.divisor{ height:0; border:none; border-top:2px dashed var(--sinal); margin:46px 0 26px; opacity:.7; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def hero(titulo):
    palavras, i = [], 0
    for palavra in titulo.split(" "):
        letras = []
        for ch in palavra:
            letras.append(f'<span class="flap" style="animation-delay:{i * 40}ms">{ch}</span>')
            i += 1
        palavras.append(f'<span class="scena-word">{"".join(letras)}</span>')
        i += 1
    st.markdown(
        f"""
        <div class="scena-hero">
          <div class="scena-board" role="heading" aria-level="1" aria-label="{titulo}">{"".join(palavras)}</div>
          <p class="scena-sub">Validação de voos de chegada e partida e dos dados RIMA do aeroporto de Juazeiro do Norte (SBJU).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def bloco_header(icone, titulo, total):
    st.markdown(
        f'<div class="bloco"><div class="nome"><span>{icone}</span>{titulo}</div>'
        f'<div class="total"><b>{total}</b>operações verificadas</div></div>',
        unsafe_allow_html=True,
    )


def painel_header(numero, titulo):
    st.markdown(f'<div class="painel"><span class="n">Painel {numero}</span><span class="t">{titulo}</span></div>',
                unsafe_allow_html=True)


def check_header(titulo, n):
    classe = "ok" if n == 0 else "viol"
    st.markdown(f'<div class="check"><span class="t">{titulo}</span><span class="badge {classe}">{n}</span></div>',
                unsafe_allow_html=True)


def ok(msg):
    st.markdown(f'<p class="ok-msg">{msg}</p>', unsafe_allow_html=True)


def alerta(msg):
    st.markdown(f'<p class="alerta">⚠️ {msg}</p>', unsafe_allow_html=True)


def info_box(msg):
    st.markdown(f'<div class="info-box">ℹ️ {msg}</div>', unsafe_allow_html=True)


def divisor():
    st.markdown('<hr class="divisor">', unsafe_allow_html=True)


def tabela(obj):
    """Exibe DataFrame/Styler em largura total (compatível com versões novas e antigas do Streamlit)."""
    try:
        st.dataframe(obj, hide_index=True, width="stretch")
    except TypeError:
        st.dataframe(obj, hide_index=True, use_container_width=True)


def grafico(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


# =====================================================================
# 🧾 REGISTRO PARA O RELATÓRIO TXT (apenas lê os resultados já calculados)
# =====================================================================
RELATORIO = {"arquivo": None, "tipo": None, "pax": None, "blocos": []}


def novo_bloco(nome, total_ope):
    RELATORIO["blocos"].append({"nome": nome, "total": int(total_ope), "checks": []})


def _fmt_data(v):
    try:
        if pd.isna(v):
            return "–"
    except (TypeError, ValueError):
        pass
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.strftime("%d/%m/%Y")
    return str(v)


def registrar(verificacao, df_viol):
    if not RELATORIO["blocos"]:
        return
    itens = []
    for _, row in df_viol.iterrows():
        itens.append((_fmt_data(row.get("Data")), str(row.get("Id.Vuelo", "–"))))
    RELATORIO["blocos"][-1]["checks"].append({"nome": verificacao, "qtd": len(df_viol), "itens": itens})


def detectar_pax(df):
    nomes_pax = {"PAX", "PAX TOTAL", "TOTAL PAX", "PASAJEROS", "PASSAGEIROS"}
    for col in df.columns:
        if str(col).strip().upper().replace(".", "") in nomes_pax:
            base = df[df["Sit."] == "OPE"] if "Sit." in df.columns else df
            return int(pd.to_numeric(base[col], errors="coerce").fillna(0).sum())
    return None


def agora():
    return datetime.now(_TZ) if _TZ else datetime.now()


def gerar_relatorio_txt():
    momento = agora()
    total_ops = sum(b["total"] for b in RELATORIO["blocos"])

    linhas = [
        "RELATÓRIO DE VALIDAÇÕES",
        "=" * 50,
        "",
        "Sistema: Análise de Operações SCENA",
        f"Arquivo analisado: {RELATORIO['arquivo']}",
        f"Estrutura identificada: {RELATORIO['tipo']}",
        f"Leitura realizada em: {momento.strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "1. RESUMO GERAL",
        "-" * 20,
        f"Total de Operações: {total_ops:,}",
    ]
    if RELATORIO["pax"] is not None:
        linhas.append(f"Total de Passageiros: {RELATORIO['pax']:,}")
    else:
        linhas.append("Total de Passageiros: não informado no arquivo")
    for b in RELATORIO["blocos"]:
        linhas.append(f"  {b['nome']}: {b['total']:,} " + ("operação" if b["total"] == 1 else "operações"))
    linhas.append("")

    secao = 1
    voos_violados = set()
    total_checks = 0
    for b in RELATORIO["blocos"]:
        for c in b["checks"]:
            secao += 1
            total_checks += 1
            linhas.append(f"{secao}. {b['nome'].upper()} – {c['nome'].upper()}")
            linhas.append("-" * 20)
            linhas.append(f"Total de violações: {c['qtd']}")
            for data, voo in c["itens"]:
                linhas.append(f"  - {data} | {voo}")
                voos_violados.add((b["nome"], voo, data))
            linhas.append("")

    pct = (len(voos_violados) / total_ops * 100) if total_ops else 0.0
    secao += 1
    linhas += [
        f"{secao}. ESTATÍSTICAS FINAIS",
        "-" * 20,
        f"Verificações executadas: {total_checks}",
        f"Voos com alguma violação: {len(voos_violados):,}",
        f"Percentual de voos com alguma violação: {pct:.1f}%",
    ]
    nome = f"relatorio_validacoes_SCENA_{momento.strftime('%Y%m%d_%H%M')}.txt"
    return "\n".join(linhas), nome, total_ops, len(voos_violados)


# =====================================================================
# 🛫 CABEÇALHO
# =====================================================================
hero("Análise de Operações SCENA")


# ========================
# 📥 Função para carregar dados
# ========================
def carregar_voos(arquivo):
    df = pd.read_excel(arquivo, sheet_name="data")

    # Renomear coluna de data, se necessário
    if "Fecha" in df.columns:
        df.rename(columns={"Fecha": "Data"}, inplace=True)

    df = df[df["Id.Vuelo"].notna()].copy()

    # Converter colunas que existirem
    colunas_data = ["Data", "ETime", "AIBT", "F.ETime", "ALDT", "AOBT", "ATOT"]
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], dayfirst=True, errors="coerce")

    df_completo = df.copy()

    # Filtrar datas a partir de 01/02/2024, se a coluna existir
    if "Data" in df.columns:
        df = df[df["Data"].notna()]
        df = df[df["Data"] >= pd.to_datetime("2024-02-01")]

    return df, df_completo


# ========================
# 🛩️ Painel 1: ETime ≠ AIBT
# ========================
def mostrar_painel1(df):
    resultado = df[(df["Sit."] == "OPE") & (df["ETime"] != df["AIBT"])].copy()
    resultado["Data"] = resultado["Data"].dt.strftime("%d/%m/%Y")
    resultado["ETime"] = resultado["ETime"].dt.strftime("%H:%M")
    resultado["AIBT"] = resultado["AIBT"].dt.strftime("%H:%M")

    painel_header(1, "Divergência entre ETime e AIBT (a partir de 01/02/2024)")
    check_header("Divergência entre ETime e AIBT", len(resultado))
    registrar("Divergência entre ETime e AIBT", resultado)
    if resultado.empty:
        ok("Nenhuma divergência encontrada entre ETime e AIBT.")
    else:
        tabela(resultado[["Data", "Id.Vuelo", "ETime", "AIBT", "Sit."]])


# ========================
# 🛩️ Painel 2: Inconsistências Operacionais
# ========================
def mostrar_painel2(df):
    painel_header(2, "Inconsistências operacionais")

    # 1. Sit. = OPE e Est. ≠ IBK
    est_diferente = df[(df["Sit."] == "OPE") & (df["Est."].notna()) & (df["Est."] != "IBK")].copy()
    check_header("Voos operados (OPE) com estação divergente de IBK", len(est_diferente))
    registrar("Voos operados (OPE) com estação divergente de IBK", est_diferente)
    if est_diferente.empty:
        ok("Nenhum voo com Est. diferente de IBK.")
    else:
        est_diferente["Data"] = est_diferente["Data"].dt.strftime("%d/%m/%Y")
        tabela(est_diferente[["Data", "Id.Vuelo", "Sit.", "Est."]].reset_index(drop=True))

    # 2. Sit. = OPE e Stand = HOLD
    stand_hold = df[(df["Sit."] == "OPE") & (df["Stand"].notna()) & (df["Stand"].str.upper() == "HOLD")].copy()
    check_header("Stand em HOLD", len(stand_hold))
    registrar("Stand em HOLD", stand_hold)
    if stand_hold.empty:
        ok("Nenhum voo com Stand igual a HOLD.")
    else:
        stand_hold["Data"] = stand_hold["Data"].dt.strftime("%d/%m/%Y")
        tabela(stand_hold[["Data", "Id.Vuelo", "Sit.", "Stand"]].reset_index(drop=True))

    # 2.5 Verificar SV proibida em voos comerciais (não ZZZ-)
    sv_proibida_comercial = ["D", "E", "K", "N", "T", "W"]

    voos_comerciais = df[
        (df["Sit."] == "OPE") &
        (df["Id.Vuelo"].notna()) &
        (~df["Id.Vuelo"].str.startswith("ZZZ-")) &
        (df["Sv."].isin(sv_proibida_comercial))
    ].copy()

    check_header("Categoria proibida em voos comerciais", len(voos_comerciais))
    registrar("Categoria proibida em voos comerciais", voos_comerciais)

    if voos_comerciais.empty:
        ok("Nenhum voo comercial com categoria proibida.")
    else:
        voos_comerciais["Data"] = voos_comerciais["Data"].dt.strftime("%d/%m/%Y")
        tabela(voos_comerciais[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True))

    # 3. AIBT ≤ ALDT
    tempo_incoerente = df[
        df["F.ETime"].notna() & df["AIBT"].notna() & df["ALDT"].notna() &
        (df["AIBT"] <= df["ALDT"])
    ].copy()

    check_header("Calço ≤ Pouso", len(tempo_incoerente))
    registrar("Calço menor ou igual ao Pouso", tempo_incoerente)

    # Exibe a mensagem de alerta caso haja AIBT == ALDT
    if not tempo_incoerente.empty and (tempo_incoerente["AIBT"] == tempo_incoerente["ALDT"]).any():
        alerta("Atenção: Pouso = Calço. Ajuste necessário.")

    if tempo_incoerente.empty:
        ok("Nenhum voo com Calço inferior ou igual ao Pouso.")
    else:
        # Formatar
        tempo_incoerente["Data"] = tempo_incoerente["Data"].dt.strftime("%d/%m/%Y")
        tempo_incoerente["AIBT"] = tempo_incoerente["AIBT"].dt.strftime("%H:%M")
        tempo_incoerente["ALDT"] = tempo_incoerente["ALDT"].dt.strftime("%H:%M")

    # Renomear colunas para exibição
    df_exibir = tempo_incoerente.rename(columns={"AIBT": "Calço", "ALDT": "Pouso"})

    # Estilizar linha se Calço == Pouso
    def destacar_linha_igualdade(row):
        return ['background-color: #f9d6d3' if row['Calço'] == row['Pouso'] else '' for _ in row]

    styled_df = df_exibir[["Data", "Id.Vuelo", "Calço", "Pouso"]].style.apply(destacar_linha_igualdade, axis=1)

    tabela(styled_df)


# ========================
# 🛩️ Painel 3: Análise Voos AVG
# ========================
def mostrar_painel3(df):
    painel_header(3, "Análise de voos AVG")

    df_zzz = df[(df["Sit."] == "OPE") & (df["Id.Vuelo"].str.startswith("ZZZ-"))].copy()

    if df_zzz.empty:
        ok("Nenhum voo ZZZ- com Situação OPE encontrado.")
        return

    # 1. Verificar se matrícula no Id.Vuelo bate com Registro
    df_zzz["Matrícula"] = df_zzz["Id.Vuelo"].str.replace("ZZZ-", "", regex=False)
    matricula_diferente = df_zzz[df_zzz["Matrícula"] != df_zzz["Registro"]][["Id.Vuelo", "Registro", "Sv."]]
    check_header("Matrícula divergente do Registro", len(matricula_diferente))
    if matricula_diferente.empty:
        ok("Todos os voos ZZZ- têm matrícula compatível com o Registro.")
    else:
        matricula_diferente["Data"] = df_zzz["Data"].dt.strftime("%d/%m/%Y")
        tabela(matricula_diferente[["Data", "Id.Vuelo", "Registro", "Sv."]].reset_index(drop=True))
    registrar("Matrícula divergente do Registro", matricula_diferente)

    # 2. Verificar inconsistências em voos AVG (ZZZ-)

    # Categorias base proibidas para todos
    sv_proibidas_geral = ["A", "B", "C", "E", "F", "G", "H", "J", "L", "M", "N", "O", "P", "Q", "R", "S", "U", "V", "X", "Y", "Z"]

    # Proibidas para ZZZ-P (aviação geral)
    sv_proibidas_zzz_p = sv_proibidas_geral + ["W"]

    # Proibidas para ZZZ-[não P] (aviação militar)
    sv_proibidas_militar = sv_proibidas_geral + ["D", "K", "T"]

    # Filtrar DataFrame original ZZZ-
    df_zzz_p = df_zzz[df_zzz["Id.Vuelo"].str.startswith("ZZZ-P")].copy()
    df_zzz_mil = df_zzz[df_zzz["Id.Vuelo"].str.startswith("ZZZ-") & ~df_zzz["Id.Vuelo"].str.startswith("ZZZ-P")].copy()

    # Detectar inconsistentes
    zzz_p_invalidos = df_zzz_p[df_zzz_p["Sv."].isin(sv_proibidas_zzz_p)].copy()
    zzz_mil_invalidos = df_zzz_mil[df_zzz_mil["Sv."].isin(sv_proibidas_militar)].copy()

    # Juntar tudo
    zzz_inconsistentes = pd.concat([zzz_p_invalidos, zzz_mil_invalidos], ignore_index=True)

    # Exibir
    check_header("Categorias proibidas em voos AVG (ZZZ-)", len(zzz_inconsistentes))
    registrar("Categorias proibidas em voos AVG (ZZZ-)", zzz_inconsistentes)

    if zzz_inconsistentes.empty:
        ok("Nenhum voo AVG (ZZZ-) com categoria proibida.")
    else:
        zzz_inconsistentes["Data"] = zzz_inconsistentes["Data"].dt.strftime("%d/%m/%Y")
        tabela(zzz_inconsistentes[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True))

    # 3. Verificar se Id.Vuelo é idêntico a Id.Asociado
    voo_diferente_associado = df_zzz[df_zzz["Id.Vuelo"] != df_zzz["Id.Asociado"]][["Data", "Id.Vuelo", "Stand", "Id.Asociado"]].copy()

    check_header("Operações divergentes de associados", len(voo_diferente_associado))
    registrar("Operações divergentes de associados", voo_diferente_associado)

    if voo_diferente_associado.empty:
        ok("Todos os voos ZZZ- possuem Id.Asociado igual ao Id.Vuelo.")
    else:
        # Formatar Data
        voo_diferente_associado["Data"] = pd.to_datetime(voo_diferente_associado["Data"]).dt.strftime("%d/%m/%Y")

    # Substituir None/NaN por traço
    voo_diferente_associado["Id.Asociado"] = voo_diferente_associado["Id.Asociado"].fillna("–")

    # Função de estilização para a coluna "Id.Asociado"
    def colorir_associado(val):
        return "background-color: #f9d6d3" if val != "–" else ""

    # Aplicar estilo apenas na coluna "Id.Asociado"
    styled_df = voo_diferente_associado.style.map(
        colorir_associado,
        subset=["Id.Asociado"]
    )

    tabela(styled_df)


# ========================
# 📤 Painéis de Saída
# ========================
def mostrar_painel_saida(df):
    painel_header(1, "Divergência entre ETime e AOBT (a partir de 01/02/2024)")

    # ✅ Converter colunas relevantes para datetime
    for col in ["Data", "ETime", "AOBT"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # ✅ Aplicar filtro após conversão
    resultado = df[
        (df["Sit."] == "OPE") &
        (df["Data"] >= pd.to_datetime("2024-02-01")) &
        (df["ETime"] != df["AOBT"])
    ].copy()

    # ✅ Formatar para exibição
    resultado["Data"] = resultado["Data"].dt.strftime("%d/%m/%Y")
    resultado["ETime"] = resultado["ETime"].dt.strftime("%H:%M")
    resultado["AOBT"] = resultado["AOBT"].dt.strftime("%H:%M")

    check_header("Divergência entre ETime e AOBT", len(resultado))
    registrar("Divergência entre ETime e AOBT", resultado)

    if resultado.empty:
        ok("Nenhuma divergência encontrada entre ETime e AOBT.")
    else:
        tabela(resultado[["Data", "Id.Vuelo", "ETime", "AOBT"]].reset_index(drop=True))


def mostrar_painel2_saida(df):
    painel_header(2, "Inconsistências operacionais")

    # 🔧 Converter colunas de data/hora para datetime
    for col in ["Data"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # 🔧 Forçar colunas de texto para string e limpar NaNs
    df["Id.Vuelo"] = df["Id.Vuelo"].astype(str)
    df["Sv."] = df["Sv."].astype(str)

    # 1. Estação divergente de AIR
    est_diferente = df[
        (df["Sit."] == "OPE") &
        (df["Est."].notna()) &
        (df["Est."] != "AIR")
    ].copy()

    check_header("Voos operados (OPE) com estação divergente de AIR", len(est_diferente))
    registrar("Voos operados (OPE) com estação divergente de AIR", est_diferente)
    if est_diferente.empty:
        ok("Todos os voos OPE possuem estação AIR.")
    else:
        est_diferente["Data"] = est_diferente["Data"].dt.strftime("%d/%m/%Y")
        tabela(est_diferente[["Data", "Id.Vuelo", "Sit.", "Est."]].reset_index(drop=True))

    # 2. Stand = HOLD
    stand_hold = df[
        (df["Sit."] == "OPE") &
        (df["Stand"].notna()) &
        (df["Stand"].str.upper() == "HOLD")
    ].copy()

    check_header("Stand em HOLD", len(stand_hold))
    registrar("Stand em HOLD", stand_hold)
    if stand_hold.empty:
        ok("Nenhum voo com Stand igual a HOLD.")
    else:
        stand_hold["Data"] = stand_hold["Data"].dt.strftime("%d/%m/%Y")
        tabela(stand_hold[["Data", "Id.Vuelo", "Sit.", "Stand"]].reset_index(drop=True))

    # 3. Categoria proibida em voos comerciais (não ZZZ-)
    sv_proibida_comercial = ["D", "E", "K", "N", "T", "W"]
    sv_invalidos = df[
        (df["Sit."] == "OPE") &
        (df["Id.Vuelo"] != "nan") &
        (~df["Id.Vuelo"].str.startswith("ZZZ-")) &
        (df["Sv."].isin(sv_proibida_comercial))
    ].copy()

    check_header("Categoria proibida em voos comerciais", len(sv_invalidos))
    registrar("Categoria proibida em voos comerciais", sv_invalidos)
    if sv_invalidos.empty:
        ok("Nenhum voo comercial com categoria proibida.")
    else:
        sv_invalidos["Data"] = sv_invalidos["Data"].dt.strftime("%d/%m/%Y")
        tabela(sv_invalidos[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True))

    # 4. ATOT ≤ AOBT
    for col in ["ATOT", "AOBT"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    atot_aobt = df[
        (df["Sit."] == "OPE") &
        df["ATOT"].notna() &
        df["AOBT"].notna() &
        (df["ATOT"] <= df["AOBT"])
    ].copy()

    check_header("Decolagem ≤ Saída de pátio", len(atot_aobt))
    registrar("Decolagem menor ou igual a Saída de pátio", atot_aobt)

    if (atot_aobt["ATOT"] == atot_aobt["AOBT"]).any():
        alerta("Atenção: Saída de pátio = Decolagem. Ajuste necessário.")

    if atot_aobt.empty:
        ok("Nenhum voo com Decolagem inferior ou igual à Saída de pátio.")
    else:
        atot_aobt["Data"] = atot_aobt["Data"].dt.strftime("%d/%m/%Y")
        atot_aobt["ATOT"] = atot_aobt["ATOT"].dt.strftime("%H:%M")
        atot_aobt["AOBT"] = atot_aobt["AOBT"].dt.strftime("%H:%M")

        df_exibir = atot_aobt.rename(columns={
            "ATOT": "Decolagem",
            "AOBT": "Descalço (Saída de Pátio)"
        })

        def colorir_iguais(row):
            return ['background-color: #f9d6d3' if row["Decolagem"] == row["Descalço (Saída de Pátio)"] else '' for _ in row]

        df_styled = df_exibir[["Data", "Id.Vuelo", "Descalço (Saída de Pátio)", "Decolagem"]].reset_index(drop=True)
        styled_df = df_styled.style.apply(colorir_iguais, axis=1)
        tabela(styled_df)


def mostrar_painel3_saida(df):
    painel_header(3, "Análise de voos AVG (ZZZ-)")

    # Garantir que as colunas de texto estão como string
    df["Id.Vuelo"] = df["Id.Vuelo"].astype(str)
    df["Registro"] = df["Registro"].astype(str)
    df["Sv."] = df["Sv."].astype(str)
    df["Id.Asociado"] = df["Id.Asociado"].astype(str)

    # Converter a coluna de data, se necessário
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

    # 1. Filtrar voos ZZZ- com Situação OPE
    df_zzz = df[
        (df["Sit."] == "OPE") &
        (df["Id.Vuelo"] != "nan") &
        (df["Id.Vuelo"].str.startswith("ZZZ-"))
    ].copy()

    if df_zzz.empty:
        info_box("Nenhum voo AVG (ZZZ-) com Situação OPE encontrado.")
        return

    # 2. Matrícula divergente do Registro
    df_zzz["Matrícula"] = df_zzz["Id.Vuelo"].str.replace("ZZZ-", "", regex=False)
    matricula_diferente = df_zzz[df_zzz["Matrícula"] != df_zzz["Registro"]][["Id.Vuelo", "Registro", "Sv.", "Data"]].copy()

    check_header("Matrícula divergente do Registro", len(matricula_diferente))
    registrar("Matrícula divergente do Registro", matricula_diferente)
    if matricula_diferente.empty:
        ok("Todos os voos ZZZ- têm matrícula compatível com o Registro.")
    else:
        matricula_diferente["Data"] = pd.to_datetime(matricula_diferente["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        tabela(matricula_diferente[["Data", "Id.Vuelo", "Registro", "Sv."]].reset_index(drop=True))

    # 3. Categorias proibidas em voos AVG
    sv_proibidas_geral = ["A", "B", "C", "E", "F", "G", "H", "J", "L", "M", "N", "O", "P", "Q", "R", "S", "U", "V", "X", "Y", "Z"]
    sv_proibidas_zzz_p = sv_proibidas_geral + ["W"]
    sv_proibidas_militar = sv_proibidas_geral + ["D", "K", "T"]

    df_zzz_p = df_zzz[
        (df_zzz["Id.Vuelo"].str.startswith("ZZZ-P")) &
        (df_zzz["Sv."].isin(sv_proibidas_zzz_p))
    ].copy()

    df_zzz_mil = df_zzz[
        (~df_zzz["Id.Vuelo"].str.startswith("ZZZ-P")) &
        (df_zzz["Sv."].isin(sv_proibidas_militar))
    ].copy()

    zzz_inconsistentes = pd.concat([df_zzz_p, df_zzz_mil], ignore_index=True)

    check_header("Categorias proibidas em voos AVG (ZZZ-)", len(zzz_inconsistentes))
    registrar("Categorias proibidas em voos AVG (ZZZ-)", zzz_inconsistentes)
    if zzz_inconsistentes.empty:
        ok("Nenhum voo AVG (ZZZ-) com categoria proibida.")
    else:
        zzz_inconsistentes["Data"] = pd.to_datetime(zzz_inconsistentes["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        tabela(zzz_inconsistentes[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True))

    # 4. Operações divergentes de associados
    voo_diferente_associado = df_zzz[
        df_zzz["Id.Vuelo"] != df_zzz["Id.Asociado"]
    ][["Data", "Id.Vuelo", "Stand", "Id.Asociado"]].copy()

    check_header("Operações divergentes de associados", len(voo_diferente_associado))
    registrar("Operações divergentes de associados", voo_diferente_associado)
    if voo_diferente_associado.empty:
        ok("Todos os voos ZZZ- possuem Id.Asociado igual ao Id.Vuelo.")
    else:
        voo_diferente_associado["Data"] = pd.to_datetime(voo_diferente_associado["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        voo_diferente_associado["Id.Asociado"] = voo_diferente_associado["Id.Asociado"].replace("nan", "–")

        def colorir_associado(val):
            return "background-color: #f9d6d3" if val != "–" else ""

        styled_df = voo_diferente_associado.style.map(colorir_associado, subset=["Id.Asociado"])
        tabela(styled_df)


# =====================================================================
# 🚀 Execução principal – ARQUIVO SCENA
# =====================================================================
st.markdown(
    '<p class="up-titulo">📁 Faça o upload do arquivo Excel – '
    '<strong>VOOS DE CHEGADA (ÚNICO), PARTIDA (ÚNICO) OU CHEGADA/PARTIDA (CONJUNTO)</strong></p>'
    '<p class="up-nota">Utilize arquivos com os dados de <em>chegada (único)</em>, <em>partida (único)</em> '
    'ou <em>chegada/partida (conjunto)</em>. Ao final da leitura, baixe o relatório TXT como comprovante.</p>',
    unsafe_allow_html=True,
)

arquivo = st.file_uploader(
    label="Arquivo Excel SCENA", type=["xlsx", "xls"], key="arquivo_completo", label_visibility="collapsed"
)

# Espaço reservado logo abaixo do upload para o comprovante TXT
area_comprovante = st.container()

if arquivo:
    df, df_completo = carregar_voos(arquivo)
    colunas = df_completo.columns.tolist()

    tem_chegada = "AIBT" in colunas
    tem_saida_associada = any(col.startswith("Assoc.") for col in colunas)
    tem_saida_simples = "AOBT" in colunas and not tem_saida_associada and not tem_chegada

    RELATORIO["arquivo"] = arquivo.name
    RELATORIO["pax"] = detectar_pax(df_completo)
    if tem_chegada and (tem_saida_associada or tem_saida_simples):
        RELATORIO["tipo"] = "Chegada/Partida (conjunto)"
    elif tem_chegada:
        RELATORIO["tipo"] = "Chegada (único)"
    elif tem_saida_associada or tem_saida_simples:
        RELATORIO["tipo"] = "Partida (único)"

    # 📥 Painéis de Chegada
    if tem_chegada:
        total_chegada = len(df_completo[df_completo["Sit."] == "OPE"])
        bloco_header("↘", "Voos de chegada", total_chegada)
        novo_bloco("Chegada", total_chegada)
        mostrar_painel1(df)
        mostrar_painel2(df_completo)
        mostrar_painel3(df_completo)

    # 📤 Painéis de Saída com colunas associadas
    if tem_saida_associada:
        df_saida = df_completo[[col for col in colunas if col.startswith("Assoc.")]].copy()
        df_saida.columns = [col.replace("Assoc. ", "") for col in df_saida.columns]
        df_saida = df_saida.loc[:, ~df_saida.columns.duplicated()]

        total_saida = len(df_saida[df_saida["Sit."] == "OPE"])
        divisor()
        bloco_header("↗", "Voos de saída (associados)", total_saida)
        novo_bloco("Saída associados", total_saida)
        mostrar_painel_saida(df_saida)
        mostrar_painel2_saida(df_saida)
        mostrar_painel3_saida(df_saida)

    # 📤 Painéis de Saída clássica (sem assoc.)
    if tem_saida_simples:
        # Só mostra a linha divisória se também houver dados de chegada (arquivo combinado)
        if tem_chegada:
            divisor()

        total_saida = len(df_completo[df_completo["Sit."] == "OPE"])
        bloco_header("↗", "Voos de saída", total_saida)
        novo_bloco("Saída", total_saida)
        mostrar_painel_saida(df_completo)
        mostrar_painel2_saida(df_completo)
        mostrar_painel3_saida(df_completo)

    if not (tem_chegada or tem_saida_associada or tem_saida_simples):
        st.error("❌ Arquivo inválido: nenhuma estrutura de chegada ou saída reconhecida.")
    else:
        # 🧾 Comprovante de leitura em TXT
        txt, nome_txt, total_ops, n_viol = gerar_relatorio_txt()
        with area_comprovante:
            st.markdown(
                f'<div class="recibo"><h4>Leitura concluída</h4>'
                f'<p><b>{arquivo.name}</b> ({RELATORIO["tipo"]}): {total_ops:,} operações verificadas, '
                f'{n_viol:,} com alguma violação.</p></div>'.replace(",", "."),
                unsafe_allow_html=True,
            )
            st.download_button(
                "📄 Baixar comprovante de leitura (TXT)",
                data=txt.encode("utf-8"),
                file_name=nome_txt,
                mime="text/plain",
                key="download_txt_scena",
            )

else:
    info_box('<strong>Envie um arquivo Excel com os dados dos voos – <span>ANÁLISE VOOS SISTEMA SCENA</span>.</strong>')


# =====================================================================
# 📋 SEÇÃO RIMA
# =====================================================================
divisor()

st.markdown(
    '<p class="up-titulo">📁 Faça o upload do arquivo Excel – <strong>ANÁLISE RIMA (EM EXCEL)</strong></p>'
    '<p class="up-nota">Os arquivos RIMA vêm no formato CSV. Para a leitura correta, converta-os para XLSX ou XLS: '
    'Arquivo &gt; Salvar como &gt; Pasta de Trabalho do Excel.</p>',
    unsafe_allow_html=True,
)

arquivo_rima = st.file_uploader(label="Arquivo Excel RIMA", type=["xlsx", "xls"], key="rima",
                                label_visibility="collapsed")


def mostrar_painel_rima(df):
    painel_header("RIMA", "Divergência entre Calço e Toque")

    # Converter colunas de data
    for col in ["CALCO_DATA", "TOQUE_DATA", "PREVISTO_DATA"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Converter horários como string e garantir HH:MM
    for col in ["CALCO_HORARIO", "TOQUE_HORARIO"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.slice(0, 5)

    # Filtrar divergência
    divergentes = df[
        df["CALCO_DATA"].notna() &
        df["TOQUE_DATA"].notna() &
        (df["CALCO_DATA"] != df["TOQUE_DATA"])
    ].copy()

    # Criar coluna Movimento
    divergentes["Movimento"] = divergentes["MOVIMENTO_TIPO"].map({"P": "Pouso", "D": "Decolagem"})

    # Colunas auxiliares formatadas
    divergentes["Data"] = divergentes["PREVISTO_DATA"].dt.strftime("%d/%m/%Y")
    divergentes["Matrícula"] = divergentes["AERONAVE_MARCAS"]
    divergentes["Operador"] = divergentes["AERONAVE_OPERADOR"]

    divergentes["Nº Voo"] = divergentes["VOO_NUMERO"].astype(str).str.replace(",", "").str.strip()

    divergentes["Calço Aeronave"] = (
        "Calço " + divergentes["CALCO_DATA"].dt.strftime("%d/%m/%Y") +
        " – " + divergentes["CALCO_HORARIO"].astype(str).str.strip().str[:5]
    )

    divergentes["Pouso ou Decolagem"] = (
        divergentes["Movimento"] + " " +
        divergentes["TOQUE_DATA"].dt.strftime("%d/%m/%Y") +
        " – " + divergentes["TOQUE_HORARIO"].astype(str).str.strip().str[:5]
    )

    # Ordem final
    colunas_exibir = [
        "Data", "Movimento", "Matrícula", "Operador", "Nº Voo",
        "Calço Aeronave", "Pouso ou Decolagem"
    ]

    check_header("Divergência Calço ≠ Toque", len(divergentes))

    if divergentes.empty:
        ok("Nenhum voo com divergência entre CALCO_DATA e TOQUE_DATA.")
    else:
        tabela(divergentes[colunas_exibir].reset_index(drop=True))

        csv = divergentes[colunas_exibir].to_csv(index=False, sep=";", encoding="utf-8")
        st.download_button("📥 Baixar CSV (RIMA)", csv, file_name="rima_divergencias.csv", mime="text/csv")


def carregar_rima(arquivo):
    df = pd.read_excel(arquivo)
    return df, df.copy()


if arquivo_rima:
    df_rima, df_rima_completo = carregar_rima(arquivo_rima)
    mostrar_painel_rima(df_rima_completo)

    # ========================
    # 🕓 ANÁLISE DE HORÁRIO DE PICO – FILTRO MOVIMENTO + TOTAL OPERAÇÕES
    # ========================
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 5])
    with col1:
        filtro_mov = st.radio(
            "Filtrar por tipo de movimento:",
            ("Todas", "Desembarque", "Embarque"),
            horizontal=False
        )

    with col2:
        painel_header("Pico", "Análise de horário de pico – SBJU")

    try:
        if all(col in df_rima_completo.columns for col in ["CALCO_HORARIO", "PAX_LOCAL", "PAX_CONEXAO_DOMESTICO", "AERONAVE_OPERADOR", "MOVIMENTO_TIPO"]):

            # 🔹 Filtragem conforme o rádio selecionado
            if filtro_mov == "Desembarque":
                df_filtrado = df_rima_completo[df_rima_completo["MOVIMENTO_TIPO"].astype(str).str.upper().eq("P")]
            elif filtro_mov == "Embarque":
                df_filtrado = df_rima_completo[df_rima_completo["MOVIMENTO_TIPO"].astype(str).str.upper().eq("D")]
            else:
                df_filtrado = df_rima_completo.copy()

            # 🔹 Converter horário
            calco_dt = pd.to_datetime(
                df_filtrado["CALCO_HORARIO"].astype(str).str.strip(),
                format="%H:%M:%S", errors="coerce"
            )
            mask_na = calco_dt.isna()
            if mask_na.any():
                calco_dt.loc[mask_na] = pd.to_datetime(
                    df_filtrado.loc[mask_na, "CALCO_HORARIO"].astype(str).str.strip(),
                    format="%H:%M", errors="coerce"
                )
            df_filtrado["CALCO_HORARIO_NUM"] = calco_dt.dt.hour

            # 🔹 Converter PAX
            df_filtrado["PAX_LOCAL"] = pd.to_numeric(df_filtrado["PAX_LOCAL"], errors="coerce")
            df_filtrado["PAX_CONEXAO_DOMESTICO"] = pd.to_numeric(df_filtrado["PAX_CONEXAO_DOMESTICO"], errors="coerce")

            # 🔹 Filtrar apenas aviação comercial
            df_comercial = df_filtrado[df_filtrado["AERONAVE_OPERADOR"] != "GERAL"].copy()
            df_comercial["TOTAL_PAX"] = df_comercial["PAX_LOCAL"].fillna(0) + df_comercial["PAX_CONEXAO_DOMESTICO"].fillna(0)

            # 🔹 Criar faixa horária
            df_comercial["Faixa Horária"] = df_comercial["CALCO_HORARIO_NUM"].apply(
                lambda x: f"{int(x):02d}:00 - {int(x):02d}:59"
            )

            # 🔹 Agrupar por faixa e operador
            grupo_operador = (
                df_comercial.groupby(["Faixa Horária", "AERONAVE_OPERADOR"])["TOTAL_PAX"]
                .sum()
                .reset_index()
            )

            # 🔹 Companhia top por faixa
            operador_top = grupo_operador.loc[
                grupo_operador.groupby("Faixa Horária")["TOTAL_PAX"].idxmax()
            ].rename(columns={
                "AERONAVE_OPERADOR": "Companhia Aérea",
                "TOTAL_PAX": "PAX Total Cia Aérea"
            })

            # 🔹 Totais por faixa
            analise_pico = (
                df_comercial.groupby("Faixa Horária")
                .agg(
                    Total_PAX=("TOTAL_PAX", "sum"),
                    Total_Operações=("TOTAL_PAX", "count")
                )
                .reset_index()
            )

            # 🔹 Merge final
            analise_pico = analise_pico.merge(operador_top, on="Faixa Horária", how="left")
            analise_pico = analise_pico.sort_values(by="Total_PAX", ascending=False).reset_index(drop=True)

            # 🔹 Formatar números
            analise_pico["Total_PAX"] = analise_pico["Total_PAX"].map(lambda x: f"{int(x):,}".replace(",", "."))
            analise_pico["PAX Total Cia Aérea"] = analise_pico["PAX Total Cia Aérea"].map(lambda x: f"{int(x):,}".replace(",", "."))
            analise_pico["Total_Operações"] = analise_pico["Total_Operações"].map(lambda x: f"{int(x):,}".replace(",", "."))

            # 🔹 Renomear colunas
            analise_pico.rename(columns={
                "Total_PAX": "Total PAX",
                "Total_Operações": "Total de Operações"
            }, inplace=True)

            # 🔹 Exibir tabela
            tabela(analise_pico)

            # 🔹 Gráfico interativo (Plotly)
            analise_plot = analise_pico.copy()
            analise_plot["Total PAX"] = analise_plot["Total PAX"].str.replace(".", "").astype(int)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=analise_plot["Faixa Horária"],
                y=analise_plot["Total PAX"],
                text=[f"{v:,.0f}".replace(",", ".") for v in analise_plot["Total PAX"]],
                textposition="outside",
                marker=dict(color="#1D3352", line=dict(color="#F2B705", width=1.5)),
                hovertemplate="<b>%{x}</b><br>Total PAX: %{text}<extra></extra>"
            ))

            fig.update_layout(
                title=dict(
                    text=f"Horário de pico – total de passageiros ({filtro_mov})",
                    x=0.5,
                    xanchor="center",
                    font=dict(size=20, color="#13233A", family="Barlow Condensed, sans-serif")
                ),
                font=dict(family="IBM Plex Sans, sans-serif", color="#1B2430"),
                xaxis=dict(title="Faixa horária", tickangle=-45),
                yaxis=dict(title="Total de passageiros", showgrid=False),
                bargap=0.3,
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=500
            )

            grafico(fig)

            # 🔹 Botão para download
            csv_pico = analise_pico.to_csv(index=False, sep=";", encoding="utf-8")
            st.download_button(
                "📥 Baixar CSV – Análise de horário de pico",
                csv_pico,
                file_name=f"rima_horario_pico_{filtro_mov.lower()}.csv",
                mime="text/csv"
            )

        else:
            info_box("As colunas necessárias para a análise de horário de pico não foram encontradas no arquivo RIMA.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar a análise de horário de pico: {e}")

else:
    info_box('<strong>Envie um arquivo Excel com os dados dos voos – <span>ANÁLISE RIMA (EXCEL)</span>.</strong>')
