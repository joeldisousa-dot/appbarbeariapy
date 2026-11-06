
import streamlit as st
import requests
import re

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote


# ============================================================
# CONFIGURAÇÕES
# ============================================================

NOME_BARBEARIA = "Barbearia Joel"
TZ = ZoneInfo("America/Sao_Paulo")

DIAS_A_FRENTE = 14
PASSO_MIN = 30

WHATSAPP_PADRAO = "5531999999999"

SCRIPT_URL = st.secrets.get("SCRIPT_URL", "").strip() if "SCRIPT_URL" in st.secrets else ""

if not SCRIPT_URL:
    st.error("Configure SCRIPT_URL nas Secrets do Streamlit.")
    st.stop()


# ============================================================
# SERVIÇOS
# ============================================================

SERVICOS = {
    "Corte Masculino": {
        "preco": 50.00,
        "duracao": 30,
        "icone": "✂️",
        "descricao": "Estilo e precisão"
    },
    "Barba": {
        "preco": 40.00,
        "duracao": 30,
        "icone": "🧔",
        "descricao": "Modelagem perfeita"
    },
    "Corte Infantil": {
        "preco": 40.00,
        "duracao": 30,
        "icone": "👦",
        "descricao": "Cuidado especial"
    },
    "Corte + Barba": {
        "preco": 80.00,
        "duracao": 60,
        "icone": "💈",
        "descricao": "Visual completo"
    },
    "Desenho no Cabelo": {
        "preco": 30.00,
        "duracao": 30,
        "icone": "🎨",
        "descricao": "Personalize seu estilo"
    }
}


# ============================================================
# PROFISSIONAIS
# ============================================================

PROFISSIONAIS = {
    "Joel": {
        "dias": [0, 1, 2, 3, 4, 5],
        "inicio": "09:00",
        "fim": "19:00",
        "almoco_inicio": "12:00",
        "almoco_fim": "13:00"
    }
}


# ============================================================
# PÁGINA
# ============================================================

st.set_page_config(
    page_title="Barbearia Joel | Agendamento",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# VISUAL
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
}

.stApp {
    background: #101010;
    color: #ffffff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #eab344 !important;
    font-weight: 800 !important;
}

p, label, span {
    color: #eeeeee;
}

