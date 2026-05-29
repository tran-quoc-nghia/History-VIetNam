"""
etl/import_data.py - Import dữ liệu từ file Excel vào Neo4j
"""
from neo4j import GraphDatabase
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class ExcelToNeo4jImporter:
    def __init__(self, excel_file='DuLieuLichSu.xlsx'):
        self.excel_file = excel_file
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        
        if self.password == '12345678':
            print("LỖI: Bạn chưa thay đổi mật khẩu trong file .env!")
            exit(1)
            
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    def close(self):
        if self.driver:
            self.driver.close()
            
    def clear_database(self, session):
        session.run("MATCH (n) DETACH DELETE n")
        print("Đã xóa dữ liệu cũ trong Neo4j.")

    def create_indexes(self, session):
        # Đã cập nhật GiaiDoan thành ThoiKy
        labels = ['NhanVat', 'SuKien', 'ToChuc', 'HiepDinh', 'QuocGia', 'ThoiKy']
        for label in labels:
            session.run(f"CREATE INDEX {label.lower()}_id IF NOT EXISTS FOR (n:{label}) ON (n.id)")
        print("Đã tạo Indexes để tối ưu tốc độ.")

    def _read_sheet(self, sheet_name):
        """Đọc sheet Excel, sửa lỗi phông chữ, khoảng trắng và số thập phân"""
        try:
            # Tìm tên sheet không phân biệt hoa thường
            xls = pd.ExcelFile(self.excel_file)
            actual_sheet_name = next((s for s in xls.sheet_names if s.lower() == sheet_name.lower()), None)
            
            if not actual_sheet_name:
                print(f" -> Bỏ qua sheet '{sheet_name}' (Không tìm thấy trong file Excel).")
                return []

            df = pd.read_excel(self.excel_file, sheet_name=actual_sheet_name)
            
            # Xóa khoảng trắng thừa ở header
            df.columns = df.columns.astype(str).str.strip()
            
            # Fix lỗi Pandas tự động đổi số nguyên thành số thập phân nếu cột có ô trống (NaN)
            # Ví dụ: 1945 thành 1945.0
            for col in df.columns:
                if df[col].dtype == 'float64':
                    # Kiểm tra xem cột có chứa toàn bộ số nguyên hay không
                    if df[col].dropna().apply(lambda x: x.is_integer() if isinstance(x, float) else False).all():
                        df[col] = df[col].astype('Int64') # Int64 hỗ trợ NaN

            # Thay thế NaN thành None để Neo4j hiểu là NULL
            df = df.where(pd.notnull(df), None)
            return df.to_dict('records')
            
        except Exception as e:
            print(f"Lỗi đọc sheet {sheet_name}: {e}")
            return []

    def import_nodes(self, session):
        """Import các Node từ Excel"""
        sheets_mapping = {
            'NhanVat': 'NhanVat',
            'SuKien': 'SuKien',
            'ToChuc': 'ToChuc',
            'HiepDinh': 'HiepDinh',
            'QuocGia': 'QuocGia',
            'ThoiKy': 'ThoiKy', # Cập nhật Map ThoiKy
        }
        
        for sheet_name, label in sheets_mapping.items():
            records = self._read_sheet(sheet_name)
            if not records:
                continue
                
            query = f"""
            UNWIND $records AS record
            CREATE (n:{label})
            SET n = record
            """
            session.run(query, {"records": records})
            print(f" - Đã import {len(records)} node {label}")

    def import_relationships(self, session):
        """Import Relationships từ sheet Relationships"""
        # Tìm sheet "relationships" bất kể hoa hay thường
        relationships = self._read_sheet('relationships')
        
        if not relationships:
            print("Không có dữ liệu relationships.")
            return

        success_count = 0
        for rel in relationships:
            source_id = rel.get('source_id')
            source_label = rel.get('source_label')
            target_id = rel.get('target_id')
            target_label = rel.get('target_label')
            relation_type = rel.get('relation')

            if not all([source_id, source_label, target_id, target_label, relation_type]):
                continue

            # Sử dụng toString() để tránh lỗi lệch kiểu (int vs float vs string)
            query = f"""
            MATCH (source:{source_label}) WHERE toString(source.id) = toString($source_id)
            MATCH (target:{target_label}) WHERE toString(target.id) = toString($target_id)
            MERGE (source)-[:`{relation_type}`]->(target)
            """
            session.run(query, {"source_id": str(source_id).strip(), "target_id": str(target_id).strip()})
            success_count += 1
            
        print(f" - Đã import {success_count} relationships.")

    def run(self):
        if not os.path.exists(self.excel_file):
            print(f"LỖI: Không tìm thấy file {self.excel_file}. Vui lòng đặt file đúng vị trí.")
            return

        print("=" * 60)
        print("BẮT ĐẦU IMPORT DỮ LIỆU TỪ EXCEL VÀO NEO4J")
        print("=" * 60)
        
        with self.driver.session() as session:
            self.clear_database(session)
            self.create_indexes(session)
            
            print("\n[1/2] Đang tạo Nodes...")
            self.import_nodes(session)
            
            print("\n[2/2] Đang thiết lập Relationships...")
            self.import_relationships(session)
            
        print("\n🎉 HOÀN TẤT IMPORT DỮ LIỆU!")

if __name__ == "__main__":
    # Đảm bảo đường dẫn file Excel trỏ đúng chỗ
    importer = ExcelToNeo4jImporter('DuLieuLichSu.xlsx')
    try:
        importer.run()
    finally:
        importer.close()