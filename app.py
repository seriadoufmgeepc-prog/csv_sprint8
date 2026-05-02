
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
        st.success("v6.0 - Sprint 9: validação reforçada para restrições inválidas e UGs não homologadas.")


def _safe_import_ui():
    availability = {}
    try:
        from ui.import_tab import render_import_tab as _render_import_tab_v6
        availability["import"] = _render_import_tab_v6
    except Exception:
        availability["import"] = None
    try:
        from ui.edit_tab import render_edit_tab as _render_edit_tab_v6
        availability["edit"] = _render_edit_tab_v6
    except Exception:
        availability["edit"] = None
    try:
        from ui.summary_tab import render_summary_tab as _render_summary_tab_v6
        availability["summary"] = _render_summary_tab_v6
    except Exception:
        availability["summary"] = None
    try:
        from ui.export_tab import render_export_tab as _render_export_tab_v6
        availability["export"] = _render_export_tab_v6
    except Exception:
        availability["export"] = None
    try:
        from ui.conrestcon_tab import render_conrestcon_tab as _render_conrestcon_tab_v6
        availability["conrestcon"] = _render_conrestcon_tab_v6
    except Exception:
        availability["conrestcon"] = None
    try:
        from ui.homologation_tab import render_homologation_tab as _render_homologation_tab_v6
        availability["homologation"] = _render_homologation_tab_v6
    except Exception:
        availability["homologation"] = None
    return availability

_ui_v6 = _safe_import_ui()
render_import_tab_v6 = _ui_v6.get("import")
render_edit_tab_v6 = _ui_v6.get("edit")
render_summary_tab_v6 = _ui_v6.get("summary")
render_export_tab_v6 = _ui_v6.get("export")
render_conrestcon_tab_v6 = _ui_v6.get("conrestcon")
render_homologation_tab_v6 = _ui_v6.get("homologation")

from pypdf import PdfReader


import json

def render_homologation_tab_inline():
    st.markdown("### Homologação")
    st.caption("Fallback local da aba Homologação. Sprint 9 focada no reforço do motor de validação para restrições inválidas e UGs não homologadas.")

    checklist_default = [
        {"id": "H-01", "frente": "Importação", "cenario": "Processar PDF do Tesouro Gerencial", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-02", "frente": "Importação", "cenario": "Processar CSV SIAFI existente", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-03", "frente": "Importação", "cenario": "Processar planilha estruturada", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-04", "frente": "Conferência e Edição", "cenario": "Aplicar capitalização", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-05", "frente": "Conferência e Edição", "cenario": "Aplicar padronização por restrição", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-06", "frente": "Conferência e Edição", "cenario": "Registrar memória de alterações", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-07", "frente": "Resumo", "cenario": "Gerar resumo por UG", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-08", "frente": "Resumo", "cenario": "Gerar resumo por restrição", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-09", "frente": "Exportação", "cenario": "Exportar CSV modular", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-10", "frente": "Exportação", "cenario": "Exportar Excel modular", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-11", "frente": "Validação", "cenario": "Detectar erros impeditivos", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
        {"id": "H-12", "frente": "Comparação", "cenario": "Comparar modular x legado", "status": "Pendente", "resultado": "", "divergencia": "", "classificacao": ""},
    ]

    if "homologation_items_inline" not in st.session_state:
        st.session_state["homologation_items_inline"] = checklist_default

    items = st.session_state["homologation_items_inline"]
    st.markdown("#### Registro de execução da homologação")
    st.dataframe(pd.DataFrame(items), use_container_width=True, height=320)

    ids = [item["id"] for item in items]
    selected = st.selectbox("Selecionar item para registrar", options=ids, key="inline_homo_item")
    item = next((x for x in items if x["id"] == selected), None)
    if item:
        c1, c2 = st.columns(2)
        with c1:
            status = st.selectbox("Status", options=["Pendente", "Em teste", "Concluído"], index=["Pendente", "Em teste", "Concluído"].index(item.get("status", "Pendente")), key="inline_homo_status")
            classificacao = st.selectbox(
                "Classificação",
                options=["", "Aprovado", "Aprovado com ressalva", "Reprovado"],
                index=["", "Aprovado", "Aprovado com ressalva", "Reprovado"].index(item.get("classificacao", "") if item.get("classificacao", "") in ["", "Aprovado", "Aprovado com ressalva", "Reprovado"] else ""),
                key="inline_homo_class",
            )
        with c2:
            resultado = st.text_area("Resultado", value=item.get("resultado", ""), key="inline_homo_resultado", height=100)
            divergencia = st.text_area("Divergência / observação", value=item.get("divergencia", ""), key="inline_homo_div", height=100)

        if st.button("Salvar registro do item", use_container_width=True, key="inline_homo_save"):
            item["status"] = status
            item["classificacao"] = classificacao
            item["resultado"] = resultado
            item["divergencia"] = divergencia
            st.success("Registro de homologação atualizado.")
            st.rerun()

    with st.expander("Checklist orientativo da homologação", expanded=False):
        st.markdown(
            "- H-01 a H-03: Importação\n"
            "- H-04 a H-06: Conferência e Edição\n"
            "- H-07 a H-08: Resumos\n"
            "- H-09 a H-10: Exportação\n"
            "- H-11: Validação\n"
            "- H-12: Comparação com o legado"
        )


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


def validate_rows(
    rows: List[RestrictionRow],
    bloquear_duplicidades: bool = True,
    valid_ugs: Optional[set] = None,
) -> Tuple[List[str], List[str]]:
    errors, warnings = [], []
    if not rows:
        errors.append("Nenhuma linha de detalhe foi gerada.")
        return errors, warnings

    seen = {}
    if valid_ugs is not None and len(valid_ugs) == 0:
        warnings.append("Nenhuma base homologada de UGs foi carregada. A validação de UGs não homologadas não será aplicada.")

    for idx, row in enumerate(rows, start=1):
        ug = str(row.ug).zfill(6) if row.ug else ""
        restr = str(row.restricao).zfill(3) if row.restricao else ""

        if not re.fullmatch(r"\d{6}", row.ug):
            errors.append(f"Linha {idx}: UG inválida ({row.ug}).")
        if not re.fullmatch(r"\d{3}", row.restricao):
            errors.append(f"Linha {idx}: código de restrição inválido ({row.restricao}).")
        elif restr not in CONRESTCON_MOTIVOS:
            errors.append(f"Linha {idx}: código de restrição inexistente na CONRESTCON ({row.restricao}).")

        if valid_ugs is not None and len(valid_ugs) > 0 and ug and ug not in valid_ugs:
            errors.append(f"Linha {idx}: UG não homologada na base oficial de validação ({row.ug}).")

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

    if bloquear_duplicidades:
        for key, count in seen.items():
            if count > 1:
                errors.append(f"Duplicidade UG + Restrição identificada: UG {key[0]} / Restrição {key[1]}.")

    return errors, warnings
