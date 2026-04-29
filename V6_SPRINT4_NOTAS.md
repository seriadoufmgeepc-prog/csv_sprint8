# v6.0 - Sprint 4

## Escopo implementado
- criação das abas modulares em `ui/import_tab.py`, `ui/edit_tab.py`, `ui/summary_tab.py`, `ui/export_tab.py` e `ui/conrestcon_tab.py`;
- início do consumo direto dos serviços pela interface modular;
- criação de um painel inicial de status da importação;
- ativação de uma trilha paralela da interface da v6.0 por meio de toggle, preservando o fluxo legado como fallback.

## Observação
A Sprint 4 não substitui totalmente a interface anterior. Ela introduz uma interface modular funcional paralela, permitindo evolução incremental com menor risco.

## Próxima sprint sugerida
Sprint 5:
- integrar CONRESTCON ao novo fluxo modular;
- conectar memória de alterações à interface;
- aprofundar edição em lote e filtros no modo modular;
- ampliar exportações da nova interface.
