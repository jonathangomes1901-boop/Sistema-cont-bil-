import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página (Nome "Jon" removido)
st.set_page_config(page_title="Sistema Contábil 2026", layout="wide")

# --- INICIALIZAÇÃO DO ESTADO DOS CAMPOS E HISTÓRICOS ---
if 'historico_aluguel' not in st.session_state:
    st.session_state.historico_aluguel = []
if 'historico_irrf' not in st.session_state:
    st.session_state.historico_irrf = []
if 'aluguel_erro' not in st.session_state:
    st.session_state.aluguel_erro = None
if 'irrf_erro' not in st.session_state:
    st.session_state.irrf_erro = None

# Inicializadores dos inputs para evitar conflitos de reset
if 'venc_input' not in st.session_state:
    st.session_state.venc_input = date.today()
if 'pagto_input' not in st.session_state:
    st.session_state.pagto_input = date.today()
if 'val_base_input' not in st.session_state:
    st.session_state.val_base_input = None
if 'p_multa_input' not in st.session_state:
    st.session_state.p_multa_input = None
if 'p_juros_input' not in st.session_state:
    st.session_state.p_juros_input = None
if 'obs_alu_input' not in st.session_state:
    st.session_state.obs_alu_input = ""

if 'renda_input' not in st.session_state:
    st.session_state.renda_input = None
if 'simplificado_input' not in st.session_state:
    st.session_state.simplificado_input = "Sim"
if 'obs_ir_input' not in st.session_state:
    st.session_state.obs_ir_input = ""


def formatar_moeda(valor):
    """
    Formata números para o padrão brasileiro de moeda (R$ X.XXX,XX)
    - Símbolo: R$ antes do valor com um espaço
    - Separador de milhar: Ponto (.)
    - Separador decimal: Vírgula (,)
    - Casas decimais: Sempre duas (centavos)
    """
    if valor is None: 
        return "R$ 0,00"
    
    # Formata inicialmente no padrão americano com duas casas decimais (Ex: 1,250.00)
    val_str = f"{valor:,.2f}"
    
    # Inverte os separadores: vírgula vira ponto, ponto vira vírgula
    val_str = val_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return f"R$ {val_str}"


# --- CALLBACKS DE CÁLCULO ---

def calcular_aluguel_callback():
    val_base = st.session_state.val_base_input
    if val_base is not None and val_base > 0:
        venc = st.session_state.venc_input
        pagto = st.session_state.pagto_input
        p_multa = st.session_state.p_multa_input or 0.0
        p_juros = st.session_state.p_juros_input or 0.0
        obs_alu = st.session_state.obs_alu_input
        
        atraso = max(0, (pagto - venc).days)
        v_multa = val_base * (p_multa / 100.0) if atraso > 0 else 0.0
        v_juros = (val_base * (p_juros / 100.0) / 30.0) * atraso
        total = val_base + v_multa + v_juros
        
        # Salva no histórico com a formatação monetária corrigida
        st.session_state.historico_aluguel.insert(0, {
            "Data Pagto": pagto.strftime('%d/%m/%Y'), 
            "Aluguel": formatar_moeda(val_base),
            "Multa": formatar_moeda(v_multa), 
            "Juros": formatar_moeda(v_juros),
            "Total": formatar_moeda(total), 
            "Obs": obs_alu
        })
        
        # Limpa os campos de forma segura
        st.session_state.val_base_input = None
        st.session_state.p_multa_input = None
        st.session_state.p_juros_input = None
        st.session_state.obs_alu_input = ""
        st.session_state.venc_input = date.today()
        st.session_state.pagto_input = date.today()
        st.session_state.aluguel_erro = None
    else:
        st.session_state.aluguel_erro = "⚠️ Insira o valor do aluguel para realizar o cálculo."


