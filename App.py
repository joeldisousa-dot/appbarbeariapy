
import streamlit as st
import requests
import json
import re
from datetime import datetime, date, time, timedelta
from urllib.parse import quote

# ============================================================
# CONFIGURAÇÕES
# ============================================================

st.set_page_config(
    page_title="Barbearia Joel | Agendamento",
    page_icon="💈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

try:
    SCRIPT_URL = str(st.secrets["SCRIPT_URL"]).strip()
except Exception:
    SCRIPT_URL = ""

WHATSAPP_PADRAO = "5531999999999"  # Substitua pelo número real
NOME_SISTEMA = "BARBEARIA JOEL"

PROFISSIONAIS = {
    "Joel": {
        "dias": [0, 1, 2, 3, 4, 5],
        "inicio": "09:00",
        "fim": "19:00",
        "almoco_inicio": "12:00",
        "almoco_fim": "13:00"
    }
}

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
# ESTILO VISUAL
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}

.stApp {
    background: #101010;
    color: #ffffff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 900px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4, p, label {
    font-family: 'Montserrat', sans-serif !important;
}

.brand {
    text-align: center;
    padding: 25px 10px 20px 10px;
    border-bottom: 1px solid #b88a32;
    margin-bottom: 25px;
}

.brand-icon {
    font-size: 48px;
    margin-bottom: 5px;
}

.brand-title {
    color: #eab344;
    font-size: 34px;
    font-weight: 800;
    letter-spacing: 2px;
    margin: 0;
}

.brand-subtitle {
    color: #ffffff;
    font-size: 12px;
    letter-spacing: 3px;
    margin-top: 8px;
}

.brand-slogan {
    color: #eab344;
    font-size: 15px;
    font-style: italic;
    margin-top: 15px;
}

.section-title {
    color: #eab344;
    font-size: 22px;
    font-weight: 800;
    margin: 15px 0 8px 0;
}

.section-description {
    color: #cccccc;
    font-size: 13px;
    margin-bottom: 20px;
}

.service-card {
    background: #ffffff;
    border: 1px solid #eab344;
    border-radius: 12px;
    padding: 17px;
    min-height: 130px;
    margin-bottom: 10px;
    color: #000000 !important;
}

.service-card * {
    color: #000000 !important;
}

.service-icon {
    font-size: 25px;
}

.service-name {
    font-size: 15px;
    font-weight: 800;
    margin-top: 7px;
}

.service-description {
    font-size: 11px;
    margin-top: 4px;
}

.service-price {
    color: #9a6a12 !important;
    font-weight: 800;
    font-size: 16px;
    margin-top: 8px;
}

.step-indicator {
    color: #eab344;
    font-size: 12px;
    font-weight: 700;
    text-align: center;
    margin: 12px 0 20px 0;
    letter-spacing: 1px;
}

