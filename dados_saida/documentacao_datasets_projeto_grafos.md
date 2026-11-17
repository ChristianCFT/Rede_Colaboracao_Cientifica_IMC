# Documentação dos Datasets — Projeto de Grafos (UNIFEI)

Este documento apresenta uma breve descrição de cada dataset e de suas respectivas colunas utilizadas no projeto de análise e construção da rede de colaboração acadêmica.

---

## Resumo da Arquitetura

* **`dataset_completo_UNIFEI.csv`**: Cadastro geral e informações institucionais dos pesquisadores da universidade.
* **`dataset_atividades_IMC.csv`**: Informações detalhadas sobre as atividades acadêmicas extraídas dos currículos.
* **`dataset_entrada_IMC.csv`**: Atividades e características individuais de cada pesquisador (nós do grafo).
* **`dataset_saida_IMC.csv`**: Relações e atividades compartilhadas entre os pesquisadores, utilizadas na construção da rede de colaboração (arestas do grafo).

---

## 1. `dataset_completo_UNIFEI.csv`

Contém o cadastro geral dos pesquisadores da UNIFEI, reunindo suas principais informações institucionais.

### Colunas
* **`pesquisador_id`**: Identificador único do pesquisador.
* **`nome`**: Nome do pesquisador.
* **`instituto`**: Instituto ao qual está vinculado.
* **`area`**: Área de atuação do pesquisador.
* **`ciape`**: Identificador CIAPE.
* **`lattes_url`**: Endereço do Currículo Lattes.

---

## 2. `dataset_atividades_IMC.csv`

Contém as atividades acadêmicas identificadas nos currículos dos pesquisadores, incluindo artigos, projetos, orientações, bancas e produções técnico-tecnológicas.

### Colunas
* **`id_atividade`**: Identificador da atividade.
* **`dimensao`**: Categoria da atividade (`ART`, `PRJ`, `ORI`, `BAN` ou `PTT`).
* **`posicao_no_vetor`**: Posição da categoria no vetor.
* **`tipo_atividade`**: Tipo geral da atividade.
* **`subtipo`**: Classificação específica da atividade.
* **`titulo`**: Título da atividade.
* **`ano`**: Ano da atividade.
* **`doi`**: Identificador DOI, quando disponível.
* **`numero_registro`**: Número de registro da atividade.
* **`aluno_ou_candidato`**: Aluno ou candidato relacionado à atividade.
* **`periodo_projeto`**: Período de realização do projeto.
* **`situacao_projeto`**: Situação do projeto.
* **`ids_participantes`**: Identificadores dos participantes.
* **`nomes_participantes`**: Nomes dos participantes.
* **`institutos_participantes`**: Institutos dos participantes.
* **`papeis_participantes`**: Papéis dos participantes na atividade.
* **`metodo_identificacao`**: Método utilizado para identificar os participantes.
* **`ids_participantes_IMC`**: Identificadores dos participantes vinculados ao IMC.
* **`qtd_participantes_identificados`**: Quantidade de participantes identificados.
* **`qtd_participantes_IMC`**: Quantidade de participantes do IMC.
* **`envolve_IMC`**: Indica se a atividade envolve participantes do IMC.
* **`nomes_nao_resolvidos`**: Nomes de participantes que não foram identificados.
* **`registrado_no_cv_de`**: Pesquisador em cujo currículo a atividade foi encontrada.
* **`qtd_registros_unificados`**: Quantidade de registros reunidos na atividade.
* **`fontes`**: Referências aos registros de origem.
* **`chave_deduplicacao`**: Chave utilizada para identificar atividades duplicadas.

---

## 3. `dataset_entrada_IMC.csv`

Organiza as informações individualmente por pesquisador, reunindo seus dados institucionais e as atividades associadas a cada um. Também possui um vetor de contagem que representa a quantidade de atividades individuais em cada categoria.

### Colunas
* **`nome do pesquisador`**: Nome do pesquisador.
* **`instituto`**: Instituto ao qual está vinculado.
* **`area de trabalho`**: Área de atuação.
* **`artigos científicos`**: IDs dos artigos associados ao pesquisador.
* **`projetos de pesquisa`**: IDs dos projetos associados ao pesquisador.
* **`orientação`**: IDs das orientações associadas ao pesquisador.
* **`bancas acadêmicas`**: IDs das bancas associadas ao pesquisador.
* **`produção técnico-tecnológica`**: IDs das produções associadas ao pesquisador.
* **`pesquisador_id`**: Identificador do pesquisador.
* **`vetor contagem`**: Quantidade de atividades individuais em cada categoria.
* **`observacao`**: Informações ou observações adicionais.

---

## 4. `dataset_saida_IMC.csv`

Contém as relações entre pares de pesquisadores. Cada registro representa uma relação e apresenta as atividades compartilhadas entre os dois pesquisadores.

### Colunas
* **`nome do pesquisador 1`**: Nome do primeiro pesquisador.
* **`nome do pesquisador 2`**: Nome do segundo pesquisador.
* **`instituto pesquisador 1`**: Instituto do primeiro pesquisador.
* **`instituto pesquisador 2`**: Instituto do segundo pesquisador.
* **`area de trabalho pesquisador 1`**: Área de atuação do primeiro pesquisador.
* **`area de trabalho pesquisador 2`**: Área de atuação do segundo pesquisador.
* **`vetor bruto`**: Listas dos IDs das atividades compartilhadas entre os pesquisadores.
* **`id pesquisador 1`**: Identificador do primeiro pesquisador.
* **`id pesquisador 2`**: Identificador do segundo pesquisador.
* **`tipo de relacao`**: Classificação da relação conforme os institutos dos pesquisadores.
* **`vetor contagem`**: Quantidade de atividades compartilhadas em cada categoria.
