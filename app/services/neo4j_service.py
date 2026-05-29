# app/services/neo4j_service.py
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jService:
    def __init__(self):
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        # Kiểm tra kết nối
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30,
                max_connection_pool_size=10,
                connection_acquisition_timeout=60
            )
            # Kiểm tra kết nối
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Kết nối Neo4j thành công!")
        except Exception as e:
            print(f"❌ Lỗi kết nối Neo4j: {e}")
            self.driver = None
    
    def get_driver(self):
        return self.driver
    
    def close(self):
        if self.driver:
            self.driver.close()