
from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import csv
import io
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import streamlit as st
try:
    from core.session import initialize_session_state
except ModuleNotFoundError:
    def initialize_session_state():
        return None

try:
    from ui.components import render_sprint_banner
except ModuleNotFoundError:
    def render_sprint_banner():
        st.info("v6.0 - Sprint 4: interface em migração para os serviços modulares.")

try:
    from ui.import_tab import render_import_tab as render_import_tab_v6
    from ui.edit_tab import render_edit_tab as render_edit_tab_v6
    from ui.summary_tab import render_summary_tab as render_summary_tab_v6
    from ui.export_tab import render_export_tab as render_export_tab_v6
    from ui.conrestcon_tab import render_conrestcon_tab as render_conrestcon_tab_v6
    from ui.homologation_tab import render_homologation_tab as render_homologation_tab_v6
except ModuleNotFoundError:
    render_import_tab_v6 = None
    render_edit_tab_v6 = None
    render_summary_tab_v6 = None
    render_export_tab_v6 = None
    render_conrestcon_tab_v6 = None
    render_homologation_tab_v6 = None

from pypdf import PdfReader

APP_TITLE = "Gerador de CSV para Upload de Restrições Contábeis no SIAFI"
APP_SUBTITLE = ""
ORGAO_CODE = "26238"

TEMPLATE_LIBRARY: Dict[str, Dict[str, str]] = {
    "634 - Falta avaliação bens móveis/imóveis/intangíveis/outros": {
        "restricao": "634",
        "motivo": "Bens adquiridos antes de 2010 permanecem com valores históricos, necessitando de reavaliação.",
        "providencia": "Aguardando providências por parte da Administração Central para a realização do processo de reavaliação dos bens.",
    },
    "642 - Falta/registro incompleto de depreciação, amortização ou exaustão": {
        "restricao": "642",
        "motivo": "Bens adquiridos antes de 2010 não estão sendo depreciados.",
        "providencia": "Aguardando providências por parte da Administração Central para a realização do processo de reavaliação dos bens e, consequentemente, início do processo de depreciação.",
    },
    "640 - Saldo contábil de bens móveis não confere com RMB": {
        "restricao": "640",
        "motivo": "Saldo contábil de bens móveis não confere com RMB.",
        "providencia": "O saldo será ajustado no mês subsequente após a regularização dos registros patrimoniais.",
    },
    "603 - Saldo contábil do almoxarifado não confere com RMA": {
        "restricao": "603",
        "motivo": "Saldo contábil do almoxarifado não confere com RMA.",
        "providencia": "A divergência será analisada e ajustada no mês subsequente.",
    },
    "302 - Falta ou atraso de remessa do RMA ou RMB": {
        "restricao": "302",
        "motivo": "Falta ou atraso de remessa do RMA ou RMB.",
        "providencia": "Os lançamentos pendentes serão efetuados após o recebimento do relatório correspondente.",
    },
    "315 - Falta/restrição na conformidade de registros de gestão": {
        "restricao": "315",
        "motivo": "Ocorrência identificada na conformidade de registros de gestão.",
        "providencia": "Situação comunicada à área competente para regularização e acompanhamento.",
    },
    "697 - Saldo invertido": {
        "restricao": "697",
        "motivo": "Saldo invertido decorrente de classificação ou registro contábil inadequado.",
        "providencia": "O saldo será ajustado no mês subsequente, após análise do registro causador.",
    },
}

RESTRICTION_STANDARD_TEXT: Dict[str, Dict[str, str]] = {
    item["restricao"]: {"motivo": item["motivo"], "providencia": item["providencia"]}
    for item in TEMPLATE_LIBRARY.values()
}

CONRESTCON_MOTIVOS: Dict[str, str] = {
    "300": "Falta de conciliação bancária",
    "301": "Falta de remessa do mapa gerencial da dívida ativa",
    "302": "Falta ou atraso de remessa do RMA ou RMB",
    "303": "Falta de remessa do relatório de selos de controle",
    "304": "Falta de remessa do relatório de mercadorias apreendidas",
    "305": "Inconsistência na arrecadação por código de receita x destinação",
    "306": "Apropriação de despesas fora do período de competência",
    "307": "Receitas registradas fora do período",
    "308": "Divergência entre VPA e VPD de cota, repasse e sub-repasse",
    "309": "Divergência entre variações ativas e passivas extraorçamentárias",
    "310": "Classificação indevida de programa de trabalho",
    "311": "UCG órgão incompatível com estrutura formal",
    "312": "Volume significativo de execução orçamentária sem indicação de UGR",
    "313": "Registro de despesa alocada indevidamente à UCG/órgão",
    "314": "Existência de UGR sem vinculação a uma UCG",
    "315": "Falta ou restrição de conformidade dos registros de gestão",
    "316": "Falta ou atraso no cumprimento de diligências",
    "317": "Falta ou registro incompatível - AFAC",
    "318": "Não atendimento à orientação do órgão contábil setorial/central",
    "319": "Falta de registro de restrição ou conformidade dos registros de gestão",
    "320": "Falta de preenchimento da ficha cadastral de obrigação no SIAFI",
    "321": "Falta de atualização de provisão",
    "322": "Falta de registro e/ou inconsistência de centro de custos",
    "323": "Não inclusão de nota explicativa no SIAFIWeb",
    "538": "Saldos de imóveis de uso especial não conferem com SPIUNET",
    "550": "Falta de reconhecimento de passivo",
    "601": "Outros - variações ativas orçamentárias",
    "602": "Falta de registro contábil de débitos e créditos lançados pelo banco",
    "603": "Saldo contábil do almoxarifado não confere com RMA",
    "604": "Falta de atualização de ativos circulantes",
    "605": "Falta de reclassificação para curto prazo de valores de longo prazo - ativos",
    "606": "Saldo alongado ou indevido em contas transitórias do ativo circulante",
    "607": "Outros - ativo circulante",
    "608": "Saldo invertido - ativo circulante",
    "609": "Saldo contábil do almoxarifado não confere com controle",
    "610": "Saque com cartão de pagamento sem liquidação da despesa",
    "611": "Limite de contra-entrega de exercícios anteriores não devolvido",
    "612": "Divergência entre adiantamento de suprimento de fundos e controle orçamentário pago",
    "613": "Desequilíbrio entre rotina AF e PF de precatórios encaminhados",
    "614": "Não uso da vinculação de pagamento 551 - restituição de receita",
    "615": "Falta de atualização de valores do ativo não circulante",
    "616": "Outros - ativo não circulante",
    "617": "Saldo invertido - ativo não circulante",
    "618": "Falta de atualização de informações - dívida ativa LP",
    "619": "Falta de atualização de direito x receita de dívida ativa",
    "620": "Falta de atualização de ajustes para perdas da dívida ativa - CP",
    "621": "Falta de atualização de ajustes para perdas da dívida ativa - LP",
    "622": "Falta de atualização da dívida ativa",
    "623": "Falta de atualização de juros e multas da dívida ativa",
    "624": "Falta de atualização de informações - dívida ativa CP",
    "625": "Falta de registro ou atualização de ajustes para perdas prováveis",
    "626": "Omissão de baixa de valores prescritos - CP",
    "627": "Omissão de baixa de valores prescritos - LP",
    "628": "Saldo invertido - ativo não financeiro - investimentos",
    "629": "Saldo invertido - ativo não financeiro - imobilizado",
    "630": "Saldo invertido - ativo não financeiro - intangível",
    "631": "Saldo alongado ou indevido em contas transitórias do ativo não circulante - investimentos",
    "632": "Saldo alongado ou indevido em contas transitórias do ativo não circulante - imobilizado",
    "633": "Saldo alongado ou indevido em contas transitórias do ativo não circulante - intangível",
    "634": "Falta de avaliação de bens móveis, imóveis, intangíveis ou outros",
    "635": "Falta de registro ou atualização de ajustes para perdas prováveis",
    "636": "Ativo intangível diverge de controles internos",
    "640": "Saldo contábil de bens móveis não confere com RMB",
    "641": "Bens imóveis não classificados como uso especial",
    "642": "Falta ou registro incompatível de depreciação, amortização ou exaustão - ativo imobilizado",
    "643": "Falta ou evolução incompatível da amortização de ativo intangível",
    "645": "Outros - ativo permanente",
    "647": "Valores pendentes SPIUNET a ratificar",
    "650": "Restos a pagar invertidos (sem inscrição)",
    "651": "Falta ou inconsistência no contrato",
    "652": "Saldo invertido - classe 5",
    "653": "Saldo alongado ou indevido em contas de controle",
    "654": "Saldo contábil de selos de controle não confere com RMMA",
    "655": "Saldo contábil de mercadorias apreendidas não confere com RMMA",
    "656": "Convênios a comprovar com data expirada",
    "657": "Convênios a aprovar com data expirada",
    "658": "Outros - ativo compensado",
    "659": "Convênios a liberar expirados",
    "660": "Contrato de repasse a comprovar com data expirada",
    "661": "Contrato de repasse a aprovar com data expirada",
    "662": "Contrato de repasse a liberar expirados",
    "663": "Suprimento de fundos - saque superior ao limite permitido",
    "664": "Termo de parceria a liberar com vigência expirada",
    "665": "Termo de parceria a comprovar com vigência expirada",
    "666": "Termo de parceria a aprovar com vigência expirada",
    "667": "Não fechamento das classes 7 x 8",
    "668": "Acordo de cooperação técnica a comprovar - data expirada",
    "669": "Acordo de cooperação técnica a aprovar - data expirada",
    "670": "Acordo de cooperação técnica a liberar - data expirada",
    "671": "Transferência voluntária sem comprovação e não enviada para inadimplência",
    "672": "Falta de atualização de passivos circulantes",
    "673": "Falta de reclassificação do passivo não circulante para passivo circulante",
    "674": "Saldo alongado ou indevido em contas transitórias do passivo circulante",
    "675": "Outros - passivo circulante",
    "676": "Saldo invertido - passivo circulante",
    "677": "Falta ou atraso na retenção ou recolhimento de obrigações e tributos",
    "678": "Divergência da dívida interna CP",
    "679": "Divergência da dívida externa CP",
    "680": "Divergência entre valores liquidados e passivo financeiro",
    "681": "Regularização indevida de valores recebidos por GRU",
    "682": "Divergência entre títulos da dívida externa e operações de crédito",
    "683": "Regularização indevida de valores de OB canceladas",
    "684": "Falta de atualização de passivo não circulante",
    "685": "Outros - passivo não circulante",
    "686": "Saldo invertido - passivo não circulante",
    "687": "Divergência da dívida interna LP",
    "688": "Divergência da dívida externa LP",
    "689": "Falta de atualização do patrimônio líquido",
    "690": "Divergência entre capital subscrito registrado e o aprovado",
    "691": "Saldos de reservas superiores aos percentuais permitidos",
    "692": "Outros - patrimônio líquido",
    "693": "Saldo invertido - patrimônio líquido",
    "694": "Inconsistências em contas do patrimônio líquido",
    "695": "Não fechamento do grupo passivo compensado x retificadora",
    "696": "Outros - controles credores",
    "697": "Saldo invertido - classe 6",
    "698": "Divergência entre valor registrado na folha e relatórios",
    "699": "Pagamento de despesa com fonte/vinculação indevida",
    "700": "Falta de reclassificação, devolução, baixa ou anulação de suprimento de fundos",
    "701": "Outros - despesas",
    "702": "Apropriação de despesa com valor indevido",
    "703": "Erro na classificação da despesa",
    "704": "Pagamento sem liquidação da despesa",
    "705": "Falta de comprovação e prestação de contas de suprimento de fundos",
    "706": "Despesas do exercício corrente pagas com recursos de restos a pagar",
    "707": "Saldo invertido - classe 8",
    "708": "Comprovação de suprimento de fundos fora do prazo fixado",
    "709": "Concessão de terceiro suprimento de fundos sem comprovação de um dos anteriores",
    "710": "Registro de estorno de despesa indevido (receita)",
    "711": "Receita de fundo classificada como transferência",
    "712": "Outros - receita",
    "713": "Saldos alongados ou indevidos em contas transitórias de receitas",
    "714": "Saldo invertido - classe 7",
    "715": "Erro na classificação da receita",
    "716": "Registro de receita indevido (estorno de despesa)",
    "717": "Divergência entre arrecadação de receita e conta de controle",
    "718": "Outros - variações patrimoniais diminutivas",
    "719": "Saldo alongado ou indevido em contas transitórias do passivo não circulante",
    "720": "Saldo invertido - variações patrimoniais diminutivas",
    "721": "Saldo invertido - variações patrimoniais aumentativas",
    "722": "Divergência entre orçamento no SIAFI e lei/decreto (DOU)",
    "723": "NE indicadas na inscrição de RP x controle por empenho",
    "724": "Divergência entre despesa/receita de transferências estado/município",
    "725": "Divergência entre despesa/receita de transferências município/estado",
    "726": "Divergência entre saldos de exercícios anteriores e do balanço de abertura",
    "727": "Saldos não integrados",
    "728": "Integração de balancete de meses anteriores",
    "729": "Saldos incorretos por erro no processo de integração",
    "730": "Saldos de integração provisórios",
    "731": "Erro ou insuficiência na descrição do campo observação",
    "732": "Outros ingressos - balanço financeiro",
    "733": "Outros dispêndios - balanço financeiro",
    "734": "Outros ingressos - demonstração das disponibilidades financeiras - tipo 5",
    "735": "Outros dispêndios - demonstração das disponibilidades financeiras - tipo 5",
    "736": "Falta de registro de conformidade contábil",
    "737": "Utilização inadequada de eventos/situação CPR",
    "738": "Saldo invertido em contas correntes",
    "739": "Despesa realizada no balanço financeiro incompatível com a demonstração das variações patrimoniais",
    "740": "Receita realizada no balanço financeiro incompatível com o balanço orçamentário",
    "741": "Receita realizada no balanço financeiro incompatível com a demonstração das variações patrimoniais",
    "742": "Saldos invertidos - balanço patrimonial",
    "743": "Desequilíbrio entre totais do ativo e passivo",
    "744": "Desequilíbrio entre as classes",
    "745": "Saldos indevidos e/ou remanescentes no balanço financeiro",
    "746": "Desequilíbrio entre VPA/VPD na demonstração das variações patrimoniais",
    "747": "Demais incoerências - balanço financeiro",
    "748": "Demais incoerências - balanço patrimonial",
    "749": "Demais incoerências - DVP (demonstração das variações patrimoniais)",
    "750": "Demais incoerências - balanço orçamentário",
    "751": "Demais incoerências - demonstração das disponibilidades",
    "752": "Ativo financeiro (-) passivo financeiro - BP x superávit/déficit da demonstração das disponibilidades por fonte de recursos",
    "753": "Saldo invertido - balanço financeiro",
    "754": "Saldos alongados ou indevidos - demonstração das disponibilidades",
    "755": "Saldos alongados ou indevidos em contas transitórias de receitas - BF",
    "756": "Divergência entre limite de RP e disponibilidade de RP",
    "757": "Saldo alongado ou indevido em contas transitórias de receitas - DVP",
    "758": "Saldo alongado ou indevido em contas transitórias de receitas - BO",
    "759": "RP não processados (PF) x retificadora de RP não processados (PNF) - BP",
    "760": "Saldo invertido - demonstração da disponibilidade por fonte de recursos",
    "761": "Inconsistência nos registros da dívida ativa",
    "762": "Inconsistência entre limite vinculado e recursos a liberar",
    "763": "Inconsistência entre valores diferidos recebidos e concedidos",
    "764": "Saldo alongado ou indevido em contas do passivo compensado",
    "766": "Termo de cooperação a liberar - data expirada",
    "767": "Termo de cooperação a comprovar - data expirada",
    "768": "Falta de identificação de beneficiário em controle auxiliar de moradia",
    "769": "Inconsistência entre a inscrição e a execução de RP",
    "770": "Código de destinação da receita de DARF",
    "771": "Demais incoerências - demonstração dos fluxos de caixa (DFC)",
    "772": "Demais incoerências - DDR",
    "773": "TED a comprovar com data expirada",
    "774": "TED a aprovar com data expirada",
    "775": "TED a repassar expirados",
    "776": "Falta de reconhecimento de bens imóveis",
    "777": "Falta de apropriação de custos diretos no ativo imobilizado",
    "778": "Termo de fomento a liberar com vigência expirada",
    "779": "Termo de fomento a comprovar com vigência expirada",
    "780": "Termo de fomento a aprovar com vigência expirada",
    "781": "Erro na classificação da VPD",
    "782": "5º nível - distorção de classificação (AC)",
    "783": "5º nível - distorção de classificação (ANC)",
    "784": "5º nível - distorção de classificação (PC)",
    "785": "5º nível - distorção de classificação (PNC)",
    "786": "5º nível - distorção de classificação (VPD)",
    "787": "5º nível - distorção de classificação (VPA)"
}

