import pandas as pd
from graph_builder import GraphBuilder
from embeddings_utils import generate_and_store_embeddings

def main():
    """
    Main function to set up the graph database from scratch.
    """
    print("Step 1: Building the Neo4j graph from the data source.")
    graph_builder = GraphBuilder()
    try:
        graph_builder.build_graph()

        print("\nStep 2: Generating and storing embeddings.")
        generate_and_store_embeddings()

        print("\nDatabase setup is complete. You can now run the Streamlit app.")

    finally:
        graph_builder.close()

if __name__ == "__main__":
    main()
