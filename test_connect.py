from werkzeug.security import generate_password_hash
from app.services.neo4j_service import Neo4jService

neo4j_service = Neo4jService()
admin_name = "Admin Lịch Sử"
admin_email = "quocnghia2004nt@gmail.com" # Đây là email dùng để đăng nhập và nhận link reset
admin_password = "123456" # Mật khẩu bạn muốn đặt

# Băm mật khẩu
hashed_password = generate_password_hash(admin_password)

with neo4j_service.driver.session() as session:
    session.run("""
        MERGE (a:Admin {email: $email})
        SET a.name = $name, a.password = $password
    """, {"email": admin_email, "name": admin_name, "password": hashed_password})

print("Đã tạo tài khoản Admin thành công!")