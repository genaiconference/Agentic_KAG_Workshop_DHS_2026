from neo4j_graphrag.schema import get_schema
from neo4j_graphrag.retrievers import HybridCypherRetriever, Text2CypherRetriever
from neo4j_graphrag.retrievers import HybridRetriever
from neo4j_graphrag.types import LLMMessage
from neo4j_graphrag.types import RetrieverResultItem
from neo4j_graphrag.message_history import InMemoryMessageHistory
from neo4j_graphrag.generation import GraphRAG, RagTemplate
from langchain_core.tools import Tool
from prompts import rag_prompt, custom_text2cypher_prompt
from examples import examples
from langchain_classic.prompts import PromptTemplate
#from cypher import local_search_query
from langchain_core.runnables import RunnableLambda
from tqdm.auto import tqdm
from openai import OpenAI
from langchain_openai import ChatOpenAI
from neo4j_graphrag.llm import OpenAILLM
from langchain_openai import ChatOpenAI
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from neo4j import GraphDatabase
import os

load_dotenv()  # This loads .env at project root

NEO4J_URI      = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J')

# Set OPENAI_API_KEY as env variable for openai/neo4j-graphrag compatibility
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

# open_ai_client
open_ai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)



llm = ChatOpenAI(
    model_name="gpt-5-mini",
    temperature=0
)

embedder = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

INDEX_NAME = "entity_vector_index"
FULLTEXT_INDEX_NAME = "entity_fulltext_index"

DIMENSION = 1536

#--------------------------------------------------------------------------------------------------Tool Descriptions-------------------------------------------------------------------------------------------------------------------------

HYBRID_CYPHER_DESCRIPTION = """
Purpose:
Answer questions requiring graph traversal or relationship reasoning.

Use when:
- shortest paths
- relationship exploration
- multi-hop reasoning
- shared actors/directors
- graph connectivity

Examples:
- How is Inception connected to Interstellar?
- Which actors worked with both Nolan and Villeneuve?
- Movies sharing both genre and production company.

Never use for:
- general summaries
- recommendations
- simple entity lookup
"""


TEXT2CYPHER_DESCRIPTION = """
Purpose:
Answer precise, structured questions by translating natural language into a
Cypher query, executing it on the graph, and returning a grounded answer.

Use when the question needs exact, deterministic results such as:
- counts / aggregations (how many, average, total)
- filtering by properties (year, rating, language, runtime)
- ranking / top-N (highest-rated, longest, most common)
- lookups that map cleanly to structured graph patterns

Examples:
- List the top 10 highest-rated Hindi movies.
- How many movies are in the graph?
- Which movies did Christopher Nolan direct?
- Comedy movies released after 2015.

Never use for:
- open-ended summaries or themes
- semantic similarity / recommendations
"""


WEB_SEARCH_DESCRIPTION = """
Purpose:
Search the live web (via Tavily) for up-to-date movie information that is NOT
in the knowledge graph.

Use when the question is about latest / recent / current / upcoming movies or
real-world facts that change over time, such as:
- newly released or upcoming movies (this week, this month, this year)
- current box-office numbers, recent awards, latest news
- release dates, trailers, or cast announcements for new films
- anything requiring information more recent than the graph's data

Examples:
- What are the latest movies released this week?
- Upcoming Marvel movies in 2026.
- Recent Oscar winners.
- What is the newest Christopher Nolan movie?

Never use for:
- questions answerable from the movie knowledge graph
- historical/static facts already stored in the graph
"""




# -------------------------------------------------------------------------------------------------- Define Hybrid Cypher Retrieval Tool -----------------------------------------------------------------------------------------------------


def result_formatter_dynamic(record):
    data = record.data()
    if len(data) == 1 and isinstance(list(data.values())[0], dict):
        node_props = dict(list(data.values())[0])
    else:
        node_props = dict(data)
    content = "\n".join(f"{k}: {v}" for k, v in node_props.items())

    return RetrieverResultItem(
        content=content.strip(),
        metadata={
            "raw_properties": node_props,
            "score": record.get("score"),
            "node_keys": list(node_props.keys())
        }
    )


def generate_cypher_query(query):
    """
    Generate Cypher using the Text2Cypher Retriever

    """
    t2c_retriever = Text2CypherRetriever(
        llm=llm,
        neo4j_schema=get_schema(driver),
        driver=driver,
        custom_prompt=custom_text2cypher_prompt,
        examples=examples,
    )
    response = t2c_retriever.search(query_text=query)
    return response.metadata['cypher']


