
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

# Substitua pelo número real da barbearia.
# Formato: 55 + DDD + número, somente dígitos.
WHATSAPP_PADRAO = "5531999999999"


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
# CONFIGURAÇÃO STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Barbearia Joel | Agendamento",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CSS
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
    max-width: 1200px;
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
    margin-bottom: 25px;
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

.service-selected {
    border: 1px solid #eab344;
    background: #292317;
    border-radius: 12px;
    padding: 12px;
}

.service-unselected {
    border: 1px solid #49402d;
    background: #1d1d1d;
    border-radius: 12px;
    padding: 12px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CONFIGURAÇÃO DA API
# ============================================================

try:
    SCRIPT_URL = st.secrets.get("SCRIPT_URL", "").strip()
except Exception:
    SCRIPT_URL = ""

if not SCRIPT_URL:
    st.error(
        "A URL do Google Apps Script não foi configurada. "
        "Configure SCRIPT_URL nas Secrets do Streamlit."
    )
    st.stop()


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

    formatos = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M:%S"
    ]

    for formato in formatos:
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
    numeros = re.sub(r"\D", "", numero)
    return len(numeros) in (10, 11)


def gerar_whatsapp(numero, mensagem):
    numero = re.sub(r"\D", "", numero)
    return f"https://wa.me/{numero}?text={quote(mensagem)}"


def sobrepoe(inicio1, fim1, inicio2, fim2):
    return inicio1 < fim2 and inicio2 < fim1


def calcular_valores(servicos):
    valor = sum(
        SERVICOS[nome]["preco"]
        for nome in servicos
    )

    duracao = sum(
        SERVICOS[nome]["duracao"]
        for nome in servicos
    )

    return valor, duracao


# ============================================================
# BUSCAR RESERVAS
# ============================================================

@st.cache_data(ttl=15, show_spinner=False)
def buscar_reservas():
    try:
        resposta = requests.get(
            SCRIPT_URL,
            timeout=20
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if isinstance(dados, list):
            reservas = dados
        else:
            reservas = dados.get("reservas", [])

        if not isinstance(reservas, list):
            return []

        return reservas

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "O Google Apps Script demorou para responder. Tente novamente."
        )

    except requests.exceptions.RequestException as erro:
        raise RuntimeError(
            f"Não foi possível consultar os agendamentos: {erro}"
        )

    except ValueError:
        raise RuntimeError(
            "O Google Apps Script retornou uma resposta inválida."
        )


# ============================================================
# RESERVAS DO DIA
# ============================================================

def reservas_do_dia(reservas, dia, profissional):
    resultado = []

    for reserva in reservas:

        data_reserva = formatar_data(
            reserva.get("data", "")
        )

        profissional_reserva = str(
            reserva.get("profissional", "")
        ).strip()

        if data_reserva != dia:
            continue

        if profissional_reserva != profissional:
            continue

        try:
            inicio = minutos(
                formatar_hora(reserva.get("hora", ""))
            )

            duracao = int(
                reserva.get(
                    "duracao",
                    reserva.get("duracao_min", 30)
                )
            )

            if duracao <= 0:
                duracao = 30

            resultado.append(
                (inicio, inicio + duracao)
            )

        except (ValueError, TypeError):
            continue

    return resultado


# ============================================================
# HORÁRIOS DISPONÍVEIS
# ============================================================

def horarios_livres(dia, profissional, duracao, reservas):

    configuracao = PROFISSIONAIS[profissional]

    if dia.weekday() not in configuracao["dias"]:
        return []

    inicio_expediente = minutos(configuracao["inicio"])
    fim_expediente = minutos(configuracao["fim"])

    almoco_inicio = minutos(configuracao["almoco_inicio"])
    almoco_fim = minutos(configuracao["almoco_fim"])

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
            horario_atual = (
                atual.hour * 60 + atual.minute
            )

            if inicio <= horario_atual:
                continue

        conflito = any(
            sobrepoe(
                inicio,
                fim,
                ocupado_inicio,
                ocupado_fim
            )
            for ocupado_inicio, ocupado_fim in ocupados
        )

        if not conflito:
            h = inicio // 60
            m = inicio % 60

            livres.append(
                f"{h:02d}:{m:02d}"
            )

    return livres


# ============================================================
# SALVAR AGENDAMENTO
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

        try:
            retorno = resposta.json()
        except ValueError:
            return False, "O servidor retornou uma resposta inválida."

        if not isinstance(retorno, dict):
            return False, "Resposta inesperada do servidor."

        sucesso = retorno.get(
            "sucesso",
            retorno.get(
                "success",
                retorno.get("ok", None)
            )
        )

        mensagem = retorno.get(
            "mensagem",
            retorno.get(
                "message",
                "Não foi possível confirmar o agendamento."
            )
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
            "Verifique a agenda antes de tentar novamente."
        )

    except requests.exceptions.RequestException as erro:
        return False, f"Erro ao enviar agendamento: {erro}"


