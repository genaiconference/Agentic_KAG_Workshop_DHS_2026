examples = [

# ---------------------------------------------------------------------
# 1) BASIC RETRIEVAL
# ---------------------------------------------------------------------

"USER INPUT: 'List all movies.'\nQUERY: MATCH (m:Movie) RETURN m.title, m.release_date, m.vote_average ORDER BY m.title",

"USER INPUT: 'Show all actors.'\nQUERY: MATCH (p:Person)-[:CAST_IN]->(:Movie) RETURN DISTINCT p.name ORDER BY p.name",

"USER INPUT: 'List all directors.'\nQUERY: MATCH (:Movie)-[:DIRECTED_BY]->(p:Person) RETURN DISTINCT p.name ORDER BY p.name",

"USER INPUT: 'List all writers.'\nQUERY: MATCH (:Movie)-[:WRITTEN_BY]->(p:Person) RETURN DISTINCT p.name ORDER BY p.name",

"USER INPUT: 'List all genres.'\nQUERY: MATCH (g:Genre) RETURN g.name ORDER BY g.name",

"USER INPUT: 'Show all production companies.'\nQUERY: MATCH (pc:ProductionCompany) RETURN pc.name ORDER BY pc.name",

"USER INPUT: 'List all countries.'\nQUERY: MATCH (c:Country) RETURN c.name ORDER BY c.name",

"USER INPUT: 'List all languages.'\nQUERY: MATCH (l:Language) RETURN l.name ORDER BY l.name",

"USER INPUT: 'Show all keywords.'\nQUERY: MATCH (k:Keyword) RETURN k.name ORDER BY k.name",


# ---------------------------------------------------------------------
# 2) RELATIONSHIPS
# ---------------------------------------------------------------------

"USER INPUT: 'Who directed Inception?'\nQUERY: MATCH (m:Movie)-[:DIRECTED_BY]->(p:Person) WHERE toLower(m.title) CONTAINS 'inception' RETURN p.name",

"USER INPUT: 'Who wrote Inception?'\nQUERY: MATCH (m:Movie)-[:WRITTEN_BY]->(p:Person) WHERE toLower(m.title) CONTAINS 'inception' RETURN p.name",

"USER INPUT: 'Who acted in Inception?'\nQUERY: MATCH (p:Person)-[:CAST_IN]->(m:Movie) WHERE toLower(m.title) CONTAINS 'inception' RETURN DISTINCT p.name ORDER BY p.name",

"USER INPUT: 'What genres does Inception belong to?'\nQUERY: MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre) WHERE toLower(m.title) CONTAINS 'inception' RETURN g.name ORDER BY g.name",

"USER INPUT: 'Which production companies made Inception?'\nQUERY: MATCH (m:Movie)-[:PRODUCED_BY]->(pc:ProductionCompany) WHERE toLower(m.title) CONTAINS 'inception' RETURN pc.name ORDER BY pc.name",

"USER INPUT: 'Which languages are spoken in Inception?'\nQUERY: MATCH (m:Movie)-[:SPOKEN_IN]->(l:Language) WHERE toLower(m.title) CONTAINS 'inception' RETURN l.name ORDER BY l.name",

"USER INPUT: 'Which keywords are associated with Inception?'\nQUERY: MATCH (m:Movie)-[:TAGGED_WITH]->(k:Keyword) WHERE toLower(m.title) CONTAINS 'inception' RETURN k.name ORDER BY k.name",

"USER INPUT: 'Which country produced Inception?'\nQUERY: MATCH (m:Movie)-[:PRODUCED_IN]->(c:Country) WHERE toLower(m.title) CONTAINS 'inception' RETURN c.name",


# ---------------------------------------------------------------------
# 3) FILTERING
# ---------------------------------------------------------------------

"USER INPUT: 'List movies with vote average above 7.'\nQUERY: MATCH (m:Movie) WHERE m.vote_average > 7 RETURN m.title, m.vote_average ORDER BY m.vote_average DESC",

"USER INPUT: 'Movies released after 2020.'\nQUERY: MATCH (m:Movie) WHERE m.release_date >= date('2020-01-01') RETURN m.title, m.release_date ORDER BY m.release_date DESC",

"USER INPUT: 'Movies longer than 2 hours.'\nQUERY: MATCH (m:Movie) WHERE m.runtime_minutes > 120 RETURN m.title, m.runtime_minutes ORDER BY m.runtime_minutes DESC",

"USER INPUT: 'Movies with revenue above 1 billion dollars.'\nQUERY: MATCH (m:Movie) WHERE m.revenue_usd > 1000000000 RETURN m.title, m.revenue_usd ORDER BY m.revenue_usd DESC",

"USER INPUT: 'Movies with budget less than 10 million.'\nQUERY: MATCH (m:Movie) WHERE m.budget_usd < 10000000 RETURN m.title, m.budget_usd ORDER BY m.budget_usd",

"USER INPUT: 'Action movies.'\nQUERY: MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre) WHERE toLower(g.name)='action' RETURN DISTINCT m.title ORDER BY m.title",

"USER INPUT: 'English language movies.'\nQUERY: MATCH (m:Movie)-[:SPOKEN_IN]->(l:Language) WHERE toLower(l.name)='english' RETURN DISTINCT m.title ORDER BY m.title",

"USER INPUT: 'Movies tagged with time travel.'\nQUERY: MATCH (m:Movie)-[:TAGGED_WITH]->(k:Keyword) WHERE toLower(k.name) CONTAINS 'time travel' RETURN DISTINCT m.title ORDER BY m.title",


# ---------------------------------------------------------------------
# 4) AGGREGATIONS
# ---------------------------------------------------------------------

"USER INPUT: 'How many movies are there?'\nQUERY: MATCH (m:Movie) RETURN COUNT(m) AS total_movies",

"USER INPUT: 'Movies per genre.'\nQUERY: MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre) RETURN g.name, COUNT(m) AS movie_count ORDER BY movie_count DESC",

"USER INPUT: 'Movies per production company.'\nQUERY: MATCH (m:Movie)-[:PRODUCED_BY]->(pc:ProductionCompany) RETURN pc.name, COUNT(m) AS movies ORDER BY movies DESC",

"USER INPUT: 'Average movie rating by genre.'\nQUERY: MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre) RETURN g.name, avg(m.vote_average) AS avg_rating ORDER BY avg_rating DESC",

"USER INPUT: 'Top 10 highest rated movies.'\nQUERY: MATCH (m:Movie) RETURN m.title, m.vote_average ORDER BY m.vote_average DESC LIMIT 10",

"USER INPUT: 'Top 10 highest grossing movies.'\nQUERY: MATCH (m:Movie) RETURN m.title, m.revenue_usd ORDER BY m.revenue_usd DESC LIMIT 10",

"USER INPUT: 'Top 10 biggest budget movies.'\nQUERY: MATCH (m:Movie) RETURN m.title, m.budget_usd ORDER BY m.budget_usd DESC LIMIT 10",

"USER INPUT: 'Average runtime of movies.'\nQUERY: MATCH (m:Movie) RETURN avg(m.runtime_minutes) AS average_runtime",


# ---------------------------------------------------------------------
# 5) PATTERN SEARCH / RECOMMENDATIONS
# ---------------------------------------------------------------------

"USER INPUT: 'Find movies directed by Christopher Nolan.'\nQUERY: MATCH (m:Movie)-[:DIRECTED_BY]->(p:Person) WHERE toLower(p.name) CONTAINS 'christopher nolan' RETURN m.title ORDER BY m.release_date",

"USER INPUT: 'Find movies written by Quentin Tarantino.'\nQUERY: MATCH (m:Movie)-[:WRITTEN_BY]->(p:Person) WHERE toLower(p.name) CONTAINS 'quentin tarantino' RETURN m.title ORDER BY m.release_date",

"USER INPUT: 'Find movies starring Tom Hanks.'\nQUERY: MATCH (p:Person)-[:CAST_IN]->(m:Movie) WHERE toLower(p.name) CONTAINS 'tom hanks' RETURN m.title ORDER BY m.release_date",

"USER INPUT: 'Find movies directed and written by the same person.'\nQUERY: MATCH (m:Movie)-[:DIRECTED_BY]->(p:Person), (m)-[:WRITTEN_BY]->(p) RETURN DISTINCT m.title, p.name ORDER BY m.title",

"USER INPUT: 'Find movies in both Action and Science Fiction genres.'\nQUERY: MATCH (m:Movie)-[:HAS_GENRE]->(:Genre {name:'Action'}), (m)-[:HAS_GENRE]->(:Genre {name:'Science Fiction'}) RETURN DISTINCT m.title ORDER BY m.title",

"USER INPUT: 'Find movies produced in the United States and spoken in English.'\nQUERY: MATCH (m:Movie)-[:PRODUCED_IN]->(:Country {name:'United States'}), (m)-[:SPOKEN_IN]->(:Language {name:'English'}) RETURN DISTINCT m.title ORDER BY m.title",

"USER INPUT: 'Find movies tagged with both time travel and dystopia.'\nQUERY: MATCH (m:Movie)-[:TAGGED_WITH]->(:Keyword {name:'time travel'}), (m)-[:TAGGED_WITH]->(:Keyword {name:'dystopia'}) RETURN DISTINCT m.title ORDER BY m.title",

"USER INPUT: 'Find actors who worked with Christopher Nolan.'\nQUERY: MATCH (m:Movie)-[:DIRECTED_BY]->(d:Person), (a:Person)-[:CAST_IN]->(m) WHERE toLower(d.name) CONTAINS 'christopher nolan' RETURN DISTINCT a.name ORDER BY a.name",


# ---------------------------------------------------------------------
# 6) DATE / TIME RELATED
# ---------------------------------------------------------------------

"USER INPUT: 'Latest movies.'\nQUERY: MATCH (m:Movie) RETURN m.title, m.release_date ORDER BY m.release_date DESC LIMIT 10",

"USER INPUT: 'Oldest movies.'\nQUERY: MATCH (m:Movie) RETURN m.title, m.release_date ORDER BY m.release_date ASC LIMIT 10",

"USER INPUT: 'Movies released in 2023.'\nQUERY: MATCH (m:Movie) WHERE m.release_date >= date('2023-01-01') AND m.release_date < date('2024-01-01') RETURN m.title, m.release_date ORDER BY m.release_date",

"USER INPUT: 'Movies released between 2015 and 2020.'\nQUERY: MATCH (m:Movie) WHERE m.release_date >= date('2015-01-01') AND m.release_date < date('2021-01-01') RETURN m.title, m.release_date ORDER BY m.release_date"

]
