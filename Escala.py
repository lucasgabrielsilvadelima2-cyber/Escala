import os
import time
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# =========================
# CONFIGURAÇÃO INICIAL
# =========================
st.set_page_config(page_title="WFM Atlas", layout="wide")

# =========================
# ESTILO (CSS)
# =========================
st.markdown("""
<style>
.stApp { background-color: #121212; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
h1,h2,h3,h4,h5,h6,p,span,div,label { color: #FFFFFF !important; }
[data-testid="stSidebar"] { background-color: #1E1E1E; color: #FFFFFF; border-right: 1px solid #333; }
.stButton>button { background-color: #2E8B57; color: white; border-radius: 8px; border: none; font-weight: bold; padding: 0.45em 0.9em; }
.stButton>button:hover { background-color: #3CB371; color: #fff; }
.stTextInput>div>div>input, .stTextArea>div>textarea, .stSelectbox>div>div>select { background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #333; }
[data-testid="stDataFrame"] { background-color: #1E1E1E; }
</style>
<style>
/* Calendar styles */
.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 20px; }
.cal-day-header { text-align: center; font-weight: 600; padding: 10px; color: #ddd; background: #1a1a1a; border-radius: 6px; }
.cal-day-cell { min-height: 120px; border: 2px solid #333; border-radius: 8px; padding: 8px; background: #1a1a1a; position: relative; }
.cal-day-cell.other-month { opacity: 0.4; }
.cal-day-number { position: absolute; top: 6px; right: 8px; font-size: 14px; font-weight: 600; color: #bbb; }
.cal-day-content { margin-top: 24px; font-size: 12px; line-height: 1.6; color: #fff; }
.cal-day-cell.folga { background: #e6e6e6 !important; border-color: #cfcfcf !important; }
.cal-day-cell.folga .cal-day-number { color: #000 !important; }
.cal-day-cell.folga .cal-day-content { color: #000 !important; }
.cal-day-cell.folga .cal-day-content * { color: #000 !important; }
.cal-day-cell.folga .cal-time-line { color: #000 !important; }
.cal-time-line { margin: 2px 0; }
</style>
""", unsafe_allow_html=True)

# =========================
# ARQUIVOS / PATHS
# =========================
BASE = os.getcwd()
PATH_USUARIOS = os.path.join(BASE, "usuarios.csv")
PATH_ESCALA = os.path.join(BASE, "Escala.csv")
PATH_HORA_EXTRA = os.path.join(BASE, "HoraExtra.csv")
PATH_TROCA_FOLGA = os.path.join(BASE, "TrocaFolga.csv")
PATH_NOTIFICACOES = os.path.join(BASE, "Notificacoes.csv")

def ensure_csv(path, cols):
    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8-sig")

