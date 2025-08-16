
import streamlit as st
import os
from langchain.prompts.prompt import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

NEO4J_USERNAME= 'neo4j'
NEO4J_URI = "uri"
NEO4J_PASSWORD = "password"
groq_api_key   = "groqapikey"

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def setup_neo4j_indexes():
    """
    Creates the vector and full-text search indexes in Neo4j.
    """
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        with driver.session() as session:
            # Create Vector Index for semantic search (Drug nodes)
            vector_index_query_drug = """
            CREATE VECTOR INDEX drug_embedding_index IF NOT EXISTS
            FOR (n:Drug) ON (n.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
              }
            }
            """
            session.run(vector_index_query_drug)

            # Create Vector Index for Condition nodes
            vector_index_query_condition = """
            CREATE VECTOR INDEX condition_embedding_index IF NOT EXISTS
            FOR (n:Condition) ON (n.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
              }
            }
            """
            session.run(vector_index_query_condition)

            # Corrected Full-Text Search Index (without OPTIONS block)
            fts_index_query = """
            CREATE FULLTEXT INDEX node_names_fts IF NOT EXISTS
            FOR (n:Condition|Drug) ON EACH [n.ci_name]
            """
            session.run(fts_index_query)

            print("Neo4j indexes created successfully.")



def generate_and_store_embeddings():
    """
    Generates embeddings for 'ci_name' property and stores them in 'embedding' property.
    """
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        labels_to_embed = ["Condition", "Drug"]
        for label in labels_to_embed:
            query_get_names = f"MATCH (n:{label}) RETURN n.ci_name AS name"
            result = driver.session().run(query_get_names)
            names = [record["name"] for record in result if record["name"] is not None]
            
            if names:
                embeddings = embedding_model.encode(names, convert_to_tensor=False)
                with driver.session() as session:
                    for i, name in enumerate(names):
                        embedding = embeddings[i].tolist()
                        query_update_node = f"""
                        MATCH (n:{label} {{ci_name: $name}})
                        SET n.embedding = $embedding
                        """
                        session.run(query_update_node, name=name, embedding=embedding)
                print(f"Embeddings stored for all '{label}' nodes.")



@st.cache_resource
def get_llm_and_chain():
  setup_neo4j_indexes()
  generate_and_store_embeddings()

  CYPHER_GENERATION_TEMPLATE = """You are a Cypher expert for a graph database with vector and full-text search capabilities. Your task is to generate a Cypher query based on a user's question.

Schema:
- Node Labels: "Drug", "Condition", "SideEffect", "DrugClass", "Brand"
- The property 'ci_name' is used for case-insensitive matching.

Strict Rules for Search:
- For specific, short keywords or potential typos (like 'cold' for 'colds & flu'), you MUST use the full-text search index named 'node_names_fts'.
- For broader, semantic concepts, you may use the vector search index 'node_names'.

Example Full-Text Search Query:
// The system will now correctly find 'Colds & Flu' when you search for 'cold'.
CALL db.index.fulltext.queryNodes('node_names_fts', 'cold')
YIELD node AS matched_condition, score
// Then use the matched_condition in the main query
MATCH (d:Drug)-[:TREATS]->(matched_condition)
RETURN d.name

The user's question is:
{question}"""
  CYPHER_PROMPT = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)
  llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile")
  graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)

  chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        cypher_generation_chain_prompt=CYPHER_PROMPT,
        allow_dangerous_requests=True
    )
  return chain

chain = get_llm_and_chain()
import streamlit as st

st.title("💊 Drug Graph RAG Assistant")
st.write("Ask a question about drugs, conditions, and side effects.")

# Input field
query = st.text_input("Your question:", key="user_input")

# Search button
if st.button("Search"):
    if query.strip():
        with st.spinner("Thinking..."):
            response = chain.invoke({"query": query})
            st.session_state.response = response
    else:
        st.warning("Please enter a question.")

# Show response
if "response" in st.session_state and st.session_state.response:
    st.markdown("---")
    st.subheader("Answer:")
    st.write(st.session_state.response["result"])


 