def generate_cypher_query_lcel(user_question: str) -> str:
    """
    Converts a natural language question into a read-only Cypher query.

    Args:
        user_question (str): The user's natural language query.

    Returns:
        str: A syntactically correct Cypher query as a string.
    """
    # Ensure cypher_gen_prompt is a PromptTemplate before chaining
    if isinstance(custom_text2cypher_prompt, str):
        cypher_prompt_template = PromptTemplate.from_template(custom_text2cypher_prompt)
    else:
        cypher_prompt_template = custom_text2cypher_prompt

    cypher_chain = cypher_prompt_template | llm

    result = cypher_chain.invoke({"query_text":user_question, "examples":examples})

    return result.content



def get_rag_for_query_text2cypher(query: str):
    """
    Wrapper to generate a Rag object dynamically for each query
    """
    t2c_retriever = Text2CypherRetriever(
        llm=llm,
        neo4j_schema=get_schema(driver),
        driver=driver,
        custom_prompt=custom_text2cypher_prompt,
        examples=examples,
    )

    custom_template = RagTemplate(template=rag_prompt,
                                  expected_inputs=["context", "query_text"],
                                  )

    rag_obj = GraphRAG(retriever=t2c_retriever, llm=llm, prompt_template=custom_template)

    response = rag_obj.search(
        query,
        return_context=True,
        retriever_config={'top_k': 20},
        response_fallback="I can't answer this question without context"
    )
    return response.answer


def get_rag_for_query_hybrid_cypher(query: str):
    """
    Wrapper to generate a Rag object dynamically for each query
    """
    INDEX_NAME = "movie_embedding_index"
    FULLTEXT_INDEX_NAME = "movie_text_index"

    cypher_query = generate_cypher_query_lcel(query)
    print(cypher_query)
    hybrid_cypher_retriever = HybridCypherRetriever(
        driver=driver,
        vector_index_name=INDEX_NAME,
        fulltext_index_name=FULLTEXT_INDEX_NAME,
        retrieval_query=cypher_query,
        embedder=embedder,
        result_formatter=result_formatter_dynamic,
    )

    custom_template = RagTemplate(template=rag_prompt,
                                  expected_inputs=["context", "query_text"],
                                  )

    rag_obj = GraphRAG(retriever=hybrid_cypher_retriever, llm=llm, prompt_template=custom_template)

    response = rag_obj.search(
        query,
        return_context=True,
        retriever_config={'top_k': 20},
        response_fallback="I can't answer this question without context"
    )
    return response.answer


hybrid_cypher_tool = Tool(
    name="HybridCypher",
    func=get_rag_for_query_hybrid_cypher,
    description=(
        HYBRID_CYPHER_DESCRIPTION
    )
)

# ------------------------------------------------------------------------------------------------- Define Text2Cypher Tool (LangChain GraphCypherQAChain) ---------------------------------------------------------------------------------------------------------
# This tool follows the LangChain `GraphCypherQAChain` concept used in
# 08_text2cypher_workshop_demo.ipynb: it wraps the Neo4j database with a
# `Neo4jGraph` (which exposes the schema), lets the LLM generate a Cypher query,
# validates/corrects the relationship directions, executes it, and synthesizes a
# natural-language answer from the results.

# Build the LangChain Neo4jGraph + GraphCypherQAChain once and reuse them.
_text2cypher_chain = None


def _get_text2cypher_chain():
    """Lazily build (and cache) the LangChain GraphCypherQAChain."""
    global _text2cypher_chain
    if _text2cypher_chain is None:
        from langchain_neo4j import Neo4jGraph, GraphCypherQAChain

        graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            database=NEO4J_DATABASE or "neo4j",
            enhanced_schema=True,   # richer schema improves Cypher generation
        )
        graph.refresh_schema()

        _text2cypher_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=True,
            return_intermediate_steps=True,
            allow_dangerous_requests=True,   # use a READ-ONLY Neo4j user in production
        )
    return _text2cypher_chain


def get_answer_for_query_text2cypher_lc(query: str):
    """
    Translate a natural-language question into Cypher using LangChain's
    GraphCypherQAChain, execute it against Neo4j, and return a grounded answer.
    """
    chain = _get_text2cypher_chain()
    result = chain.invoke({"query": query})

    # Surface the generated Cypher for transparency/debugging.
    for step in result.get("intermediate_steps", []):
        if isinstance(step, dict) and "query" in step:
            print("Generated Cypher:\n", step["query"])

    return result["result"]


