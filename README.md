# Gerador de Arquivo (.csv) para Upload de Restrições Contábeis - SIAFI

Versão 5.8 com base na v5.7 e ajustes do prompt do usuário.

## Principais mudanças
- reorganização das abas para:
  - Importação
  - Conferência e Edição
  - Resumo por UG
  - Exportação
- unificação da conferência e da edição em uma única aba com grade principal;
- restabelecimento da padronização textual no fluxo principal;
- remoção da leitura automática do nível a partir do PDF;
- melhoria da leitura do mês de referência com tolerância a variações do cabeçalho;
- retorno do Resumo por UG incluindo UGs com e sem restrição, quando identificadas no relatório;
- exportação Excel com abas:
  - Dados Tratados
  - Resumo por UG
  - Logs e Metadados

## Execução
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Ajustes da v5.10
- Corrige a captura do mês de referência no PDF, com leitura robusta de padrões como `Mês de Referência: Mar/2026`.
- Corrige o problema em que a base podia voltar ao padrão anterior após padronização e edição manual; agora a base em trabalho só é substituída mediante processamento explícito de nova importação.


## Ajustes da v5.11
- o parâmetro de referência do PDF passa a usar a **Data e hora da consulta** em vez do campo Mês de Referência;
- o botão **Reiniciar aplicativo** foi movido para a parte inferior da guia **Importação**;
- ao reiniciar, as caixas de upload são limpas por meio da renovação das chaves dos uploaders.


## Ajustes da v5.12
- correção da captura do **Nome da UG** no Resumo por UG, limitando a leitura apenas à linha `UG: código - nome`;
- remoção da coluna **Descrição Resumida das Restrições** do resumo e da exportação correspondente.


## Ajustes da v5.13
- a referência derivada do PDF usa efetivamente a **Data e hora da consulta**; no relatório anexado, isso leva à referência **abr/2026**;
- os filtros da aba **Conferência e Edição** ganharam botão **Limpar filtros**;
- após aplicar **edição em lote**, os filtros são redefinidos automaticamente para evitar persistência indevida e efeitos colaterais visuais nas demais abas.


## Ajustes da v5.14
- exclusão do parâmetro visual **Mês do relatório**;
- inclusão do parâmetro **Emissão do relatório**, com base na Data e hora da consulta;
- a referência do arquivo passa a ser fixada no **mês anterior à emissão**;
- retorno do quadro **Resumo por Restrição** na guia **Resumo por UG** e na exportação Excel.


## Ajustes da v5.15
- remoção do parâmetro visual de **Mês do relatório**;
- inclusão explícita de **Emissão do relatório** e **Referência contábil**;
- a referência é calculada automaticamente como o mês anterior à emissão;
- correção estrutural do botão **Limpar filtros**, sem escrever em chaves de widgets já instanciados;
- os filtros da aba Conferência e Edição deixam de interferir no Resumo por UG.


## Ajuste da v5.16
- exclusão da coluna **UGs Distintas** do quadro **Resumo por Restrição**.


## Ajustes da v5.17
- exclusão efetiva do campo visual de **Mês do relatório**;
- inclusão explícita de **Emissão do relatório** e **Referência contábil**;
- correção estrutural do botão **Limpar filtros** com renovação segura das chaves dos widgets;
- após edição em lote, os filtros são redefinidos para **Todas**.


## Ajustes da v5.18
- o painel de importação passa a exibir somente **Emissão do relatório** e o nome do arquivo, sem campo visual de referência contábil;
- a referência continua sendo usada internamente apenas para compor o nome do arquivo e a lógica contábil;
- remoção definitiva de escritas nas chaves antigas dos filtros;
- correção do botão **Limpar filtros** com chaves dinâmicas e estado canônico separado.


## Ajustes da v5.19
- retorno do **Mês de referência** aos parâmetros do header, em linha com a experiência da v5.10;
- substituição do dado de origem **Mês do relatório** por **Data de emissão do relatório PDF**;
- a data de emissão continua disponível como metadado da importação, sem sobrescrever automaticamente o mês de referência do header.


## Ajuste da v5.20
- renomeação do campo de origem do relatório para **Data da consulta**.


## Ajuste da v5.21
- exclusão definitiva dos campos não funcionais de data na guia Importação;
- manutenção apenas dos parâmetros funcionais do header: Nível, Código responsável, Mês de referência, Ano de referência e Nome do arquivo CSV.


## Ajustes da v5.23
- eliminação da mensagem residual “não identificada” relacionada a data;
- o **Mês de referência** deixa de vir pré-preenchido antes da importação;
- ao importar PDF, o mês é preenchido a partir de **Mês de Referência** no cabeçalho do relatório;
- ao importar CSV de referência, o mês é preenchido a partir do header do arquivo;
- o **Ano de referência** passa a usar o ano atual do sistema até que a importação informe outro valor.


