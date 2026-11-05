
import streamlit as st
import requests
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
import re

# ============================================================
# CONFIGURAÇÕES
# ============================================================

NOME_BARBEARIA = "Barbearia Joel"

TZ = ZoneInfo("America/Sao_Paulo")

DIAS_A_FRENTE = 14
PASSO_MIN = 30

# Substitua pelo WhatsApp real da barbearia.
# Formato: código do país + DDD + número, somente números.
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

.service-card {
    background: #1d1d1d;
    border: 1px solid #49402d;
    border-radius: 14px;
    padding: 18px 10px;
    min-height: 165px;
    text-align: center;
}

.service-icon {
    font-size: 32px;
}

.service-name {
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    margin-top: 8px;
}

.service-description {
    color: #aaaaaa;
    font-size: 11px;
    margin-top: 5px;
}

.service-price {
    color: #eab344;
    font-size: 21px;
    font-weight: 800;
    margin-top: 10px;
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

div[data-testid="stAlert"] {
    border-radius: 10px;
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
    h, m = map(int, horario.split(":")[:2])
    return h * 60 + m


def formatar_hora(valor):
    if isinstance(valor, time):
        return valor.strftime("%H:%M")

    texto = str(valor).strip()

    try:
        return datetime.strptime(texto[:5], "%H:%M").strftime("%H:%M")
    except ValueError:
        return texto[:5]


def formatar_data(valor):
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
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def telefone_valido(numero):
    numeros = re.sub(r"\D", "", numero)
    return len(numeros) in (10, 11)


def gerar_whatsapp(numero, mensagem):
    numero = re.sub(r"\D", "", numero)
    return f"https://wa.me/{numero}?text={quote(mensagem)}"


def sobrepoe(inicio1, fim1, inicio2, fim2):
    return inicio1 < fim2 and inicio2 < fim1


# ============================================================
# BUSCAR RESERVAS NO GOOGLE SHEETS
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
# VERIFICAR HORÁRIOS OCUPADOS
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
# GERAR HORÁRIOS DISPONÍVEIS
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

        # Não permite agendamento durante o almoço.
        if sobrepoe(
            inicio,
            fim,
            almoco_inicio,
            almoco_fim
        ):
            continue

        # Não permite horários que já passaram.
        if dia == atual.date():
            horario_atual = atual.hour * 60 + atual.minute

            if inicio <= horario_atual:
                continue

        # Verifica conflitos com reservas existentes.
        conflito = any(
            sobrepoe(inicio, fim, ocupado_inicio, ocupado_fim)
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
# ENVIAR AGENDAMENTO PARA GOOGLE APPS SCRIPT
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

        # Aceita respostas de sucesso sem campo explícito,
        # desde que o servidor não tenha informado erro.
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
# SERVIÇOS
# ============================================================

st.markdown("## ✂️ Nossos Serviços")
st.caption("Qualidade e estilo para você ficar ainda melhor!")

colunas = st.columns(5)

for coluna, (nome, dados) in zip(colunas, SERVICOS.items()):
    with coluna:
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:center;font-size:32px;'>{dados['icone']}</div>",
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
                f"Duração: {dados['duracao']} minutos"
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
            "Escolha o serviço, profissional, data e horário."
        )

        servico = st.selectbox(
            "Selecione o serviço",
            list(SERVICOS.keys())
        )

        profissional = st.selectbox(
            "Escolha o profissional",
            list(PROFISSIONAIS.keys())
        )

        hoje = agora().date()
        ultima_data = hoje + timedelta(days=DIAS_A_FRENTE)

        dias_validos = [
            hoje + timedelta(days=i)
            for i in range(DIAS_A_FRENTE + 1)
            if (hoje + timedelta(days=i)).weekday()
            in PROFISSIONAIS[profissional]["dias"]
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

        if dia.weekday() not in PROFISSIONAIS[profissional]["dias"]:
            st.warning(
                "O profissional não atende nesta data. "
                "Escolha outro dia."
            )
            st.stop()

        duracao = SERVICOS[servico]["duracao"]

        try:
            with st.spinner("Consultando horários disponíveis..."):
                reservas = buscar_reservas()

        except RuntimeError as erro:
            st.error(str(erro))
            st.stop()

        horarios = horarios_livres(
            dia,
            profissional,
            duracao,
            reservas
        )

        if horarios:
            st.success(
                f"{len(horarios)} horário(s) disponível(is) para esta data."
            )

            horario = st.selectbox(
                "Escolha o horário",
                horarios
            )

        else:
            horario = None

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

        st.write(f"**Serviço:** {servico}")
        st.write(f"**Profissional:** {profissional}")
        st.write(f"**Data:** {dia.strftime('%d/%m/%Y')}")
        st.write(f"**Horário:** {horario or 'Não selecionado'}")
        st.write(f"**Duração:** {duracao} minutos")

        st.markdown(
            f"### :orange[Valor: {moeda(SERVICOS[servico]['preco'])}]"
        )

        confirmar = st.button(
            "✅ CONFIRMAR AGENDAMENTO",
            use_container_width=True,
            disabled=not horarios
        )

        if confirmar:

            if not cliente.strip():
                st.error("Informe seu nome completo.")

            elif not telefone_valido(telefone):
                st.error(
                    "Informe um telefone válido com DDD."
                )

            elif not horario:
                st.error("Selecione um horário.")

            else:

                # Atualiza a agenda antes de enviar.
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
                        "Escolha outro horário disponível."
                    )

                else:
                    with st.spinner("Confirmando seu agendamento..."):

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

                        st.markdown("### 🎉 Agendamento confirmado")

                        st.write(f"**Cliente:** {cliente}")
                        st.write(f"**Serviço:** {servico}")
                        st.write(f"**Data:** {dia.strftime('%d/%m/%Y')}")
                        st.write(f"**Horário:** {horario}")
                        st.write(f"**Profissional:** {profissional}")
                        st.write(
                            f"**Valor:** {moeda(SERVICOS[servico]['preco'])}"
                        )

                        mensagem_whatsapp = (
                            f"Olá! Meu agendamento na {NOME_BARBEARIA} "
                            f"foi registrado.\n\n"
                            f"Nome: {cliente}\n"
                            f"Serviço: {servico}\n"
                            f"Data: {dia.strftime('%d/%m/%Y')}\n"
                            f"Horário: {horario}\n"
                            f"Profissional: {profissional}\n"
                            f"Valor: {moeda(SERVICOS[servico]['preco'])}"
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

                    else:
                        st.error(mensagem)


# ============================================================
# INFORMAÇÕES E BENEFÍCIOS
# ============================================================

with col_informacoes:

    with st.container(border=True):

        st.markdown("## ✓ Por que agendar conosco?")

        beneficios = [
            ("★", "Atendimento profissional"),
            ("✦", "Qualidade e atenção aos detalhes"),
            ("◷", "Pontualidade no atendimento"),
            ("✂", "Estilo personalizado"),
            ("♛", "Ambiente agradável")
        ]

        for icone, descricao in beneficios:
            st.markdown(
                f"**:orange[{icone}]**  {descricao}"
            )

        st.divider()

        st.markdown("### Cuide do seu visual!")
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
