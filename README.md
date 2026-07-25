# When Agents Meet Graphs: The Rise of Knowledge-Driven GenAI
Beyond Agentic RAG into the next frontier of GenAI: Graph-Powered, Knowledge-Driven systems

## Workshop Briefing
Retrieval-Augmented Generation has rapidly evolved from basic RAG pipelines to sophisticated agentic workflows. Yet, as GenAI systems are applied to real-world problems, a critical limitation becomes clear: flat retrieval and isolated agents struggle to reason over interconnected, contextual, and evolving data.

This full-day workshop takes participants beyond Agentic RAG into the next frontier of GenAI: graph-powered, knowledge-driven systems. Designed for intermediate GenAI practitioners, the workshop explores how graphs fundamentally transform retrieval, reasoning, and orchestration. Participants will learn how to move from document-centric pipelines to relationship-aware AI systems, where entities, connections, hierarchies, and context become first-class citizens.

The session covers how graphs enhance agentic reasoning, enable multi-hop and contextual retrieval, and unlock deeper intelligence across complex data landscapes. Through architecture patterns, real-world problem scenarios, and hands-on design approaches, participants will learn how to build knowledge graphs, design graph-based retrievers, and implement Agentic Graph RAG architectures that scale beyond traditional approaches.

By the end of the workshop, participants will be able to design GenAI systems that do not just retrieve information, but reason over knowledge, connect data meaningfully, and solve complex real-world problems with greater accuracy, explainability, and impact.

**Level**: Intermediate 
## What Participants Will Learn
• Why traditional RAG and Agentic RAG struggle in complex, real-world scenarios

• The role of graphs in improving retrieval, reasoning, and contextual grounding

• Core concepts of knowledge graphs and different types of graphs

• How to design and construct a knowledge graph from structured and unstructured data

• Techniques to create meaningful interconnections across diverse data sources

• Graph-based retrieval techniques and multi-hop reasoning patterns

• How agents reason over graphs to enable richer decision-making

• Designing and implementing Agentic Graph RAG architectures

• Solving real-world GenAI problems using graph-powered systems

## Tools and Technologies
Python, Google Colab, Neo4j, ChromaDB, LangChain, LangGraph, OpenAI, Tavily, and more
**Workshop Prerequisites Deck** - https://docs.google.com/presentation/d/14VZATDNBd78u6SC14LK8YCYYkNIIxOWJ/edit?usp=drive_link&ouid=114583280908361346744&rtpof=true&sd=true

### Conceptual Pre Requisites
• Understanding of RAG | • Python is required


## Workshop Modules 
**Agentic KAG Workshop Overview Deck** - https://docs.google.com/presentation/d/1R21n8hFQU9LtM0Gb5y9ddyac2PM2Gsw6/edit?usp=drive_link&ouid=114583280908361346744&rtpof=true&sd=true

### Module 0 – Capstone, Setup, RAG Pain Points & Why Graphs 
Frame the capstone: by end of day, participants demo a graph‑powered, Agentic GenAI assistant for a real-world domain.
Use this capstone to motivate: why traditional RAG and even Agentic RAG struggle on complex, real‑world questions, and how graphs improve retrieval, reasoning, and grounding.
Set up environment (Neo4j, Python, LLM, embeddings) 

### Module 1 – Knowledge Graph Foundations 
Introduce core concepts of knowledge graphs and graph types (domain graph, lexical graph, parent‑child / community graphs).

### Module 2 – Knowledge Graph Construction with SimpleKGBuilder 
Walk through the SimpleKGBuilder package: configuration of schema (node_types, relationship_types), plugging in LLM and embeddings, and pipeline options.
Demonstrate end‑to‑end flow: raw documents → preprocessing/splitting → entity & relationship extraction → generation of domain and lexical nodes/edges → automatic schema → Entity Resolution →  graph creation in Neo4j.
Hands‑on: participants adapt the SimpleKGBuilder config to their own domain schema and run it on a small document set.

### Module 3 – Graph Based Retrieval Types & Querying the Built KG 
Describe and demo different retrieval modes over the newly built graph: GraphRAG - Cypher + graph traversal and Hybrid (vector + full-text search)

### Module 4 – Graph Analytics with GDS 
Run basic graph analytics (e.g community detection) on the constructed KG using graph data science libraries 
Show how these analytics can refine retrieval (e.g. use communities for global context)

### Module 5 – Evaluation & Comparison: Traditional RAG vs Agentic RAG vs GraphRAG vs Agentic KAG
Use a small query set to qualitatively/quantitatively compare them on relevance, correctness, completeness, and faithfulness; discuss where graph‑ and agent‑enhanced approaches clearly outperform basic RAG.

### Module 6 – A Grand Capstone Project - Personalised Movie Recommendation AI Engine  
Participants will bring all the concepts together and build a highly personalised movie recommendation engine using living knowledge graphs + Agentic KAG on Movie Intelligence & Web Search. 
