import requests
import streamlit as st
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

# ================== CONFIGURAÇÃO ==================
NOME_BARBEARIA = "Barbearia do Zé"
TZ = ZoneInfo("America/Sao_Paulo")
DIAS_A_FRENTE = 14
PASSO_MIN = 30  # intervalo entre os horários exibidos

# serviço: duração em minutos
SERVICOS = {
    "Corte": 30,
    "Barba": 30,
    "Corte + Barba": 60,
    "Sobrancelha": 15,
}

# WhatsApp (com 55 + DDD, só números) que recebe a confirmação
WHATSAPP_PADRAO = "5511999999999"

# dias: 0=segunda ... 6=domingo | "whatsapp" é opcional (número do profissional)
PROFISSIONAIS = {
    "João":   {"dias": [1, 2, 3, 4, 5], "inicio": "09:00", "fim": "19:00",
               "almoco": ("12:00", "13:00"), "whatsapp": "5511999999999"},
    "Carlos": {"dias": [2, 3, 4, 5], "inicio": "10:00", "fim": "20:00",
               "almoco": ("13:00", "14:00")},
}
# ==================================================

SCRIPT_URL = st.secrets["SCRIPT_URL"]
TOKEN = st.secrets.get("TOKEN", "")
DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]

st.set_page_config(page_title=f"Agendar | {NOME_BARBEARIA}", page_icon="💈", layout="centered")


def mins(txt):
    h, m = map(int, txt.split(":"))
    return h * 60 + m


def fmt(m):
    return f"{m // 60:02d}:{m % 60:02d}"


@st.cache_data(ttl=15)
def buscar_reservas():
    r = requests.get(SCRIPT_URL, timeout=20)
    r.raise_for_status()
    mapa = {}
    for x in r.json()["reservas"]:
        ini = mins(x["hora"])
        mapa.setdefault((x["data"], x["profissional"]), []).append(
            (ini, ini + int(x.get("duracao", 30))))
    return mapa


def horarios_livres(prof, dia, mapa, dur):
    cfg = PROFISSIONAIS[prof]
    if dia.weekday() not in cfg["dias"]:
        return []
    agora = datetime.now(TZ)
    agora_min = agora.hour * 60 + agora.minute
    abre, fecha = mins(cfg["inicio"]), mins(cfg["fim"])
    alm_i, alm_f = mins(cfg["almoco"][0]), mins(cfg["almoco"][1])
    bloqueios = mapa.get((dia.isoformat(), prof), [])
    livres, s = [], abre
    while s + dur <= fecha:
        e = s + dur
        no_almoco = s < alm_f and e > alm_i
        ocupado = any(s < bf and e > bi for bi, bf in bloqueios)
        passou = dia == agora.date() and s <= agora_min
        if not (no_almoco or ocupado or passou):
            livres.append(fmt(s))
        s += PASSO_MIN
    return livres


def rotulo_dia(d):
    return f"{DIAS_SEMANA[d.weekday()]}, {d:%d/%m}"


# ---------------- Interface ----------------
st.title(f"💈 {NOME_BARBEARIA}")
st.caption("Escolha o serviço, o profissional, o dia e o horário.")

try:
    mapa = buscar_reservas()
except Exception:
    st.error("Não consegui carregar a agenda. Tente novamente em instantes.")
    st.stop()

servico = st.selectbox("Serviço", list(SERVICOS), format_func=lambda s: f"{s} ({SERVICOS[s]} min)")
dur = SERVICOS[servico]
prof = st.radio("Profissional", list(PROFISSIONAIS), horizontal=True)

hoje = datetime.now(TZ).date()
dias = [hoje + timedelta(days=i) for i in range(DIAS_A_FRENTE)]
dias_com_vaga = [d for d in dias if horarios_livres(prof, d, mapa, dur)]

if not dias_com_vaga:
    st.warning(f"{prof} não tem horários livres nos próximos {DIAS_A_FRENTE} dias.")
    st.stop()

dia = st.selectbox("Dia", dias_com_vaga, format_func=rotulo_dia)
livres = horarios_livres(prof, dia, mapa, dur)

st.write("**Horários disponíveis**")
cols = st.columns(3)
for i, h in enumerate(livres):
    if cols[i % 3].button(h, key=f"h{h}", use_container_width=True):
        st.session_state["hora"] = h
        st.session_state["quando"] = (prof, dia.isoformat(), servico)

hora = None
if st.session_state.get("quando") == (prof, dia.isoformat(), servico):
    hora = st.session_state.get("hora")

if hora and hora in livres:
    st.divider()
    fim_txt = fmt(mins(hora) + dur)
    st.info(f"**{servico}** com **{prof}**\n\n{rotulo_dia(dia)}, das **{hora}** às **{fim_txt}**")
    nome = st.text_input("Seu nome")
    tel = st.text_input("Seu WhatsApp (com DDD)")
    if st.button("✅ Confirmar agendamento", type="primary", use_container_width=True):
        if not nome.strip() or len(tel.strip()) < 10:
            st.error("Preencha seu nome e WhatsApp com DDD.")
        else:
            try:
                r = requests.post(SCRIPT_URL, json={
                    "token": TOKEN, "data": dia.isoformat(), "hora": hora,
                    "profissional": prof, "cliente": nome.strip(),
                    "servico": servico, "telefone": tel.strip(), "duracao": dur,
                }, timeout=30).json()
            except Exception:
                r = {"ok": False, "erro": "Falha de conexão. Tente de novo."}
            buscar_reservas.clear()
            if r.get("ok"):
                st.session_state.pop("hora", None)
                st.success(f"Agendado! {prof}, {rotulo_dia(dia)} às {hora}. 💈")
                st.balloons()
                numero = PROFISSIONAIS[prof].get("whatsapp", WHATSAPP_PADRAO)
                msg = (f"Olá! Agendei {servico} com {prof}, {rotulo_dia(dia)} "
                       f"às {hora}. Meu nome é {nome.strip()}.")
                st.link_button("📲 Avisar no WhatsApp", f"https://wa.me/{numero}?text={quote(msg)}",
                               use_container_width=True)
            else:
                st.error(r.get("erro", "Erro ao agendar."))