CONRESTCON_ROWS = [
    {"Restrição": "300", "Título": "Falta de conciliação bancária"},
    {"Restrição": "301", "Título": "Falta de remessa do mapa gerencial da dívida ativa"},
    {"Restrição": "302", "Título": "Falta ou atraso de remessa do RMA ou RMB"},
    {"Restrição": "303", "Título": "Falta de remessa do relatório de selos de controle"},
    {"Restrição": "304", "Título": "Falta de remessa do relatório de mercadorias apreendidas"},
    {"Restrição": "305", "Título": "Inconsistência na arrecadação por código de receita x destinação"},
    {"Restrição": "306", "Título": "Apropriação de despesas fora do período de competência"},
    {"Restrição": "307", "Título": "Receitas registradas fora do período"},
    {"Restrição": "308", "Título": "Divergência entre VPA e VPD de cota, repasse e sub-repasse"},
    {"Restrição": "309", "Título": "Divergência entre variações ativas e passivas extraorçamentárias"},
    {"Restrição": "310", "Título": "Classificação indevida de programa de trabalho"},
    {"Restrição": "311", "Título": "UCG órgão incompatível com estrutura formal"},
    {"Restrição": "312", "Título": "Volume significativo de execução orçamentária sem indicação de UGR"},
    {"Restrição": "313", "Título": "Registro de despesa alocada indevidamente à UCG/órgão"},
    {"Restrição": "314", "Título": "Existência de UGR sem vinculação a uma UCG"},
    {"Restrição": "315", "Título": "Falta ou restrição de conformidade dos registros de gestão"},
    {"Restrição": "316", "Título": "Falta ou atraso no cumprimento de diligências"},
    {"Restrição": "317", "Título": "Falta ou registro incompatível - AFAC"},
    {"Restrição": "318", "Título": "Não atendimento à orientação do órgão contábil setorial/central"},
    {"Restrição": "319", "Título": "Falta de registro de restrição ou conformidade dos registros de gestão"},
    {"Restrição": "320", "Título": "Falta de preenchimento da ficha cadastral de obrigação no SIAFI"},
    {"Restrição": "321", "Título": "Falta de atualização de provisão"},
    {"Restrição": "322", "Título": "Falta de registro e/ou inconsistência de centro de custos"},
    {"Restrição": "323", "Título": "Não inclusão de nota explicativa no SIAFIWeb"},
    {"Restrição": "538", "Título": "Saldos de imóveis de uso especial não conferem com SPIUNET"},
    {"Restrição": "550", "Título": "Falta de reconhecimento de passivo"},
    {"Restrição": "601", "Título": "Outros - variações ativas orçamentárias"},
    {"Restrição": "602", "Título": "Falta de registro contábil de débitos e créditos lançados pelo banco"},
    {"Restrição": "603", "Título": "Saldo contábil do almoxarifado não confere com RMA"},
    {"Restrição": "604", "Título": "Falta de atualização de ativos circulantes"},
    {"Restrição": "605", "Título": "Falta de reclassificação para curto prazo de valores de longo prazo - ativos"},
    {"Restrição": "606", "Título": "Saldo alongado ou indevido em contas transitórias do ativo circulante"},
    {"Restrição": "607", "Título": "Outros - ativo circulante"},
    {"Restrição": "608", "Título": "Saldo invertido - ativo circulante"},
    {"Restrição": "609", "Título": "Saldo contábil do almoxarifado não confere com controle"},
    {"Restrição": "610", "Título": "Saque com cartão de pagamento sem liquidação da despesa"},
    {"Restrição": "611", "Título": "Limite de contra-entrega de exercícios anteriores não devolvido"},
    {"Restrição": "612", "Título": "Divergência entre adiantamento de suprimento de fundos e controle orçamentário pago"},
    {"Restrição": "613", "Título": "Desequilíbrio entre rotina AF e PF de precatórios encaminhados"},
    {"Restrição": "614", "Título": "Não uso da vinculação de pagamento 551 - restituição de receita"},
    {"Restrição": "615", "Título": "Falta de atualização de valores do ativo não circulante"},
    {"Restrição": "616", "Título": "Outros - ativo não circulante"},
    {"Restrição": "617", "Título": "Saldo invertido - ativo não circulante"},
    {"Restrição": "618", "Título": "Falta de atualização de informações - dívida ativa LP"},
    {"Restrição": "619", "Título": "Falta de atualização de direito x receita de dívida ativa"},
    {"Restrição": "620", "Título": "Falta de atualização de ajustes para perdas da dívida ativa - CP"},
    {"Restrição": "621", "Título": "Falta de atualização de ajustes para perdas da dívida ativa - LP"},
    {"Restrição": "622", "Título": "Falta de atualização da dívida ativa"},
    {"Restrição": "623", "Título": "Falta de atualização de juros e multas da dívida ativa"},
    {"Restrição": "624", "Título": "Falta de atualização de informações - dívida ativa CP"},
    {"Restrição": "625", "Título": "Falta de registro ou atualização de ajustes para perdas prováveis"},
    {"Restrição": "626", "Título": "Omissão de baixa de valores prescritos - CP"},
    {"Restrição": "627", "Título": "Omissão de baixa de valores prescritos - LP"},
    {"Restrição": "628", "Título": "Saldo invertido - ativo não financeiro - investimentos"},
    {"Restrição": "629", "Título": "Saldo invertido - ativo não financeiro - imobilizado"},
    {"Restrição": "630", "Título": "Saldo invertido - ativo não financeiro - intangível"},
    {"Restrição": "631", "Título": "Saldo alongado ou indevido em contas transitórias do ativo não circulante - investimentos"},
    {"Restrição": "632", "Título": "Saldo alongado ou indevido em contas transitórias do ativo não circulante - imobilizado"},
    {"Restrição": "633", "Título": "Saldo alongado ou indevido em contas transitórias do ativo não circulante - intangível"},
    {"Restrição": "634", "Título": "Falta de avaliação de bens móveis, imóveis, intangíveis ou outros"},
    {"Restrição": "635", "Título": "Falta de registro ou atualização de ajustes para perdas prováveis"},
    {"Restrição": "636", "Título": "Ativo intangível diverge de controles internos"},
    {"Restrição": "640", "Título": "Saldo contábil de bens móveis não confere com RMB"},
    {"Restrição": "641", "Título": "Bens imóveis não classificados como uso especial"},
    {"Restrição": "642", "Título": "Falta ou registro incompatível de depreciação, amortização ou exaustão - ativo imobilizado"},
    {"Restrição": "643", "Título": "Falta ou evolução incompatível da amortização de ativo intangível"},
    {"Restrição": "645", "Título": "Outros - ativo permanente"},
    {"Restrição": "647", "Título": "Valores pendentes SPIUNET a ratificar"},
    {"Restrição": "650", "Título": "Restos a pagar invertidos (sem inscrição)"},
    {"Restrição": "651", "Título": "Falta ou inconsistência no contrato"},
    {"Restrição": "652", "Título": "Saldo invertido - classe 5"},
    {"Restrição": "653", "Título": "Saldo alongado ou indevido em contas de controle"},
    {"Restrição": "654", "Título": "Saldo contábil de selos de controle não confere com RMMA"},
    {"Restrição": "655", "Título": "Saldo contábil de mercadorias apreendidas não confere com RMMA"},
    {"Restrição": "656", "Título": "Convênios a comprovar com data expirada"},
    {"Restrição": "657", "Título": "Convênios a aprovar com data expirada"},
    {"Restrição": "658", "Título": "Outros - ativo compensado"},
    {"Restrição": "659", "Título": "Convênios a liberar expirados"},
    {"Restrição": "660", "Título": "Contrato de repasse a comprovar com data expirada"},
    {"Restrição": "661", "Título": "Contrato de repasse a aprovar com data expirada"},
    {"Restrição": "662", "Título": "Contrato de repasse a liberar expirados"},
    {"Restrição": "663", "Título": "Suprimento de fundos - saque superior ao limite permitido"},
    {"Restrição": "664", "Título": "Termo de parceria a liberar com vigência expirada"},
    {"Restrição": "665", "Título": "Termo de parceria a comprovar com vigência expirada"},
    {"Restrição": "666", "Título": "Termo de parceria a aprovar com vigência expirada"},
    {"Restrição": "667", "Título": "Não fechamento das classes 7 x 8"},
    {"Restrição": "668", "Título": "Acordo de cooperação técnica a comprovar - data expirada"},
    {"Restrição": "669", "Título": "Acordo de cooperação técnica a aprovar - data expirada"},
    {"Restrição": "670", "Título": "Acordo de cooperação técnica a liberar - data expirada"},
    {"Restrição": "671", "Título": "Transferência voluntária sem comprovação e não enviada para inadimplência"},
    {"Restrição": "672", "Título": "Falta de atualização de passivos circulantes"},
    {"Restrição": "673", "Título": "Falta de reclassificação do passivo não circulante para passivo circulante"},
    {"Restrição": "674", "Título": "Saldo alongado ou indevido em contas transitórias do passivo circulante"},
    {"Restrição": "675", "Título": "Outros - passivo circulante"},
    {"Restrição": "676", "Título": "Saldo invertido - passivo circulante"},
    {"Restrição": "677", "Título": "Falta ou atraso na retenção ou recolhimento de obrigações e tributos"},
    {"Restrição": "678", "Título": "Divergência da dívida interna CP"},
    {"Restrição": "679", "Título": "Divergência da dívida externa CP"},
    {"Restrição": "680", "Título": "Divergência entre valores liquidados e passivo financeiro"},
    {"Restrição": "681", "Título": "Regularização indevida de valores recebidos por GRU"},
    {"Restrição": "682", "Título": "Divergência entre títulos da dívida externa e operações de crédito"},
    {"Restrição": "683", "Título": "Regularização indevida de valores de OB canceladas"},
    {"Restrição": "684", "Título": "Falta de atualização de passivo não circulante"},
    {"Restrição": "685", "Título": "Outros - passivo não circulante"},
    {"Restrição": "686", "Título": "Saldo invertido - passivo não circulante"},
    {"Restrição": "687", "Título": "Divergência da dívida interna LP"},
    {"Restrição": "688", "Título": "Divergência da dívida externa LP"},
    {"Restrição": "689", "Título": "Falta de atualização do patrimônio líquido"},
    {"Restrição": "690", "Título": "Divergência entre capital subscrito registrado e o aprovado"},
    {"Restrição": "691", "Título": "Saldos de reservas superiores aos percentuais permitidos"},
    {"Restrição": "692", "Título": "Outros - patrimônio líquido"},
    {"Restrição": "693", "Título": "Saldo invertido - patrimônio líquido"},
    {"Restrição": "694", "Título": "Inconsistências em contas do patrimônio líquido"},
    {"Restrição": "695", "Título": "Não fechamento do grupo passivo compensado x retificadora"},
    {"Restrição": "696", "Título": "Outros - controles credores"},
    {"Restrição": "697", "Título": "Saldo invertido - classe 6"},
    {"Restrição": "698", "Título": "Divergência entre valor registrado na folha e relatórios"},
    {"Restrição": "699", "Título": "Pagamento de despesa com fonte/vinculação indevida"},
    {"Restrição": "700", "Título": "Falta de reclassificação, devolução, baixa ou anulação de suprimento de fundos"},
    {"Restrição": "701", "Título": "Outros - despesas"},
    {"Restrição": "702", "Título": "Apropriação de despesa com valor indevido"},
    {"Restrição": "703", "Título": "Erro na classificação da despesa"},
    {"Restrição": "704", "Título": "Pagamento sem liquidação da despesa"},
    {"Restrição": "705", "Título": "Falta de comprovação e prestação de contas de suprimento de fundos"},
    {"Restrição": "706", "Título": "Despesas do exercício corrente pagas com recursos de restos a pagar"},
    {"Restrição": "707", "Título": "Saldo invertido - classe 8"},
    {"Restrição": "708", "Título": "Comprovação de suprimento de fundos fora do prazo fixado"},
    {"Restrição": "709", "Título": "Concessão de terceiro suprimento de fundos sem comprovação de um dos anteriores"},
    {"Restrição": "710", "Título": "Registro de estorno de despesa indevido (receita)"},
    {"Restrição": "711", "Título": "Receita de fundo classificada como transferência"},
    {"Restrição": "712", "Título": "Outros - receita"},
    {"Restrição": "713", "Título": "Saldos alongados ou indevidos em contas transitórias de receitas"},
    {"Restrição": "714", "Título": "Saldo invertido - classe 7"},
    {"Restrição": "715", "Título": "Erro na classificação da receita"},
    {"Restrição": "716", "Título": "Registro de receita indevido (estorno de despesa)"},
    {"Restrição": "717", "Título": "Divergência entre arrecadação de receita e conta de controle"},
    {"Restrição": "718", "Título": "Outros - variações patrimoniais diminutivas"},
    {"Restrição": "719", "Título": "Saldo alongado ou indevido em contas transitórias do passivo não circulante"},
    {"Restrição": "720", "Título": "Saldo invertido - variações patrimoniais diminutivas"},
    {"Restrição": "721", "Título": "Saldo invertido - variações patrimoniais aumentativas"},
    {"Restrição": "722", "Título": "Divergência entre orçamento no SIAFI e lei/decreto (DOU)"},
    {"Restrição": "723", "Título": "NE indicadas na inscrição de RP x controle por empenho"},
    {"Restrição": "724", "Título": "Divergência entre despesa/receita de transferências estado/município"},
    {"Restrição": "725", "Título": "Divergência entre despesa/receita de transferências município/estado"},
    {"Restrição": "726", "Título": "Divergência entre saldos de exercícios anteriores e do balanço de abertura"},
    {"Restrição": "727", "Título": "Saldos não integrados"},
    {"Restrição": "728", "Título": "Integração de balancete de meses anteriores"},
    {"Restrição": "729", "Título": "Saldos incorretos por erro no processo de integração"},
    {"Restrição": "730", "Título": "Saldos de integração provisórios"},
    {"Restrição": "731", "Título": "Erro ou insuficiência na descrição do campo observação"},
    {"Restrição": "732", "Título": "Outros ingressos - balanço financeiro"},
    {"Restrição": "733", "Título": "Outros dispêndios - balanço financeiro"},
    {"Restrição": "734", "Título": "Outros ingressos - demonstração das disponibilidades financeiras - tipo 5"},
    {"Restrição": "735", "Título": "Outros dispêndios - demonstração das disponibilidades financeiras - tipo 5"},
    {"Restrição": "736", "Título": "Falta de registro de conformidade contábil"},
    {"Restrição": "737", "Título": "Utilização inadequada de eventos/situação CPR"},
    {"Restrição": "738", "Título": "Saldo invertido em contas correntes"},
    {"Restrição": "739", "Título": "Despesa realizada no balanço financeiro incompatível com a demonstração das variações patrimoniais"},
    {"Restrição": "740", "Título": "Receita realizada no balanço financeiro incompatível com o balanço orçamentário"},
    {"Restrição": "741", "Título": "Receita realizada no balanço financeiro incompatível com a demonstração das variações patrimoniais"},
    {"Restrição": "742", "Título": "Saldos invertidos - balanço patrimonial"},
    {"Restrição": "743", "Título": "Desequilíbrio entre totais do ativo e passivo"},
    {"Restrição": "744", "Título": "Desequilíbrio entre as classes"},
    {"Restrição": "745", "Título": "Saldos indevidos e/ou remanescentes no balanço financeiro"},
    {"Restrição": "746", "Título": "Desequilíbrio entre VPA/VPD na demonstração das variações patrimoniais"},
    {"Restrição": "747", "Título": "Demais incoerências - balanço financeiro"},
    {"Restrição": "748", "Título": "Demais incoerências - balanço patrimonial"},
    {"Restrição": "749", "Título": "Demais incoerências - DVP (demonstração das variações patrimoniais)"},
    {"Restrição": "750", "Título": "Demais incoerências - balanço orçamentário"},
    {"Restrição": "751", "Título": "Demais incoerências - demonstração das disponibilidades"},
    {"Restrição": "752", "Título": "Ativo financeiro (-) passivo financeiro - BP x superávit/déficit da demonstração das disponibilidades por fonte de recursos"},
    {"Restrição": "753", "Título": "Saldo invertido - balanço financeiro"},
    {"Restrição": "754", "Título": "Saldos alongados ou indevidos - demonstração das disponibilidades"},
    {"Restrição": "755", "Título": "Saldos alongados ou indevidos em contas transitórias de receitas - BF"},
    {"Restrição": "756", "Título": "Divergência entre limite de RP e disponibilidade de RP"},
    {"Restrição": "757", "Título": "Saldo alongado ou indevido em contas transitórias de receitas - DVP"},
    {"Restrição": "758", "Título": "Saldo alongado ou indevido em contas transitórias de receitas - BO"},
    {"Restrição": "759", "Título": "RP não processados (PF) x retificadora de RP não processados (PNF) - BP"},
    {"Restrição": "760", "Título": "Saldo invertido - demonstração da disponibilidade por fonte de recursos"},
    {"Restrição": "761", "Título": "Inconsistência nos registros da dívida ativa"},
    {"Restrição": "762", "Título": "Inconsistência entre limite vinculado e recursos a liberar"},
    {"Restrição": "763", "Título": "Inconsistência entre valores diferidos recebidos e concedidos"},
    {"Restrição": "764", "Título": "Saldo alongado ou indevido em contas do passivo compensado"},
    {"Restrição": "766", "Título": "Termo de cooperação a liberar - data expirada"},
    {"Restrição": "767", "Título": "Termo de cooperação a comprovar - data expirada"},
    {"Restrição": "768", "Título": "Falta de identificação de beneficiário em controle auxiliar de moradia"},
    {"Restrição": "769", "Título": "Inconsistência entre a inscrição e a execução de RP"},
    {"Restrição": "770", "Título": "Código de destinação da receita de DARF"},
    {"Restrição": "771", "Título": "Demais incoerências - demonstração dos fluxos de caixa (DFC)"},
    {"Restrição": "772", "Título": "Demais incoerências - DDR"},
    {"Restrição": "773", "Título": "TED a comprovar com data expirada"},
    {"Restrição": "774", "Título": "TED a aprovar com data expirada"},
    {"Restrição": "775", "Título": "TED a repassar expirados"},
    {"Restrição": "776", "Título": "Falta de reconhecimento de bens imóveis"},
    {"Restrição": "777", "Título": "Falta de apropriação de custos diretos no ativo imobilizado"},
    {"Restrição": "778", "Título": "Termo de fomento a liberar com vigência expirada"},
    {"Restrição": "779", "Título": "Termo de fomento a comprovar com vigência expirada"},
    {"Restrição": "780", "Título": "Termo de fomento a aprovar com vigência expirada"},
    {"Restrição": "781", "Título": "Erro na classificação da VPD"},
    {"Restrição": "782", "Título": "5º nível - distorção de classificação (AC)"},
    {"Restrição": "783", "Título": "5º nível - distorção de classificação (ANC)"},
    {"Restrição": "784", "Título": "5º nível - distorção de classificação (PC)"},
    {"Restrição": "785", "Título": "5º nível - distorção de classificação (PNC)"},
    {"Restrição": "786", "Título": "5º nível - distorção de classificação (VPD)"},
    {"Restrição": "787", "Título": "5º nível - distorção de classificação (VPA)"}
]