.gold-line {
    height: 2px;
    background: linear-gradient(90deg, transparent, #eab344, transparent);
    margin: 15px 0 22px 0;
}

.summary-card {
    background: #ffffff;
    color: #000000 !important;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #eab344;
    margin: 15px 0;
}

.summary-card * {
    color: #000000 !important;
}

.summary-total {
    color: #9a6a12 !important;
    font-size: 23px;
    font-weight: 800;
}

.small-muted {
    color: #bbbbbb;
    font-size: 12px;
}

.success-card {
    background: #ffffff;
    color: #000000 !important;
    border: 1px solid #eab344;
    padding: 22px;
    border-radius: 12px;
    text-align: center;
}

.success-card * {
    color: #000000 !important;
}

div.stButton > button {
    background: #eab344;
    color: #111111 !important;
    border: none;
    border-radius: 8px;
    font-weight: 800;
    min-height: 43px;
    transition: 0.2s;
}

div.stButton > button:hover {
    background: #ffffff;
    color: #000000 !important;
    border: 1px solid #eab344;
}

div.stButton > button:disabled {
    background: #555555;
    color: #cccccc !important;
}

.stTextInput input,
.stDateInput input,
.stSelectbox input,
.stTimeInput input,
div[data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #000000 !important;
    border-radius: 7px !important;
}

.stTextInput label,
.stDateInput label,
.stSelectbox label,
.stRadio label,
.stCheckbox label {
    color: #ffffff !important;
}

.stRadio div[role="radiogroup"] label {
    color: #ffffff !important;
}

div[data-testid="stAlert"] {
    color: #000000 !important;
}

div[data-testid="stAlert"] p {
    color: #000000 !important;
}

hr {
    border-color: #444444;
}

footer {
    visibility: hidden;
}

#MainMenu {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ESTADO DA APLICAÇÃO
# ============================================================

ESTADOS_INICIAIS = {
    "etapa": 1,
    "servicos_selecionados": [],
    "profissional": "",
    "data_agendamento": None,
    "hora_agendamento": "",
    "cliente": "",
    "telefone": "",
    "confirmado": None,
    "erro": "",
    "data_anterior": None
}

for chave, valor in ESTADOS_INICIAIS.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def dinheiro(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_totais():
    valor = sum(
        SERVICOS[nome]["preco"]
        for nome in st.session_state.servicos_selecionados
    )

    duracao = sum(
        SERVICOS[nome]["duracao"]
        for nome in st.session_state.servicos_selecionados
    )

    return valor, duracao


def converter_hora(hora_texto):
    return datetime.strptime(hora_texto, "%H:%M").time()


def normalizar_telefone(numero):
    return re.sub(r"\D", "", numero or "")


def buscar_reservas():
    if not SCRIPT_URL:
        raise Exception("A URL do Google Apps Script não foi configurada.")

    resposta = requests.get(
        SCRIPT_URL,
        timeout=20
    )

    resposta.raise_for_status()
    dados = resposta.json()

    if isinstance(dados, list):
        return dados

    if isinstance(dados, dict):
        if "reservas" in dados:
            return dados["reservas"] or []

        if dados.get("sucesso") is False or dados.get("success") is False:
            raise Exception(
                dados.get("mensagem", dados.get("erro", "Erro ao consultar agenda."))
            )

    raise Exception("O retorno do Google Apps Script está em formato inesperado.")


def horario_disponivel(data_escolhida, hora_escolhida, duracao, profissional):
    configuracao = PROFISSIONAIS[profissional]

    inicio = datetime.combine(data_escolhida, converter_hora(hora_escolhida))
    fim = inicio + timedelta(minutes=duracao)

    abertura = datetime.combine(
        data_escolhida,
        converter_hora(configuracao["inicio"])
    )

    fechamento = datetime.combine(
        data_escolhida,
        converter_hora(configuracao["fim"])
    )

    almoco_inicio = datetime.combine(
        data_escolhida,
        converter_hora(configuracao["almoco_inicio"])
    )

    almoco_fim = datetime.combine(
        data_escolhida,
        converter_hora(configuracao["almoco_fim"])
    )

    if inicio < abertura or fim > fechamento:
        return False

    if inicio < almoco_fim and fim > almoco_inicio:
        return False

    agora = datetime.now()

    if data_escolhida == date.today() and inicio <= agora:
        return False

    reservas = buscar_reservas()

    for reserva in reservas:
        if not isinstance(reserva, dict):
            continue

        data_reserva = str(reserva.get("data", ""))[:10]
        profissional_reserva = str(
            reserva.get("profissional", "")
        ).strip()

        if data_reserva != data_escolhida.isoformat():
            continue

        if profissional_reserva != profissional:
            continue

        hora_reserva = str(reserva.get("hora", ""))[:5]

        try:
            inicio_reserva = datetime.combine(
                data_escolhida,
                converter_hora(hora_reserva)
            )

            duracao_reserva = int(
                reserva.get("duracao", reserva.get("duracao_min", 30)) or 30
            )

            fim_reserva = inicio_reserva + timedelta(
                minutes=duracao_reserva
            )

            if inicio < fim_reserva and fim > inicio_reserva:
                return False

        except (ValueError, TypeError):
            continue

    return True


def listar_horarios(data_escolhida, profissional, duracao):
    configuracao = PROFISSIONAIS[profissional]
    horarios = []

    inicio = converter_hora(configuracao["inicio"])
    fim = converter_hora(configuracao["fim"])

    atual = datetime.combine(data_escolhida, inicio)
    limite = datetime.combine(data_escolhida, fim)

    while atual < limite:
        hora_texto = atual.strftime("%H:%M")

        try:
            if horario_disponivel(
                data_escolhida,
                hora_texto,
                duracao,
                profissional
            ):
                horarios.append(hora_texto)
        except Exception:
            raise

        atual += timedelta(minutes=30)

    return horarios


def enviar_agendamento():
    valor, duracao = calcular_totais()

    servico_texto = " + ".join(
        st.session_state.servicos_selecionados
    )

    payload = {
        "data": st.session_state.data_agendamento.isoformat(),
        "hora": st.session_state.hora_agendamento,
        "profissional": st.session_state.profissional,
        "cliente": st.session_state.cliente.strip(),
        "servico": servico_texto,
        "telefone": normalizar_telefone(st.session_state.telefone),
        "duracao": duracao
    }

    resposta = requests.post(
        SCRIPT_URL,
        data=payload,
        timeout=30
    )

    resposta.raise_for_status()

    try:
        retorno = resposta.json()
    except ValueError:
        raise Exception("O servidor retornou uma resposta inválida.")

    if not isinstance(retorno, dict):
        raise Exception("O retorno do servidor está em formato inesperado.")

    sucesso = retorno.get(
        "sucesso",
        retorno.get("success", retorno.get("ok"))
    )

    if sucesso is not True:
        mensagem = retorno.get(
            "mensagem",
            retorno.get("erro", retorno.get("error", "Não foi possível confirmar o agendamento."))
        )
        raise Exception(mensagem)

    return payload, valor, duracao


def montar_link_whatsapp(payload, valor, duracao):
    telefone = WHATSAPP_PADRAO

    data_formatada = datetime.strptime(
        payload["data"], "%Y-%m-%d"
    ).strftime("%d/%m/%Y")

    mensagem = f"""
Olá! Gostaria de confirmar meu agendamento na {NOME_SISTEMA}.

Cliente: {payload['cliente']}
Telefone: {payload['telefone']}
Serviço(s): {payload['servico']}
Profissional: {payload['profissional']}
Data: {data_formatada}
Horário: {payload['hora']}
Duração: {duracao} minutos
Valor total: {dinheiro(valor)}

Aguardo a confirmação. Obrigado!
"""

    return (
        f"https://wa.me/{telefone}"
        f"?text={quote(mensagem.strip())}"
    )


def avancar_etapa():
    st.session_state.etapa += 1


def voltar_etapa():
    st.session_state.etapa -= 1


def reiniciar_agendamento():
    for chave, valor in ESTADOS_INICIAIS.items():
        st.session_state[chave] = valor

    for chave in ["data_temp", "hora_temp", "nome_temp", "telefone_temp"]:
        if chave in st.session_state:
            del st.session_state[chave]

# ============================================================
# CABEÇALHO
# ============================================================

st.markdown("""
<div class="brand">
    <div class="brand-icon">💈</div>
    <div class="brand-title">BARBEARIA JOEL</div>
    <div class="brand-subtitle">ESTILO • CONFIANÇA • BEM-ESTAR</div>
    <div class="brand-slogan">Seu visual em boas mãos!</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ETAPA 1 — SERVIÇOS
# ============================================================

if st.session_state.etapa == 1:

    st.markdown(
        '<div class="section-title">✂️ Nossos Serviços</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Escolha um ou mais serviços para continuar.'
        '</div>',
        unsafe_allow_html=True
    )

    nomes_servicos = list(SERVICOS.keys())

    for inicio_lista in range(0, len(nomes_servicos), 2):
        colunas = st.columns(2)

        for indice, coluna in enumerate(colunas):
            posicao = inicio_lista + indice

            if posicao >= len(nomes_servicos):
                continue

            nome = nomes_servicos[posicao]
            dados = SERVICOS[nome]

            selecionado = nome in st.session_state.servicos_selecionados

            with coluna:
                st.markdown(f"""
                <div class="service-card">
                    <div class="service-icon">{dados['icone']}</div>
                    <div class="service-name">{nome}</div>
                    <div class="service-description">{dados['descricao']}</div>
                    <div class="service-price">{dinheiro(dados['preco'])}</div>
                    <div class="service-description">{dados['duracao']} minutos</div>
                </div>
                """, unsafe_allow_html=True)

                texto_botao = (
                    "✓ Selecionado"
                    if selecionado
                    else "+ Adicionar serviço"
                )

                if st.button(
                    texto_botao,
                    key=f"servico_{posicao}",
                    use_container_width=True
                ):
                    if selecionado:
                        st.session_state.servicos_selecionados.remove(nome)
                    else:
                        st.session_state.servicos_selecionados.append(nome)

                    st.rerun()

    if st.session_state.servicos_selecionados:
        valor, duracao = calcular_totais()

        st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

        st.markdown("**Serviços selecionados:**")

        for nome in st.session_state.servicos_selecionados:
            st.write(f"✓ {nome}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Duração total", f"{duracao} minutos")

        with col2:
            st.metric("Valor total", dinheiro(valor))

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

    if st.button(
        "CONTINUAR →",
        disabled=not st.session_state.servicos_selecionados,
        use_container_width=True
    ):
        avancar_etapa()
        st.rerun()

# ============================================================
# ETAPA 2 — PROFISSIONAL
# ============================================================

elif st.session_state.etapa == 2:

    st.markdown(
        '<div class="step-indicator">ETAPA 2 DE 5 — PROFISSIONAL</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">💈 Escolha o profissional</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Selecione quem realizará seu atendimento.'
        '</div>',
        unsafe_allow_html=True
    )

    profissional = st.radio(
        "Profissional disponível",
        options=list(PROFISSIONAIS.keys()),
        index=0 if not st.session_state.profissional else
        list(PROFISSIONAIS.keys()).index(st.session_state.profissional),
        key="profissional_temp"
    )

    st.session_state.profissional = profissional

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← VOLTAR", use_container_width=True):
            voltar_etapa()
            st.rerun()

    with col2:
        if st.button("CONTINUAR →", use_container_width=True):
            avancar_etapa()
            st.rerun()

# ============================================================
# ETAPA 3 — DATA E HORÁRIO
# ============================================================

elif st.session_state.etapa == 3:

    st.markdown(
        '<div class="step-indicator">ETAPA 3 DE 5 — DATA E HORÁRIO</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">📅 Escolha a data</div>',
        unsafe_allow_html=True
    )

    hoje = date.today()
    data_inicial = hoje

    while data_inicial.weekday() not in PROFISSIONAIS[
        st.session_state.profissional
    ]["dias"]:
        data_inicial += timedelta(days=1)

    if data_inicial < hoje:
        data_inicial = hoje

    data_escolhida = st.date_input(
        "Data do atendimento",
        value=(
            st.session_state.data_agendamento
            if st.session_state.data_agendamento
            else data_inicial
        ),
        min_value=hoje,
        max_value=hoje + timedelta(days=60),
        format="DD/MM/YYYY",
        key="data_temp"
    )

    st.session_state.data_agendamento = data_escolhida

    dias_validos = PROFISSIONAIS[
        st.session_state.profissional
    ]["dias"]

    if data_escolhida.weekday() not in dias_validos:
        st.warning("O profissional não atende aos domingos.")
        horarios = []
    else:
        valor, duracao = calcular_totais()

        try:
            with st.spinner("Consultando horários disponíveis..."):
                horarios = listar_horarios(
                    data_escolhida,
                    st.session_state.profissional,
                    duracao
                )
        except Exception as erro:
            horarios = []
            st.error(f"Não foi possível consultar a agenda: {erro}")

    st.markdown(
        '<div class="section-title">🕒 Horários disponíveis</div>',
        unsafe_allow_html=True
    )

    if horarios:
        horario_atual = st.session_state.hora_agendamento

        indice_horario = (
            horarios.index(horario_atual)
            if horario_atual in horarios
            else 0
        )

        horario_escolhido = st.radio(
            "Selecione um horário",
            horarios,
            index=indice_horario,
            key="hora_temp",
            horizontal=True
        )

        st.session_state.hora_agendamento = horario_escolhido

    else:
        st.session_state.hora_agendamento = ""
        st.info("Não há horários disponíveis para essa data e duração.")

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← VOLTAR", use_container_width=True):
            voltar_etapa()
            st.rerun()

    with col2:
        if st.button(
            "CONTINUAR →",
            disabled=not st.session_state.hora_agendamento,
            use_container_width=True
        ):
            avancar_etapa()
            st.rerun()

# ============================================================
# ETAPA 4 — DADOS DO CLIENTE
# ============================================================

elif st.session_state.etapa == 4:

    st.markdown(
        '<div class="step-indicator">ETAPA 4 DE 5 — SEUS DADOS</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">👤 Dados do cliente</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Informe seus dados para concluir o agendamento.'
        '</div>',
        unsafe_allow_html=True
    )

    nome = st.text_input(
        "Nome completo",
        value=st.session_state.cliente,
        placeholder="Digite seu nome",
        key="nome_temp"
    )

    telefone = st.text_input(
        "Telefone / WhatsApp",
        value=st.session_state.telefone,
        placeholder="(31) 99999-9999",
        key="telefone_temp"
    )

    st.session_state.cliente = nome
    st.session_state.telefone = telefone

    telefone_limpo = normalizar_telefone(telefone)

    dados_validos = (
        len(nome.strip()) >= 3
        and len(telefone_limpo) >= 10
        and len(telefone_limpo) <= 13
    )

    st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← VOLTAR", use_container_width=True):
            voltar_etapa()
            st.rerun()

    with col2:
        if st.button(
            "CONTINUAR →",
            disabled=not dados_validos,
            use_container_width=True
        ):
            avancar_etapa()
            st.rerun()

# ============================================================
# ETAPA 5 — RESUMO E CONFIRMAÇÃO
# ============================================================

elif st.session_state.etapa == 5:

    st.markdown(
        '<div class="step-indicator">ETAPA 5 DE 5 — CONFIRMAÇÃO</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">📋 Resumo do agendamento</div>',
        unsafe_allow_html=True
    )

    valor, duracao = calcular_totais()

    data_formatada = st.session_state.data_agendamento.strftime(
        "%d/%m/%Y"
    )

    lista_servicos = "".join(
        f"<li>{nome}</li>"
        for nome in st.session_state.servicos_selecionados
    )

    st.markdown(f"""
    <div class="summary-card">
        <h3>💈 BARBEARIA JOEL</h3>
        <hr>
        <b>Cliente:</b> {st.session_state.cliente}<br><br>
        <b>Telefone:</b> {st.session_state.telefone}<br><br>
        <b>Serviço(s):</b>
        <ul>{lista_servicos}</ul>
        <b>Profissional:</b> {st.session_state.profissional}<br><br>
        <b>Data:</b> {data_formatada}<br><br>
        <b>Horário:</b> {st.session_state.hora_agendamento}<br><br>
        <b>Duração:</b> {duracao} minutos
        <hr>
        <div class="summary-total">Total: {dinheiro(valor)}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.confirmado:
        dados = st.session_state.confirmado

        st.markdown("""
        <div class="success-card">
            <h2>✅ Agendamento registrado!</h2>
            <p>Seu horário foi registrado com sucesso.</p>
        </div>
        """, unsafe_allow_html=True)

        link_whatsapp = montar_link_whatsapp(
            dados["payload"],
            dados["valor"],
            dados["duracao"]
        )

        st.link_button(
            "📲 ENVIAR CONFIRMAÇÃO PELO WHATSAPP",
            link_whatsapp,
            use_container_width=True
        )

        if st.button("FAZER NOVO AGENDAMENTO", use_container_width=True):
            reiniciar_agendamento()
            st.rerun()

    else:
        st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("← VOLTAR", use_container_width=True):
                voltar_etapa()
                st.rerun()

        with col2:
            if st.button(
                "CONFIRMAR AGENDAMENTO",
                use_container_width=True
            ):
                if not SCRIPT_URL:
                    st.error(
                        "Configure SCRIPT_URL nos Secrets do Streamlit."
                    )
                else:
                    try:
                        with st.spinner("Confirmando seu agendamento..."):
                            # Nova consulta antes de enviar.
                            # O Apps Script também deve validar conflitos
                            # dentro de LockService no momento da gravação.
                            if not horario_disponivel(
                                st.session_state.data_agendamento,
                                st.session_state.hora_agendamento,
                                duracao,
                                st.session_state.profissional
                            ):
                                st.error(
                                    "Esse horário acabou de ser ocupado. "
                                    "Volte e escolha outro horário."
                                )
                            else:
                                payload, valor_final, duracao_final = (
                                    enviar_agendamento()
                                )

                                st.session_state.confirmado = {
                                    "payload": payload,
                                    "valor": valor_final,
                                    "duracao": duracao_final
                                }

                                st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao confirmar o agendamento: {erro}")

# ============================================================
# RODAPÉ SIMPLES
# ============================================================

st.markdown("""
<div style="
    text-align:center;
    color:#999999;
    font-size:11px;
    margin-top:35px;
    padding-top:15px;
    border-top:1px solid #333333;">
    💈 BARBEARIA JOEL
</div>
""", unsafe_allow_html=True)