## Ajustes da v5.24
- reintrodução da função `source_signature`, eliminando o erro `NameError` no processamento do PDF;
- remoção da informação residual “NÃO IDENTIFICADA” que aparecia sem referência específica após a importação.


## Ajustes da v5.25
- correção da função `summarize_by_restriction`, eliminando o erro `NameError` no fim da tela;
- remoção adicional de textos residuais “Não identificada” na interface.


## Ajustes da v5.26
- o **Mês de referência** fica em branco antes da importação;
- após ler o **PDF** ou o **CSV**, ele é automaticamente fixado;
- depois disso, continua **editável por lista de opções**;
- no **PDF**, o preenchimento usa o campo **Mês de Referência** do cabeçalho;
- no **CSV de referência**, o preenchimento usa o **header** do arquivo;
- o **Ano de referência** continua baseado no ano atual do sistema até que a importação informe outro valor.


## Ajuste da v5.26.1
- correção do `IndentationError` na área de métricas da guia Importação;
- remoção de uma mensagem residual sem rótulo após o processamento do PDF.


## Ajustes da v5.27
- ampliação das opções de capitalização na guia **Conferência e Edição**;
- novas opções incluídas: **Sentence case**, **Title Case**, **Invert Case** e **CamelCase**;
- os textos padrão por restrição também passam a respeitar o modo de capitalização selecionado.


## Ajustes da v5.28
- o motivo padronizado por código de restrição passa a usar a tabela **CONRESTCON.xlsx** enviada pelo usuário;
- a substituição automática passa a ocorrer **somente no campo Motivo**;
- a coluna **Providência** permanece com o texto original do documento de origem quando o motivo padronizado é aplicado;
- criação da aba **CONRESTCON** para consulta da tabela, com filtro por digitação e por seleção do código de restrição.


## Ajustes da v5.29
- a faixa de opções de capitalização foi ajustada para as opções solicitadas pelo usuário;
- a capitalização passa a atuar tanto em **Motivo** quanto em **Providência**;
- inclusão de uma terceira forma de aplicação da padronização: **Linhas selecionadas**, além de **Base inteira** e **Filtro atual**.


## Ajuste da v5.29.1
- correção do erro `NameError` causado pelo uso de `escopo_padronizacao` antes de sua definição.


## Ajustes da v5.31.1
- correção do `NameError` causado por regressão na versão anterior, preservando as funções-base do app;
- correção do `ValueError` quando o mês do header está vazio;
- opções de capitalização limitadas às quatro solicitadas;
- remoção das notas explicativas indicadas pelo usuário;
- padronização e capitalização executadas com um clique por meio de formulários separados e atualização imediata da visualização.


## Ajustes da v5.32
- para os escopos **Linhas selecionadas**, a seleção passou a ser feita diretamente na grade principal por meio da coluna **Selecionar**;
- remoção das caixas específicas de seleção nos módulos de capitalização e padronização por restrição;
- a edição por capitalização passa a atuar simultaneamente sobre **Motivo** e **Providência** nos registros selecionados/escopo escolhido.


## Ajustes da v5.32.1
- o botão **Salvar Ajustes Manuais** e os contadores **Linhas no filtro** e **Linhas selecionadas** foram movidos para logo abaixo da grade principal e acima do Módulo 2;
- os títulos dos módulos da aba **Conferência e Edição** foram padronizados com o mesmo tamanho, menor e em negrito.


## Ajustes da v5.33.1
- remoção dos subtítulos duplicados na aba **Resumo por UG**;
- inserção do texto **Restrições contábeis por Unidade Gestora**;
- reposicionamento da aba **CONRESTCON** para a última posição, após **Exportação**;
- atualização do nome da funcionalidade e do subtítulo principal do aplicativo.


## Ajustes da v5.34
- inclusão de uma seção recolhível **Guia do Usuário** na aba **Importação**, acima da Etapa 1, com o passo a passo prático de uso da ferramenta.


## Ajuste da v5.34.1
- restauração da aba **CONRESTCON**, com base de dados disponível para consulta, filtro por digitação e seleção por código.


## Ajustes visuais da v5.35
- melhoria do aspecto visual geral com CSS leve para abas, métricas, expanders, botões e grades;
- inclusão de banners visuais por aba;
- diferenciação de botões de ação com ícones e botões primários/secundários;
- melhoria visual da seção de reinicialização.


## Ajustes da v5.36
- substituição da base **CONRESTCON** pela nova planilha anexada pelo usuário;
- a nova base passa a ser usada na aba **CONRESTCON**;
- a nova base continua sendo utilizada como fonte da **padronização por código de restrição** na aba **Conferência e Edição**;
- a nova base também passa a ser usada como **modelo padronizado para digitação manual** na aba **Importação**.


## Ajuste da v5.36.1
- remoção do subtítulo da ferramenta.


