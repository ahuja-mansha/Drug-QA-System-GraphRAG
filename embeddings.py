from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_and_store_embeddings():
    """
    Generates embeddings for 'ci_name' property and stores them in 'embedding' property.
    """
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
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
