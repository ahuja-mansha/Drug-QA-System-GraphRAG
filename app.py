import streamlit as st
from langchain.prompts.prompt import PromptTemplate
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_groq import ChatGroq
from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, GROQ_API_KEY

# Set up the Neo4j graph and the LLM chain once using Streamlit's cache
@st.cache_resource
def get_llm_and_chain():
    # Define a custom prompt template
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

    # Initialize the LLM
    llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.3-70b-versatile")
    
    # Initialize the Neo4j graph connector
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)

    # Create the GraphCypherQAChain
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        cypher_generation_chain_prompt=CYPHER_PROMPT,
        allow_dangerous_requests=True
    )
    return chain

st.title("💊 Drug Graph RAG Assistant")
st.write("Ask a question about drugs, conditions, and side effects.")

chain = get_llm_and_chain()

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