## Ajustes da v5.36.2
- utilização da planilha **Unidades Gestoras.xlsx** como fonte do nome da UG na tabela **Restrições contábeis por Unidade Gestora**;
- prioridade do nome da UG proveniente da planilha anexada na montagem do resumo por UG;
- remoção do subtítulo do aplicativo.


## Ajustes da v5.36.3
- no **Quadro Resumo por Restrição**, o código passou a ser exibido no formato `código - título`, com base na CONRESTCON;
- inclusão de alerta na **Edição em lote de texto** orientando a selecionar linhas no filtro ou aplicar os ajustes na base inteira.


## Ajustes da v5.36.4
- leitura automática do campo **Mês de Referência: Mar/2026** no cabeçalho do PDF;
- preenchimento automático do campo **Mês de referência** com a opção correspondente, mantendo edição manual disponível;
- ao reiniciar o relatório, o campo volta obrigatoriamente para **Selecione...**.


## Ajustes da v5.37
- implementação de um parser estruturado do cabeçalho do PDF;
- especificação do parser inserida na aba Importação;
- leitura automática dos campos do cabeçalho, com foco especial no campo `Mês de Referência: Mar/2026` para preenchimento automático do mês no header;
- manutenção da edição manual do campo de mês e retorno para `Selecione...` após reinicialização.


## Ajustes da v5.37.1
- correção da leitura do mês priorizando o cabeçalho textual da primeira página do PDF;
- ajuste do reset para forçar o campo `Mês de referência` a voltar para `Selecione...`;
- sincronização explícita do valor processado com o widget do mês no header.


## Ajustes da v5.37.2
- correção da regex do mês para aceitar o padrão invertido extraído do PDF (`Mar/2026Mês de Referência:`);
- remoção da escrita direta em chaves de widgets do Streamlit no reset, eliminando o erro `StreamlitAPIException`;
- uso de `header_widget_nonce` para recriar os campos do header após processar PDF ou reiniciar o aplicativo.


## Ajuste da v5.37.2.1
- inclusão da leitura automática do mês de referência também para arquivos CSV e Excel;
- CSV existente: uso do header do arquivo e fallback pelo nome do arquivo;
- planilha estruturada: tentativa de inferência do mês por células/colunas e fallback pelo nome do arquivo.


## Ajuste da v5.37.2.2
- reforço da leitura do mês no CSV a partir do registro Header (`H`), com tolerância a diferentes delimitadores e formatos de mês na coluna D;
- melhoria dos logs de diagnóstico para verificar o valor efetivamente capturado do header do CSV.


## Ajuste da v5.37.2.3
- correção da exibição do mês no campo do header quando o valor vem do CSV ou Excel como texto;
- normalização do mês para o mesmo tipo usado pelo seletor visual (`int`), permitindo o preenchimento automático correto.


## Ajuste da v5.37.2.4
- correção do fluxo de importação do CSV para recriar o widget do header após a leitura do mês;
- sincronização visual do campo `Mês de referência` com o valor lido do header do CSV.


## Ajuste da v5.37.2.5
- aprimoramento das mensagens de confirmação para importação de PDF e CSV;
- mensagens mais claras sobre o mês de referência efetivamente carregado no header do sistema.


## Ajuste da v5.37.2.5.1
- correção do `NameError` causado pela ausência da função `month_option_label` em mensagens de importação do CSV.


## v6.0 - Sprint 1
- estrutura modular inicial criada;
- base estável preservada;
- bootstrap da nova arquitetura adicionado ao app legado;
- próximos passos documentados em `V6_SPRINT1_NOTAS.md`.


## Ajuste da v6.0 Sprint 1.1
- correção do carregamento de módulos locais (`core`, `ui`, `utils`, etc.) via inclusão explícita do diretório raiz no `sys.path`.


## Ajuste da v6.0 Sprint 1.2
- fallback local para os imports modulares (`core.session` e `ui.components`), evitando falha de abertura do app quando o ambiente não reconhece os pacotes da nova estrutura.


## v6.0 - Sprint 2
- parsers e serviço de importação estruturados em módulos dedicados;
- base pronta para extração gradual do fluxo legado de importação.


## v6.0 - Sprint 3
- serviços de padronização, validação, resumo e auditoria iniciados;
- base pronta para migração gradual da interface na Sprint 4.


## v6.0 - Sprint 4
- interface modular inicial conectada aos serviços;
- novo modo de interface ativável por toggle, preservando fallback no fluxo legado.


## v6.0 - Sprint 5
- integração modular da CONRESTCON;
- memória de alterações conectada à interface;
- filtros, padronização por restrição e exportação modular ampliados.


## v6.0 - Sprint 6
- modo modular consolidado com exportações CSV/Excel, validação e memória de alterações.


## v6.0 - Sprint 7
- etapa de homologação funcional iniciada, com checklist, comparação e aba dedicada no modo modular.


## v6.0 - Sprint 8
- execução da homologação funcional iniciada com registro estruturado de resultados e modelo de relatório final.