def read_csv_safe(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except:
        return pd.DataFrame()

# Garante que todos existam
ensure_csv(PATH_USUARIOS, ["Usuario", "Senha", "Tipo"])
ensure_csv(PATH_ESCALA, ["Nome", "Data", "Horário", "Pausa"])
ensure_csv(PATH_HORA_EXTRA, ["Nome", "Dia", "Horas", "Motivo", "Status", "Aprovador"])
ensure_csv(PATH_TROCA_FOLGA, ["Nome", "Tipo", "Data Origem", "Nova Data", "Motivo", "Status", "PessoaTroca", "Aprovador"])
ensure_csv(PATH_NOTIFICACOES, ["Usuario", "Mensagem", "Status", "DataHora"])

usuarios = read_csv_safe(PATH_USUARIOS)
escala = read_csv_safe(PATH_ESCALA)
hora_extra = read_csv_safe(PATH_HORA_EXTRA)
trocas = read_csv_safe(PATH_TROCA_FOLGA)
notificacoes = read_csv_safe(PATH_NOTIFICACOES)

# =========================
# FUNÇÕES AUXILIARES
# =========================
def enviar_notificacao(usuario, msg):
    global notificacoes
    nova = {
        "Usuario": usuario,
        "Mensagem": msg,
        "Status": "Nao Lida",
        "DataHora": pd.Timestamp.now()
    }
    notificacoes = pd.concat([notificacoes, pd.DataFrame([nova])], ignore_index=True)
    notificacoes.to_csv(PATH_NOTIFICACOES, index=False, encoding="utf-8-sig")

def rerun(): st.rerun()

def logout():
    for k in list(st.session_state.keys()):
        st.session_state.pop(k, None)
    st.session_state.logado = False
    st.session_state.usuario = ""
    st.session_state.tipo = ""
    rerun()

# =========================
# LOGIN
# =========================
if "logado" not in st.session_state: st.session_state.logado = False
if "usuario" not in st.session_state: st.session_state.usuario = ""
if "tipo" not in st.session_state: st.session_state.tipo = ""

if not st.session_state.logado:
    st.title("🔐 WFM Atlas – Login")
    login = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuarios.empty:
            st.error("Nenhum usuário cadastrado no arquivo usuarios.csv")
        else:
            mask = (usuarios["Usuario"].str.lower() == login.lower()) & (usuarios["Senha"].astype(str) == senha)
            if not usuarios[mask].empty:
                st.session_state.usuario = usuarios.loc[mask, "Usuario"].values[0]
                st.session_state.tipo = usuarios.loc[mask, "Tipo"].values[0].lower()
                st.session_state.logado = True
                rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# =========================
# TOPO (Sair)
# =========================
top_container = st.container()
with top_container:
    cols = st.columns([1,1,1,1,6,1.3])
    with cols[-1]:
        if st.button("Sair", key="btn_sair_topo"):
            logout()

# =========================
# SIDEBAR MENU
# =========================
tipo_usuario = st.session_state.tipo.strip().lower()
is_gestor = tipo_usuario in ["adm", "admin", "administrador", "gestor"]

if is_gestor:
    pagina = st.sidebar.radio("Menu", ["📋 Aprovar Hora Extra", "🔁 Aprovar Trocas", "🗂 Histórico"])
else:
    pagina = st.sidebar.radio("Menu", ["📅 Escala", "🕓 Hora Extra", "🔁 Troca de Folga", "🗂 Histórico"])

st.title(f"WFM Atlas – {pagina}")

# =========================
# CONTEÚDO (AGENTE)
# =========================
if not is_gestor:
    if pagina == "📅 Escala":
        if escala.empty:
            st.info("Nenhuma escala cadastrada.")
        else:
            # Filtro por colaborador atual e tratamento de datas
            df = escala.copy()
            # Tentar parsear data no formato DD/MM/YYYY
            try:
                df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce").dt.date
            except:
                # Fallback para formato padrão
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
            df = df[df["Nome"].astype(str).str.lower() == st.session_state.usuario.lower()]

            # Seletores de mês/ano
            hoje = date.today()
            col_m, col_y = st.columns([1,1])
            with col_m:
                mes = st.selectbox("Mês", list(range(1,13)), index=(hoje.month-1))
            with col_y:
                ano = st.selectbox("Ano", list(range(hoje.year-2, hoje.year+3)), index=2)

            # Preparar mapa de entradas existentes
            por_dia = {}
            for _, r in df.iterrows():
                d = r["Data"]
                if pd.isna(d):
                    continue
                # Tentar diferentes nomes de coluna (pode ter encoding issues)
                horario_col = r.get("Horário", r.get("HorÃ¡rio", ""))
                pausa_col = r.get("Pausa", "")
                por_dia[d] = {
                    "horario": str(horario_col),
                    "pausa": str(pausa_col)
                }

            # Função para parsear horário
            def parse_horario(h):
                h = (h or "").strip()
                if "-" in h:
                    partes = h.split("-", 1)
                    return partes[0].strip(), partes[1].strip()
                return "", ""

            # Gerar calendário
            cal = calendar.Calendar(firstweekday=0)  # Segunda-feira = 0
            semanas = cal.monthdatescalendar(ano, mes)
            
            # Cabeçalho dos dias da semana
            dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            
            html = '<div class="calendar-grid">'
            
            # Cabeçalho
            for dia in dias_semana:
                html += f'<div class="cal-day-header">{dia}</div>'
            
            # Dias do calendário
            for semana in semanas:
                for dia in semana:
                    is_other_month = dia.month != mes
                    other_month_class = " other-month" if is_other_month else ""
                    
                    # Buscar dados do dia
                    entry = por_dia.get(dia, None)
                    
                    if entry:
                        horario_raw = (entry.get("horario") or "").strip()
                        pausa = (entry.get("pausa") or "").strip()
                        
                        # Detectar folga
                        is_folga = "folga" in horario_raw.lower() or "off" in horario_raw.lower()
                        folga_class = " folga" if is_folga else ""
                        
                        # Parsear horário
                        hi, hf = parse_horario(horario_raw)
                        
                        # Se for folga, mostrar "FOLGA" em preto
                        if is_folga:
                            content = '<div class="cal-day-content"><div class="cal-time-line" style="color: #000000 !important; font-weight: bold !important;">FOLGA</div></div>'
                        else:
                            # Mostrar horários (sempre mostrar os 3 campos, sem rótulos)
                            hi_display = hi if hi else "—"
                            hf_display = hf if hf else "—"
                            pausa_display = pausa if pausa and pausa != "-" else "—"
                            
                            content = f'''<div class="cal-day-content">
                                <div class="cal-time-line">{hi_display}</div>
                                <div class="cal-time-line">{hf_display}</div>
                                <div class="cal-time-line">{pausa_display}</div>
                            </div>'''
                    else:
                        # Dia sem registro
                        folga_class = ""
                        content = '<div class="cal-day-content"><div class="cal-time-line">—</div></div>'
                    
                    html += f'''<div class="cal-day-cell{other_month_class}{folga_class}">
                        <div class="cal-day-number">{dia.day}</div>
                        {content}
                    </div>'''
            
            html += '</div>'
            
            st.markdown(html, unsafe_allow_html=True)

    elif pagina == "🕓 Hora Extra":
        st.subheader("Solicitar Hora Extra")
        dia = st.date_input("Data", min_value=date(2024,1,1))

        # Dropdown de duração (15 em 15 min, máximo 2 horas)
        opcoes_min = list(range(15, 121, 15))  # 15..120
        def format_label(minutos: int) -> str:
            h, m = divmod(minutos, 60)
            if minutos == 60:
                return "1 hora"
            if minutos == 120:
                return "2 horas"
            if h == 0:
                return f"{m} min"
            return f"{h}:{m:02d} hora"

        labels = [format_label(m) for m in opcoes_min]
        label_to_minutes = {format_label(m): m for m in opcoes_min}
        label_default = format_label(60)  # 1 hora padrão
        dur_label = st.selectbox("Duração", labels, index=labels.index(label_default))
        dur_min = label_to_minutes[dur_label]

        motivo = st.text_area("Motivo")
        if st.button("Enviar Solicitação"):
            # Validação de segurança (máximo 2 horas)
            if dur_min > 120:
                st.error("A duração máxima permitida é de 2 horas.")
            else:
                horas_str = f"{dur_min//60:02d}:{dur_min%60:02d}"
                nova = pd.DataFrame([{
                    "Nome": st.session_state.usuario,
                    "Dia": dia,
                    "Horas": horas_str,
                    "Motivo": motivo,
                    "Status": "Pendente",
                    "Aprovador": ""
                }])
                hora_extra = pd.concat([hora_extra, nova], ignore_index=True)
                hora_extra.to_csv(PATH_HORA_EXTRA, index=False, encoding="utf-8-sig")
                enviar_notificacao("adm", f"Nova solicitação de hora extra de {st.session_state.usuario}")
                st.success("Solicitação enviada!")

        st.subheader("Minhas Solicitações")
        minhas = hora_extra[hora_extra["Nome"] == st.session_state.usuario]
        st.dataframe(minhas if not minhas.empty else pd.DataFrame([{"Status": "Nenhuma solicitação"}]))

    elif pagina == "🔁 Troca de Folga":
        st.subheader("Solicitar Troca de Folga / Horário")
        
        # Radio buttons para tipo de troca
        tipo = st.radio("Tipo", ["Troca de folga", "Troca de horário"], horizontal=True)
        
        data_origem = st.date_input("Data Original")
        nova_data = st.date_input("Nova Data")
        
        # Função para buscar agentes disponíveis na data selecionada
        def obter_agentes_disponiveis(data_selecionada):
            if escala.empty or pd.isna(data_selecionada):
                return []
            
            df_escala = escala.copy()
            # Tentar parsear data no formato DD/MM/YYYY
            try:
                df_escala["Data"] = pd.to_datetime(df_escala["Data"], format="%d/%m/%Y", errors="coerce").dt.date
            except:
                df_escala["Data"] = pd.to_datetime(df_escala["Data"], errors="coerce").dt.date
            
            # Filtrar pela data selecionada
            df_data = df_escala[df_escala["Data"] == data_selecionada]
            
            agentes_disponiveis = []
            for _, row in df_data.iterrows():
                nome = str(row.get("Nome", "")).strip()
                if not nome or nome.lower() == st.session_state.usuario.lower():
                    continue  # Pular o próprio usuário
                
                # Tentar diferentes nomes de coluna (pode ter encoding issues)
                horario_col = row.get("Horário", row.get("HorÃ¡rio", ""))
                horario_str = str(horario_col).strip()
                
                # Verificar se não é folga
                is_folga = "folga" in horario_str.lower() or "off" in horario_str.lower()
                if is_folga:
                    continue  # Pular folgas
                
                # Formatar horário para exibição
                if horario_str and horario_str != "nan":
                    agentes_disponiveis.append({
                        "nome": nome,
                        "horario": horario_str
                    })
            
            return agentes_disponiveis
        
        # Campo de pessoa para troca - mostra agentes disponíveis quando data é selecionada
        pessoa = None
        if nova_data:
            agentes = obter_agentes_disponiveis(nova_data)
            if agentes:
                # Criar lista de opções com nome e horário
                opcoes_agentes = [f"{ag['nome']} - {ag['horario']}" for ag in agentes]
                opcoes_agentes.insert(0, "Selecione um agente...")
                pessoa_selecionada = st.selectbox("Pessoa para troca", opcoes_agentes)
                if pessoa_selecionada and pessoa_selecionada != "Selecione um agente...":
                    # Extrair apenas o nome (antes do " - ")
                    pessoa = pessoa_selecionada.split(" - ")[0].strip()
            else:
                st.info("Nenhum agente disponível encontrado para esta data.")
                pessoa_input = st.text_input("Pessoa para troca (digite manualmente)")
                pessoa = pessoa_input.strip() if pessoa_input else None
        else:
            st.info("Selecione uma data para ver os agentes disponíveis.")
            pessoa_input = st.text_input("Pessoa para troca")
            pessoa = pessoa_input.strip() if pessoa_input else None
        
        motivo = st.text_area("Motivo")
        if st.button("Enviar Troca"):
            if not pessoa:
                st.error("Por favor, selecione ou digite uma pessoa para troca.")
            else:
                nova = pd.DataFrame([{
                    "Nome": st.session_state.usuario,
                    "Tipo": tipo,
                    "Data Origem": data_origem,
                    "Nova Data": nova_data,
                    "Motivo": motivo,
                    "Status": "Pendente",
                    "PessoaTroca": pessoa,
                    "Aprovador": ""
                }])
                trocas = pd.concat([trocas, nova], ignore_index=True)
                trocas.to_csv(PATH_TROCA_FOLGA, index=False, encoding="utf-8-sig")
                enviar_notificacao("adm", f"{st.session_state.usuario} solicitou {tipo.lower()}")
                st.success("Solicitação enviada!")

        st.subheader("Minhas Solicitações")
        minhas = trocas[trocas["Nome"] == st.session_state.usuario]
        st.dataframe(minhas if not minhas.empty else pd.DataFrame([{"Status": "Nenhuma troca enviada"}]))

    elif pagina == "🗂 Histórico":
        st.subheader("Histórico de Solicitações")
        df1 = hora_extra[hora_extra["Nome"] == st.session_state.usuario]
        df2 = trocas[trocas["Nome"] == st.session_state.usuario]
        if df1.empty and df2.empty:
            st.info("Nenhum histórico encontrado.")
        else:
            st.write("**Hora Extra:**")
            st.dataframe(df1)
            st.write("**Trocas:**")
            st.dataframe(df2)

# =========================
# CONTEÚDO (GESTOR)
# =========================
else:
    if pagina == "📋 Aprovar Hora Extra":
        st.header("Aprovação de Horas Extras")
        pend_extras = hora_extra[hora_extra["Status"].str.lower() == "pendente"]
        if pend_extras.empty:
            st.info("Nenhuma solicitação pendente.")
        for idx, row in pend_extras.iterrows():
            with st.expander(f"{row['Nome']} - {row['Dia']} ({row['Horas']}h)"):
                st.write(row["Motivo"])
                c1, c2 = st.columns(2)
                if c1.button("Aprovar", key=f"ap_extra_{idx}"):
                    hora_extra.loc[idx, ["Status","Aprovador"]] = ["Aprovado", st.session_state.usuario]
                    enviar_notificacao(row["Nome"], "Sua hora extra foi aprovada.")
                    hora_extra.to_csv(PATH_HORA_EXTRA, index=False, encoding="utf-8-sig")
                    st.success("Aprovado!")
                    rerun()
                if c2.button("Reprovar", key=f"rep_extra_{idx}"):
                    hora_extra.loc[idx, ["Status","Aprovador"]] = ["Reprovado", st.session_state.usuario]
                    enviar_notificacao(row["Nome"], "Sua hora extra foi reprovada.")
                    hora_extra.to_csv(PATH_HORA_EXTRA, index=False, encoding="utf-8-sig")
                    st.error("Reprovado!")
                    rerun()

    elif pagina == "🔁 Aprovar Trocas":
        st.header("Aprovação de Trocas de Folga / Horário")
        pend_trocas = trocas[trocas["Status"].str.lower() == "pendente"]
        if pend_trocas.empty:
            st.info("Nenhuma troca pendente.")
        for idx, row in pend_trocas.iterrows():
            with st.expander(f"{row['Nome']} - {row['Tipo']} ({row['Data Origem']} → {row['Nova Data']})"):
                st.write(row["Motivo"])
                c1, c2 = st.columns(2)
                if c1.button("Aprovar", key=f"ap_troca_{idx}"):
                    trocas.loc[idx, ["Status","Aprovador"]] = ["Aprovado", st.session_state.usuario]
                    enviar_notificacao(row["Nome"], "Sua troca foi aprovada.")
                    trocas.to_csv(PATH_TROCA_FOLGA, index=False, encoding="utf-8-sig")
                    st.success("Aprovado!")
                    rerun()
                if c2.button("Reprovar", key=f"rep_troca_{idx}"):
                    trocas.loc[idx, ["Status","Aprovador"]] = ["Reprovado", st.session_state.usuario]
                    enviar_notificacao(row["Nome"], "Sua troca foi reprovada.")
                    trocas.to_csv(PATH_TROCA_FOLGA, index=False, encoding="utf-8-sig")
                    st.error("Reprovado!")
                    rerun()

    elif pagina == "🗂 Histórico":
        st.subheader("Histórico de Solicitações")
        st.dataframe(hora_extra)
        st.dataframe(trocas)

