from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from langchain_groq import ChatGroq
from langchain_experimental.chat_models import Llama2Chat
from langchain.chains import GraphCypherQAChain
from langchain.prompts import PromptTemplate

# Import credentials from your config file
from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, GROQ_API_KEY

class GraphQueryEngine:
    def __init__(self):
        # Initialize the Neo4j graph instance
        self.graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD
        )
        
        # Refresh the schema to ensure the LLM has the latest graph structure
        self.graph.refresh_schema()

        # The custom prompt to guide the LLM's query generation.
        CYPHER_GENERATION_TEMPLATE = """
        You are an expert Cypher translator from English to Cypher.
        You MUST adhere to the following schema and rules with extreme precision.

        Schema:
        - Node Labels: "Drug", "Condition", "SideEffect", "DrugClass", "Brand"
        - Relationship Types: "TREATS", "CAUSES_SIDE_EFFECT", "BELONGS_TO_CLASS", "MARKETED_AS"

        Strict Rules for String Matching:
        - DO NOT use the 'name' property for string matching.
        - INSTEAD, for all string matching on node labels, you MUST use the property 'ci_name'.
        - The 'ci_name' property contains the lowercase version of the original name.
        - Your query MUST use the `toLower()` function on the user's input for every comparison.
        
        Example:
        - To find a condition related to "acne", the ONLY correct query format is:
          `MATCH (c:Condition) WHERE c.ci_name = toLower("acne")`

        The question is:
        {question}
        """

        # Initialize the LLM (Large Language Model)
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama2-70b-4096"
        )
        
        # Create the LangChain GraphCypherQAChain with the custom prompt
        self.chain = GraphCypherQAChain.from_llm(
            cypher_llm=self.llm,
            qa_llm=self.llm,
            graph=self.graph,
            verbose=True,
            cypher_generation_chain_prompt=PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE),
            allow_dangerous_requests=True
        )

    def query(self, question: str) -> str:
        """Runs a natural language question against the graph query chain."""
        return self.chain.invoke({"query": question})["result"]

if __name__ == "__main__":
    try:
        engine = GraphQueryEngine()
        user_query = "What drugs are marketed as Ziana?"
        print(f"User Query: {user_query}")
        response = engine.query(user_query)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
