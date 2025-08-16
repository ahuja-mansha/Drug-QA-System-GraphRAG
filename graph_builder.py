import pandas as pd
from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class GraphBuilder:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def create_indexes(self):
        """Creates indexes for a faster traversal of the graph."""
        with self.driver.session() as session:
            print("Creating indexes...")
            session.run("CREATE OR REPLACE INDEX FOR (d:Drug) ON (d.name)")
            session.run("CREATE OR REPLACE INDEX FOR (c:Condition) ON (c.name)")
            session.run("CREATE OR REPLACE INDEX FOR (se:SideEffect) ON (se.name)")
            session.run("CREATE OR REPLACE INDEX FOR (dc:DrugClass) ON (dc.name)")
            session.run("CREATE OR REPLACE INDEX FOR (br:Brand) ON (br.name)")
            print("Indexes created!")

    def build_graph(self, csv_path: str = None):
        """Builds the Neo4j graph from the specified CSV data source and creates indexes."""
        with self.driver.session() as session:
            print("Building graph... This may take a few minutes.")
            
            # The Cypher query provided by the user
            cypher_query = '''
            LOAD CSV WITH HEADERS FROM 'https://datasetpath' AS row
            
            WITH row,
              replace(trim(row.drug_name), '\"', '') AS drug_name,
              replace(trim(row.generic_name), '\"', '') AS generic_name,
              replace(trim(row.rx_otc), '\"', '') AS rx_or_otc,
              replace(trim(row.rating), '\"', '') AS rating_raw,
              replace(trim(row.no_of_reviews), '\"', '') AS no_of_reviews_raw,
              replace(trim(row.medical_condition), '\"', '') AS condition_raw,
              replace(trim(row.side_effects), '\"', '') AS side_effects_raw,
              replace(trim(row.drug_classes), '\"', '') AS drug_classes_raw,
              replace(trim(row.brand_names), '\"', '') AS brand_names_raw
            
            WHERE drug_name IS NOT NULL AND drug_name <> ""
            
            MERGE (d:Drug {name: drug_name})
            SET d.generic_name = generic_name,
              d.rx_or_otc = rx_or_otc,
              d.rating = CASE WHEN rating_raw <> "" THEN toFloat(rating_raw) ELSE NULL END,
              d.num_reviews = CASE WHEN no_of_reviews_raw <> "" THEN toInteger(no_of_reviews_raw) ELSE NULL END,
              d.condition_description = condition_raw
            
            WITH d, condition_raw, side_effects_raw, drug_classes_raw, brand_names_raw,
              CASE
                WHEN condition_raw <> "" AND condition_raw CONTAINS "Other names:"
                THEN trim(split(condition_raw, "Other names:")[0])
                ELSE condition_raw
              END AS conditionName
            
            WHERE conditionName IS NOT NULL AND conditionName <> ""
            MERGE (c:Condition {name: conditionName})
            MERGE (d)-[:TREATS]->(c)
            
            WITH d, side_effects_raw, drug_classes_raw, brand_names_raw
            
            FOREACH (effect IN [x IN split(side_effects_raw, ';') WHERE x IS NOT NULL AND trim(x) <> ""] |
              MERGE (se:SideEffect {name: trim(effect)})
              MERGE (d)-[:HAS_SIDE_EFFECT]->(se)
            )
            
            WITH d, drug_classes_raw, brand_names_raw
            
            FOREACH (classItem IN [x IN split(drug_classes_raw, ',') WHERE x IS NOT NULL AND trim(x) <> ""] |
              MERGE (dc:DrugClass {name: trim(classItem)})
              MERGE (d)-[:BELONGS_TO_CLASS]->(dc)
            )
            
            WITH d, brand_names_raw
            
            FOREACH (brand IN [x IN split(brand_names_raw, ',') WHERE x IS NOT NULL AND trim(x) <> ""] |
              MERGE (br:Brand {name: trim(brand)})
              MERGE (d)-[:MARKETED_AS]->(br)
            )
            '''
            session.run(cypher_query)
            print("Graph building complete!")
            self.create_indexes()
