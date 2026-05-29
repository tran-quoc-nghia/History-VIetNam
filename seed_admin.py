from werkzeug.security import generate_password_hash
from app.services.neo4j_service import Neo4jService
import uuid

def create_admin_account():
    # Khởi tạo kết nối đến CSDL Neo4j
    neo4j_service = Neo4jService()
    
    # Thông tin tài khoản bạn yêu cầu
    email = "quocnghia2004nt@gmail.com"
    raw_password = "123456" 
    
    # Bắt buộc mã hóa mật khẩu theo thư viện của hệ thống
    hashed_password = generate_password_hash(raw_password)
    
    # Câu lệnh Cypher dùng MERGE để tránh tạo trùng lặp
    query = """
    MERGE (a:Account {email: $email})
    ON CREATE SET 
        a.id = $id,
        a.name = 'Trần Quốc Nghĩa',
        a.password = $hashed_password,
        a.role = 'admin',
        a.created_at = datetime()
    ON MATCH SET 
        a.role = 'admin',
        a.password = $hashed_password
    RETURN a
    """
    
    try:
        with neo4j_service.driver.session() as db_session:
            result = db_session.run(query, {
                "id": f"acc_{uuid.uuid4().hex[:8]}",
                "email": email,
                "hashed_password": hashed_password
            })
            
            if result.single():
                print("Tài khoản quản trị (Admin) đã được tạo thành công!")
                print("-------------------------------------------------")
                print(f"Email đăng nhập : {email}")
                print(f"Mật khẩu        : {raw_password}")
                print("Vai trò         : admin")
                print("-------------------------------------------------")
            else:
                print("Có lỗi xảy ra, không thể tạo tài khoản.")
    except Exception as e:
        print(f"Lỗi thao tác với Database Neo4j: {e}")

if __name__ == "__main__":
    create_admin_account()