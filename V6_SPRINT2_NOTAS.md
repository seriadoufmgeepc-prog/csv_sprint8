# v6.0 - Sprint 2

## Escopo implementado
- modularização inicial do parser de cabeçalho em `parsers/header_parser.py`;
- modularização inicial do parser de PDF em `parsers/pdf_parser.py`;
- modularização inicial do parser de CSV em `parsers/csv_parser.py`;
- modularização inicial do parser de Excel/planilha em `parsers/excel_parser.py`;
- criação do `services/import_service.py` para orquestrar importação por origem.

## Observação
Nesta sprint, os módulos foram implementados e preparados para uso. O `app.py` legado ainda não foi completamente reescrito para depender apenas desses serviços, mas a base técnica da importação já está estruturada.

## Próxima sprint sugerida
Sprint 3:
- extrair padronização textual;
- extrair validações;
- extrair resumos;
- iniciar memória de alterações.
