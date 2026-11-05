
import html
import requests
import streamlit as st

from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo


# =========================================================
# 1. CONFIGURAÇÕES DA BARBEARIA
# =========================================================

NOME_BARBEARIA = "Barbearia Joel"

TZ = ZoneInfo("America/Sao_Paulo")

DIAS_A_FRENTE = 14
PASSO_MIN = 30

# ATENÇÃO: ajuste os preços conforme os valores reais.

SERVICOS = {
    "Corte Masculino": {
        "duracao": 30,
        "preco": 50.00,
        "icone": "✂️",
        "descricao": "Estilo e precisão"
    },
    "Barba": {
        "duracao": 30,
        "preco": 40.00,
        "icone": "🧔",
        "descricao": "Modelagem perfeita"
    },
    "Corte Infantil": {
        "duracao": 30,
        "preco": 40.00,
        "icone": "👦",
        "descricao": "Cuidado especial"
    },
    "Corte + Barba": {
        "duracao": 60,
        "preco": 80.00,
        "icone": "💈",
        "descricao": "Visual completo"
    },
    "Desenho no Cabelo": {
        "duracao": 30,
        "preco": 30.00,
        "icone": "🎨",
        "descricao": "Personalize seu estilo"
    }
}

# Informe o WhatsApp real da barbearia:
# DDI + DDD + número, somente números.
WHATSAPP_PADRAO = "5531999999999"

# Configuração dos profissionais.
# 0=segunda, 1=terça, 2=quarta, 3=quinta,
# 4=sexta, 5=sábado, 6=domingo.

PROFISSIONAIS = {
    "Joel": {
        "dias": [0, 1, 2, 3, 4, 5],
        "inicio": "09:00",
        "fim": "19:00",
        "almoco": ("12:00", "13:00"),
        "whatsapp": WHATSAPP_PADRAO
    }
}

DIAS_SEMANA = [
    "segunda",
    "terça",
    "quarta",
    "quinta",
    "sexta",
    "sábado",
    "domingo"
]


# =========================================================
# 2. CONFIGURAÇÃO DO STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Barbearia Joel | Agendamento",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SCRIPT_URL = st.secrets.get("SCRIPT_URL", "").strip()

if not SCRIPT_URL:
    st.error(
        "A URL do Google Apps Script não foi configurada. "
        "Acesse Manage app → Settings → Secrets."
    )
    st.stop()


# =========================================================
# 3. IDENTIDADE VISUAL
# =========================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top, #252525 0%, #101010 48%, #080808 100%);
    color: #ffffff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

h1, h2, h3, p, label {
    color: #ffffff;
}

.gold {
    color: #eab344;
}