# ============================================================
# ESTADO DA SELEÇÃO DOS SERVIÇOS
# ============================================================

if "servicos_selecionados" not in st.session_state:
    st.session_state.servicos_selecionados = []

if "confirmacao_pendente" not in st.session_state:
    st.session_state.confirmacao_pendente = False


# ============================================================
# CABEÇALHO
# ============================================================

st.markdown("""
<div class="hero">
    <div style="font-size:48px;">💈</div>
    <div class="hero-title">BARBEARIA JOEL</div>
    <div class="hero-subtitle">ESTILO • CONFIANÇA • BEM-ESTAR</div>
    <div style="
        color:#eab344;
        font-size:19px;
        font-style:italic;
        margin-top:15px;">
        Seu visual em boas mãos!
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# SERVIÇOS - BOTÕES MULTIPLA SELEÇÃO
# ============================================================

st.markdown("##  Nossos Serviços")

st.caption(
    "Escolha um ou mais serviços. "
    "O valor e a duração serão calculados automaticamente."
)

colunas = st.columns(5)

for indice, (nome, dados) in enumerate(SERVICOS.items()):

    selecionado = (
        nome in st.session_state.servicos_selecionados
    )

    with colunas[indice]:

        with st.container(border=True):

            st.markdown(
                f"<div style='text-align:center;font-size:34px;'>{dados['icone']}</div>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"**{nome}**"
            )

            st.caption(dados["descricao"])

            st.markdown(
                f"### :orange[{moeda(dados['preco'])}]"
            )

            st.caption(
                f"{dados['duracao']} minutos"
            )

            if st.button(
                "✓ Selecionado" if selecionado else "+ Adicionar",
                key=f"servico_{indice}",
                use_container_width=True,
                type="primary" if selecionado else "secondary"
            ):

                if selecionado:
                    st.session_state.servicos_selecionados.remove(nome)
                else:
                    st.session_state.servicos_selecionados.append(nome)

                st.rerun()


# ============================================================
# RESUMO DOS SERVIÇOS SELECIONADOS
# ============================================================

servicos_selecionados = (
    st.session_state.servicos_selecionados
)

if servicos_selecionados:

    valor_total, duracao = calcular_valores(
        servicos_selecionados
    )

    servico = " + ".join(servicos_selecionados)

    with st.container(border=True):

        st.markdown("### 🧾 Resumo dos serviços")

        for nome in servicos_selecionados:
            dados = SERVICOS[nome]

            st.write(
                f"{dados['icone']} **{nome}** — "
                f"{moeda(dados['preco'])} "
                f"({dados['duracao']} min)"
            )

        st.divider()

        col_valor, col_duracao = st.columns(2)

        with col_valor:
            st.metric(
                "Valor total",
                moeda(valor_total)
            )

        with col_duracao:
            st.metric(
                "Duração total",
                f"{duracao} min"
            )

else:

    st.info(
        "Selecione pelo menos um serviço para continuar."
    )


st.divider()


# ============================================================
# ÁREA PRINCIPAL
# ============================================================

col_agendamento, col_informacoes = st.columns(
    [1.7, 1],
    gap="large"
)


# ============================================================
# AGENDAMENTO
# ============================================================

with col_agendamento:

    with st.container(border=True):

        st.markdown("## 📅 Agende seu horário")

        st.write(
            "Informe seus dados e escolha uma data e horário."
        )

        profissional = st.selectbox(
            "Escolha o profissional",
            list(PROFISSIONAIS.keys())
        )

        hoje = agora().date()

        ultima_data = hoje + timedelta(
            days=DIAS_A_FRENTE
        )

        dias_validos = [
            hoje + timedelta(days=i)
            for i in range(DIAS_A_FRENTE + 1)
            if (
                hoje + timedelta(days=i)
            ).weekday() in PROFISSIONAIS[profissional]["dias"]
        ]

        if not dias_validos:
            st.warning("Não há datas disponíveis.")
            st.stop()

        dia = st.date_input(
            "Escolha a data",
            value=dias_validos[0],
            min_value=hoje,
            max_value=ultima_data
        )

        horario = None
        horarios = []

        if dia.weekday() not in PROFISSIONAIS[profissional]["dias"]:

            st.warning(
                "O profissional não atende nesta data. "
                "Escolha outro dia."
            )

        elif not servicos_selecionados:

            st.info(
                "Primeiro selecione pelo menos um serviço."
            )

        else:

            try:

                with st.spinner(
                    "Consultando horários disponíveis..."
                ):

                    reservas = buscar_reservas()

                horarios = horarios_livres(
                    dia,
                    profissional,
                    duracao,
                    reservas
                )

            except RuntimeError as erro:

                st.error(str(erro))

        if horarios:

            st.success(
                f"{len(horarios)} horário(s) disponível(is)."
            )

            horario = st.selectbox(
                "Escolha o horário",
                horarios
            )

        elif (
            dia.weekday() in PROFISSIONAIS[profissional]["dias"]
            and servicos_selecionados
        ):

            st.warning(
                "Não há horários disponíveis nesta data. "
                "Escolha outro dia."
            )

        st.divider()

        st.markdown("### 👤 Seus dados")

        cliente = st.text_input(
            "Nome completo",
            placeholder="Digite seu nome"
        )

        telefone = st.text_input(
            "Telefone / WhatsApp",
            placeholder="(31) 99999-9999",
            max_chars=20
        )

        st.divider()

        st.markdown("### 🧾 Resumo do agendamento")

        st.write(
            f"**Serviços:** {servico if servicos_selecionados else 'Não selecionados'}"
        )

        st.write(
            f"**Profissional:** {profissional}"
        )

        st.write(
            f"**Data:** {dia.strftime('%d/%m/%Y')}"
        )

        st.write(
            f"**Horário:** {horario or 'Não selecionado'}"
        )

        st.write(
            f"**Duração total:** "
            f"{f'{duracao} minutos' if servicos_selecionados else 'Não definida'}"
        )

        st.markdown(
            f"### :orange[Valor total: {moeda(valor_total) if servicos_selecionados else 'R$ 0,00'}]"
        )

        confirmar = st.button(
            "✅ CONFIRMAR AGENDAMENTO",
            use_container_width=True,
            disabled=(
                not servicos_selecionados
                or not horarios
                or not horario
            )
        )

        if confirmar:

            if not cliente.strip():

                st.error(
                    "Informe seu nome completo."
                )

            elif not telefone_valido(telefone):

                st.error(
                    "Informe um telefone válido com DDD."
                )

            else:

                # Atualiza a agenda antes de tentar gravar.
                buscar_reservas.clear()

                try:

                    reservas_atualizadas = buscar_reservas()

                    horarios_atualizados = horarios_livres(
                        dia,
                        profissional,
                        duracao,
                        reservas_atualizadas
                    )

                except RuntimeError as erro:

                    st.error(str(erro))
                    horarios_atualizados = []

                if horario not in horarios_atualizados:

                    st.error(
                        "Este horário acabou de ser reservado. "
                        "Escolha outro horário."
                    )

                else:

                    with st.spinner(
                        "Confirmando seu agendamento..."
                    ):

                        sucesso, mensagem = salvar_agendamento(
                            dia=dia,
                            horario=horario,
                            profissional=profissional,
                            cliente=cliente,
                            servico=servico,
                            telefone=telefone,
                            duracao=duracao
                        )

                    if sucesso:

                        buscar_reservas.clear()

                        st.success(
                            "Agendamento registrado com sucesso!"
                        )

                        st.balloons()

                        st.markdown(
                            "### 🎉 Agendamento confirmado"
                        )

                        st.write(
                            f"**Cliente:** {cliente}"
                        )

                        st.write(
                            f"**Serviços:** {servico}"
                        )

                        st.write(
                            f"**Data:** {dia.strftime('%d/%m/%Y')}"
                        )

                        st.write(
                            f"**Horário:** {horario}"
                        )

                        st.write(
                            f"**Profissional:** {profissional}"
                        )

                        st.write(
                            f"**Duração:** {duracao} minutos"
                        )

                        st.write(
                            f"**Valor total:** {moeda(valor_total)}"
                        )

                        mensagem_whatsapp = (
                            f"Olá! Meu agendamento na {NOME_BARBEARIA} "
                            f"foi registrado.\n\n"
                            f"Nome: {cliente}\n"
                            f"Serviços: {servico}\n"
                            f"Data: {dia.strftime('%d/%m/%Y')}\n"
                            f"Horário: {horario}\n"
                            f"Profissional: {profissional}\n"
                            f"Duração: {duracao} minutos\n"
                            f"Valor total: {moeda(valor_total)}"
                        )

                        link_whatsapp = gerar_whatsapp(
                            WHATSAPP_PADRAO,
                            mensagem_whatsapp
                        )

                        st.link_button(
                            "📲 CONTINUAR PELO WHATSAPP",
                            link_whatsapp,
                            use_container_width=True
                        )

                        # Limpa a seleção após o registro.
                        st.session_state.servicos_selecionados = []

                    else:

                        st.error(mensagem)




        st.write(
            "Reserve seu horário de forma rápida e prática."
        )

    with st.container(border=True):

        st.markdown("## ◷ Horário de Atendimento")

        st.markdown("**Segunda a sábado**")

        st.markdown(
            "### :orange[09h às 19h]"
        )

        st.caption(
            "Intervalo para almoço: 12h às 13h."
        )

    with st.container(border=True):

        st.markdown("## 💈 Nossa missão")

        st.write(
            "Oferecer qualidade, estilo e cuidado em cada atendimento."
        )

        st.write(
            "Seu bem-estar e sua satisfação são nossa prioridade!"
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
