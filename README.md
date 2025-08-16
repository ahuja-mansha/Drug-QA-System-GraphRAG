# Drug-QA-System-using-GraphRAG
# 💊 Drug Knowledge Graph RAG (Graph Retrieval-Augmented Generation)

## Project Overview
This project implements a **Graph Retrieval-Augmented Generation (GraphRAG)** system for drug-related knowledge.  
We build a **Neo4j-based Knowledge Graph** from structured drug data and integrate it with a **Large Language Model (LLM)** to enable natural language Q&A.  

The system uses a **hybrid retrieval strategy**:
- **Full-text search** for keyword-based matching  
- **Vector similarity search** for semantic retrieval using embeddings  
- **Cypher queries** for structured graph reasoning  
- **LLM synthesis** for generating natural language answers grounded in graph knowledge  

---

## ✨ Key Features
- **GraphRAG Pipeline**: Natural language → Retrieval (keyword + semantic + Cypher) → Graph results → LLM-generated answer.  
- **Knowledge Graph Construction**: Drugs, conditions, and side effects represented as nodes and relationships.  
- **Hybrid Retrieval**: Combines **symbolic graph search** with **semantic search**.  
- **LLM-Powered Queries (LangChain + Groq)**: Natural language interface for medical Q&A.  
- **Interactive Exploration**: Supports queries like:
  - “What are the side effects of Aspirin?”  
  - “Which other medicines that belong to the same drug class as Carboxine treat Hayfever?”  
  - "What are the side effects of drug having generic name as ibuprofen?"”  

---

## Dataset
The dataset [`drugs_escaped.csv`](./drugs_escaped.csv) contains structured information about drugs and their effects.  

**Main columns:**
- `drug` → Drug name (e.g., Aspirin, Metformin)  
- `condition` → Condition treated (e.g., Diabetes, Hypertension)  
- `side_effect` → Known side effects (e.g., Nausea, Headache)  

This dataset is transformed into a **graph schema** with nodes and relationships for GraphRAG.  

---

## Knowledge Graph Schema
The Neo4j graph consists of:  

- **Nodes**:    
  - Drug {name: STRING, generic_name: STRING, rx_or_otc: STRING, condition_description: STRING, rating: FLOAT, num_reviews: INTEGER}
  - Condition {name: STRING}
  - SideEffect {name: STRING}
  - DrugClass {name: STRING}
  - Brand {name: STRING}

- **Relationships**:
  - (:Drug)-[:TREATS]->(:Condition)
  - (:Drug)-[:HAS_SIDE_EFFECT]->(:SideEffect)
  - (:Drug)-[:BELONGS_TO_CLASS]->(:DrugClass)
  - (:Drug)-[:MARKETED_AS]->(:Brand)`  

This graph is the **retrieval layer** for the RAG pipeline.  

---

## Retrieval Modes
The project combines **multiple retrieval strategies**:

1. **Full-Text Search (Neo4j)**  
   - Supports keyword lookups over drugs, conditions, and side effects.  
   - Example:  
     ```cypher
     CALL db.index.fulltext.queryNodes("drugIndex", "aspirin") YIELD node, score
     RETURN node.name, score
     ```

2. **Vector Similarity Search**  
   - Uses `sentence-transformers` (`all-MiniLM-L6-v2`) to embed text.  
   - Embeddings stored in Neo4j vector index.  
   - Supports semantic search 

3. **Cypher Queries (Structured Search)**  
   - Leverages graph structure to reason about relationships.  
   - Example:  
     ```cypher
     MATCH (d:Drug)-[:TREATS]->(c:Condition {name: "Hypertension"}) 
     MATCH (d)-[:CAUSES]->(s:SideEffect) 
     RETURN d.name, collect(s.name)
     ```

4. **LLM Synthesis (GraphRAG)**  
   - LangChain + Groq LLM converts **user questions → Cypher/semantic search → natural language answers**.  

---

### 1. Clone Repository
```bash
git clone https://github.com/ahuja-mansha/Drug-QA-System-GraphRAG.git
cd Drug-QA-System-GraphRAG


