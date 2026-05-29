import os
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

class Config:
    """Lớp cấu hình"""
    # Neo4j configuration
    NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j+s://d1e2d8a7.databases.neo4j.io')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'UDxy-hB0WZq51UXnVNRRf9hLqRYIE4XdVY7NmF6zRGA')
    NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'd5fd4540')
    SECRET_KEY = os.getenv('SECRET_KEY', '5621190cd9d10bc4978e9e779fc50c8219a3a4e6293cdbc5dd6598e9c3ff764b')

    @staticmethod
    def validate():
        """Kiểm tra cấu hình trước khi kết nối"""
        required_vars = [Config.NEO4J_URI, Config.NEO4J_USER, Config.NEO4J_PASSWORD]
        if not all(required_vars):
            print("CẢNH BÁO: Thiếu thông tin kết nối Neo4j trong file .env")
            return False
        print(f"Kết nối đến: {Config.NEO4J_URI}")
        print(f"Database: {Config.NEO4J_DATABASE}")
        return True