.hero {
    background: linear-gradient(135deg, #202020, #090909);
    border: 1px solid #b8862b;
    border-radius: 18px;
    padding: 35px 20px;
    text-align: center;
    margin-bottom: 30px;
}

.hero-icon {
    font-size: 48px;
}

.hero-title {
    color: #eab344;
    font-size: 38px;
    font-weight: 800;
    letter-spacing: 3px;
}

.hero-subtitle {
    color: #ffffff;
    font-size: 14px;
    letter-spacing: 4px;
}

.hero-slogan {
    color: #eab344;
    font-size: 19px;
    font-style: italic;
    margin-top: 15px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #51432b;
    border-radius: 14px;
    background: #181818;
}

.stButton > button {
    border-radius: 9px;
    border: 1px solid #d9a43b;
    background: #d9a43b;
    color: #111111;
    font-weight: 700;
    min-height: 43px;
}

.stButton > button:hover {
    background: #f0c15c;
    border-color: #f0c15c;
    color: #000000;
}

.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stDateInput input {
    background: #252525;
    color: #ffffff;
    border-radius: 8px;
}

.stTextInput label,
.stSelectbox label,
.stDateInput label {
    color: #eab344 !important;
    font-weight: 600;
}

hr {
    border-color: #51432b;
}

.footer {
    text-align: center;
    color: #999999;
    font-size: 12px;
    padding: 25px 0 5px 0;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# ESTADO DO AGENDAMENTO
# ============================================================

PADROES = {
    "etapa": 1,
    "servicos": [],
    "profissional": None,
    "data": None,
    "horario": None,
    "cliente": "",
    "telefone": "",
    "confirmado": None
}

for chave, valor in PADROES.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


def ir_para(etapa):
    st.session_state.etapa = etapa


def reiniciar():
    for chave, valor in PADROES.items():
        st.session_state[chave] = valor

    for chave in [
        "selecionados_temp",
        "profissional_temp",
        "data_temp",
        "horario_temp",
        "cliente_temp",
        "telefone_temp"
    ]:
        st.session_state.pop(chave, None)

    st.rerun()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def agora():
    return datetime.now(TZ)


def minutos(horario):
    h, m = map(int, str(horario)[:5].split(":"))
    return h * 60 + m


def formatar_hora(valor):
    if isinstance(valor, datetime):
        return valor.strftime("%H:%M")

    texto = str(valor).strip()

    try:
        return datetime.strptime(texto[:5], "%H:%M").strftime("%H:%M")
    except ValueError:
        return texto[:5]


def formatar_data(valor):
    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()

    for formato in [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]:
        try:
            return datetime.strptime(texto[:19], formato).date()
        except ValueError:
            continue

    return None


def moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def telefone_valido(numero):
    return len(re.sub(r"\D", "", numero)) in (10, 11)


def sobrepoe(inicio1, fim1, inicio2, fim2):
    return inicio1 < fim2 and inicio2 < fim1


def calcular_valores(servicos):
    valor = sum(SERVICOS[n]["preco"] for n in servicos)
    duracao = sum(SERVICOS[n]["duracao"] for n in servicos)
    return valor, duracao


# ============================================================
# GOOGLE SHEETS
# ============================================================

@st.cache_data(ttl=15, show_spinner=False)
def buscar_reservas():
    try:
        resposta = requests.get(SCRIPT_URL, timeout=20)
        resposta.raise_for_status()

        dados = resposta.json()

        if isinstance(dados, list):
            return dados

        reservas = dados.get("reservas", [])

        if not isinstance(reservas, list):
            return []

        return reservas

    except requests.exceptions.Timeout:
        raise RuntimeError("O Google Apps Script demorou para responder.")

    except requests.exceptions.RequestException as erro:
        raise RuntimeError(f"Erro ao consultar a agenda: {erro}")

    except ValueError:
        raise RuntimeError("Resposta inválida do Google Apps Script.")


def reservas_do_dia(reservas, dia, profissional):
    resultado = []

    for reserva in reservas:
        data_reserva = formatar_data(reserva.get("data", ""))

        nome_profissional = str(
            reserva.get("profissional", "")
        ).strip()

        if data_reserva != dia or nome_profissional != profissional:
            continue

        try:
            inicio = minutos(formatar_hora(reserva.get("hora", "")))

            duracao = int(
                reserva.get(
                    "duracao",
                    reserva.get("duracao_min", 30)
                )
            )

            if duracao <= 0:
                duracao = 30

            resultado.append((inicio, inicio + duracao))

        except (ValueError, TypeError):
            continue

    return resultado


# ============================================================
# HORÁRIOS LIVRES
# ============================================================

def horarios_livres(dia, profissional, duracao, reservas):

    config = PROFISSIONAIS[profissional]

    if dia.weekday() not in config["dias"]:
        return []

    inicio_expediente = minutos(config["inicio"])
    fim_expediente = minutos(config["fim"])
    almoco_inicio = minutos(config["almoco_inicio"])
    almoco_fim = minutos(config["almoco_fim"])

    ocupados = reservas_do_dia(
        reservas,
        dia,
        profissional
    )

    livres = []
    atual = agora()

    for inicio in range(
        inicio_expediente,
        fim_expediente,
        PASSO_MIN
    ):
        fim = inicio + duracao

        if fim > fim_expediente:
            continue

        if sobrepoe(
            inicio,
            fim,
            almoco_inicio,
            almoco_fim
        ):
            continue

        if dia == atual.date():
            horario_atual = atual.hour * 60 + atual.minute

            if inicio <= horario_atual:
                continue

        conflito = any(
            sobrepoe(inicio, fim, oi, of)
            for oi, of in ocupados
        )

        if not conflito:
            livres.append(f"{inicio // 60:02d}:{inicio % 60:02d}")

    return livres


# ============================================================
# GRAVAR RESERVA
# ============================================================

def salvar_agendamento(
    dia,
    horario,
    profissional,
    cliente,
    servico,
    telefone,
    duracao
):
    dados = {
        "data": dia.isoformat(),
        "hora": horario,
        "profissional": profissional,
        "cliente": cliente.strip(),
        "servico": servico,
        "telefone": re.sub(r"\D", "", telefone),
        "duracao": int(duracao)
    }

    try:
        resposta = requests.post(
            SCRIPT_URL,
            json=dados,
            timeout=30
        )

        resposta.raise_for_status()
        retorno = resposta.json()

        if not isinstance(retorno, dict):
            return False, "Resposta inesperada do servidor."

        sucesso = retorno.get(
            "sucesso",
            retorno.get("success", retorno.get("ok", None))
        )

        mensagem = retorno.get(
            "mensagem",
            retorno.get("message", "Não foi possível confirmar.")
        )

        if sucesso is True:
            return True, mensagem

        if sucesso is False:
            return False, mensagem

        erro = retorno.get("erro", retorno.get("error"))

        if erro:
            return False, str(erro)

        return True, mensagem

    except requests.exceptions.Timeout:
        return False, (
            "O servidor demorou para responder. "
            "Confira a agenda antes de tentar novamente."
        )

    except requests.exceptions.RequestException as erro:
        return False, f"Erro ao enviar agendamento: {erro}"

    except ValueError:
        return False, "O servidor retornou uma resposta inválida."


# ============================================================
# CABEÇALHO FIXO
# ============================================================

st.markdown("""
<div class="hero">
    <div class="hero-icon">💈</div>
    <div class="hero-title">BARBEARIA JOEL</div>
    <div class="hero-subtitle">
        ESTILO • CONFIANÇA • BEM-ESTAR
    </div>
    <div class="hero-slogan">
        Seu visual em boas mãos!
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# INDICADOR DE ETAPAS
# ============================================================

etapas = [
    "Serviços",
    "Profissional",
    "Data e horário",
    "Seus dados",
    "Resumo"
]

st.progress(st.session_state.etapa / 5)

st.caption(
    f"ETAPA {st.session_state.etapa} DE 5 — "
    f"{etapas[st.session_state.etapa - 1]}"
)


# ============================================================
# ETAPA 1 — SERVIÇOS
# ============================================================

if st.session_state.etapa == 1:

    st.markdown("## ✂️ Nossos Serviços")

    st.write(
        "Escolha um ou mais serviços. "
        "O valor e a duração serão calculados automaticamente."
    )

    if "selecionados_temp" not in st.session_state:
        st.session_state.selecionados_temp = list(
            st.session_state.servicos
        )

    colunas = st.columns(5)

    for indice, (nome, dados) in enumerate(SERVICOS.items()):

        selecionado = nome in st.session_state.selecionados_temp

        with colunas[indice]:

            with st.container(border=True):

                st.markdown(
                    f"<div style='text-align:center;font-size:36px;'>{dados['icone']}</div>",
                    unsafe_allow_html=True
                )

                st.markdown(f"**{nome}**")
                st.caption(dados["descricao"])

                st.markdown(
                    f"### :orange[{moeda(dados['preco'])}]"
                )

                st.caption(f"{dados['duracao']} minutos")

                if st.button(
                    "✓ Selecionado" if selecionado else "+ Adicionar",
                    key=f"selecionar_{indice}",
                    use_container_width=True,
                    type="primary" if selecionado else "secondary"
                ):
                    if selecionado:
                        st.session_state.selecionados_temp.remove(nome)
                    else:
                        st.session_state.selecionados_temp.append(nome)

                    st.rerun()

    if st.session_state.selecionados_temp:

        total, tempo = calcular_valores(
            st.session_state.selecionados_temp
        )

        st.divider()
        st.markdown("### Resumo dos serviços")

        for nome in st.session_state.selecionados_temp:
            st.write(
                f"• {nome} — {moeda(SERVICOS[nome]['preco'])}"
            )

        c1, c2 = st.columns(2)

        c1.metric("Valor total", moeda(total))
        c2.metric("Duração total", f"{tempo} minutos")

    st.divider()

    if st.button(
        "CONTINUAR PARA PROFISSIONAL ➜",
        use_container_width=True,
        disabled=not st.session_state.selecionados_temp
    ):
        st.session_state.servicos = list(
            st.session_state.selecionados_temp
        )
        st.session_state.profissional = None
        st.session_state.data = None
        st.session_state.horario = None
        st.session_state.confirmado = None
        ir_para(2)
        st.rerun()


# ============================================================
# ETAPA 2 — PROFISSIONAL
# ============================================================

elif st.session_state.etapa == 2:

    st.markdown("## 👤 Escolha o profissional")

    st.write("Selecione quem realizará seu atendimento.")

    profissional_escolhido = st.selectbox(
        "Profissional",
        list(PROFISSIONAIS.keys()),
        index=(
            list(PROFISSIONAIS.keys()).index(
                st.session_state.profissional
            )
            if st.session_state.profissional in PROFISSIONAIS
            else 0
        ),
        key="profissional_temp"
    )

    with st.container(border=True):
        st.markdown("### 💈 Joel")
        st.write("Atendimento profissional e personalizado.")
        st.caption("Segunda a sábado, das 09h às 19h.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Voltar aos serviços", use_container_width=True):
            ir_para(1)
            st.rerun()

    with col2:
        if st.button("CONTINUAR ➜", use_container_width=True):
            st.session_state.profissional = profissional_escolhido
            st.session_state.data = None
            st.session_state.horario = None
            ir_para(3)
            st.rerun()


# ============================================================
# ETAPA 3 — DATA E HORÁRIO
# ============================================================

elif st.session_state.etapa == 3:

    st.markdown("## 📅 Escolha a data e o horário")

    st.write(
        "Selecione um dia e depois escolha um dos horários disponíveis."
    )

    hoje = agora().date()
    ultima_data = hoje + timedelta(days=DIAS_A_FRENTE)

    dias_validos = [
        hoje + timedelta(days=i)
        for i in range(DIAS_A_FRENTE + 1)
        if (
            hoje + timedelta(days=i)
        ).weekday() in PROFISSIONAIS[st.session_state.profissional]["dias"]
    ]

    if not dias_validos:
        st.warning("Não existem datas disponíveis.")
        st.stop()

    data_escolhida = st.date_input(
        "Data do atendimento",
        value=(
            st.session_state.data
            if st.session_state.data in dias_validos
            else dias_validos[0]
        ),
        min_value=hoje,
        max_value=ultima_data,
        key="data_temp"
    )

    profissional = st.session_state.profissional
    _, duracao = calcular_valores(st.session_state.servicos)

    horarios = []

    if data_escolhida.weekday() not in PROFISSIONAIS[profissional]["dias"]:

        st.warning("O profissional não atende nesta data.")

    else:

        try:
            with st.spinner("Consultando disponibilidade..."):
                reservas = buscar_reservas()

            horarios = horarios_livres(
                data_escolhida,
                profissional,
                duracao,
                reservas
            )

        except RuntimeError as erro:
            st.error(str(erro))

    horario_escolhido = None

    if horarios:

        st.success(f"{len(horarios)} horário(s) disponível(is).")

        if (
            st.session_state.horario in horarios
            and st.session_state.data == data_escolhida
        ):
            indice_horario = horarios.index(st.session_state.horario)
        else:
            indice_horario = 0

        horario_escolhido = st.radio(
            "Horários disponíveis",
            horarios,
            index=indice_horario,
            horizontal=True,
            key="horario_temp"
        )

    elif data_escolhida.weekday() in PROFISSIONAIS[profissional]["dias"]:

        st.warning(
            "Não há horários disponíveis para essa combinação de serviços."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Voltar", use_container_width=True):
            ir_para(2)
            st.rerun()

    with col2:
        if st.button(
            "CONTINUAR ➜",
            use_container_width=True,
            disabled=not horario_escolhido
        ):
            st.session_state.data = data_escolhida
            st.session_state.horario = horario_escolhido
            ir_para(4)
            st.rerun()


# ============================================================
# ETAPA 4 — DADOS DO CLIENTE
# ============================================================

elif st.session_state.etapa == 4:

    st.markdown("## 👤 Seus dados")

    st.write(
        "Informe seus dados para registrar o agendamento."
    )

    cliente = st.text_input(
        "Nome completo",
        value=st.session_state.cliente,
        placeholder="Digite seu nome",
        key="cliente_temp"
    )

    telefone = st.text_input(
        "Telefone / WhatsApp",
        value=st.session_state.telefone,
        placeholder="(31) 99999-9999",
        max_chars=20,
        key="telefone_temp"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Voltar", use_container_width=True):
            ir_para(3)
            st.rerun()

    with col2:
        if st.button(
            "CONTINUAR PARA RESUMO ➜",
            use_container_width=True
        ):

            if not cliente.strip():
                st.error("Informe seu nome completo.")

            elif not telefone_valido(telefone):
                st.error("Informe um telefone válido com DDD.")

            else:
                st.session_state.cliente = cliente.strip()
                st.session_state.telefone = telefone
                ir_para(5)
                st.rerun()


# ============================================================
# ETAPA 5 — RESUMO E CONFIRMAÇÃO
# ============================================================

elif st.session_state.etapa == 5:

    st.markdown("## 🧾 Resumo do agendamento")

    valor_total, duracao = calcular_valores(
        st.session_state.servicos
    )

    servico = " + ".join(st.session_state.servicos)

    with st.container(border=True):

        st.markdown("### Serviços escolhidos")

        for nome in st.session_state.servicos:
            dados = SERVICOS[nome]

            st.write(
                f"{dados['icone']} **{nome}** — "
                f"{moeda(dados['preco'])}"
            )

        st.divider()

        st.write(f"**Serviços:** {servico}")
        st.write(f"**Profissional:** {st.session_state.profissional}")
        st.write(f"**Data:** {st.session_state.data.strftime('%d/%m/%Y')}")
        st.write(f"**Horário:** {st.session_state.horario}")
        st.write(f"**Cliente:** {st.session_state.cliente}")
        st.write(f"**Telefone:** {st.session_state.telefone}")
        st.write(f"**Duração total:** {duracao} minutos")

        st.markdown(
            f"### :orange[Valor total: {moeda(valor_total)}]"
        )

    if st.session_state.confirmado:

        confirmado = st.session_state.confirmado

        st.success("🎉 Agendamento confirmado!")

        mensagem_whatsapp = (
            f"Olá! Meu agendamento na {NOME_BARBEARIA} "
            f"foi registrado.\n\n"
            f"Nome: {confirmado['cliente']}\n"
            f"Serviços: {confirmado['servico']}\n"
            f"Data: {confirmado['data']}\n"
            f"Horário: {confirmado['horario']}\n"
            f"Profissional: {confirmado['profissional']}\n"
            f"Duração: {confirmado['duracao']} minutos\n"
            f"Valor total: {moeda(confirmado['valor'])}"
        )

        st.link_button(
            "📲 CONTINUAR PELO WHATSAPP",
            gerar_whatsapp(WHATSAPP_PADRAO, mensagem_whatsapp),
            use_container_width=True
        )

        if st.button("Fazer novo agendamento", use_container_width=True):
            reiniciar()

    else:

        col1, col2 = st.columns(2)

        with col1:
            if st.button("← Voltar aos dados", use_container_width=True):
                ir_para(4)
                st.rerun()

        with col2:
            confirmar = st.button(
                "✅ CONFIRMAR AGENDAMENTO",
                use_container_width=True
            )

        if confirmar:

            buscar_reservas.clear()

            try:
                reservas_atualizadas = buscar_reservas()

                horarios_atualizados = horarios_livres(
                    st.session_state.data,
                    st.session_state.profissional,
                    duracao,
                    reservas_atualizadas
                )

            except RuntimeError as erro:
                st.error(str(erro))
                horarios_atualizados = []

            if st.session_state.horario not in horarios_atualizados:

                st.error(
                    "Este horário acabou de ser ocupado. "
                    "Volte e escolha outro horário."
                )

            else:

                with st.spinner("Registrando seu agendamento..."):

                    sucesso, mensagem = salvar_agendamento(
                        dia=st.session_state.data,
                        horario=st.session_state.horario,
                        profissional=st.session_state.profissional,
                        cliente=st.session_state.cliente,
                        servico=servico,
                        telefone=st.session_state.telefone,
                        duracao=duracao
                    )

                if sucesso:

                    buscar_reservas.clear()

                    st.session_state.confirmado = {
                        "cliente": st.session_state.cliente,
                        "servico": servico,
                        "profissional": st.session_state.profissional,
                        "data": st.session_state.data.strftime("%d/%m/%Y"),
                        "horario": st.session_state.horario,
                        "duracao": duracao,
                        "valor": valor_total
                    }

                    st.success("Agendamento registrado com sucesso!")

                    st.rerun()

                else:
                    st.error(mensagem)


# ============================================================
# INFORMAÇÕES FIXAS
# ============================================================

st.divider()

col_info1, col_info2 = st.columns(2)

with col_info1:

    with st.container(border=True):

        st.markdown("### Reserve seu horário")

        st.write(
            "Reserve seu horário de forma rápida e prática."
        )

    with st.container(border=True):

        st.markdown("## 💈 Nossa missão")

        st.write(
            "Oferecer qualidade, estilo e cuidado em cada atendimento."
        )

        st.write(
            "Seu bem-estar e sua satisfação são nossa prioridade!"
        )

with col_info2:

    with st.container(border=True):

        st.markdown("## ◷ Horário de Atendimento")

        st.markdown("**Segunda a sábado**")

        st.markdown("### :orange[09h às 19h]")

        st.caption(
            "Intervalo para almoço: 12h às 13h."
        )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.markdown("""
<div class="footer">
    <strong style="color:#eab344;">BARBEARIA JOEL</strong><br>
    ESTILO • CONFIANÇA • BEM-ESTAR<br><br>
    © 2026 Barbearia Joel — Todos os direitos reservados.
</div>
""", unsafe_allow_html=True)
