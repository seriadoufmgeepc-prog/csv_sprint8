# v6.0 - Sprint 1

## Escopo implementado
- congelamento da base estável v5.37.2.5.1 como ponto de partida;
- criação da estrutura modular do projeto;
- centralização inicial de constantes em `core/constants.py`;
- criação dos modelos centrais em `core/models.py`;
- criação do controle inicial de sessão em `core/session.py`;
- criação dos módulos placeholder para parsers, services, ui e tests;
- manutenção do fluxo legado em `app.py`, com bootstrap da nova estrutura.

## Próxima sprint sugerida
Sprint 2:
- mover parser de PDF;
- mover parser de CSV;
- mover parser de Excel;
- consolidar `header_parser.py`;
- conectar `services/import_service.py`.