def calcular_irrf_callback():
    renda = st.session_state.renda_input
    if renda is not None and renda > 0:
        usar_simplificado = st.session_state.simplificado_input
        obs_ir = st.session_state.obs_ir_input
        
        base_calc = max(0.0, renda - (607.20 if usar_simplificado == "Sim" else 0.0))

        if base_calc <= 2259.20: 
            aliq, deduc = 0.0, 0.0
        elif base_calc <= 2826.65: 
            aliq, deduc = 7.5, 169.44
        elif base_calc <= 3751.05: 
            aliq, deduc = 15.0, 381.44
        elif base_calc <= 4664.68: 
            aliq, deduc = 22.5, 675.49
        else: 
            aliq, deduc = 27.5, 908.73
        
        ir_tabela = (base_calc * (aliq / 100.0)) - deduc
        ir_tabela = max(0.0, ir_tabela)

        # Mecanismo de Redução de Alíquotas 2026
        reducao = 0.0
        if renda <= 5000.00:
            reducao = 312.89
        elif 5000.01 <= renda <= 7350.00:
            reducao = 978.62 - (0.133145 * renda)
            
        reducao_efetiva = min(ir_tabela, max(0.0, reducao))
        ir_final = ir_tabela - reducao_efetiva

        # Salva no histórico com a formatação monetária corrigida
        st.session_state.historico_irrf.insert(0, {
            "Rendimento": formatar_moeda(renda),
            "IR Tabela": formatar_moeda(ir_tabela),
            "Redutor": formatar_moeda(reducao_efetiva),
            "IR a Pagar": formatar_moeda(ir_final),
            "Líquido": formatar_moeda(renda - ir_final),
            "Obs": obs_ir
        })
        
        # Limpa os campos de forma segura
        st.session_state.renda_input = None
        st.session_state.simplificado_input = "Sim"
        st.session_state.obs_ir_input = ""
        st.session_state.irrf_erro = None
    else:
        st.session_state.irrf_erro = "⚠️ Insira o rendimento mensal para realizar o cálculo."


# --- INTERFACE GRÁFICA ---

# Título ajustado para remover referências nominais e focar na área Contábil
st.title("⚖️ Sistema Contábil - Prontidão para 2026")

tab1, tab2 = st.tabs(["📊 Aluguel (Multa/Juros)", "💸 IRRF (Redução 2026)"])

# --- TELA 1: ALUGUEL ---
with tab1:
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        st.subheader("Cálculo de Aluguel")
        
        if st.session_state.aluguel_erro:
            st.error(st.session_state.aluguel_erro)
            st.session_state.aluguel_erro = None
            
        # Campos de entrada soltos (sem formulário) para evitar que a tecla "Enter" execute ações
        st.date_input("Vencimento", key="venc_input")
        st.date_input("Pagamento", key="pagto_input")
        st.number_input("Valor do Aluguel (R$)", min_value=0.0, step=0.01, format="%.2f", placeholder="0,00", key="val_base_input")
        st.number_input("Multa (%)", min_value=0, step=1, placeholder="Ex: 2", key="p_multa_input")
        st.number_input("Juros Mensal (%)", min_value=0, step=1, placeholder="Ex: 1", key="p_juros_input")
        st.text_input("Observação", key="obs_alu_input")
        
        # O processamento só é disparado no clique físico deste botão
        st.button("Calcular Registro", use_container_width=True, on_click=calcular_aluguel_callback, type="primary")

    with col_out:
        st.write("### Histórico de Aluguéis")
        st.dataframe(pd.DataFrame(st.session_state.historico_aluguel), use_container_width=True, hide_index=True)

# --- TELA 2: IRRF ---
with tab2:
    st.subheader("Cálculo IRPF - Mecanismo de Redução 2026")
    c_ir_in, c_ir_out = st.columns([1, 2])
    
    with c_ir_in:
        if st.session_state.irrf_erro:
            st.error(st.session_state.irrf_erro)
            st.session_state.irrf_erro = None
            
        # Campos de entrada soltos (sem formulário)
        st.number_input("Rendimento Mensal Bruto (R$)", min_value=0.0, step=0.01, format="%.2f", placeholder="Digite o valor", key="renda_input")
        st.radio("Desconto Simplificado (R$ 607,20)?", ["Sim", "Não"], key="simplificado_input")
        st.text_input("Observação", key="obs_ir_input")
        
        # O processamento só é disparado no clique físico deste botão
        st.button("Calcular Imposto", use_container_width=True, on_click=calcular_irrf_callback, type="primary")

    with c_ir_out:
        if st.session_state.historico_irrf:
            st.metric("IMPOSTO DEVIDO", st.session_state.historico_irrf[0]["IR a Pagar"])
            st.write("### Histórico IRRF")
            st.dataframe(pd.DataFrame(st.session_state.historico_irrf), use_container_width=True, hide_index=True)

# Barra lateral para limpeza geral
if st.sidebar.button("Limpar Todos os Registros"):
    st.session_state.historico_aluguel = []
    st.session_state.historico_irrf = []
    st.rerun()