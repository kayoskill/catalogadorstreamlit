from datetime import date, datetime
from time import time
import streamlit as st
from modulos.conexao import Conexao_Iq
import pandas as pd
import numpy as np

st.set_page_config(page_title='Sr. Diretor', page_icon='〽')


@st.cache
def velas_frame(dicionario):
    frame = pd.DataFrame.from_dict(dicionario, orient='index')
    frame.drop(columns=['id', 'at'], inplace=True)
    frame.rename(columns={'from': 'inicio', 'to': 'fim',
                          'open': 'abertura', 'close': 'fechamento'}, inplace=True)
    frame['i_index'] = frame['inicio']
    frame['i_index'] = pd.to_datetime(
        frame['i_index'] - 10800, unit='s')
    frame['inicio'] = pd.to_datetime(
        frame['inicio']-10800, unit='s').dt.time
    frame['fim'] = pd.to_datetime(
        frame['fim'] - 10800, unit='s')
    frame.set_index('i_index', inplace=True)
    frame['direcao'] = np.where(
        frame['abertura'] == frame['fechamento'], 'doji', np.where(frame['abertura'] > frame['fechamento'], 'call', 'put'))
    return frame


def login(email, senha):
    iq = Conexao_Iq()
    iq.login(email, senha)
    return iq


@st.cache
def catalogar(frame, porcentagem):
    lista_horario = frame['inicio'].unique()
    dicionario = {}
    for l in lista_horario:
        call = frame.loc[(frame['inicio'] == l) & (
            frame['direcao'] == 'call')].shape[0]
        put = frame.loc[(frame['inicio'] == l) & (
            frame['direcao'] == 'put')].shape[0]
        doji = frame.loc[(frame['inicio'] == l) & (
            frame['direcao'] == 'doji')].shape[0]
        soma = (call+put+doji)
        p_call, p_put, p_doji = (call / soma) * \
            100, (put / soma) * 100, (doji / soma) * 100
        if p_call >= porcentagem or p_put >= porcentagem or p_doji >= porcentagem:
            dicionario.update(
                {l.strftime('%H:%M:%S'): {'call': round(p_call, 2), 'put': round(p_put, 2), 'doji': round(p_doji, 2)}})
        df = pd.DataFrame.from_dict(dicionario, orient='index')
    return df


st.sidebar.title('Painel de Configurações')
st.sidebar.subheader('Acesso a conta IQ:')
usuario = st.sidebar.text_input('Digite seu usuario:')
senha = st.sidebar.text_input('Digite sua senha:', type='password')
conectou, ativos, timeframe, periodo, data_inicio, iniciar = False, False, False, False, False, False
if usuario and senha:
    iq = login(usuario, senha)
    conectou = iq.checando()
    if not conectou:
        st.sidebar.error(conectou)

if conectou:
    abrir = open('modulos/lista_ativos.txt', 'rb+')
    ll_salva = []
    if ll_salva:
        for l in abrir.readlines():
            ll_salva.append(l)
        for l in iq.listar_ativos():
            if not l in ll_salva:
                abrir.write(f'{l}\n')
    abrir.close()
    abrir_lista = open('modulos/lista_ativos.txt')
    lista_ativos = [x.replace('\n', '') for x in abrir_lista.readlines()]

    st.sidebar.subheader('Ajustes para informações:')
    ativos = st.sidebar.multiselect('Selecione os ativos:', lista_ativos)
    periodo = st.sidebar.slider(
        'Selecione o periodo:', min_value=1, max_value=60)
    timeframe = st.sidebar.select_slider('Selecione Timeframe:', [
        '1', '5', '15', '30', '60', '120'])
    if timeframe:
        data_input = st.sidebar.date_input(
            'Data Inicial:', datetime.today().date())
        hora_input = st.sidebar.text_input(
            'Hora Inicial:', datetime.today().time().strftime('%H:%M'))
        if data_input and hora_input:
            data_inicio = f'{data_input} {hora_input}'
            data_inicio = datetime.fromisoformat(data_inicio)
    porcentagem = st.sidebar.number_input(
        'Igual ou maior:', min_value=1.00, max_value=100.00)
    iniciar = st.sidebar.button('Catalogar')

# Centro
st.title('Catalogador e Check-List')

if iniciar:
    for ativo in ativos:
        dic_velas = iq.velas(ativo, timeframe, periodo, data_inicio)
        fra_velas = velas_frame(dic_velas)
        print(fra_velas)
        cata = catalogar(fra_velas, porcentagem)
        st.write(f'{ativo}')
        st.dataframe(cata)