UG_NAME_MAP: Dict[str, str] = {
    "152370": "Diretoria de Educação a Distância e Educação Digital",
    "153062": "Universidade Federal de Minas Gerais",
    "153254": "Administração Geral da UFMG",
    "153255": "Biblioteca Universitária da UFMG",
    "153256": "Editora da UFMG",
    "153257": "Centro de Comunicação da UFMG",
    "153258": "Diretoria de Tecnologia da Informação",
    "153260": "Centro Esportivo Universitário da UFMG",
    "153261": "Hospital das Clínicas da UFMG",
    "153262": "Imprensa Universitária da UFMG",
    "153263": "Laboratório de Computação Científica da UFMG",
    "153264": "Museu Histórico Natural da UFMG",
    "153265": "Departamento de Obras da UFMG",
    "153267": "Departamento de Manutenção e Operação da Infraestrutura da UFMG",
    "153269": "Pró-Reitoria de Administração da UFMG",
    "153270": "Pró-Reitoria de Planejamento e Desenvolvimento da UFMG",
    "153271": "Pró-Reitoria de Graduação da UFMG",
    "153272": "Pró-Reitoria de Extensão da UFMG",
    "153273": "Pró-Reitoria de Pesquisa da UFMG",
    "153274": "Pró-Reitoria de Pós-Graduação da UFMG",
    "153275": "Escola de Arquitetura da UFMG",
    "153276": "Escola de Belas Artes da UFMG",
    "153277": "Escola de Ciência da Informação da UFMG",
    "153278": "Escola de Educação Física, Fisioterapia e Terapia Ocupacional da UFMG",
    "153279": "Escola de Enfermagem da UFMG",
    "153280": "Escola de Engenharia da UFMG",
    "153281": "Escola de Música da UFMG",
    "153282": "Escola de Veterinária da UFMG",
    "153283": "Faculdade de Ciências Econômicas da UFMG",
    "153284": "Faculdade de Direito da UFMG",
    "153285": "Faculdade de Educacao da UFMG",
    "153286": "Faculdade de Farmácia da UFMG",
    "153287": "Faculdade de Filosofia e Ciências Humanas da UFMG",
    "153288": "Faculdade de Letras da UFMG",
    "153289": "Faculdade de Medicina da UFMG",
    "153290": "Faculdade de Odontologia da UFMG",
    "153291": "Instituto de Ciências Biológicas da UFMG",
    "153292": "Instituto de Ciências Exatas da UFMG",
    "153293": "Instituto de Geociências da UFMG",
    "153294": "Centro Pedagógico da UFMG",
    "153295": "Colégio Técnico da UFMG",
    "153296": "Instituto de Ciências Agrárias da UFMG",
    "154459": "Pró-Reitoria de Cultura da UFMG"
}

MONTHS = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
MONTH_ABBR_PT = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
}
MONTH_ABBR_REV = {v: k for k, v in MONTH_ABBR_PT.items()}

NIVEL_OPTIONS = {
    "1": "1 - Conformidade Contábil de UG",
    "2": "2 - Conformidade Contábil de Órgão",
}


@dataclass
class RestrictionRow:
    ug: str
    restricao: str
    motivo: str = ""
    providencia: str = ""
    valor: str = ""


@dataclass
class UGSummaryRow:
    ug: str
    nome_ug: str = ""
    quantidade_restricoes: int = 0
    codigos_restricao: str = "-"
    descricoes_resumidas: str = "-"
    situacao: str = "Sem restrição"



@dataclass
class ReportMetadata:
    # Campos operacionais já utilizados pela ferramenta
    setorial_contabil: str = ""
    mes_referencia: str = ""
    mes_referencia_raw: str = ""
    mes_referencia_identificado: bool = False
    mes_referencia_falha: str = ""

    # Campos adicionais do cabeçalho do PDF
    data_hora_consulta: str = ""
    usuario_mascarado: str = ""
    titulo_relatorio: str = ""
    nivel_relatorio: str = ""
    situacao_relatorio: str = ""
    entidade_relatorio: str = ""
    tipo_relatorio: str = ""

    logs: List[str] = None

    def __post_init__(self):
        if self.logs is None:
            self.logs = []


def normalize_spaces(text: str) -> str:
    if text is None:
        return ""
    text = str(text).replace("\r", " ").replace("\n", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_text_field(text: str, limit: int = 1024) -> str:
    text = normalize_spaces(text)
    text = text.replace("¿", "'")
    text = re.sub(r"\s*;\s*", "; ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s*\.\s*", ". ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].strip()


def strip_pdf_artifacts(text: str, limit: int = 1024) -> str:
    text = clean_text_field(text, limit=limit)
    if not text:
        return ""
    artifact_patterns = [
        r"\b\d{3}\s+\d+\s+de\s+\d+\b.*$",
        r"\b\d+\s+de\s+\d+\b.*$",
        r"\bVers[aã]o\s+Data/Hora\b.*$",
        r"\bOpera[cç][aã]o\b.*$",
        r"\bAltera[cç][aã]o\b.*$",
        r"\bUnidade\s+Gestora\s+e\s+Conformista\b.*$",
        r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\b.*$",
    ]
    for pattern in artifact_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+", " ", text).strip(" ;,.:-")
    return text[:limit].strip()



def sentence_case_ptbr(text: str) -> str:
    text = normalize_spaces(text)
    if not text:
        return ""
    lowered = text.lower()
    return lowered[0].upper() + lowered[1:]


def title_case_ptbr(text: str) -> str:
    text = normalize_spaces(text)
    if not text:
        return ""
    lower_words = {"de", "da", "do", "das", "dos", "e", "em", "para", "por", "com", "a", "o", "as", "os"}
    words = re.split(r"(\s+)", text.lower())
    out = []
    first_word_seen = False
    for token in words:
        if not token or token.isspace():
            out.append(token)
            continue
        if not first_word_seen or token not in lower_words:
            out.append(token[:1].upper() + token[1:])
        else:
            out.append(token)
        first_word_seen = True
    return "".join(out)


def invert_case_ptbr(text: str) -> str:
    text = normalize_spaces(text)
    return "".join(ch.lower() if ch.isupper() else ch.upper() if ch.islower() else ch for ch in text)


def camel_case_ptbr(text: str) -> str:
    text = normalize_spaces(text)
    if not text:
        return ""
    parts = re.split(r"[^A-Za-zÀ-ÿ0-9]+", text)
    parts = [p for p in parts if p]
    if not parts:
        return ""
    first = parts[0].lower()
    rest = [p[:1].upper() + p[1:].lower() for p in parts[1:]]
    return first + "".join(rest)




def apply_capitalization_mode(text: str, mode: str) -> str:
    if not text:
        return ""
    if mode == "Primeira letra maiúscula":
        return sentence_case_ptbr(text)
    if mode == "minúsculas":
        return text.lower()
    if mode == "MAIÚSCULAS":
        return text.upper()
    if mode == "Capitalizar Cada Palavra":
        return title_case_ptbr(text)
    return text


def finalize_punctuation(text: str) -> str:
    text = normalize_spaces(text)
    if not text:
        return ""
    text = re.sub(r"[;:,\.\-\s]+$", "", text)
    return text + "."


def sanitize_digits(value: str, length: Optional[int] = None) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if length is None:
        return digits
    return digits.zfill(length) if digits else ""


def parse_currency_to_siafi(value: str) -> str:
    if value is None:
        return ""
    text = normalize_spaces(str(value))
    if not text:
        return ""
    text = text.replace("R$", "").replace(" ", "")
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text:
        return ""
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        cents = round(float(text) * 100)
    except ValueError:
        return ""
    if cents < 0:
        return ""
    out = str(cents)
    return out if len(out) <= 17 else ""


def format_siafi_value_to_brl(value: str) -> str:
    if not value:
        return ""
    cents = int(value)
    reais = cents / 100
    return f"R$ {reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def month_abbr_pt(month: int) -> str:
    return MONTH_ABBR_PT.get(int(month), "mes")



def build_standard_filename(month: int | str, year: str) -> str:
    if month in ("", None):
        return ""
    month = int(month)
    year_digits = sanitize_digits(year, None)
    yy = year_digits[-2:] if len(year_digits) >= 2 else str(datetime.now().year)[-2:]
    return f"{month:02d}_{month_abbr_pt(month)}_{yy}.csv"



def extract_pdf_header_page(uploaded_file) -> str:
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    reader = PdfReader(uploaded_file)
    first_page = reader.pages[0].extract_text() or ""
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    return first_page



def parse_pdf_header_from_first_page(header_text: str) -> Dict[str, str]:
    text = header_text.replace("\xa0", " ")

    def search(pattern: str) -> str:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return ""
        value = m.group(1) if m.lastindex else m.group(0)
        return normalize_spaces(value)

    data_hora_consulta = search(r"Data\s*e\s*hora\s*da\s*consulta\s*:\s*(\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2})")
    usuario_mascarado = search(r"Usu[aá]rio\s*:\s*([\*\.\-\d]+)")
    titulo_relatorio = search(r"(RELAT[ÓO]RIO\s+DE\s+CONFORMIDADE\s+CONT[ÁA]BIL)")
    nivel_relatorio = search(r"N[ií]vel\s*:\s*([12]\s*\-\s*Conformidade\s+Cont[aá]bil\s+de\s+(?:UG|[ÓO]rg[aã]o))")
    situacao_relatorio = search(r"Situa[cç][aã]o\s*:\s*([23]\s*\-\s*(?:Com|Sem)\s+Restri[cç][aã]o)")
    entidade_relatorio = search(r"Entidade\s*:\s*(\d{6}\s*\-\s*[^\n\r]+?)\s*(?:M[eê]s\s+de\s+Refer[êe]ncia|[A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})")
    tipo_relatorio = search(r"(Relat[óo]rio\s+Completo\s+por\s+Setorial\s+Cont[aá]bil)")
    setorial_contabil = search(r"Setorial\s+Cont[aá]bil\s*:\s*(\d{6}\s*\-\s*[^\n\r]+)")

    mes_raw = ""
    month_patterns = [
        r"M[eê]s\s*de\s*Refer[êe]ncia\s*:\s*([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})",
        r"([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})\s*M[eê]s\s*de\s*Refer[êe]ncia\s*:",
        r"([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})M[eê]s\s*de\s*Refer[êe]ncia\s*:",
        r"M[eê]s\s*de\s*Refer[êe]ncia\s*\n?\s*([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})",
        r"([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})\s*Relat[óo]rio\s+Completo\s+por\s+Setorial\s+Cont[aá]bil",
    ]
    for pat in month_patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            mes_raw = normalize_spaces(m.group(1))
            break

    mes_norm = normalize_month_reference(mes_raw) if mes_raw else ""

    return {
        "data_hora_consulta": data_hora_consulta,
        "usuario_mascarado": usuario_mascarado,
        "titulo_relatorio": titulo_relatorio,
        "nivel_relatorio": nivel_relatorio,
        "situacao_relatorio": situacao_relatorio,
        "entidade_relatorio": entidade_relatorio,
        "tipo_relatorio": tipo_relatorio,
        "setorial_contabil_linha": setorial_contabil,
        "mes_referencia_raw": mes_raw,
        "mes_referencia": mes_norm,
    }


def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    texts: List[str] = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)


def detect_csv_delimiter(lines: List[str]) -> str:
    if not lines:
        return ";"
    sample = "\n".join(lines[:10])
    candidates = [";", "\t", ","]
    counts = {d: max([ln.count(d) for ln in lines[:10]] or [0]) for d in candidates}
    delimiter = max(counts, key=counts.get)
    if counts[delimiter] == 0:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=";\t,").delimiter
        except Exception:
            delimiter = ";"
    return delimiter



