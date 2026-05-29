import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from app.services.neo4j_service import Neo4jService
from app import create_app

# Load các biến môi trường từ file .env
load_dotenv()

def init_default_admin():
    """Hàm tự động tạo Admin nếu database chưa có tài khoản nào"""
    neo4j_service = Neo4jService()
    try:
        with neo4j_service.driver.session() as session:
            # Kiểm tra số lượng Admin hiện có
            result = session.run("MATCH (a:Admin) RETURN count(a) as total").single()
            
            # Nếu hệ thống trống (total == 0), tiến hành tạo tài khoản mới
            if result and result["total"] == 0:
                print("[*] Database chưa có Admin. Đang khởi tạo tài khoản mặc định...")
                
                # Lấy dữ liệu từ .env
                name = os.getenv("DEFAULT_ADMIN_NAME", "Admin Lịch Sử")
                email = os.getenv("DEFAULT_ADMIN_EMAIL", "quocnghia2004nt@gmail.com")
                password = os.getenv("DEFAULT_ADMIN_PASSWORD", "123456")
                
                # Băm (hash) mật khẩu
                hashed_password = generate_password_hash(password)
                
                # Lưu vào Neo4j
                session.run("""
                    CREATE (a:Admin {
                        name: $name,
                        email: $email,
                        password: $password
                    })
                """, {"name": name, "email": email, "password": hashed_password})
                
                print(f"[+] Đã tạo thành công Admin với email: {email}")
            else:
                print(f"[*] Hệ thống đã có sẵn {result['total']} tài khoản Admin. Bỏ qua bước khởi tạo.")
    except Exception as e:
        print(f"[!] Lỗi khi kiểm tra/tạo Admin mặc định: {e}")

app = create_app()

if __name__ == '__main__':
    # Gọi hàm tạo tài khoản mặc định trước khi server bắt đầu lắng nghe request
    init_default_admin()
    
    app.run(debug=True, host='0.0.0.0', port=5000)