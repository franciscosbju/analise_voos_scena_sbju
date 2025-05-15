import streamlit as st
import pandas as pd

st.set_page_config(page_title="Análise de Voos SBJU", layout="wide")
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin-bottom: 0;">Análise de Operações SCENA - SBJU</h1>
        </div>
        <div>
            <img src="https://i.imgur.com/YetM1cb.png" alt="Logo AENA" style="height: 80px;">
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

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

    st.markdown("## 🟥 Painel 1 – Divergência entre ETime e AIBT - A partir de 01/02/2024")
    if resultado.empty:
        st.success("Nenhuma divergência encontrada entre ETime e AIBT.")
    else:
        st.dataframe(resultado[["Data", "Id.Vuelo", "ETime", "AIBT", "Sit."]], hide_index=True, use_container_width=True)
        
# ========================
# 🛩️ Painel 2: Inconsistências Operacionais
# ========================
def mostrar_painel2(df):
    st.markdown("## 🟥 Painel 2 – Inconsistências Operacionais")

    # 1. Sit. = OPE e Est. ≠ IBK
    est_diferente = df[(df["Sit."] == "OPE") & (df["Est."].notna()) & (df["Est."] != "IBK")].copy()
    st.subheader(f"❌ Voos Operados (OPE) mas com Estação divergente de IBK ({len(est_diferente)})")
    if est_diferente.empty:
        st.success("Nenhum voo com Est. diferente de IBK.")
    else:
        est_diferente["Data"] = est_diferente["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(est_diferente[["Data", "Id.Vuelo", "Sit.", "Est."]].reset_index(drop=True), hide_index=True, use_container_width=True)
        
    # 2. Sit. = OPE e Stand = HOLD
    stand_hold = df[(df["Sit."] == "OPE") & (df["Stand"].notna()) & (df["Stand"].str.upper() == "HOLD")].copy()
    st.subheader(f"❌ Stand em HOLD ({len(stand_hold)})")
    if stand_hold.empty:
        st.success("Nenhum voo com Stand igual a HOLD.")
    else:
        stand_hold["Data"] = stand_hold["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(stand_hold[["Data", "Id.Vuelo", "Sit.", "Stand"]].reset_index(drop=True), hide_index=True, use_container_width=True)
        
    # 2.5 Verificar SV proibida em voos comerciais (não ZZZ-)
    sv_proibida_comercial = ["D", "E", "K", "N", "T", "W"]

    voos_comerciais = df[
        (df["Sit."] == "OPE") &
        (df["Id.Vuelo"].notna()) &
        (~df["Id.Vuelo"].str.startswith("ZZZ-")) &
        (df["Sv."].isin(sv_proibida_comercial))
    ].copy()

    st.subheader(f"❌ Categoria proibida em voos comerciais ({len(voos_comerciais)})")

    if voos_comerciais.empty:
        st.success("Nenhum voo comercial com categoria proibida.")
    else:
        voos_comerciais["Data"] = voos_comerciais["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            voos_comerciais[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True),
            hide_index=True,
            use_container_width=True
        )

    # 3. AIBT ≤ ALDT
    tempo_incoerente = df[
        df["F.ETime"].notna() & df["AIBT"].notna() & df["ALDT"].notna() &
        (df["AIBT"] <= df["ALDT"])
    ].copy()

    st.subheader(f"❌ Calço ≤ Pouso ({len(tempo_incoerente)})")

    # Exibe a mensagem de alerta caso haja AIBT == ALDT
    if not tempo_incoerente.empty and (tempo_incoerente["AIBT"] == tempo_incoerente["ALDT"]).any():
        st.markdown(
            '<p style="color:red; font-weight:bold;">⚠️ Atenção: Pouso = Calço - Ajuste Necessário.</p>',
            unsafe_allow_html=True
        )

    if tempo_incoerente.empty:
        st.success("Nenhum voo com Calço inferior ou Igual ao Pouso.")
    else:
        # Formatar
        tempo_incoerente["Data"] = tempo_incoerente["Data"].dt.strftime("%d/%m/%Y")
        tempo_incoerente["AIBT"] = tempo_incoerente["AIBT"].dt.strftime("%H:%M")
        tempo_incoerente["ALDT"] = tempo_incoerente["ALDT"].dt.strftime("%H:%M")

    # Renomear colunas para exibição
    df_exibir = tempo_incoerente.rename(columns={"AIBT": "Calço", "ALDT": "Pouso"})

    # Estilizar linha se Calço == Pouso
    def destacar_linha_igualdade(row):
        return ['background-color: #ffcccc' if row['Calço'] == row['Pouso'] else '' for _ in row]

    styled_df = df_exibir[["Data", "Id.Vuelo", "Calço", "Pouso"]].style.apply(destacar_linha_igualdade, axis=1)

    st.dataframe(styled_df, hide_index=True, use_container_width=True)

# ========================
# 🛩️ Painel 3: Análise Voos AVG
# ========================
def mostrar_painel3(df):
    st.markdown("## 🟥 Painel 3 – Análise Voos AVG")

    df_zzz = df[(df["Sit."] == "OPE") & (df["Id.Vuelo"].str.startswith("ZZZ-"))].copy()

    if df_zzz.empty:
        st.success("Nenhum voo ZZZ- com Situação OPE encontrado.")
        return

    # 1. Verificar se matrícula no Id.Vuelo bate com Registro
    df_zzz["Matrícula"] = df_zzz["Id.Vuelo"].str.replace("ZZZ-", "", regex=False)
    matricula_diferente = df_zzz[df_zzz["Matrícula"] != df_zzz["Registro"]][["Id.Vuelo", "Registro", "Sv."]]
    st.subheader(f"❌ Matrícula divergente do Registro ({len(matricula_diferente)})")
    if matricula_diferente.empty:
        st.success("Todos os voos ZZZ- têm matrícula compatível com o Registro.")
    else:
        matricula_diferente["Data"] = df_zzz["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(matricula_diferente[["Data", "Id.Vuelo", "Registro", "Sv."]].reset_index(drop=True), hide_index=True, use_container_width=True)

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
    st.subheader(f"❌ Categorias proibidas em voos AVG (ZZZ-) ({len(zzz_inconsistentes)})")

    if zzz_inconsistentes.empty:
        st.success("Nenhum voo AVG (ZZZ-) com categoria proibida.")
    else:
        zzz_inconsistentes["Data"] = zzz_inconsistentes["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            zzz_inconsistentes[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True),
            hide_index=True,
            use_container_width=True
        )

    # 3. Verificar se Id.Vuelo é idêntico a Id.Asociado
    voo_diferente_associado = df_zzz[df_zzz["Id.Vuelo"] != df_zzz["Id.Asociado"]][["Data", "Id.Vuelo", "Stand", "Id.Asociado"]].copy()

    st.subheader(f"❌ Operações divergentes de associados ({len(voo_diferente_associado)})")

    if voo_diferente_associado.empty:
        st.success("Todos os voos ZZZ- possuem Id.Asociado igual ao Id.Vuelo.")
    else:
    # Formatar Data
        voo_diferente_associado["Data"] = pd.to_datetime(voo_diferente_associado["Data"]).dt.strftime("%d/%m/%Y")

    # Substituir None/NaN por traço
    voo_diferente_associado["Id.Asociado"] = voo_diferente_associado["Id.Asociado"].fillna("–")

    # Função de estilização para a coluna "Id.Asociado"
    def colorir_associado(val):
        return "background-color: #ffcccc" if val != "–" else ""

    # Aplicar estilo apenas na coluna "Id.Asociado"
    styled_df = voo_diferente_associado.style.applymap(colorir_associado, subset=["Id.Asociado"])

    # Exibir DataFrame com índice oculto e layout wide
    st.dataframe(styled_df, hide_index=True, use_container_width=True)

# ========================
# 🚀 Execução principal
# ========================
st.markdown(
    """
    <div style="display: flex; align-items: center; font-size: 17px; margin-bottom: 10px;">
        <span style="font-size: 20px;">📁</span>
        <span style="margin-left: 8px;">
            Faça o upload do arquivo Excel - <strong style="color:red;">VOOS DE CHEGADA/PARTIDA</strong>
        </span>
    </div>
    <div style="color: #555; font-size: 14px; margin-top: -8px; margin-left: 30px;">
        Utilize apenas um arquivo com os dados de <em>chegada</em> e <em>partida</em> juntos.
    </div>
    """,
    unsafe_allow_html=True
)

arquivo = st.file_uploader(label="", type=["xlsx", "xls"], key="arquivo_completo")

def mostrar_painel_saida(df):
    st.markdown("## 🟥 Painel 1 – Divergência entre ETime e AOBT - A partir de 01/02/2024")

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

    if resultado.empty:
        st.success("Nenhuma divergência encontrada entre ETime e AOBT.")
    else:
        st.dataframe(
            resultado[["Data", "Id.Vuelo", "ETime", "AOBT"]].reset_index(drop=True),
            hide_index=True,
            use_container_width=True
        )

def mostrar_painel2_saida(df):
    st.markdown("## 🟥 Painel 2 – Inconsistências Operacionais")

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

    st.subheader(f"❌ Voos Operados (OPE) mas com Estação divergente de AIR ({len(est_diferente)})")
    if est_diferente.empty:
        st.success("Todos os voos OPE possuem estação AIR.")
    else:
        est_diferente["Data"] = est_diferente["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(est_diferente[["Data", "Id.Vuelo", "Sit.", "Est."]].reset_index(drop=True), hide_index=True, use_container_width=True)

    # 2. Stand = HOLD
    stand_hold = df[
        (df["Sit."] == "OPE") &
        (df["Stand"].notna()) &
        (df["Stand"].str.upper() == "HOLD")
    ].copy()

    st.subheader(f"❌ Stand = HOLD ({len(stand_hold)})")
    if stand_hold.empty:
        st.success("Nenhum voo com Stand igual a HOLD.")
    else:
        stand_hold["Data"] = stand_hold["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(stand_hold[["Data", "Id.Vuelo", "Sit.", "Stand"]].reset_index(drop=True), hide_index=True, use_container_width=True)

    # 3. Categoria proibida em voos comerciais (não ZZZ-)
    sv_proibida_comercial = ["D", "E", "K", "N", "T", "W"]
    sv_invalidos = df[
        (df["Sit."] == "OPE") &
        (df["Id.Vuelo"] != "nan") &
        (~df["Id.Vuelo"].str.startswith("ZZZ-")) &
        (df["Sv."].isin(sv_proibida_comercial))
    ].copy()

    st.subheader(f"❌ Categoria proibida em voos comerciais ({len(sv_invalidos)})")
    if sv_invalidos.empty:
        st.success("Nenhum voo comercial com categoria proibida.")
    else:
        sv_invalidos["Data"] = sv_invalidos["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(sv_invalidos[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True), hide_index=True, use_container_width=True)

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

    st.subheader(f"❌ Decolagem ≤ Saída Pátio ({len(atot_aobt)})")

    if (atot_aobt["ATOT"] == atot_aobt["AOBT"]).any():
        st.markdown(
            '<p style="color:red; font-weight:bold;">⚠️ Atenção: Saída de pátio = Decolagem - Ajuste Necessário.</p>',
            unsafe_allow_html=True
        )

    if atot_aobt.empty:
        st.success("Nenhum voo com Decolagem inferior ou igual a Saída de Pátio.")
    else:
        atot_aobt["Data"] = atot_aobt["Data"].dt.strftime("%d/%m/%Y")
        atot_aobt["ATOT"] = atot_aobt["ATOT"].dt.strftime("%H:%M")
        atot_aobt["AOBT"] = atot_aobt["AOBT"].dt.strftime("%H:%M")

        df_exibir = atot_aobt.rename(columns={
            "ATOT": "Decolagem",
            "AOBT": "Descalço (Saída de Pátio)"
        })

        def colorir_iguais(row):
            return ['background-color: #ffcccc' if row["Decolagem"] == row["Descalço (Saída de Pátio)"] else '' for _ in row]

        df_styled = df_exibir[["Data", "Id.Vuelo", "Descalço (Saída de Pátio)", "Decolagem"]].reset_index(drop=True)
        styled_df = df_styled.style.apply(colorir_iguais, axis=1)
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

def mostrar_painel3_saida(df):
    st.markdown("## 🟥 Painel 3 – Análise Voos AVG (ZZZ-)")

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
        st.info("Nenhum voo AVG (ZZZ-) com Situação OPE encontrado.")
        return

    # 2. Matrícula divergente do Registro
    df_zzz["Matrícula"] = df_zzz["Id.Vuelo"].str.replace("ZZZ-", "", regex=False)
    matricula_diferente = df_zzz[df_zzz["Matrícula"] != df_zzz["Registro"]][["Id.Vuelo", "Registro", "Sv.", "Data"]].copy()

    st.subheader(f"❌ Matrícula divergente do Registro ({len(matricula_diferente)})")
    if matricula_diferente.empty:
        st.success("Todos os voos ZZZ- têm matrícula compatível com o Registro.")
    else:
        matricula_diferente["Data"] = pd.to_datetime(matricula_diferente["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(matricula_diferente[["Data", "Id.Vuelo", "Registro", "Sv."]].reset_index(drop=True), hide_index=True, use_container_width=True)

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

    st.subheader(f"❌ Categorias proibidas em voos AVG (ZZZ-) ({len(zzz_inconsistentes)})")
    if zzz_inconsistentes.empty:
        st.success("Nenhum voo AVG (ZZZ-) com categoria proibida.")
    else:
        zzz_inconsistentes["Data"] = pd.to_datetime(zzz_inconsistentes["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(zzz_inconsistentes[["Data", "Id.Vuelo", "Sv."]].reset_index(drop=True), hide_index=True, use_container_width=True)

    # 4. Operações divergentes de associados
    voo_diferente_associado = df_zzz[
        df_zzz["Id.Vuelo"] != df_zzz["Id.Asociado"]
    ][["Data", "Id.Vuelo", "Stand", "Id.Asociado"]].copy()

    st.subheader(f"❌ Operações divergentes de associados ({len(voo_diferente_associado)})")
    if voo_diferente_associado.empty:
        st.success("Todos os voos ZZZ- possuem Id.Asociado igual ao Id.Vuelo.")
    else:
        voo_diferente_associado["Data"] = pd.to_datetime(voo_diferente_associado["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        voo_diferente_associado["Id.Asociado"] = voo_diferente_associado["Id.Asociado"].replace("nan", "–")

        def colorir_associado(val):
            return "background-color: #ffcccc" if val != "–" else ""

        styled_df = voo_diferente_associado.style.applymap(colorir_associado, subset=["Id.Asociado"])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)

if arquivo:
    df, df_completo = carregar_voos(arquivo)

    # Título para seção de chegada (exibido apenas após upload)
    st.markdown(
    """
    <h2 style="text-align: center; color: #2e7d32;">📥 Análise de Voos de Chegada</h2>
    <p style="text-align: center; color: red; font-size: 16px; margin-top: -10px;">
        Total de Operações Verificadas: <strong>{}</strong>
    </p>
    """.format(len(df_completo[df_completo["Sit."] == "OPE"])),
    unsafe_allow_html=True
)

    mostrar_painel1(df)
    mostrar_painel2(df_completo)
    mostrar_painel3(df_completo)

    # 🔄 Preparar DataFrame de saída com base nas colunas "Assoc."
    df_saida = df_completo[[col for col in df_completo.columns if col.startswith("Assoc.")]].copy()

    # Remove o prefixo "Assoc. " dos nomes das colunas
    df_saida.columns = [col.replace("Assoc. ", "") for col in df_saida.columns]

    # Remove colunas duplicadas, se houver
    df_saida = df_saida.loc[:, ~df_saida.columns.duplicated()]

    # 🔻 Linha divisória única e título de saída (em verde, centralizado)
    st.markdown(
    """
    <hr style="border: 2px dashed red; margin-top: 40px; margin-bottom: 20px;">
    <h2 style="text-align: center; color: #2e7d32;">📤 Análise de Voos de Saída (Associados)</h2>
    <p style="text-align: center; color: red; font-size: 16px; margin-top: -10px;">
        Total de Operações Verificadas: <strong>{}</strong>
    </p>
    """.format(len(df_saida[df_saida["Sit."] == "OPE"])),
    unsafe_allow_html=True
)

    # ▶️ Painéis de Saída
    mostrar_painel_saida(df_saida)
    mostrar_painel2_saida(df_saida)
    mostrar_painel3_saida(df_saida)

else:
    st.markdown(
        '<div style="background-color:#e1f5fe; padding:10px; border-radius:5px;">'
        'ℹ️ <strong>Envie um arquivo Excel com os dados dos voos – <span style="color:red;">ANÁLISE VOOS CHEGADA/PARTIDA - SCENA</span>.</strong>'
        '</div>',
        unsafe_allow_html=True
    )

# Linha divisória vermelha e tracejada para separar a seção RIMA
st.markdown(
    '<hr style="border: 2px dashed red; margin-top: 40px; margin-bottom: 20px;">',
    unsafe_allow_html=True
)

# Título personalizado da nova seção – ANÁLISE RIMA
st.markdown(
    '<span style="font-size:18px;">📁 Faça o upload do arquivo Excel – <strong style="color:red;">ANÁLISE RIMA (EM EXCEL)</strong></span>',
    unsafe_allow_html=True
)

arquivo_rima = st.file_uploader(label="", type=["xlsx", "xls"], key="rima")

def mostrar_painel_rima(df):
    st.markdown("## 📋 Análise RIMA – Divergência entre Calço e Toque")

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

    st.subheader(f"❌ Divergência Calço ≠ Toque ({len(divergentes)})")

    if divergentes.empty:
        st.success("Nenhum voo com divergência entre CALCO_DATA e TOQUE_DATA.")
    else:
        st.dataframe(divergentes[colunas_exibir].reset_index(drop=True), hide_index=True, use_container_width=True)

        csv = divergentes[colunas_exibir].to_csv(index=False, sep=";", encoding="utf-8")
        st.download_button("📥 Baixar CSV (RIMA)", csv, file_name="rima_divergencias.csv", mime="text/csv")

def carregar_rima(arquivo):
    df = pd.read_excel(arquivo)
    return df, df.copy()

if arquivo_rima:
    df_rima, df_rima_completo = carregar_rima(arquivo_rima)
    mostrar_painel_rima(df_rima_completo)

else:
    st.markdown(
        '<div style="background-color:#e1f5fe; padding:10px; border-radius:5px;">'
        'ℹ️ <strong>Envie um arquivo Excel com os dados dos voos – <span style="color:red;">ANÁLISE RIMA (EXCEL)</span>.</strong>'
        '</div>',
        unsafe_allow_html=True
    )