def source_signature(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    try:
        payload = uploaded_file.getvalue()
    except Exception:
        return ""
    return f"{getattr(uploaded_file, 'name', '')}|{len(payload)}"


def normalize_month_reference(raw: str) -> str:
    raw = normalize_spaces(raw).lower()
    translit = (
        raw.replace("ç", "c")
           .replace("á", "a").replace("à", "a").replace("â", "a").replace("ã", "a")
           .replace("é", "e").replace("ê", "e")
           .replace("í", "i")
           .replace("ó", "o").replace("ô", "o").replace("õ", "o")
           .replace("ú", "u")
    )
    m = re.search(r"\b([a-z]{3})\s*/\s*((?:19|20)?\d{2,4})\b", translit)
    if not m:
        return ""
    mon = m.group(1)[:3]
    year = m.group(2)
    if len(year) == 2:
        year = f"20{year}"
    month_num = MONTH_ABBR_REV.get(mon)
    if not month_num:
        return ""
    return f"{MONTH_ABBR_PT[month_num]}/{year}"









def parse_month_year_value(raw: str) -> Tuple[str, str]:
    raw_norm = normalize_spaces("" if raw is None else str(raw))
    if not raw_norm:
        return "", ""

    norm = normalize_month_reference(raw_norm)
    if norm:
        try:
            month_num = MONTH_ABBR_REV.get(norm.split("/")[0], "")
            year = norm.split("/")[1]
            return str(month_num), str(year)
        except Exception:
            pass

    m = re.search(r"\b(0?[1-9]|1[0-2])\s*[/\-]\s*((?:19|20)\d{2})\b", raw_norm)
    if m:
        return str(int(m.group(1))), m.group(2)

    translit = (
        raw_norm.lower()
        .replace("ç", "c")
        .replace("á", "a").replace("à", "a").replace("â", "a").replace("ã", "a")
        .replace("é", "e").replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u")
    )
    nomes = {
        "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
        "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
    }
    for nome, num in nomes.items():
        m2 = re.search(rf"\b{nome}\b\s*[/\-]?\s*((?:19|20)\d{{2}})\b", translit)
        if m2:
            return str(num), m2.group(1)

    return "", ""


def infer_month_year_from_filename(filename: str) -> Tuple[str, str]:
    name = Path(filename).stem.lower()

    m = re.search(r"\b(0?[1-9]|1[0-2])[_\- ]([a-zçãáâéêíóôõú]{3,9})[_\- ]((?:19|20)?\d{2,4})\b", name)
    if m:
        month_num = str(int(m.group(1)))
        year = m.group(3)
        if len(year) == 2:
            year = f"20{year}"
        return month_num, year

    m = re.search(r"\b([a-zçãáâéêíóôõú]{3,9})[_\- ]((?:19|20)?\d{2,4})\b", name)
    if m:
        month_num, year = parse_month_year_value(f"{m.group(1)}/{m.group(2)}")
        if month_num:
            return month_num, year

    m = re.search(r"\b(0?[1-9]|1[0-2])[_\- ]((?:19|20)\d{2})\b", name)
    if m:
        return str(int(m.group(1))), m.group(2)

    return "", ""


def infer_month_year_from_structured_df(df: pd.DataFrame) -> Tuple[str, str]:
    if df is None or df.empty:
        return "", ""

    for col in df.columns:
        col_norm = normalize_spaces(str(col)).lower()
        if "mês de referência" in col_norm or "mes de referencia" in col_norm or col_norm in {"mês", "mes", "referência", "referencia"}:
            vals = df[col].dropna().astype(str).tolist()
            for val in vals[:12]:
                month_num, year = parse_month_year_value(val)
                if month_num:
                    return month_num, year

    sample = df.head(12).fillna("").astype(str)
    for _, row in sample.iterrows():
        for val in row.tolist():
            month_num, year = parse_month_year_value(val)
            if month_num:
                return month_num, year

    return "", ""
def extract_consulta_month(raw_text: str) -> Tuple[str, str]:
    text = raw_text.replace("\xa0", " ")
    patterns = [
        r"M[eê]s\s*de\s*Refer[êe]ncia\s*[:\-]?\s*([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})",
        r"M[eê]s\s*Refer[êe]ncia\s*[:\-]?\s*([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})",
        r"Refer[êe]ncia\s*[:\-]?\s*([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})",
        r"M[eê]s\s*[:\-]?\s*([A-Za-zÀ-ÿ]{3}\s*/\s*(?:19|20)?\d{2,4})",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            raw_month = m.group(1)
            norm = normalize_month_reference(raw_month)
            if norm:
                return norm, raw_month
    return "", ""


def parse_pdf_header_fields(raw_text: str) -> Dict[str, str]:
    """
    Especificação do parser do cabeçalho do PDF de Conformidade Contábil.

    Campos-alvo:
    1. Data e hora da consulta
       Ex.: 'Data e hora da consulta: 16/04/2026 15:24'
    2. Usuário
       Ex.: 'Usuário: ***.565.596-**'
    3. Título do relatório
       Ex.: 'RELATÓRIO DE CONFORMIDADE CONTÁBIL'
    4. Nível
       Ex.: '1 - Conformidade Contábil de UG'
    5. Situação
       Ex.: '3 - Com Restrição' ou '2 - Sem Restrição'
    6. Entidade
       Ex.: '153254 - ADMINISTRACAO GERAL/UFMG'
    7. Mês de Referência
       Ex.: 'Mar/2026'
    8. Tipo do relatório
       Ex.: 'Relatório Completo por Setorial Contábil'
    9. Setorial Contábil
       Ex.: '153062 - UNIVERSIDADE FEDERAL DE MINAS GERAIS'

    Estratégia:
    - priorizar leitura na primeira página textual do documento;
    - aceitar quebras de linha entre rótulo e valor;
    - normalizar espaços extras;
    - não depender de posição fixa, e sim do rótulo textual.
    """
    text = raw_text.replace("\xa0", " ")

    def search(pattern: str) -> str:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return ""
        value = m.group(1) if m.lastindex else m.group(0)
        return normalize_spaces(value)

    data_hora_consulta = search(r"Data\s*e\s*hora\s*da\s*consulta\s*:\s*(\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2})")
    usuario_mascarado = search(r"Usu[aá]rio\s*:\s*([\*\.\-\d]+)")
    titulo_relatorio = search(r"(RELAT[ÓO]RIO\s+DE\s+CONFORMIDADE\s+CONT[ÁA]BIL)")
    nivel_relatorio = search(r"N[ií]vel\s*:\s*([12]\s*\-\s*Conformidade\s+Cont[aá]bil\s+de\s+(?:UG|[ÓO]rg[aã]o))")
    situacao_relatorio = search(r"Situa[cç][aã]o\s*:\s*([23]\s*\-\s*(?:Com|Sem)\s+Restri[cç][aã]o)")
    entidade_relatorio = search(r"Entidade\s*:\s*(\d{6}\s*\-\s*[^\n\r]+?)\s*M[eê]s\s+de\s+Refer[êe]ncia")
    tipo_relatorio = search(r"(Relat[óo]rio\s+Completo\s+por\s+Setorial\s+Cont[aá]bil)")
    setorial_contabil = search(r"Setorial\s+Cont[aá]bil\s*:\s*(\d{6}\s*\-\s*[^\n\r]+)")

    mes_norm, mes_raw = extract_consulta_month(text)

    return {
        "data_hora_consulta": data_hora_consulta,
        "usuario_mascarado": usuario_mascarado,
        "titulo_relatorio": titulo_relatorio,
        "nivel_relatorio": nivel_relatorio,
        "situacao_relatorio": situacao_relatorio,
        "entidade_relatorio": entidade_relatorio,
        "tipo_relatorio": tipo_relatorio,
        "setorial_contabil_linha": setorial_contabil,
        "mes_referencia_raw": mes_raw,
        "mes_referencia": mes_norm,
    }




def extract_report_metadata(raw_text: str, header_text: str = "") -> ReportMetadata:
    md = ReportMetadata()

    parsed = parse_pdf_header_fields(raw_text)
    if header_text:
        parsed_header = parse_pdf_header_from_first_page(header_text)
        # Prioriza mês do cabeçalho da primeira página quando encontrado
        if parsed_header.get("mes_referencia"):
            parsed["mes_referencia"] = parsed_header.get("mes_referencia", "")
            parsed["mes_referencia_raw"] = parsed_header.get("mes_referencia_raw", "")
        for key in ["data_hora_consulta", "usuario_mascarado", "titulo_relatorio", "nivel_relatorio", "situacao_relatorio", "entidade_relatorio", "tipo_relatorio", "setorial_contabil_linha"]:
            if parsed_header.get(key):
                parsed[key] = parsed_header[key]

    md.data_hora_consulta = parsed.get("data_hora_consulta", "")
    md.usuario_mascarado = parsed.get("usuario_mascarado", "")
    md.titulo_relatorio = parsed.get("titulo_relatorio", "")
    md.nivel_relatorio = parsed.get("nivel_relatorio", "")
    md.situacao_relatorio = parsed.get("situacao_relatorio", "")
    md.entidade_relatorio = parsed.get("entidade_relatorio", "")
    md.tipo_relatorio = parsed.get("tipo_relatorio", "")

    setorial_line = parsed.get("setorial_contabil_linha", "")
    setorial_match = re.search(r"(\d{6})", setorial_line)
    if setorial_match:
        md.setorial_contabil = setorial_match.group(1)

    md.mes_referencia_raw = parsed.get("mes_referencia_raw", "")
    md.mes_referencia = parsed.get("mes_referencia", "")
    md.mes_referencia_identificado = bool(md.mes_referencia)
    md.mes_referencia_falha = ""

    if md.data_hora_consulta:
        md.logs.append(f"Data e hora da consulta identificada: {md.data_hora_consulta}.")
    if md.usuario_mascarado:
        md.logs.append(f"Usuário identificado no cabeçalho: {md.usuario_mascarado}.")
    if md.nivel_relatorio:
        md.logs.append(f"Nível identificado: {md.nivel_relatorio}.")
    if md.situacao_relatorio:
        md.logs.append(f"Situação identificada: {md.situacao_relatorio}.")
    if md.entidade_relatorio:
        md.logs.append(f"Entidade identificada: {md.entidade_relatorio}.")
    if md.setorial_contabil:
        md.logs.append(f"Setorial contábil identificada: {md.setorial_contabil}.")
    if md.mes_referencia:
        md.logs.append(f"Mês de referência identificado no PDF: {md.mes_referencia}.")
    else:
        md.logs.append("Mês de referência não identificado no cabeçalho do PDF.")
    return md


def parse_report_text(raw_text: str) -> List[RestrictionRow]:
    text = raw_text.replace("\xa0", " ")
    parts = re.split(r"(?=\bUG:\s*\d{6}\s*-)", text)
    rows: List[RestrictionRow] = []
    pattern = re.compile(
        r"Restrição:\s*(\d{3})\s*-.*?"
        r"(?:Valor:\s*([\d\.,]+))?\s*"
        r"Motivo:\s*(.*?)\s*"
        r"Provid[êe]ncia:\s*(.*?)\s*"
        r"(?=Restrição:\s*\d{3}\s*-|\d{3}\s+\d+\s+de\s+\d+|Versão\s+Data/Hora|Operação|Alteração|Unidade\s+Gestora\s+e\s+Conformista|$)",
        flags=re.DOTALL | re.IGNORECASE,
    )
    for part in parts:
        ug_match = re.search(r"\bUG:\s*(\d{6})\s*-", part)
        if not ug_match:
            continue
        ug = ug_match.group(1)
        for m in pattern.finditer(part):
            valor = parse_currency_to_siafi(m.group(2)) if m.group(2) else ""
            rows.append(
                RestrictionRow(
                    ug=ug,
                    restricao=m.group(1),
                    motivo=strip_pdf_artifacts(m.group(3) or ""),
                    providencia=strip_pdf_artifacts(m.group(4) or ""),
                    valor=valor,
                )
            )
    return rows



def extract_all_ugs_from_report(raw_text: str) -> pd.DataFrame:
    text = raw_text.replace("\xa0", " ")
    lines = text.splitlines()

    rows = []
    current_status = "Sem restrição"

    for raw_line in lines:
        line = normalize_spaces(raw_line)
        if not line:
            continue

        # status base por bloco/página
        if re.search(r"\bCom Restrição\b", line, flags=re.IGNORECASE):
            current_status = "Com restrição"
        elif re.search(r"\bSem Restrição\b", line, flags=re.IGNORECASE):
            current_status = "Sem restrição"

        # captura apenas a linha da UG e limita o nome até o fim da linha
        m = re.match(r"UG:\s*(\d{6})\s*-\s*([^\n\r]+)$", line, flags=re.IGNORECASE)
        if m:
            ug = m.group(1)
            nome = m.group(2).strip()

            # limpeza defensiva caso a extração venha colada com resíduos
            nome = re.sub(
                r"\s*(Grupo:|Restrição:|Motivo:|Providência:|001\s+\d+\s+de\s+\d+|Versão\s+Data/Hora|Operação|Alteração).*",
                "",
                nome,
                flags=re.IGNORECASE,
            ).strip(" -")
            rows.append({"UG": ug, "Nome da UG": UG_NAME_MAP.get(ug, nome), "SituaçãoBase": current_status})

    if not rows:
        return pd.DataFrame(columns=["UG", "Nome da UG", "SituaçãoBase"])

    df = pd.DataFrame(rows).drop_duplicates(subset=["UG"], keep="first")
    return df.sort_values("UG").reset_index(drop=True)




def parse_existing_csv(uploaded_file) -> Tuple[Dict[str, str], List[RestrictionRow]]:
    raw = uploaded_file.getvalue()
    decoded = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            decoded = raw.decode(enc)
            break
        except Exception:
            continue
    if decoded is None:
        raise ValueError("Não foi possível ler o CSV com as codificações suportadas.")

    lines = [line for line in decoded.splitlines() if line.strip() and not line.strip().lower().startswith("sep=")]
    if len(lines) < 2:
        raise ValueError("CSV inválido: o arquivo precisa conter ao menos header e trailer.")

    delimiter = detect_csv_delimiter(lines)
    parsed = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter, quotechar='"'))

    first = None
    last = None
    first_idx = None
    last_idx = None

    for i, row in enumerate(parsed):
        if not row:
            continue
        rec0 = str(row[0]).strip().replace("\ufeff", "")
        if first is None and rec0 == "H":
            first = row
            first_idx = i
        if rec0 == "T":
            last = row
            last_idx = i

    if first is None:
        raise ValueError("CSV inválido: não foi localizado o registro Header iniciado por H.")
    if last is None or last_idx is None or first_idx is None or last_idx <= first_idx:
        raise ValueError("CSV inválido: não foi localizado o registro Trailer iniciado por T.")

    while len(first) < 7:
        first.append("")

    nivel = normalize_spaces(first[1] if len(first) > 1 else "1")
    if nivel not in {"1", "2"}:
        nivel = "1"

    codigo_responsavel = sanitize_digits(first[2] if len(first) > 2 else "", None)

    raw_month = normalize_spaces(first[3] if len(first) > 3 else "")
    month_num = ""
    if raw_month:
        # tenta como inteiro puro (3, 03)
        digits = sanitize_digits(raw_month, None)
        if digits and digits.isdigit():
            try:
                n = int(digits)
                if 1 <= n <= 12:
                    month_num = str(n)
            except Exception:
                pass
        # tenta interpretar formatos textuais (03/2026, mar/2026, março/2026, 03-mar)
        if not month_num:
            m1, _y1 = parse_month_year_value(raw_month)
            if m1:
                month_num = m1
        if not month_num:
            file_month, _file_year = infer_month_year_from_filename(getattr(uploaded_file, "name", ""))
            month_num = file_month or ""

    file_month, file_year = infer_month_year_from_filename(getattr(uploaded_file, "name", ""))

    header = {
        "nivel": nivel,
        "codigo_responsavel": codigo_responsavel,
        "mes": month_num or file_month,
        "setorial_contabil": "",
        "ano": file_year or str(datetime.now().year),
    }

    rows: List[RestrictionRow] = []
    for row in parsed[first_idx + 1:last_idx]:
        if not row:
            continue
        rec = normalize_spaces(str(row[0]))
        if rec != "D":
            continue
        while len(row) < 7:
            row.append("")
        rows.append(
            RestrictionRow(
                ug=sanitize_digits(row[1] if len(row) > 1 else "", 6),
                restricao=sanitize_digits(row[2] if len(row) > 2 else "", 3),
                motivo=strip_pdf_artifacts(row[3] if len(row) > 3 else ""),
                providencia=strip_pdf_artifacts(row[4] if len(row) > 4 else ""),
                valor=sanitize_digits(row[5] if len(row) > 5 else "", None),
            )
        )
    return header, rows