text2cypher_tool = Tool(
    name="Text2Cypher",
    func=get_answer_for_query_text2cypher_lc,
    description=(
        TEXT2CYPHER_DESCRIPTION
    )
)

# ------------------------------------------------------------------------------------------------- Define Web Search Tool (Tavily) ---------------------------------------------------------------------------------------------------------
# A live web-search tool backed by the Tavily API. The agent should pick this
# tool for questions about the LATEST / RECENT / UPCOMING movies or any
# real-world facts that are newer than the knowledge graph.

# Build the Tavily client once and reuse it.
_tavily_client = None


def _get_tavily_client():
    """Lazily build (and cache) the Tavily client."""
    global _tavily_client
    if _tavily_client is None:
        from tavily import TavilyClient
        _tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    return _tavily_client


def web_search(query: str):
    """
    Search the live web via Tavily for the latest/recent movie information and
    return an LLM-synthesized answer grounded in the search results.
    """
    if not TAVILY_API_KEY:
        return ("Web search is unavailable: TAVILY_API_KEY is not set. "
                "Add it to your .env to enable the Web Search tool.")

    client = _get_tavily_client()
    results = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
        topic="general",
    )

    # Tavily can return a ready-made answer; prefer it, else build context.
    tavily_answer = results.get("answer")
    sources = results.get("results", [])
    context = "\n\n".join(
        f"Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}"
        for r in sources
    )

    if llm is None:
        return tavily_answer or ("Web results:\n\n" + context)

    prompt = (
        "You are answering a question about the LATEST/RECENT movies using the "
        "live web search results below. Give a concise, up-to-date answer and "
        "cite the source titles.\n\n"
        f"Question: {query}\n\n"
        f"Tavily answer (may be empty): {tavily_answer}\n\n"
        f"Search results:\n{context}\n\n"
        "Answer:"
    )
    return getattr(llm.invoke(prompt), "content", "")


web_search_tool = Tool(
    name="WebSearch",
    func=web_search,
    description=(
        WEB_SEARCH_DESCRIPTION
    )
)


# ------------------------------------------------------------------------------------------------- Define Global Search Tool ---------------------------------------------------------------------------------------------------------

def find_relevant_communities(driver, question, embeddings=None, top_k=3):
    """Return the top-k communities most relevant to `question`.

    Uses the vector index when an embedding model is available, otherwise
    falls back to a simple keyword CONTAINS match on the summary/title.
    """
    if embeddings is not None:
        qvec = embeddings.embed_query(question)
        cypher = """
        CALL db.index.vector.queryNodes('community_embedding', $k, $qvec)
        YIELD node, score
        RETURN node.id AS id, node.title AS title, node.summary AS summary, score
        ORDER BY score DESC
        """
        params = {"k": top_k, "qvec": qvec}
    else:
        # Keyword fallback: match any word from the question against summary/title.
        words = [w for w in question.lower().split() if len(w) > 3]
        cypher = """
        MATCH (c:Community)
        WHERE any(w IN $words WHERE toLower(coalesce(c.summary,'') + ' ' + coalesce(c.title,'')) CONTAINS w)
        RETURN c.id AS id, c.title AS title, c.summary AS summary, 0.0 AS score
        LIMIT $k
        """
        params = {"words": words, "k": top_k}

    with driver.session() as s:
        return [r.data() for r in s.run(cypher, **params)]


def movies_in_communities(driver, community_ids, limit_per_community=10):
    """Traverse :IN_COMMUNITY to fetch Movie members for the given communities."""
    cypher = """
    MATCH (c:Community)<-[:IN_COMMUNITY]-(m:Movie)
    WHERE c.id IN $ids
    WITH c, collect(DISTINCT m.title)[0..$lim] AS movies
    RETURN c.id AS community, c.title AS title, movies
    """
    with driver.session() as s:
        return [r.data() for r in s.run(cypher, ids=community_ids, lim=limit_per_community)]


# %pip install --quiet langchain langchainhub langchain-openai
from langchain_core.tools import tool


