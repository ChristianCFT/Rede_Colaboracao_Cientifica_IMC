// =====================================================================
// consultas.cypher — Perguntas do tema respondidas no grafo heterogêneo
// Cole uma de cada vez no Aura. Use a aba "Graph" para ver o desenho
// e a aba "Table" para ver a tabela. Tire print das duas para o relatório.
// =====================================================================


// ---- C1. Com quais institutos o IMC colabora, e por qual tipo de atividade?
// (pergunta: "qual a situação de colaboração entre institutos?")
MATCH (i1:Instituto {sigla:'IMC'})<-[:LOTADO_EM]-(p1:Pesquisador)-[:PARTICIPOU]->(a:Atividade)
      <-[:PARTICIPOU]-(p2:Pesquisador)-[:LOTADO_EM]->(i2:Instituto)
WHERE i2.sigla <> 'IMC' AND i2.sigla <> 'EXT'
RETURN i2.sigla AS instituto, a.tipo AS tipo_atividade, count(DISTINCT a) AS atividades
ORDER BY instituto, atividades DESC;


// ---- C2. Quais ÁREAS conectam o IMC a institutos com quem ele não tem artigos?
// (pergunta 1 do tema: "quais áreas conectam institutos que não colaboram diretamente?")
MATCH (imc:Instituto {sigla:'IMC'})<-[:LOTADO_EM]-(p1:Pesquisador)-[:ATUA_EM]->(ar:Area)
      <-[:ATUA_EM]-(p2:Pesquisador)-[:LOTADO_EM]->(outro:Instituto)
WHERE outro.sigla <> 'IMC' AND outro.sigla <> 'EXT'
  AND NOT EXISTS {
    MATCH (imc)<-[:LOTADO_EM]-(:Pesquisador)-[:PARTICIPOU]->(art:Atividade {tipo:'ARTIGO'})
          <-[:PARTICIPOU]-(:Pesquisador)-[:LOTADO_EM]->(outro)
  }
RETURN outro.sigla AS instituto_sem_artigos_com_imc, ar.nome AS area_em_comum,
       count(DISTINCT p1) AS docentes_imc, count(DISTINCT p2) AS docentes_outro
ORDER BY docentes_imc + docentes_outro DESC;


// ---- C3. Pares que trabalham juntos em projetos/bancas mas NUNCA publicaram juntos
// (pergunta 4 do tema: "como relações que a coautoria não captura alteram a leitura da rede?")
MATCH (p1:Pesquisador)-[c:COLABORA]-(p2:Pesquisador)
WHERE c.apta = 1 AND c.artigos = 0 AND (c.projetos > 0 OR c.bancas > 0) AND p1.id < p2.id
MATCH (p1)-[:LOTADO_EM]->(i1), (p2)-[:LOTADO_EM]->(i2)
RETURN p1.nome, i1.sigla, p2.nome, i2.sigla, c.projetos, c.bancas
ORDER BY c.projetos + c.bancas DESC LIMIT 20;


// ---- C4. Caminho mais curto de colaboração entre dois docentes
// (mostra o grafo como "mapa": por quem a informação passaria?)
// Troque os nomes por quaisquer dois docentes.
MATCH (a:Pesquisador {nome:'ADLER DINIZ DE SOUZA'}), (b:Pesquisador {nome:'HEVILLA NOBRE CEZAR'})
MATCH caminho = shortestPath((a)-[:COLABORA*..6]-(b))
RETURN caminho;


// ---- C5. Os temas mais trabalhados pelo IMC (pela área dos docentes)
// (pergunta 5 do tema: "quais as principais áreas de pesquisa?")
MATCH (:Instituto {sigla:'IMC'})<-[:LOTADO_EM]-(p:Pesquisador)-[:ATUA_EM]->(ar:Area)
RETURN ar.nome AS area, count(p) AS docentes ORDER BY docentes DESC;


// ---- C6. Visual: a ego-rede do IMC (só pares confirmados), para print no relatório
MATCH (p1:Pesquisador)-[c:COLABORA]-(p2:Pesquisador)
WHERE c.apta = 1
RETURN p1, c, p2 LIMIT 300;
