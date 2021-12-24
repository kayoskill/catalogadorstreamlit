from datetime import datetime
from iqoptionapi.stable_api import IQ_Option
import streamlit as st
import time
import pandas as pd
import numpy as np


class Conexao_Iq():
    def __init__(self) -> None:
        pass

    def login(self, email, senha):
        self._api = IQ_Option(email, senha)

    def checando(self):
        self.conectou, self._rea = self._api.connect()
        if self.conectou:
            print('Conectado')
            return 'Conectado'
        else:
            if self._rea == "[Errno -2] Name or service not known":
                print('Sem Conexão')
                return 'Sem Conexão'
            elif self._rea == 'error_password':
                print('Erro Senha')
                return 'Error Senha'

    def listar_ativos(self):
        lista = []
        dicionario = self._api.get_all_open_time()
        for k, v in dicionario['digital'].items():
            lista.append(k)
        return lista

    def velas(self, ativo, timeframe, periodo, data):
        data = time.mktime(data.timetuple())
        periodo = ((60 * 24) / int(timeframe)) * int(periodo)
        timeframe = int(timeframe) * 60
        dados = self._api.get_candles(
            ativo, timeframe, periodo, data)
        dicionario = {}
        for dado in dados:
            dicionario.update({dado['from']: dado})
        return dicionario

    @staticmethod
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

    @staticmethod
    def catalogar(frame, porcentagem=10):
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


if __name__ == '__main__':
    api = Conexao_Iq()
    api.login('kcfservicos95@gmail.com', '90576edkf')
    if api.checando() == 'Conectado':
        dados = api.velas('EURUSD-OTC', 1, 1, datetime.now())
        f = api.velas_frame(dados)
        d = api.catalogar(f)
        print(d)