def parse_structured_table(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        raw = uploaded_file.getvalue()
        decoded = None
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                decoded = raw.decode(enc)
                break
            except Exception:
                continue
        if decoded is None:
            raise ValueError("Não foi possível ler a planilha CSV.")
        lines = [line for line in decoded.splitlines() if line.strip()]
        delim = detect_csv_delimiter(lines)
        return pd.read_csv(io.StringIO(decoded), delimiter=delim)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(uploaded_file)
    raise ValueError("Formato tabular não suportado. Utilize CSV, XLSX ou XLS.")


def _find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    normalized = {re.sub(r"\s+", " ", str(c).strip().lower()): c for c in df.columns}
    for candidate in candidates:
        candidate = candidate.lower()
        for key, original in normalized.items():
            if candidate == key or candidate in key:
                return original
    return None


def map_table_to_rows(df: pd.DataFrame) -> List[RestrictionRow]:
    ug_col = _find_column(df, ["ug", "unidade gestora", "codigo ug", "código ug"])
    restr_col = _find_column(df, ["restrição", "restricao", "codigo restrição", "código restrição", "codigo restricao"])
    mot_col = _find_column(df, ["motivo"])
    prov_col = _find_column(df, ["providência", "providencia"])
    val_col = _find_column(df, ["valor", "valor restrição", "valor restricao"])
    if not ug_col or not restr_col:
        raise ValueError("A planilha precisa conter, no mínimo, colunas de UG e Restrição.")
    rows: List[RestrictionRow] = []
    for _, row in df.iterrows():
        ug = sanitize_digits(row.get(ug_col, ""), 6)
        restr = sanitize_digits(row.get(restr_col, ""), 3)
        if not ug or not restr:
            continue
        motivo = clean_text_field("" if mot_col is None or pd.isna(row.get(mot_col, "")) else str(row.get(mot_col, "")))
        providencia = clean_text_field("" if prov_col is None or pd.isna(row.get(prov_col, "")) else str(row.get(prov_col, "")))
        valor = ""
        if val_col is not None and not pd.isna(row.get(val_col, "")):
            valor = parse_currency_to_siafi(str(row.get(val_col, "")))
        rows.append(RestrictionRow(ug=ug, restricao=restr, motivo=motivo, providencia=providencia, valor=valor))
    return rows


def rows_to_dataframe(rows: List[RestrictionRow]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["UG", "Restrição", "Motivo", "Providência", "Valor_SIAFI", "Valor_Formatado"])
    df = pd.DataFrame([asdict(r) for r in rows]).rename(
        columns={"ug": "UG", "restricao": "Restrição", "motivo": "Motivo", "providencia": "Providência", "valor": "Valor_SIAFI"}
    )
    df["Valor_Formatado"] = df["Valor_SIAFI"].apply(format_siafi_value_to_brl)
    return df


def conrestcon_to_dataframe() -> pd.DataFrame:
    return pd.DataFrame(CONRESTCON_ROWS)


def filter_conrestcon_dataframe(df: pd.DataFrame, code_query: str, selected_code: str) -> pd.DataFrame:
    out = df.copy()
    code_query = normalize_spaces(code_query)
    if selected_code and selected_code != "Todos":
        out = out[out["Restrição"].astype(str) == str(selected_code)]
    if code_query:
        out = out[
            out["Restrição"].astype(str).str.contains(code_query, case=False, na=False)
            | out["Título"].astype(str).str.contains(code_query, case=False, na=False)
        ]
    return out.sort_values("Restrição").reset_index(drop=True)


def dataframe_to_rows(df: pd.DataFrame) -> List[RestrictionRow]:
    rows: List[RestrictionRow] = []
    if df is None or df.empty:
        return rows
    for _, row in df.iterrows():
        ug = sanitize_digits(row.get("UG", ""), 6)
        restr = sanitize_digits(row.get("Restrição", ""), 3)
        if not ug or not restr:
            continue
        motivo = clean_text_field("" if pd.isna(row.get("Motivo", "")) else str(row.get("Motivo", "")))
        providencia = clean_text_field("" if pd.isna(row.get("Providência", "")) else str(row.get("Providência", "")))
        valor_raw = "" if pd.isna(row.get("Valor_SIAFI", "")) else str(row.get("Valor_SIAFI", ""))
        valor = sanitize_digits(valor_raw, None)
        rows.append(RestrictionRow(ug=ug, restricao=restr, motivo=motivo, providencia=providencia, valor=valor))
    return rows



def standardize_text_value(text: str, capitalizacao: str) -> str:
    text = strip_pdf_artifacts(text)
    text = re.sub(r"\s+", " ", text).strip()
    replacements = {
        "administracao central": "Administração Central",
        "reavaliacao": "reavaliação",
        "depreciacao": "depreciação",
        "providencias": "providências",
    }
    txt_norm = text.lower()
    for old, new in replacements.items():
        txt_norm = txt_norm.replace(old, new.lower())
    text = txt_norm
    text = apply_capitalization_mode(text, capitalizacao)
    return finalize_punctuation(text) if text else ""



def standardize_row_text(row: RestrictionRow, usar_texto_padrao_por_restricao: bool, capitalizacao: str) -> RestrictionRow:
    motivo = row.motivo
    providencia = row.providencia

    if usar_texto_padrao_por_restricao and row.restricao in CONRESTCON_MOTIVOS:
        motivo = apply_capitalization_mode(CONRESTCON_MOTIVOS[row.restricao], capitalizacao)
        motivo = finalize_punctuation(motivo) if motivo else ""
        providencia = standardize_text_value(providencia, capitalizacao) if providencia else ""
    else:
        motivo = standardize_text_value(motivo, capitalizacao) if motivo else ""
        providencia = standardize_text_value(providencia, capitalizacao) if providencia else ""

    return RestrictionRow(
        ug=sanitize_digits(row.ug, 6),
        restricao=sanitize_digits(row.restricao, 3),
        motivo=motivo,
        providencia=providencia,
        valor=sanitize_digits(row.valor, None),
    )


def standardize_rows(rows: List[RestrictionRow], usar_texto_padrao_por_restricao: bool, capitalizacao: str) -> Tuple[List[RestrictionRow], List[int]]:
    updated = []
    changed_indices = []
    for idx, row in enumerate(rows):
        new_row = standardize_row_text(row, usar_texto_padrao_por_restricao, capitalizacao)
        updated.append(new_row)
        if asdict(new_row) != asdict(row):
            changed_indices.append(idx)
    return updated, changed_indices


def filter_rows(rows: List[RestrictionRow], ug_filter: str, restr_filter: str) -> List[RestrictionRow]:
    out = []
    for row in rows:
        ug_ok = ug_filter == "Todas" or row.ug == ug_filter
        restr_ok = restr_filter == "Todas" or row.restricao == restr_filter
        if ug_ok and restr_ok:
            out.append(row)
    return out


def replace_filtered_rows(all_rows: List[RestrictionRow], filtered_rows: List[RestrictionRow], ug_filter: str, restr_filter: str) -> Tuple[List[RestrictionRow], List[int]]:
    updated = []
    changed_indices = []
    filtered_iter = iter(filtered_rows)
    for idx, row in enumerate(all_rows):
        ug_ok = ug_filter == "Todas" or row.ug == ug_filter
        restr_ok = restr_filter == "Todas" or row.restricao == restr_filter
        if ug_ok and restr_ok:
            try:
                new_row = next(filtered_iter)
                updated.append(new_row)
                if asdict(new_row) != asdict(row):
                    changed_indices.append(idx)
            except StopIteration:
                changed_indices.append(idx)
        else:
            updated.append(row)
    remaining = list(filtered_iter)
    if remaining:
        start_idx = len(updated)
        updated.extend(remaining)
        changed_indices.extend(list(range(start_idx, start_idx + len(remaining))))
    return updated, changed_indices


def apply_batch_text_update(rows: List[RestrictionRow], ug_filter: str, restr_filter: str, motivo: str, providencia: str, overwrite: bool = False) -> Tuple[List[RestrictionRow], List[int]]:
    new_rows = []
    changed_indices = []
    for idx, row in enumerate(rows):
        ug_ok = ug_filter == "Todas" or row.ug == ug_filter
        restr_ok = restr_filter == "Todas" or row.restricao == restr_filter
        if ug_ok and restr_ok:
            new_motivo = row.motivo
            new_providencia = row.providencia
            if motivo and (overwrite or not normalize_spaces(new_motivo)):
                new_motivo = clean_text_field(motivo)
            if providencia and (overwrite or not normalize_spaces(new_providencia)):
                new_providencia = clean_text_field(providencia)
            new_row = RestrictionRow(ug=row.ug, restricao=row.restricao, motivo=new_motivo, providencia=new_providencia, valor=row.valor)
            new_rows.append(new_row)
            if asdict(new_row) != asdict(row):
                changed_indices.append(idx)
        else:
            new_rows.append(row)
    return new_rows, changed_indices




def standardize_selected_indices(rows: List[RestrictionRow], selected_indices: List[int], usar_texto_padrao_por_restricao: bool, capitalizacao: str) -> Tuple[List[RestrictionRow], List[int]]:
    selected_set = set(selected_indices)
    updated: List[RestrictionRow] = []
    changed_indices: List[int] = []
    for idx, row in enumerate(rows):
        if idx in selected_set:
            new_row = standardize_row_text(row, usar_texto_padrao_por_restricao, capitalizacao)
            updated.append(new_row)
            if asdict(new_row) != asdict(row):
                changed_indices.append(idx)
        else:
            updated.append(row)
    return updated, changed_indices


def get_scope_global_indices(rows: List[RestrictionRow], scope: str, ug_filter: str, restr_filter: str, selected_indices: List[int]) -> List[int]:
    if scope == "Base inteira":
        return list(range(len(rows)))
    if scope == "Filtro atual":
        return [idx for idx, row in enumerate(rows) if (ug_filter == "Todas" or row.ug == ug_filter) and (restr_filter == "Todas" or row.restricao == restr_filter)]
    return list(selected_indices or [])



def apply_capitalization_to_scope(rows: List[RestrictionRow], target_indices: List[int], capitalizacao: str) -> Tuple[List[RestrictionRow], List[int]]:
    selected_set = set(target_indices)
    updated: List[RestrictionRow] = []
    changed_indices: List[int] = []
    for idx, row in enumerate(rows):
        if idx not in selected_set:
            updated.append(row)
            continue

        motivo = standardize_text_value(row.motivo, capitalizacao) if row.motivo else ""
        providencia = standardize_text_value(row.providencia, capitalizacao) if row.providencia else ""

        new_row = RestrictionRow(
            ug=sanitize_digits(row.ug, 6),
            restricao=sanitize_digits(row.restricao, 3),
            motivo=motivo,
            providencia=providencia,
            valor=sanitize_digits(row.valor, None),
        )
        updated.append(new_row)
        if asdict(new_row) != asdict(row):
            changed_indices.append(idx)
    return updated, changed_indices


def apply_restriction_standardization_to_scope(rows: List[RestrictionRow], target_indices: List[int]) -> Tuple[List[RestrictionRow], List[int]]:
    selected_set = set(target_indices)
    updated: List[RestrictionRow] = []
    changed_indices: List[int] = []
    for idx, row in enumerate(rows):
        if idx not in selected_set:
            updated.append(row)
            continue
        motivo = row.motivo
        if row.restricao in CONRESTCON_MOTIVOS:
            motivo = finalize_punctuation(CONRESTCON_MOTIVOS[row.restricao])
        new_row = RestrictionRow(
            ug=sanitize_digits(row.ug, 6),
            restricao=sanitize_digits(row.restricao, 3),
            motivo=motivo,
            providencia=row.providencia,
            valor=sanitize_digits(row.valor, None),
        )
        updated.append(new_row)
        if asdict(new_row) != asdict(row):
            changed_indices.append(idx)
    return updated, changed_indices



def render_edit_module_title(title: str):
    st.markdown(
        f"<div style='font-size: 1.0rem; font-weight: 700; margin: 0.35rem 0 0.5rem 0;'>{title}</div>",
        unsafe_allow_html=True,
    )
def validate_header(nivel: str, codigo_responsavel: str, mes: int, setorial_contabil: str = "") -> List[str]:
    issues = []
    if nivel not in {"1", "2"}:
        issues.append("Nível inválido. Utilize apenas 1 (UG) ou 2 (Órgão).")
    if nivel == "2" and codigo_responsavel != ORGAO_CODE:
        issues.append(f"Para nível Órgão, o código responsável deve ser {ORGAO_CODE}.")
    if nivel == "1":
        if not re.fullmatch(r"\d{6}", codigo_responsavel):
            issues.append("Para nível UG, o código responsável deve conter 6 dígitos.")
        if setorial_contabil and codigo_responsavel != setorial_contabil:
            issues.append("Para nível UG, o código responsável deve corresponder à Setorial Contábil do relatório/base.")
    if mes < 1 or mes > 12:
        issues.append("Mês de referência deve estar entre 1 e 12.")
    return issues


def validate_rows(rows: List[RestrictionRow], bloquear_duplicidades: bool = True) -> Tuple[List[str], List[str]]:
    errors, warnings = [], []
    if not rows:
        errors.append("Nenhuma linha de detalhe foi gerada.")
        return errors, warnings
    seen = {}
    for idx, row in enumerate(rows, start=1):
        if not re.fullmatch(r"\d{6}", row.ug):
            errors.append(f"Linha {idx}: UG inválida ({row.ug}).")
        if not re.fullmatch(r"\d{3}", row.restricao):
            errors.append(f"Linha {idx}: código de restrição inválido ({row.restricao}).")
        if len(row.motivo) > 1024:
            errors.append(f"Linha {idx}: motivo excede 1024 caracteres.")
        if len(row.providencia) > 1024:
            errors.append(f"Linha {idx}: providência excede 1024 caracteres.")
        if row.valor and not re.fullmatch(r"\d{1,17}", row.valor):
            errors.append(f"Linha {idx}: valor deve conter apenas dígitos, com até 17 posições.")
        key = (row.ug, row.restricao)
        seen[key] = seen.get(key, 0) + 1
        if not row.motivo:
            warnings.append(f"Linha {idx}: motivo está vazio.")
        if not row.providencia:
            warnings.append(f"Linha {idx}: providência está vazia.")
    duplicates = [f"UG {ug} + restrição {restr}" for (ug, restr), count in seen.items() if count > 1]
    if duplicates:
        msg = "Foram identificadas duplicidades de UG + restrição: " + "; ".join(duplicates[:20])
        if bloquear_duplicidades:
            errors.append(msg)
        else:
            warnings.append(msg)
    return errors, warnings


def build_csv_content(nivel: str, codigo_responsavel: str, mes: int, rows: List[RestrictionRow]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(["H", nivel, codigo_responsavel, mes, " ", " ", "|"])
    for row in rows:
        writer.writerow(["D", row.ug, row.restricao, row.motivo, row.providencia, row.valor, "|"])
    writer.writerow(["T", len(rows), "", "", "", "", "|"])
    return output.getvalue()






def summarize_by_restriction(rows: List[RestrictionRow]) -> pd.DataFrame:
    df = rows_to_dataframe(rows)
    if df.empty:
        return pd.DataFrame(columns=["Restrição", "Quantidade"])
    out = (
        df.groupby("Restrição", dropna=False)
        .agg(Quantidade=("UG", "count"))
        .reset_index()
        .sort_values(["Quantidade", "Restrição"], ascending=[False, True])
    )
    out["Restrição"] = out["Restrição"].astype(str).apply(
        lambda code: f"{str(code).zfill(3)} - {CONRESTCON_MOTIVOS.get(str(code).zfill(3), '')}".rstrip(" -")
    )
    return out


def rows_to_summary(rows: List[RestrictionRow], all_ugs_df: pd.DataFrame) -> pd.DataFrame:
    df_rows = rows_to_dataframe(rows)
    grouped = {}
    if not df_rows.empty:
        for ug, g in df_rows.groupby("UG"):
            codes = sorted(set(g["Restrição"].astype(str)))
            grouped[str(ug)] = {
                "Quantidade de Restrições": int(len(g)),
                "Códigos de Restrição": "; ".join(codes),
                "Situação": "Com restrição",
            }

    base = all_ugs_df.copy() if all_ugs_df is not None and not all_ugs_df.empty else pd.DataFrame(columns=["UG", "Nome da UG"])
    if base.empty and grouped:
        base = pd.DataFrame({"UG": sorted(grouped.keys()), "Nome da UG": [""] * len(grouped)})

    if "SituaçãoBase" in base.columns:
        base = base.rename(columns={"SituaçãoBase": "Situação"})
    else:
        base["Situação"] = "Sem restrição"

    if "Nome da UG" not in base.columns:
        base["Nome da UG"] = ""
    base["UG"] = base["UG"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(6)
    base["Nome da UG"] = base.apply(
        lambda r: UG_NAME_MAP.get(str(r.get("UG", "")).zfill(6), r.get("Nome da UG", "")),
        axis=1,
    )

    out_rows = []
    seen_ugs = set()
    for _, rec in base.iterrows():
        ug = sanitize_digits(rec.get("UG", ""), 6)
        if not ug:
            continue
        seen_ugs.add(ug)
        nome_ug = UG_NAME_MAP.get(ug, rec.get("Nome da UG", ""))
        if ug in grouped:
            out_rows.append({
                "UG": ug,
                "Nome da UG": nome_ug,
                "Quantidade de Restrições": grouped[ug]["Quantidade de Restrições"],
                "Códigos de Restrição": grouped[ug]["Códigos de Restrição"],
                "Situação": "Com restrição",
            })
        else:
            out_rows.append({
                "UG": ug,
                "Nome da UG": nome_ug,
                "Quantidade de Restrições": 0,
                "Códigos de Restrição": "-",
                "Situação": rec.get("Situação", "Sem restrição") or "Sem restrição",
            })

    for ug, info in grouped.items():
        if ug not in seen_ugs:
            out_rows.append({
                "UG": ug,
                "Nome da UG": UG_NAME_MAP.get(ug, ""),
                "Quantidade de Restrições": info["Quantidade de Restrições"],
                "Códigos de Restrição": info["Códigos de Restrição"],
                "Situação": "Com restrição",
            })

    if not out_rows:
        return pd.DataFrame(columns=["UG", "Nome da UG", "Quantidade de Restrições", "Códigos de Restrição", "Situação"])

    return pd.DataFrame(out_rows).sort_values(["UG"]).reset_index(drop=True)


def dataframe_to_xlsx_bytes(dfs: Dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            safe = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe, index=False)
    return buffer.getvalue()


def generate_validation_report(header: Dict[str, str], rows: List[RestrictionRow], errors: List[str], warnings: List[str], metadata: ReportMetadata) -> str:
    lines = [
        "RELATÓRIO DE VALIDAÇÃO - CSV DE RESTRIÇÕES SIAFI",
        "",
        f"Nível: {header.get('nivel', '')}",
        f"Código responsável: {header.get('codigo_responsavel', '')}",
        f"Mês: {header.get('mes', '')}",
        f"Ano: {header.get('ano', '')}",
        f"Setorial contábil identificada: {metadata.setorial_contabil or ''}",
                f"Quantidade de detalhes: {len(rows)}",
        "",
        "LOGS E METADADOS:",
    ]
    lines.extend([f"- {x}" for x in metadata.logs] or ["- Sem logs."])
    lines.extend(["", "ERROS:"])
    lines.extend([f"- {e}" for e in errors] or ["- Nenhum erro identificado."])
    lines.extend(["", "ALERTAS:"])
    lines.extend([f"- {w}" for w in warnings] or ["- Nenhum alerta identificado."])
    return "\n".join(lines)


def inject_template(target_df: pd.DataFrame, ug: str, template_name: str) -> pd.DataFrame:
    template = TEMPLATE_LIBRARY[template_name]
    new_row = {
        "UG": sanitize_digits(ug, 6),
        "Restrição": template["restricao"],
        "Motivo": template["motivo"],
        "Providência": template["providencia"],
        "Valor": "",
    }
    return pd.concat([target_df, pd.DataFrame([new_row])], ignore_index=True)






def reset_conferencia_filters():
    st.session_state["conferencia_filtro_ug_val"] = "Todas"
    st.session_state["conferencia_filtro_restr_val"] = "Todas"
    st.session_state["conferencia_filter_nonce"] = st.session_state.get("conferencia_filter_nonce", 0) + 1


def style_change_flags(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    def highlight_row(row):
        manual = str(row.get("Alterado_Manual", "")).strip().lower() == "sim"
        lote = str(row.get("Editado_Lote", "")).strip().lower() == "sim"
        auto = str(row.get("Padronizado_Auto", "")).strip().lower() == "sim"
        if manual:
            style = "background-color: #fff3cd; color: #7a4b00; font-weight: 600;"
        elif lote:
            style = "background-color: #dbeafe; color: #1d4ed8; font-weight: 600;"
        elif auto:
            style = "background-color: #dcfce7; color: #166534; font-weight: 600;"
        else:
            style = ""
        return [style] * len(row)

    return df.style.apply(highlight_row, axis=1)



def reset_app():
    st.session_state.manual_df = pd.DataFrame(columns=["UG", "Restrição", "Motivo", "Providência", "Valor"])
    st.session_state.header_defaults = {"nivel": "1", "codigo_responsavel": "153062", "mes": "", "ano": str(datetime.now().year), "setorial_contabil": ""}
    st.session_state.report_metadata = asdict(ReportMetadata())
    st.session_state.working_rows = []
    st.session_state.all_ugs_df = pd.DataFrame(columns=["UG", "Nome da UG", "SituaçãoBase"])
    st.session_state.manually_edited_indices = []
    st.session_state.batch_edited_indices = []
    st.session_state.auto_standardized_indices = []
    st.session_state.last_edit_message = ""
    st.session_state.import_logs = []
    st.session_state.last_loaded_signature = ""
    st.session_state.last_loaded_origin = ""
    st.session_state.uploader_nonce = st.session_state.get("uploader_nonce", 0) + 1
    st.session_state.conferencia_filter_nonce = 0
    st.session_state.conferencia_filtro_ug_val = "Todas"
    st.session_state.conferencia_filtro_restr_val = "Todas"
    st.session_state.conferencia_filter_nonce = 0
    st.session_state.header_widget_nonce = st.session_state.get("header_widget_nonce", 0) + 1





def month_option_label(month_value) -> str:
    if month_value in ("", None):
        return "Selecione..."
    try:
        month_int = int(str(month_value))
        if month_int in MONTHS:
            return f"{month_int:02d} - {MONTHS[month_int]}"
    except Exception:
        pass
    return str(month_value)


def render_header_inputs(defaults: Dict[str, str], metadata: ReportMetadata):
    setorial_detectada = sanitize_digits(defaults.get("setorial_contabil", "") or metadata.setorial_contabil, 6)

    current_year = str(datetime.now().year)
    default_year = str(defaults.get("ano", current_year) or current_year)

    raw_default_month = defaults.get("mes", "")
    if str(raw_default_month).strip() == "":
        default_month = ""
    else:
        try:
            default_month = int(str(raw_default_month))
        except Exception:
            digits = sanitize_digits(raw_default_month, None)
            default_month = int(digits) if digits and digits.isdigit() and 1 <= int(digits) <= 12 else ""

    widget_nonce = st.session_state.get("header_widget_nonce", 0)

    month_options = [""] + list(MONTHS.keys())

    c1, c2, c3 = st.columns([1.1, 1.1, 1.1])
    with c1:
        nivel = st.radio(
            "Nível da conformidade",
            options=["1", "2"],
            horizontal=False,
            format_func=lambda x: NIVEL_OPTIONS[x],
            index=0 if defaults.get("nivel", "1") == "1" else 1,
            key=f"header_nivel_{widget_nonce}",
        )
    with c2:
        if nivel == "2":
            codigo_responsavel = ORGAO_CODE
            st.text_input("Código responsável", value=codigo_responsavel, disabled=True, key=f"header_codigo_{widget_nonce}")
        else:
            codigo_responsavel = setorial_detectada or sanitize_digits(defaults.get("codigo_responsavel", "153062"), 6)
            st.text_input("Código responsável", value=codigo_responsavel, disabled=True, key=f"header_codigo_{widget_nonce}")
    with c3:
        selected_month = st.selectbox(
            "Mês de referência",
            options=month_options,
            index=month_options.index(default_month) if default_month in month_options else 0,
            format_func=lambda x: "Selecione..." if x == "" else f"{x:02d} - {MONTHS[x]}",
            key=f"header_mes_referencia_{widget_nonce}",
        )

    d1, d2 = st.columns([1.0, 1.2])
    with d1:
        ano_ref = st.text_input("Ano de referência", value=default_year, max_chars=4, key=f"header_ano_referencia_{widget_nonce}")
    with d2:
        nome_arquivo = build_standard_filename(selected_month, ano_ref) if selected_month != "" else ""
        st.text_input("Nome do arquivo CSV", value=nome_arquivo, disabled=True, key=f"header_nome_arquivo_{widget_nonce}")

    return nivel, codigo_responsavel, selected_month, ano_ref, nome_arquivo


st.set_page_config(page_title=APP_TITLE, layout="wide")

initialize_session_state()


def inject_visual_styles():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.15rem;
            padding-bottom: 1.5rem;
        }
        .app-hero {
            background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
            border: 1px solid #dbeafe;
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.9rem;
        }
        .app-hero-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.25rem;
        }
        .app-hero-text {
            color: #334155;
            font-size: 0.95rem;
            margin: 0;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.45rem;
            margin-bottom: 0.4rem;
        }
        button[role="tab"] {
            border-radius: 999px !important;
            background: #f3f7fb !important;
            border: 1px solid #dbe3ef !important;
            padding: 0.4rem 0.95rem !important;
        }
        button[role="tab"][aria-selected="true"] {
            background: #dbeafe !important;
            color: #1e3a8a !important;
            border-color: #93c5fd !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 0.65rem 0.8rem;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #dbe3ef;
            border-radius: 14px;
            overflow: hidden;
            background: #ffffff;
        }
        div[data-testid="stExpander"] details summary p {
            font-weight: 700 !important;
        }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
            border-radius: 12px;
            overflow: hidden;
        }
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 10px;
            font-weight: 700;
            min-height: 2.65rem;
            border: 1px solid #cbd5e1;
            transition: all 0.15s ease-in-out;
        }
        div.stButton > button:hover, div.stDownloadButton > button:hover {
            transform: translateY(-1px);
            border-color: #60a5fa;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.12);
        }
        .visual-note {
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            padding: 0.8rem 0.95rem;
            border-radius: 10px;
            margin: 0.4rem 0 0.8rem 0;
            color: #334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_visual_banner(title: str, text: str, icon: str = "ℹ️"):
    st.markdown(
        f"""
        <div class="app-hero">
            <div class="app-hero-title">{icon} {title}</div>
            <p class="app-hero-text">{text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

inject_visual_styles()


if "manual_df" not in st.session_state:
    st.session_state.manual_df = pd.DataFrame(columns=["UG", "Restrição", "Motivo", "Providência", "Valor"])
if "header_defaults" not in st.session_state:
    st.session_state.header_defaults = {"nivel": "1", "codigo_responsavel": "153062", "mes": "", "ano": str(datetime.now().year), "setorial_contabil": ""}
if "report_metadata" not in st.session_state:
    st.session_state.report_metadata = asdict(ReportMetadata())
if "working_rows" not in st.session_state:
    st.session_state.working_rows = []
if "all_ugs_df" not in st.session_state:
    st.session_state.all_ugs_df = pd.DataFrame(columns=["UG", "Nome da UG", "SituaçãoBase"])
if "manually_edited_indices" not in st.session_state:
    st.session_state.manually_edited_indices = []
if "batch_edited_indices" not in st.session_state:
    st.session_state.batch_edited_indices = []
if "auto_standardized_indices" not in st.session_state:
    st.session_state.auto_standardized_indices = []
if "last_edit_message" not in st.session_state:
    st.session_state.last_edit_message = ""
if "import_logs" not in st.session_state:
    st.session_state.import_logs = []
if "header_widget_nonce" not in st.session_state:
    st.session_state.header_widget_nonce = 0
if "conferencia_filtro_ug_val" not in st.session_state:
    st.session_state.conferencia_filtro_ug_val = "Todas"
if "conferencia_filtro_restr_val" not in st.session_state:
    st.session_state.conferencia_filtro_restr_val = "Todas"
    st.session_state.last_loaded_signature = ""
    st.session_state.last_loaded_origin = ""
    st.session_state.uploader_nonce = st.session_state.get("uploader_nonce", 0) + 1
    st.session_state.conferencia_filter_nonce = 0
    st.session_state.conferencia_filtro_ug_val = "Todas"
    st.session_state.conferencia_filtro_restr_val = "Todas"
    st.session_state.conferencia_filter_nonce = 0
if "last_loaded_signature" not in st.session_state:
    st.session_state.last_loaded_signature = ""
if "last_loaded_origin" not in st.session_state:
    st.session_state.last_loaded_origin = ""
if "uploader_nonce" not in st.session_state:
    st.session_state.uploader_nonce = 0
if "conferencia_filter_nonce" not in st.session_state:
    st.session_state.conferencia_filter_nonce = 0

st.title(APP_TITLE)
render_visual_banner("Ferramenta de geração e conferência", "Importe dados, padronize textos, revise por UG e exporte o CSV final pronto para upload.", "✨")

st.sidebar.header("Opções de validação")
bloquear_duplicidades = st.sidebar.checkbox("Bloquear duplicidade UG + restrição", value=True)
permitir_alerta_campos_vazios = st.sidebar.checkbox("Alertar motivo/providência vazios", value=True)

render_sprint_banner()

modo_modular_v6 = st.toggle("Usar interface modular da v6.0 (Sprint 6)", value=True)


if modo_modular_v6 and all([render_import_tab_v6, render_edit_tab_v6, render_summary_tab_v6, render_export_tab_v6, render_conrestcon_tab_v6]):
    tabs = st.tabs(["📥 Importação", "🛠️ Conferência e Edição", "📊 Resumo por UG", "📤 Exportação", "📚 CONRESTCON"])
    with tabs[0]:
        render_import_tab_v6()
    with tabs[1]:
        render_edit_tab_v6()
    with tabs[2]:
        render_summary_tab_v6()
    with tabs[3]:
        render_export_tab_v6()
    with tabs[4]:
        render_conrestcon_tab_v6()
    st.stop()

tabs = st.tabs(["📥 Importação", "🛠️ Conferência e Edição", "📊 Resumo por UG", "📤 Exportação", "📚 CONRESTCON"])


with tabs[0]:
    render_visual_banner("Importação de dados", "Escolha a origem dos dados e confira os parâmetros do header antes de iniciar o tratamento da base.", "📥")

    with st.expander("Guia do Usuário", expanded=False):
        st.markdown("""
### Passo a passo prático de uso

**1. Abrir a aplicação**  
Ao abrir o app, você verá as abas principais:
- **Importação**
- **Conferência e Edição**
- **Resumo por UG**
- **Exportação**
- **CONRESTCON**

**2. Importar a base de dados**  
Na aba **Importação**, escolha a origem dos dados:
- **PDF do Tesouro Gerencial**
- **Planilha estruturada (CSV/Excel)**
- **CSV SIAFI já existente**
- **Digitação manual**

**3. Se usar PDF do Tesouro Gerencial**
1. Clique em **Envie o relatório em PDF**.
2. Selecione o arquivo.
3. Clique em **Processar PDF**.
4. O sistema fará a leitura das restrições e preencherá os dados da base.

**4. Se usar planilha estruturada**
1. Envie o arquivo CSV/Excel.
2. Clique em **Processar planilha**.
3. O sistema carregará os registros para edição.

**5. Se usar CSV SIAFI já existente**
1. Envie o CSV.
2. Clique em **Processar CSV existente**.
3. O app lerá o header e os detalhes do arquivo.

**6. Se usar digitação manual**
1. Preencha ou edite a grade manual.
2. Clique em **Processar digitação manual**.

**7. Conferir os parâmetros do header**  
Ainda na aba **Importação**, confira:
- **Nível da conformidade**
- **Código responsável**
- **Mês de referência**
- **Ano de referência**
- **Nome do arquivo CSV**

**8. Reiniciar a aplicação, se necessário**  
Na parte inferior da aba **Importação** existe o botão **Reiniciar Aplicativo e Limpar Dados**.  
Use-o para apagar a base carregada, limpar filtros, remover arquivos anexados e começar novamente.

**9. Filtrar os registros para edição**  
Na aba **Conferência e Edição**, use os filtros por:
- **UG**
- **Restrição**

Eles definem quais registros serão exibidos e afetados pelas ações.

**10. Usar a grade principal**  
Na grade principal você pode:
- visualizar os registros;
- editar manualmente os campos;
- marcar linhas específicas na coluna **Selecionar**.

A coluna **Selecionar** é usada quando quiser aplicar ações apenas em **linhas selecionadas**.

**11. Salvar ajustes manuais**
Depois de editar diretamente a grade, clique em **Salvar Ajustes Manuais**.

**12. Aplicar capitalização**  
No **Módulo 2 — Edição por capitalização**:
- escolha o tipo de capitalização;
- escolha o escopo:
  - **Base inteira**
  - **Filtro atual**
  - **Linhas selecionadas**
- clique em **Aplicar Capitalização**.

A capitalização será aplicada às colunas **Motivo** e **Providência**.

**13. Aplicar padronização por código de restrição**  
No **Módulo 3 — Padronização por código de restrição**:
- escolha o escopo;
- clique em **Aplicar Padronização por Restrição**.

O sistema padroniza o campo **Motivo** com base na tabela **CONRESTCON**.

**14. Fazer edição em lote**  
No **Módulo 4 — Edição em lote de texto**:
1. preencha um novo **Motivo** e/ou uma nova **Providência**;
2. marque se deseja sobrescrever textos existentes;
3. clique em **Aplicar Edição em Lote**.

**15. Consultar o resumo por UG**  
Na aba **Resumo por UG**, você verá:
- **Restrições contábeis por Unidade Gestora**
- **Quadro Resumo por Restrição**

**16. Consultar a tabela CONRESTCON**  
Na aba **CONRESTCON**, você pode:
- pesquisar por código;
- filtrar por digitação;
- consultar o título padronizado da restrição.

**17. Exportar o resultado**  
Na aba **Exportação**:
1. revise a prévia;
2. confira se não há erros impeditivos;
3. baixe o arquivo desejado.

**18. Fluxo recomendado**
1. **Importação**
2. **Conferência e Edição**
3. **Resumo por UG**
4. **Exportação**
5. consulta à **CONRESTCON** quando necessário

**19. Dicas práticas**
- Use **Filtro atual** para tratar apenas uma UG ou restrição.
- Use **Linhas selecionadas** para tratar casos específicos.
- Sempre clique em **Salvar Ajustes Manuais** depois de editar a grade.
- Antes de exportar, confira o **Mês de referência**, o **Ano** e o **Nome do arquivo**.
""")

    st.markdown("### Etapa 1 — Importação")
    origem = st.radio(
        "Escolha a origem dos dados",
        options=["PDF do Tesouro Gerencial", "Planilha estruturada (CSV/Excel)", "CSV SIAFI já existente", "Digitação manual"],
        horizontal=True,
    )

    rows: List[RestrictionRow] = []
    header_defaults = st.session_state.header_defaults.copy()
    metadata = ReportMetadata(**st.session_state.report_metadata)

    if origem == "PDF do Tesouro Gerencial":
        uploaded_pdf = st.file_uploader("Envie o relatório em PDF", type=["pdf"], key=f"pdf_upload_{st.session_state.get('uploader_nonce', 0)}")
        if uploaded_pdf is not None:
            if st.button("Processar PDF", use_container_width=True):
                header_text = extract_pdf_header_page(uploaded_pdf)
                raw_text = extract_text_from_pdf(uploaded_pdf)
                rows = parse_report_text(raw_text)
                metadata = extract_report_metadata(raw_text, header_text=header_text)
                st.session_state.report_metadata = asdict(metadata)
                header_defaults["setorial_contabil"] = metadata.setorial_contabil
                if metadata.mes_referencia:
                    try:
                        header_defaults["mes"] = MONTH_ABBR_REV.get(metadata.mes_referencia.split("/")[0], "")
                        header_defaults["ano"] = metadata.mes_referencia.split("/")[1]
                    except Exception:
                        pass
                else:
                    header_defaults["mes"] = ""
                st.session_state.header_defaults = header_defaults.copy()
                st.session_state.header_widget_nonce = st.session_state.get("header_widget_nonce", 0) + 1
                st.session_state.all_ugs_df = extract_all_ugs_from_report(raw_text)
                st.session_state.import_logs = metadata.logs
                st.session_state.working_rows = [asdict(r) for r in rows]
                st.session_state.manually_edited_indices = []
                st.session_state.batch_edited_indices = []
                st.session_state.auto_standardized_indices = []
                st.session_state.last_loaded_signature = source_signature(uploaded_pdf)
                st.session_state.last_loaded_origin = origem
                st.success(f"PDF processado com sucesso. {len(rows)} restrições foram identificadas automaticamente. Mês de referência carregado: {month_option_label(header_defaults.get('mes', ''))}.")
        i1, i2 = st.columns(2)
        current_md = ReportMetadata(**st.session_state.report_metadata)
        i1.metric("Setorial contábil", current_md.setorial_contabil or "")
        i2.metric("UGs mapeadas no relatório", len(st.session_state.all_ugs_df))

    elif origem == "Planilha estruturada (CSV/Excel)":
        uploaded_table = st.file_uploader("Envie planilha com colunas UG, Restrição, Motivo, Providência e Valor", type=["csv", "xlsx", "xls"], key=f"table_upload_{st.session_state.get('uploader_nonce', 0)}")
        if uploaded_table is not None:
            try:
                df_source = parse_structured_table(uploaded_table)
                st.dataframe(df_source, use_container_width=True, height=220)
                if st.button("Processar planilha", use_container_width=True):
                    rows = map_table_to_rows(df_source)
                    file_month, file_year = infer_month_year_from_filename(getattr(uploaded_table, "name", ""))
                    df_month, df_year = infer_month_year_from_structured_df(df_source)
                    inferred_month = df_month or file_month
                    inferred_year = df_year or file_year or str(datetime.now().year)

                    header_defaults["mes"] = inferred_month or ""
                    header_defaults["ano"] = inferred_year
                    st.session_state.header_defaults.update(header_defaults)
                    st.session_state.header_widget_nonce = st.session_state.get("header_widget_nonce", 0) + 1

                    st.session_state.working_rows = [asdict(r) for r in rows]
                    st.session_state.manually_edited_indices = []
                    st.session_state.batch_edited_indices = []
                    st.session_state.auto_standardized_indices = []
                    st.session_state.last_loaded_signature = source_signature(uploaded_table)
                    st.session_state.last_loaded_origin = origem
                    st.session_state.import_logs = [
                        f"Mês inferido da planilha/arquivo: {month_option_label(inferred_month) if inferred_month else '(não identificado)'}",
                        f"Ano inferido da planilha/arquivo: {inferred_year}",
                    ]
                    if rows:
                        ugs = sorted({r.ug for r in rows})
                        st.session_state.all_ugs_df = pd.DataFrame({"UG": ugs, "Nome da UG": ["" for _ in ugs], "SituaçãoBase": ["Com restrição" for _ in ugs]})
                    st.success(f"{len(rows)} restrições carregadas da planilha.")
            except Exception as e:
                st.error(str(e))


    elif origem == "CSV SIAFI já existente":
        uploaded_csv = st.file_uploader("Envie um CSV já existente para conferência e reprocessamento", type=["csv"], key=f"csv_upload_{st.session_state.get('uploader_nonce', 0)}")
        if uploaded_csv is not None:
            if st.button("Processar CSV existente", use_container_width=True):
                header_defaults, rows = parse_existing_csv(uploaded_csv)
                if not header_defaults.get("ano"):
                    header_defaults["ano"] = str(datetime.now().year)
                if "mes" not in header_defaults:
                    header_defaults["mes"] = ""

                st.session_state.header_defaults.update(header_defaults)
                st.session_state.header_widget_nonce = st.session_state.get("header_widget_nonce", 0) + 1

                st.session_state.working_rows = [asdict(r) for r in rows]
                st.session_state.manually_edited_indices = []
                st.session_state.batch_edited_indices = []
                st.session_state.auto_standardized_indices = []
                st.session_state.last_loaded_signature = source_signature(uploaded_csv)
                st.session_state.last_loaded_origin = origem
                st.session_state.import_logs = [
                    f"Leitura do CSV concluída. Mês localizado no header do arquivo: {month_option_label(header_defaults.get('mes', ''))}",
                    f"Mês aplicado ao header do sistema: {month_option_label(header_defaults.get('mes', ''))}",
                    f"Ano lido/inferido do CSV: {header_defaults.get('ano', str(datetime.now().year))}",
                    f"DEBUG valor final do header[mes]: {header_defaults.get('mes', '')}",
                    f"DEBUG tipo do valor do mês: {type(header_defaults.get('mes', '')).__name__}",
                    f"DEBUG nome do arquivo CSV: {getattr(uploaded_csv, 'name', '')}",
                ]
                if rows:
                    ugs = sorted({r.ug for r in rows})
                    st.session_state.all_ugs_df = pd.DataFrame({"UG": ugs, "Nome da UG": ["" for _ in ugs], "SituaçãoBase": ["Com restrição" for _ in ugs]})
                st.success(f"CSV processado com sucesso. {len(rows)} registros de detalhe foram carregados. Mês de referência carregado: {month_option_label(header_defaults.get('mes', ''))}.")

    else:
        c_a, c_b = st.columns([2, 3])
        with c_a:
            ug_modelo = st.text_input("UG para inserir modelo", value="153062")
            modelo = st.selectbox("Modelo padronizado (CONRESTCON)", options=[f'{r["Restrição"]} - {r["Título"]}' for r in CONRESTCON_ROWS])
            if st.button("Adicionar modelo na grade"):
                codigo_modelo = re.sub(r"\D", "", str(modelo).split(" - ")[0]).zfill(3)
                titulo_modelo = CONRESTCON_MOTIVOS.get(codigo_modelo, "")
                new_row = {
                    "UG": sanitize_digits(ug_modelo, 6),
                    "Restrição": codigo_modelo,
                    "Motivo": titulo_modelo,
                    "Providência": "",
                    "Valor": "",
                }
                st.session_state.manual_df = pd.concat([st.session_state.manual_df, pd.DataFrame([new_row])], ignore_index=True)
        with c_b:
            st.caption("Você pode inserir modelos padronizados com base na nova tabela CONRESTCON e complementar manualmente os campos da grade.")
        if st.session_state.manual_df.empty:
            st.session_state.manual_df = pd.DataFrame([{
                "UG": "153258",
                "Restrição": "634",
                "Motivo": "Bens adquiridos antes de 2010 permanecem com valores históricos, necessitando de reavaliação.",
                "Providência": "Aguardando providências por parte da Administração Central para a realização do processo de reavaliação dos bens.",
                "Valor": "",
            }])
        edited_df = st.data_editor(st.session_state.manual_df, num_rows="dynamic", use_container_width=True, height=300)
        st.session_state.manual_df = edited_df.copy()
        if st.button("Processar digitação manual", use_container_width=True):
            rows = map_table_to_rows(edited_df)
            st.session_state.working_rows = [asdict(r) for r in rows]
            st.session_state.manually_edited_indices = []
            st.session_state.batch_edited_indices = []
            st.session_state.auto_standardized_indices = []
            st.session_state.last_loaded_signature = f"manual|{len(edited_df)}"
            st.session_state.last_loaded_origin = origem
            if rows:
                ugs = sorted({r.ug for r in rows})
                st.session_state.all_ugs_df = pd.DataFrame({"UG": ugs, "Nome da UG": ["" for _ in ugs], "SituaçãoBase": ["Com restrição" for _ in ugs]})
            st.success(f"{len(rows)} linhas manuais carregadas na base.")

    metadata = ReportMetadata(**st.session_state.report_metadata)
    defaults = st.session_state.header_defaults.copy()
    st.markdown("### Parâmetros do Header")
    nivel, codigo_responsavel, mes, ano, nome_arquivo = render_header_inputs(defaults, metadata)
    st.session_state.header_defaults.update({"nivel": nivel, "codigo_responsavel": codigo_responsavel, "mes": mes, "ano": ano})

    if st.session_state.import_logs:
        with st.expander("Logs e metadados da importação", expanded=False):
            for item in st.session_state.import_logs:
                st.write(f"- {item}")

    if st.session_state.working_rows:
        st.info(f"Base em trabalho preservada com {len(st.session_state.working_rows)} registro(s). Ela só será substituída quando você clicar em um botão de processamento nesta guia.")

    st.markdown("---")
    st.markdown("### Reinicialização")
    st.markdown('<div class="visual-note"><strong>Atenção:</strong> ao reiniciar, a base em trabalho, os parâmetros e os arquivos anexados nas caixas de upload serão limpos.</div>', unsafe_allow_html=True)
    if st.button("🔄 Reiniciar aplicativo", use_container_width=True, key="reset_bottom_import", type="secondary"):
        reset_app()
        st.rerun()





with tabs[1]:
    render_visual_banner("Conferência e edição", "Use filtros, faça ajustes manuais ou em lote e aplique capitalização e padronização visualmente na grade principal.", "🛠️")
    st.markdown("### Etapa 2 — Conferência e Edição")
    st.caption("A base em trabalho é preservada após padronizações e ajustes manuais. Ela não retorna ao padrão anterior, a menos que você processe uma nova importação.")

    if st.session_state.last_edit_message:
        st.success(st.session_state.last_edit_message)
        st.session_state.last_edit_message = ""

    rows = [RestrictionRow(**r) for r in st.session_state.working_rows] if st.session_state.working_rows else []
    preview_df = rows_to_dataframe(rows)

    if preview_df.empty:
        st.info("Importe uma base na guia Importação.")
    else:
        ugs_disponiveis = ["Todas"] + sorted(preview_df["UG"].dropna().astype(str).unique().tolist())
        restr_disponiveis = ["Todas"] + sorted(preview_df["Restrição"].dropna().astype(str).unique().tolist())

        current_ug_val = st.session_state.get("conferencia_filtro_ug_val", "Todas")
        current_restr_val = st.session_state.get("conferencia_filtro_restr_val", "Todas")
        if current_ug_val not in ugs_disponiveis:
            current_ug_val = "Todas"
            st.session_state["conferencia_filtro_ug_val"] = "Todas"
        if current_restr_val not in restr_disponiveis:
            current_restr_val = "Todas"
            st.session_state["conferencia_filtro_restr_val"] = "Todas"

        nonce = st.session_state.get("conferencia_filter_nonce", 0)

        render_edit_module_title("Módulo 1 — Filtros de seleção")
        f1, f2, f3 = st.columns([1, 1, 0.9])
        with f1:
            filtro_ug = st.selectbox(
                "Filtrar por UG",
                options=ugs_disponiveis,
                index=ugs_disponiveis.index(current_ug_val) if current_ug_val in ugs_disponiveis else 0,
                key=f"conferencia_filtro_ug_widget_{nonce}",
            )
        with f2:
            filtro_restr = st.selectbox(
                "Filtrar por restrição",
                options=restr_disponiveis,
                index=restr_disponiveis.index(current_restr_val) if current_restr_val in restr_disponiveis else 0,
                key=f"conferencia_filtro_restr_widget_{nonce}",
            )
        with f3:
            st.write("")
            st.write("")
            if st.button("🧹 Limpar filtros", use_container_width=True, key=f"limpar_filtros_{nonce}", type="secondary"):
                reset_conferencia_filters()
                st.rerun()

        st.session_state["conferencia_filtro_ug_val"] = filtro_ug
        st.session_state["conferencia_filtro_restr_val"] = filtro_restr

        indices_filtrados = [idx for idx, row in enumerate(rows) if (filtro_ug == "Todas" or row.ug == filtro_ug) and (filtro_restr == "Todas" or row.restricao == filtro_restr)]
        rows_filtradas = [rows[idx] for idx in indices_filtrados]
        preview_filtrado = rows_to_dataframe(rows_filtradas)
        preview_filtrado.insert(0, "Selecionar", False)

        render_edit_module_title("Grade principal de conferência e edição")
        st.caption("Clique diretamente na coluna Selecionar da grade principal para marcar as linhas que serão usadas no escopo 'Linhas selecionadas'.")
        editor_key = f"editor_conferencia_{filtro_ug}_{filtro_restr}_{len(rows_filtradas)}"
        edited_preview = st.data_editor(
            preview_filtrado[["Selecionar", "UG", "Restrição", "Motivo", "Providência", "Valor_SIAFI"]] if not preview_filtrado.empty else preview_filtrado,
            num_rows="dynamic",
            use_container_width=True,
            height=430,
            key=editor_key,
        )

        selected_global_indices = []
        if not edited_preview.empty and "Selecionar" in edited_preview.columns:
            selected_positions = edited_preview.index[edited_preview["Selecionar"] == True].tolist()
            selected_global_indices = [indices_filtrados[pos] for pos in selected_positions if pos < len(indices_filtrados)]

        controls1, controls2, controls3 = st.columns([1.2, 1, 1])
        with controls1:
            if st.button("💾 Salvar Ajustes Manuais", use_container_width=True, type="primary"):
                filtered_updated_rows = dataframe_to_rows(edited_preview.drop(columns=["Selecionar"], errors="ignore"))
                rows_updated, changed_indices = replace_filtered_rows(rows, filtered_updated_rows, filtro_ug, filtro_restr)
                st.session_state.working_rows = [asdict(r) for r in rows_updated]
                manual_flags = set(st.session_state.manually_edited_indices)
                manual_flags.update(changed_indices)
                st.session_state.manually_edited_indices = sorted(manual_flags)
                st.session_state.last_edit_message = "Ajustes manuais salvos com sucesso aos registros filtrados."
                st.rerun()
        with controls2:
            st.metric("Linhas no filtro", len(rows_filtradas))
        with controls3:
            st.metric("Linhas selecionadas", len(selected_global_indices))

        render_edit_module_title("Módulo 2 — Edição por capitalização")
        with st.form("form_capitalizacao", clear_on_submit=False):
            c1, c2 = st.columns([1.4, 1.2])
            with c1:
                capitalizacao = st.selectbox(
                    "Tipo de capitalização",
                    options=["Primeira letra maiúscula", "minúsculas", "MAIÚSCULAS", "Capitalizar Cada Palavra"],
                    index=0,
                )
            with c2:
                escopo_capitalizacao = st.radio(
                    "Escopo da capitalização",
                    options=["Base inteira", "Filtro atual", "Linhas selecionadas"],
                    horizontal=False,
                )
            submitted_cap = st.form_submit_button("🔤 Aplicar Capitalização", use_container_width=True, type="primary")

        if submitted_cap:
            target_indices = get_scope_global_indices(rows, escopo_capitalizacao, filtro_ug, filtro_restr, selected_global_indices)
            updated_rows, changed_indices = apply_capitalization_to_scope(rows, target_indices, capitalizacao)
            st.session_state.working_rows = [asdict(r) for r in updated_rows]
            auto_flags = set(st.session_state.auto_standardized_indices)
            auto_flags.update(changed_indices)
            st.session_state.auto_standardized_indices = sorted(auto_flags)
            scope_msg = "à base inteira" if escopo_capitalizacao == "Base inteira" and filtro_ug == "Todas" and filtro_restr == "Todas" else ("às linhas selecionadas" if escopo_capitalizacao == "Linhas selecionadas" else "aos registros filtrados")
            st.session_state.last_edit_message = f"Capitalização aplicada com sucesso {scope_msg}."
            st.rerun()

        render_edit_module_title("Módulo 3 — Padronização por código de restrição")
        with st.form("form_padronizacao_restricao", clear_on_submit=False):
            escopo_restricao = st.radio(
                "Escopo da padronização por restrição",
                options=["Base inteira", "Filtro atual", "Linhas selecionadas"],
                horizontal=False,
            )
            submitted_restr = st.form_submit_button("🧩 Aplicar Padronização por Restrição", use_container_width=True, type="primary")

        if submitted_restr:
            target_indices = get_scope_global_indices(rows, escopo_restricao, filtro_ug, filtro_restr, selected_global_indices)
            updated_rows, changed_indices = apply_restriction_standardization_to_scope(rows, target_indices)
            st.session_state.working_rows = [asdict(r) for r in updated_rows]
            auto_flags = set(st.session_state.auto_standardized_indices)
            auto_flags.update(changed_indices)
            st.session_state.auto_standardized_indices = sorted(auto_flags)
            scope_msg = "à base inteira" if escopo_restricao == "Base inteira" and filtro_ug == "Todas" and filtro_restr == "Todas" else ("às linhas selecionadas" if escopo_restricao == "Linhas selecionadas" else "aos registros filtrados")
            st.session_state.last_edit_message = f"Padronização por código de restrição aplicada com sucesso {scope_msg}."
            st.rerun()

        with st.expander("Módulo 4 — Edição em lote de texto", expanded=False):
            st.warning("Selecionar linhas no filtro ou aplicar ajuste(s) na base inteira.")
            b1, b2, b3 = st.columns(3)
            with b1:
                novo_motivo = st.text_area("Novo motivo", height=100)
            with b2:
                nova_providencia = st.text_area("Nova providência", height=100)
            with b3:
                overwrite = st.checkbox("Sobrescrever textos existentes", value=False)
                if st.button("✏️ Aplicar Edição em Lote", use_container_width=True, type="primary"):
                    rows_updated, changed_indices = apply_batch_text_update(rows, filtro_ug, filtro_restr, clean_text_field(novo_motivo), clean_text_field(nova_providencia), overwrite=overwrite)
                    st.session_state.working_rows = [asdict(r) for r in rows_updated]
                    lote_flags = set(st.session_state.batch_edited_indices)
                    lote_flags.update(changed_indices)
                    st.session_state.batch_edited_indices = sorted(lote_flags)
                    st.session_state.last_edit_message = "Edição em lote aplicada com sucesso aos registros filtrados."
                    st.rerun()

        rows = [RestrictionRow(**r) for r in st.session_state.working_rows]
        base_df = rows_to_dataframe(rows)
        manual_flags = set(st.session_state.manually_edited_indices)
        batch_flags = set(st.session_state.batch_edited_indices)
        auto_flags = set(st.session_state.auto_standardized_indices)
        base_df.insert(0, "Alterado_Manual", ["Sim" if idx in manual_flags else "" for idx in range(len(base_df))])
        base_df.insert(1, "Editado_Lote", ["Sim" if idx in batch_flags else "" for idx in range(len(base_df))])
        base_df.insert(2, "Padronizado_Auto", ["Sim" if idx in auto_flags else "" for idx in range(len(base_df))])

        st.caption("Destaques visuais: amarelo = alteração manual | azul = edição em lote | verde = padronização automática.")
        st.dataframe(style_change_flags(base_df), use_container_width=True, height=260)

with tabs[2]:
    render_visual_banner("Resumo por UG", "Acompanhe a consolidação das restrições por unidade gestora e o quadro resumo por restrição.", "📊")
    st.markdown("### Etapa 3 — Resumo por UG")
    rows = [RestrictionRow(**r) for r in st.session_state.working_rows] if st.session_state.working_rows else []
    all_ugs_df = st.session_state.all_ugs_df if isinstance(st.session_state.all_ugs_df, pd.DataFrame) else pd.DataFrame()
    summary_df = rows_to_summary(rows, all_ugs_df)
    restr_summary_df = summarize_by_restriction(rows)

    if summary_df.empty:
        st.info("Não há dados suficientes para montar o resumo por UG.")
    else:
        st.markdown("**Restrições contábeis por Unidade Gestora**")
        st.dataframe(summary_df, use_container_width=True, height=360)
        c1, c2, c3 = st.columns(3)
        c1.metric("UGs totais", len(summary_df))
        c2.metric("UGs com restrição", int((summary_df["Situação"] == "Com restrição").sum()))
        c3.metric("UGs sem restrição", int((summary_df["Situação"] == "Sem restrição").sum()))

        st.markdown("**Quadro Resumo por Restrição**")
        st.dataframe(restr_summary_df, use_container_width=True, height=260)

with tabs[3]:
    render_visual_banner("Exportação", "Baixe o CSV final e os arquivos auxiliares após concluir a conferência da base.", "📤")
    st.markdown("### Etapa 4 — Exportação")
    rows = [RestrictionRow(**r) for r in st.session_state.working_rows] if st.session_state.working_rows else []
    metadata = ReportMetadata(**st.session_state.report_metadata)
    defaults = st.session_state.header_defaults.copy()
    all_ugs_df = st.session_state.all_ugs_df if isinstance(st.session_state.all_ugs_df, pd.DataFrame) else pd.DataFrame()

    if not rows:
        st.info("Importe uma base na guia Importação.")
    else:
        nivel = defaults.get("nivel", "1")
        codigo_sanitizado = sanitize_digits(defaults.get("codigo_responsavel", ""), None)
        mes_raw = defaults.get("mes", "")
        mes = int(mes_raw) if str(mes_raw).strip() != "" else 3
        ano = str(defaults.get("ano", "2026"))
        nome_arquivo = build_standard_filename(mes, ano)
        setorial_para_validacao = sanitize_digits(defaults.get("setorial_contabil", "") or metadata.setorial_contabil, 6)

        header_issues = validate_header(nivel, codigo_sanitizado, mes, setorial_contabil=setorial_para_validacao)
        row_errors, row_warnings = validate_rows(rows, bloquear_duplicidades=bloquear_duplicidades)
        if not permitir_alerta_campos_vazios:
            row_warnings = [w for w in row_warnings if "vazio" not in w.lower()]
        all_errors = header_issues + row_errors

        header_dict = {
            "nivel": nivel,
            "codigo_responsavel": codigo_sanitizado,
            "mes": str(mes),
            "ano": str(ano),
            "setorial_contabil": setorial_para_validacao,
        }
        summary_df = rows_to_summary(rows, all_ugs_df)
        validation_txt = generate_validation_report(header_dict, rows, all_errors, row_warnings, metadata)
        csv_content = build_csv_content(nivel, codigo_sanitizado, mes, rows)
        dados_tratados_df = rows_to_dataframe(rows)
        logs_df = pd.DataFrame({"Log": metadata.logs or ["Sem logs."]})

        st.write(f"Nome sugerido do arquivo: **{nome_arquivo}**")

        if all_errors:
            st.error("Foram identificados erros impeditivos para geração do CSV.")
            for err in all_errors:
                st.write(f"- {err}")
        else:
            st.success("Nenhum erro impeditivo encontrado. O arquivo pode ser gerado.")

        if row_warnings:
            st.warning("Foram identificados alertas de conferência.")
            for warn in row_warnings[:30]:
                st.write(f"- {warn}")

        st.subheader("Prévia do CSV gerado")
        st.code("\n".join(csv_content.splitlines()[:25]), language="text")

        excel_bytes = dataframe_to_xlsx_bytes({
            "Dados Tratados": dados_tratados_df,
            "Resumo por UG": summary_df,
            "Resumo por Restrição": summarize_by_restriction(rows),
            "Logs e Metadados": logs_df,
        })

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "⬇️ Baixar CSV pronto para upload",
                data=csv_content.encode("utf-8"),
                file_name=nome_arquivo,
                mime="text/csv",
                disabled=bool(all_errors),
            )
        with d2:
            st.download_button(
                "📗 Baixar Excel final",
                data=excel_bytes,
                file_name=nome_arquivo.replace(".csv", "_relatorios.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="secondary",
            )
        with d3:
            st.download_button(
                "📝 Baixar relatório de validação",
                data=validation_txt.encode("utf-8"),
                file_name="relatorio_validacao_restricoes.txt",
                mime="text/plain",
                type="secondary",
            )

        with st.expander("Checklist de conferência antes do upload", expanded=False):
            st.markdown(
                """
1. Confirmar o **nível do header**.
2. Confirmar o **código responsável**.
3. Validar o **mês de referência**.
4. Conferir **UG** e **restrição** em todas as linhas.
5. Revisar **motivo** e **providência** após a padronização.
6. Observar os destaques visuais das alterações.
7. Confirmar a quantidade de detalhes no **Trailer**.
8. Verificar a conversão do **valor monetário**.
9. Confirmar o nome do arquivo no padrão `##_###_##.csv`.
10. Conferir a aba **Resumo por UG** antes da exportação final.
"""
            )


with tabs[4]:
    render_visual_banner("Consulta CONRESTCON", "Pesquise os códigos de restrição e consulte os títulos padronizados aplicáveis ao campo Motivo.", "📚")
    st.markdown("### Etapa 5 — CONRESTCON")
    st.caption("Tabela atualizada de consulta dos códigos de restrição e respectivos títulos padronizados, utilizada no campo Motivo e como modelo para digitação manual.")

    conrest_df = conrestcon_to_dataframe()
    codigos = ["Todos"] + sorted(conrest_df["Restrição"].astype(str).tolist())

    c1, c2 = st.columns([1.1, 1.4])
    with c1:
        conrest_select = st.selectbox("Selecionar código de restrição", options=codigos, index=0)
    with c2:
        conrest_query = st.text_input("Filtrar por digitação", placeholder="Digite o código ou parte do título")

    filtered_conrest = filter_conrestcon_dataframe(conrest_df, conrest_query, conrest_select)

    m1, m2 = st.columns(2)
    m1.metric("Códigos na tabela", len(conrest_df))
    m2.metric("Resultados do filtro", len(filtered_conrest))

    st.dataframe(filtered_conrest, use_container_width=True, height=420)