.hero {
    background:
        linear-gradient(110deg, rgba(0,0,0,.96), rgba(24,24,24,.88)),
        radial-gradient(circle at right, #6b4815, #111);
    border: 1px solid #61471d;
    border-radius: 20px;
    padding: 36px 25px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 8px 30px rgba(0,0,0,.4);
}

.hero-logo {
    font-size: 48px;
    margin-bottom: 5px;
}

.hero h1 {
    font-size: 43px;
    font-weight: 800;
    margin: 0;
    letter-spacing: 2px;
}

.hero h1 span {
    color: #eab344;
}

.hero p {
    color: #d0d0d0;
    font-size: 15px;
    margin-top: 12px;
    letter-spacing: 2px;
}

.section-title {
    font-size: 25px;
    font-weight: 800;
    margin: 25px 0 5px 0;
}

.section-subtitle {
    color: #b8b8b8;
    margin-bottom: 20px;
}

.service-card {
    background: linear-gradient(145deg, #242424, #111111);
    border: 1px solid #51412a;
    border-radius: 16px;
    padding: 20px 12px;
    text-align: center;
    min-height: 205px;
    box-shadow: 0 5px 15px rgba(0,0,0,.3);
    transition: .2s;
}

.service-card:hover {
    border-color: #eab344;
    transform: translateY(-3px);
}

.service-icon {
    font-size: 43px;
    margin-bottom: 12px;
}

.service-name {
    color: #ffffff;
    font-weight: 800;
    font-size: 15px;
    min-height: 40px;
}

.service-description {
    color: #bdbdbd;
    font-size: 12px;
    margin: 5px 0 12px;
}

.service-price {
    background: linear-gradient(90deg, #b77c19, #f5c75c);
    color: #17100a;
    font-size: 19px;
    font-weight: 800;
    padding: 8px;
    border-radius: 9px;
}

.panel {
    background: linear-gradient(145deg, #202020, #111111);
    border: 1px solid #51412a;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 20px;
}

.price-highlight {
    color: #f2bd4d;
    font-size: 26px;
    font-weight: 800;
    margin: 5px 0 15px;
}

div[data-testid="stButton"] > button {
    border-radius: 10px;
    border: 1px solid #dca63c;
    background: linear-gradient(90deg, #b77c19, #f2bd4d);
    color: #15100a;
    font-weight: 800;
    min-height: 44px;
}

div[data-testid="stButton"] > button:hover {
    border: 1px solid #ffe09a;
    color: #000000;
    background: #ffd36c;
}

div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div,
div[data-testid="stDateInput"] input {
    border-radius: 9px;
}

.footer {
    text-align: center;
    border-top: 1px solid #62491e;
    margin-top: 35px;
    padding: 25px 10px;
    color: #bdbdbd;
    font-size: 13px;
}

.footer strong {
    color: #eab344;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 4. FUNÇÕES AUXILIARES
# =========================================================

def mins(txt):
    h, m = map(int, txt.split(":"))
    return h * 60 + m


def fmt(valor):
    return f"{valor // 60:02d}:{valor % 60:02d}"


def moeda(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def rotulo_dia(dia):
    nome = DIAS_SEMANA[dia.weekday()].capitalize()
    return f"{nome}, {dia:%d/%m/%Y}"


# =========================================================
# 5. CONSULTA À PLANILHA GOOGLE SHEETS
# =========================================================

@st.cache_data(ttl=15)
def buscar_reservas():

    resposta = requests.get(
        SCRIPT_URL,
        timeout=20
    )

    resposta.raise_for_status()

    dados = resposta.json()

    mapa = {}

    for reserva in dados.get("reservas", []):

        if not reserva.get("data") or not reserva.get("hora"):
            continue

        inicio = mins(reserva["hora"])

        duracao = int(reserva.get("duracao", 30))

        chave = (
            reserva["data"],
            reserva["profissional"]
        )

        mapa.setdefault(chave, []).append(
            (inicio, inicio + duracao)
        )

    return mapa


# =========================================================
# 6. CÁLCULO DOS HORÁRIOS DISPONÍVEIS
# =========================================================

def horarios_livres(profissional, dia, mapa, duracao):

    config = PROFISSIONAIS[profissional]

    if dia.weekday() not in config["dias"]:
        return []

    agora = datetime.now(TZ)

    agora_minutos = agora.hour * 60 + agora.minute

    abre = mins(config["inicio"])
    fecha = mins(config["fim"])

    almoco_inicio = mins(config["almoco"][0])
    almoco_fim = mins(config["almoco"][1])

    bloqueios = mapa.get(
        (dia.isoformat(), profissional),
        []
    )

    livres = []

    inicio = abre

    while inicio + duracao <= fecha:

        fim = inicio + duracao

        intervalo_almoco = (
            inicio < almoco_fim and fim > almoco_inicio
        )

        ocupado = any(
            inicio < bloqueio_fim and fim > bloqueio_inicio
            for bloqueio_inicio, bloqueio_fim in bloqueios
        )

        horario_passado = (
            dia == agora.date()
            and inicio <= agora_minutos
        )

        if (
            not intervalo_almoco
            and not ocupado
            and not horario_passado
        ):
            livres.append(fmt(inicio))

        inicio += PASSO_MIN

    return livres


# =========================================================
# 7. CABEÇALHO
# =========================================================

st.markdown("""
<div class="hero">
    <div class="hero-logo">💈</div>
    <h1>BARBEARIA <span>JOEL</span></h1>
    <p>ESTILO • CONFIANÇA • BEM-ESTAR</p>

    <div style="
        color:#eab344;
        font-size:19px;
        font-style:italic;
        margin-top:15px">
        Seu visual em boas mãos!
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 8. SERVIÇOS E PREÇOS
# =========================================================

st.markdown("""
<div class="section-title">
    <span class="gold">✂</span> Nossos Serviços
</div>

<div class="section-subtitle">
    Qualidade e estilo para você ficar ainda melhor!
</div>
""", unsafe_allow_html=True)

colunas = st.columns(5)

for coluna, (nome, dados) in zip(colunas, SERVICOS.items()):

    with coluna:

        st.markdown(f"""
        <div class="service-card">
            <div class="service-icon">{dados['icone']}</div>

            <div class="service-name">
                {html.escape(nome)}
            </div>

            <div class="service-description">
                {html.escape(dados['descricao'])}
            </div>

            <div class="service-price">
                {moeda(dados['preco'])}
            </div>

            <div style="color:#aaa;font-size:11px;margin-top:8px">
                {dados['duracao']} minutos
            </div>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# 9. CARREGAR A AGENDA
# =========================================================

try:

    mapa = buscar_reservas()

except Exception as erro:

    st.error(
        "Não foi possível carregar a agenda. "
        "Verifique a conexão com o Google Apps Script."
    )

    st.caption(str(erro))

    st.stop()


# =========================================================
# 10. ÁREA DE AGENDAMENTO
# =========================================================

st.markdown("""
<div class="section-title">
    <span class="gold">▦</span> Agende seu Horário
</div>

<div class="section-subtitle">
    Escolha o serviço, o profissional, a data e o horário disponível.
</div>
""", unsafe_allow_html=True)

col_agenda, col_beneficios = st.columns(
    [1.05, 0.95],
    gap="large"
)


# =========================================================
# 11. FORMULÁRIO DE AGENDAMENTO
# =========================================================

with col_agenda:

    st.markdown('<div class="panel">', unsafe_allow_html=True)

    servico = st.selectbox(
        "Escolha o serviço",
        list(SERVICOS.keys())
    )

    dados_servico = SERVICOS[servico]

    duracao = dados_servico["duracao"]

    st.markdown(
        f'<div class="price-highlight">{moeda(dados_servico["preco"])}</div>',
        unsafe_allow_html=True
    )

    profissional = st.selectbox(
        "Profissional",
        list(PROFISSIONAIS.keys())
    )

    hoje = datetime.now(TZ).date()

    dias = [
        hoje + timedelta(days=i)
        for i in range(DIAS_A_FRENTE)
    ]

    dias_com_vagas = [
        dia for dia in dias
        if horarios_livres(
            profissional,
            dia,
            mapa,
            duracao
        )
    ]

    if not dias_com_vagas:

        st.warning(
            f"Não há horários disponíveis para {profissional} "
            f"nos próximos {DIAS_A_FRENTE} dias."
        )

        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    dia = st.selectbox(
        "Data do atendimento",
        dias_com_vagas,
        format_func=rotulo_dia
    )

    livres = horarios_livres(
        profissional,
        dia,
        mapa,
        duracao
    )

    st.markdown("**Horários disponíveis**")

    if not livres:

        st.warning(
            "Não existem horários livres para esta data."
        )

        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    if "hora" not in st.session_state:
        st.session_state["hora"] = None

    chave_selecao = (
        profissional,
        dia.isoformat(),
        servico
    )

    if st.session_state.get("chave_selecao") != chave_selecao:

        st.session_state["hora"] = None
        st.session_state["chave_selecao"] = chave_selecao

    colunas_horarios = st.columns(3)

    for indice, horario in enumerate(livres):

        with colunas_horarios[indice % 3]:

            selecionado = (
                st.session_state["hora"] == horario
            )

            texto_botao = (
                f"✓ {horario}"
                if selecionado
                else horario
            )

            if st.button(
                texto_botao,
                key=f"horario_{dia}_{horario}",
                use_container_width=True
            ):

                st.session_state["hora"] = horario
                st.rerun()

    hora = st.session_state["hora"]

    if hora and hora not in livres:

        hora = None
        st.session_state["hora"] = None

    if hora:

        fim = fmt(mins(hora) + duracao)

        st.success(
            f"Selecionado: {rotulo_dia(dia)} "
            f"das {hora} às {fim}."
        )

    st.markdown("---")

    st.markdown("**Seus dados**")

    nome = st.text_input(
        "Nome completo",
        placeholder="Digite seu nome"
    )

    telefone = st.text_input(
        "WhatsApp com DDD",
        placeholder="Ex.: 31987654321"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    confirmar = st.button(
        "📅 CONFIRMAR AGENDAMENTO",
        type="primary",
        use_container_width=True
    )


# =========================================================
# 12. BENEFÍCIOS E HORÁRIO DE ATENDIMENTO
# =========================================================

with col_beneficios:

    beneficios = [
        ("★", "Atendimento profissional"),
        ("✦", "Qualidade e atenção aos detalhes"),
        ("◷", "Pontualidade no atendimento"),
        ("✂", "Estilo personalizado"),
        ("♛", "Ambiente agradável")
    ]

    beneficios_html = ""

    for icone, descricao in beneficios:

        beneficios_html += f"""
        <div style="
            display:flex;
            align-items:center;
            gap:14px;
            padding:12px 8px;
            color:#eeeeee;
            font-size:15px;
            border-bottom:1px solid #383838;
        ">
            <span style="
                color:#eab344;
                font-size:23px;
                min-width:28px;
            ">{icone}</span>

            <span>{html.escape(descricao)}</span>
        </div>
        """

    st.markdown(f"""
    <div class="panel">

        <h3>
            <span class="gold">✓</span>
            Por que agendar conosco?
        </h3>

        {beneficios_html}

        <div style="
            color:#eab344;
            font-size:25px;
            font-weight:800;
            text-align:center;
            padding:22px 5px 10px;
        ">
            Cuide do seu visual!
        </div>

        <div style="
            text-align:center;
            color:#bbbbbb;
            font-size:13px;
            padding-bottom:12px;
        ">
            Reserve seu horário de forma rápida e prática.
        </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="panel">

        <h3>
            <span class="gold">◷</span>
            Horário de Atendimento
        </h3>

        <p>Segunda a sábado</p>

        <p style="
            color:#eab344;
            font-size:23px;
            font-weight:800;
        ">
            09h às 19h
        </p>

        <p style="color:#aaa;font-size:13px">
            Os horários disponíveis são atualizados conforme a agenda.
        </p>

    </div>
    """, unsafe_allow_html=True)


# =========================================================
# 13. CONFIRMAÇÃO DO AGENDAMENTO
# =========================================================

if confirmar:

    if not hora:

        st.error("Selecione um horário disponível.")

    elif not nome.strip():

        st.error("Informe seu nome completo.")

    else:

        numeros = "".join(
            c for c in telefone if c.isdigit()
        )

        if len(numeros) < 10:

            st.error(
                "Informe um WhatsApp válido com DDD."
            )

        else:

            try:

                # Limpa o cache antes de consultar novamente.
                # Assim, a verificação utiliza os dados mais recentes.
                buscar_reservas.clear()

                mapa_atualizado = buscar_reservas()

                livres_atualizados = horarios_livres(
                    profissional,
                    dia,
                    mapa_atualizado,
                    duracao
                )

                if hora not in livres_atualizados:

                    st.error(
                        "Este horário acabou de ser reservado. "
                        "Escolha outro horário."
                    )

                    st.session_state["hora"] = None

                    st.rerun()

                else:

                    # Envia o agendamento ao Google Apps Script.
                    resposta = requests.post(
                        SCRIPT_URL,
                        json={
                            "data": dia.isoformat(),
                            "hora": hora,
                            "profissional": profissional,
                            "cliente": nome.strip(),
                            "servico": servico,
                            "telefone": numeros,
                            "duracao": duracao
                        },
                        timeout=30
                    )

                    resposta.raise_for_status()

                    resultado = resposta.json()

                    if resultado.get("ok"):

                        st.session_state["hora"] = None

                        buscar_reservas.clear()

                        st.success(
                            "Agendamento realizado com sucesso!"
                        )

                        st.balloons()

                        st.markdown(f"""
                        <div class="panel">

                            <h3 style="
                                color:#eab344;
                                text-align:center;
                            ">
                                💈 Agendamento confirmado!
                            </h3>

                            <p>
                                <strong>Cliente:</strong>
                                {html.escape(nome.strip())}
                            </p>

                            <p>
                                <strong>Serviço:</strong>
                                {html.escape(servico)}
                            </p>

                            <p>
                                <strong>Profissional:</strong>
                                {html.escape(profissional)}
                            </p>

                            <p>
                                <strong>Data:</strong>
                                {rotulo_dia(dia)}
                            </p>

                            <p>
                                <strong>Horário:</strong>
                                {hora} às {fmt(mins(hora) + duracao)}
                            </p>

                            <p>
                                <strong>Valor:</strong>
                                {moeda(dados_servico['preco'])}
                            </p>

                        </div>
                        """, unsafe_allow_html=True)

                        numero = PROFISSIONAIS[profissional].get(
                            "whatsapp",
                            WHATSAPP_PADRAO
                        )

                        mensagem = (
                            f"Olá! Meu agendamento na {NOME_BARBEARIA} "
                            f"foi realizado. "
                            f"Serviço: {servico}. "
                            f"Profissional: {profissional}. "
                            f"Data: {rotulo_dia(dia)}. "
                            f"Horário: {hora}. "
                            f"Nome: {nome.strip()}."
                        )

                        link_whatsapp = (
                            f"https://wa.me/{numero}?text={quote(mensagem)}"
                        )

                        st.link_button(
                            "📲 Enviar confirmação pelo WhatsApp",
                            link_whatsapp,
                            use_container_width=True
                        )

                    else:

                        st.error(
                            resultado.get(
                                "erro",
                                "Não foi possível concluir o agendamento."
                            )
                        )

            except requests.exceptions.Timeout:

                st.error(
                    "O servidor demorou para responder. "
                    "Verifique a agenda antes de tentar novamente."
                )

            except requests.exceptions.RequestException as erro:

                st.error(
                    "Não foi possível conectar ao Google Apps Script."
                )

                st.caption(str(erro))

            except Exception as erro:

                st.error(
                    "Ocorreu um erro ao realizar o agendamento."
                )

                st.caption(str(erro))


# =========================================================
# 14. RODAPÉ
# =========================================================

st.markdown("""
<div class="footer">

    <strong>💈 BARBEARIA JOEL</strong>

    <br><br>

    Mais que um corte, um cuidado com você!

    <br><br>

    <span style="color:#eab344">
        Estilo • Confiança • Bem-estar
    </span>

    <br><br>

    © Barbearia Joel - Todos os direitos reservados.

</div>
""", unsafe_allow_html=True)
