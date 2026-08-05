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

HYBRID_DESCRIPTION = """
Purpose:
Generic semantic fallback retrieval.

Use ONLY when every other tool is unsuitable.

Never choose this tool if another tool clearly matches.
"""


# -------------------------------------------------------------------------------------------------- Define Hybrid Retrieval Tool -----------------------------------------------------------------------------------------------------------
def get_rag_for_query_hybrid(query: str):
    """
    Wrapper to generate a Rag object dynamically for each query
    """
    hybrid_retriever = HybridRetriever(
        driver=driver,
        vector_index_name="movie_embedding_index",
        fulltext_index_name="movie_text_index",
        embedder=embedder,
    )

    custom_template = RagTemplate(template=rag_prompt,
                                  expected_inputs=["context", "query_text"],
                                  )

    rag_obj = GraphRAG(retriever=hybrid_retriever, llm=llm, prompt_template=custom_template)

    response = rag_obj.search(
        query,
    )
    return response.answer


hybrid_tool = Tool(
    name="Hybrid",
    func=get_rag_for_query_hybrid,
    description=(
        HYBRID_DESCRIPTION
    )
)


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
    comms = find_relevant_communities(driver, question, embeddings=embedder, top_k=3)
    if not comms:
        return "No relevant communities found. Run Steps 2–4 first."
    ids = [c["id"] for c in comms]
    movie_rows = movies_in_communities(driver, ids)
    context_lines = []
    for c in comms:
        movies = next((m["movies"] for m in movie_rows if m["community"] == c["id"]), [])
        context_lines.append(
            f"- {c.get('title') or c['id']}: {c['summary']}\n"
            f"  Movies: {', '.join(movies) if movies else '(none)'}"
        )
    context = "\n".join(context_lines)
    if llm is None:
        return "🔎 (no LLM) Retrieved context:\n\n" + context
    prompt = (
        "Answer the question using ONLY the community context below.\n\n"
        f"Question: {question}\n\nCommunity context:\n{context}\n\n"
        "Give a concise, grounded answer and mention relevant movies."
    )
    return getattr(llm.invoke(prompt), "content", "")


