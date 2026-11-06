// =====================================================================
// importar.cypher — Carrega o grafo do IMC no Neo4j Aura
//
// ANTES DE RODAR:
//   1. Rode  python gerar_neo4j.py Dataset_Entrada_IMC.csv Dataset_Saida_IMC.csv
//   2. Suba a pasta neo4j/ para o repositório do GitHub do grupo (público).
//   3. Abra um dos CSVs no GitHub, clique em "Raw" e copie o endereço até a pasta.
//      Ex.: https://raw.githubusercontent.com/USUARIO/REPO/main/neo4j/
//   4. Troque BASE_URL abaixo por esse endereço (em TODAS as linhas LOAD CSV).
//
// COMO RODAR NO AURA:
//   Abra a instância -> "Query" -> cole um bloco de cada vez -> Ctrl+Enter.
//   Rode na ordem: 0, 1, 2, 3, 4, 5.
// =====================================================================


// ---- 0. Regras de unicidade (deixam a importação rápida e evitam duplicatas)
CREATE CONSTRAINT pesquisador_id IF NOT EXISTS FOR (p:Pesquisador) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT atividade_id   IF NOT EXISTS FOR (a:Atividade)   REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT instituto_sigla IF NOT EXISTS FOR (i:Instituto)  REQUIRE i.sigla IS UNIQUE;
CREATE CONSTRAINT area_nome      IF NOT EXISTS FOR (a:Area)        REQUIRE a.nome IS UNIQUE;


// ---- 1. Pesquisadores e institutos
LOAD CSV WITH HEADERS FROM 'BASE_URL/pesquisadores.csv' AS l
MERGE (p:Pesquisador {id: l.id})
SET p.nome = l.nome, p.vinculo = l.vinculo, p.foco_imc = toInteger(l.foco_imc),
    p.status = l.status, p.url_lattes = l.url_lattes
MERGE (i:Instituto {sigla: l.instituto})
MERGE (p)-[:LOTADO_EM]->(i);


// ---- 2. Áreas de trabalho
LOAD CSV WITH HEADERS FROM 'BASE_URL/pesquisador_area.csv' AS l
MATCH (p:Pesquisador {id: l.pesquisador_id})
MERGE (a:Area {nome: l.area})
MERGE (p)-[:ATUA_EM]->(a);


// ---- 3. Atividades (artigos, projetos, orientações, bancas, produção técnica)
LOAD CSV WITH HEADERS FROM 'BASE_URL/atividades.csv' AS l
MERGE (a:Atividade {id: l.id})
SET a.tipo = l.tipo, a.subtipo = l.subtipo, a.titulo = l.titulo,
    a.ano = toInteger(l.ano);


// ---- 4. Quem participou de qual atividade (e com qual papel)
LOAD CSV WITH HEADERS FROM 'BASE_URL/participacoes.csv' AS l
MATCH (p:Pesquisador {id: l.pesquisador_id})
MATCH (a:Atividade {id: l.atividade_id})
MERGE (p)-[r:PARTICIPOU {papel: l.papel}]->(a);


// ---- 5. Camadas: relação direta entre pares de pesquisadores (do dataset de saída)
LOAD CSV WITH HEADERS FROM 'BASE_URL/colaboracoes.csv' AS l
MATCH (p1:Pesquisador {id: l.p1})
MATCH (p2:Pesquisador {id: l.p2})
MERGE (p1)-[c:COLABORA]-(p2)
SET c.artigos = toInteger(l.artigos), c.projetos = toInteger(l.projetos),
    c.orientacoes = toInteger(l.orientacoes), c.bancas = toInteger(l.bancas),
    c.tecnica = toInteger(l.tecnica), c.apta = toInteger(l.apta);


// ---- Conferência: quantos de cada tipo de nó e relação foram criados
// Esperado: Pesquisador 1116, Atividade 4595, Area 30 | PARTICIPOU 7765, COLABORA 2130, LOTADO_EM 1116, ATUA_EM 189
MATCH (n) RETURN labels(n)[0] AS tipo_no, count(*) AS quantidade ORDER BY quantidade DESC;
MATCH ()-[r]->() RETURN type(r) AS tipo_relacao, count(*) AS quantidade ORDER BY quantidade DESC;