# --- Helpers backing the tools ----------------------------------------------
def _all_community_summaries(driver, limit=100):
    q = """
    MATCH (c:Community)
    WHERE c.summary IS NOT NULL
    RETURN c.id AS id, c.title AS title, c.summary AS summary, coalesce(c.size, 0) AS size
    ORDER BY size DESC
    LIMIT $limit
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q, limit=limit)]


# --- TOOL 1: GLOBAL SEARCH (theme-level, whole graph) ------------------------
@tool
def global_search_tool(question: str) -> str:
    """Purpose:
        Answer high-level questions requiring understanding of the ENTIRE movie graph.

        Use when:
        - overall trends
        - summaries
        - comparisons across communities
        - dataset-wide insights
        - graph overview
        - themes
        - statistics

        Examples:
        - Summarize this movie graph.
        - What themes dominate?
        - Compare sci-fi and fantasy communities.
        - What genres are most common?

        Never use for:
        - specific movies
        - actors
        - directors
        - recommendations
        - follow-up questions
        - entity lookup
    """
    comms = _all_community_summaries(driver)
    if not comms:
        return "No community summaries found. Run Steps 2–4 first."
    context = "\n".join(
        f"- {c.get('title') or c['id']} ({c['size']} members): {c['summary']}"
        for c in comms
    )
    if llm is None:
        return "🔎 (no LLM) Community summaries:\n\n" + context
    prompt = (
        "You are answering a BROAD question about a movie dataset using the "
        "community summaries below. Synthesize across communities.\n\n"
        f"Question: {question}\n\nCommunity summaries:\n{context}\n\n"
        "Give a concise, thematic answer."
    )
    return getattr(llm.invoke(prompt), "content", "")



# # ------------------------------------------------------------------------------------------------- Define Local Search Tool ---------------------------------------------------------------------------------------------------------
def retrieve_entities(driver, ids):
    cypher="""
    MATCH (c:Community)<-[:IN_COMMUNITY]-(n)
    WHERE c.id IN $ids
    RETURN c.id AS community, collect(DISTINCT coalesce(n.title,n.name)) AS entities
    """
    with driver.session() as s:
        return [r.data() for r in s.run(cypher,ids=ids)]


def retrieve_relationships(driver, ids):
    cypher="""
    MATCH (c:Community)<-[:IN_COMMUNITY]-(a)-[r]-(b)
    WHERE c.id IN $ids
    RETURN c.id AS community,
           collect(DISTINCT {source:coalesce(a.title,a.name),rel:type(r),target:coalesce(b.title,b.name)}) AS relationships
    """
    with driver.session() as s:
        return [r.data() for r in s.run(cypher,ids=ids)]

def retrieve_source_text(driver, ids):
    cypher="""
    MATCH (c:Community)<-[:IN_COMMUNITY]-(m:Movie)
    WHERE c.id IN $ids
    RETURN c.id AS community, collect(DISTINCT m.overview)[0..10] AS text_units
    """
    with driver.session() as s:
        return [r.data() for r in s.run(cypher,ids=ids)]
        

def build_local_context(comms, entities, rels, texts):
    sections=[]
    for c in comms:
        cid=c["id"]
        e=next((x for x in entities if x["community"]==cid),{})
        r=next((x for x in rels if x["community"]==cid),{})
        t=next((x for x in texts if x["community"]==cid),{})
        sections.append(
            f"Community Report\n{c['summary']}\n\nEntities\n{e.get('entities',[])}\n\nRelationships\n{r.get('relationships',[])}\n\nSource Text\n{t.get('text_units',[])}"
        )
    return "\n\n".join(sections)

# --- TOOL 2: LOCAL SEARCH (entity/topic-specific) ---------------------------
@tool
def local_search_tool(question: str) -> str:
    """Purpose:
        Answer questions about SPECIFIC entities.

        Use when the question mentions:
        - movie
        - actor
        - director
        - genre
        - production company
        - keyword
        - franchise
        - language
        - country

        Examples:
        - Movies like Inception
        - Christopher Nolan movies
        - Movies starring Tom Hanks
        - Crime movies from the 1990s

        Never use for:
        - graph summaries
        - trends
        - dataset statistics"""
    comms=find_relevant_communities(driver,question,embedder)
    if not comms:
        return "No relevant communities found. Run Steps 2–4 first."
    ids=[c["id"] for c in comms]
    entities=retrieve_entities(driver,ids)
    rels=retrieve_relationships(driver,ids)
    texts=retrieve_source_text(driver,ids)
    context=build_local_context(comms,entities,rels,texts)
    prompt = (
        "Answer the question using ONLY the community context below.\n\n"
        f"Question: {question}\n\nCommunity context:\n{context}\n\n"
        "Give a concise, grounded answer and mention relevant movies."
    )
    return getattr(llm.invoke(prompt), "content", "")


