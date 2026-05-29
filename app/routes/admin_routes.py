from datetime import datetime
import os
import uuid
import re
from flask import Blueprint, current_app, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from app.services.neo4j_service import Neo4jService
import io
import pandas as pd
from flask import send_file
from openpyxl.styles import Alignment, Font
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from app import mail
import random


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
neo4j_service = Neo4jService()

RELATIONSHIP_TRANSLATIONS = {
    # Nhóm Nhân vật - Sự kiện
    'CHI_HUY': 'Chỉ huy', 
    'CHI_DAO': 'Chỉ đạo', 
    'TRUC_TIEP_CHI_DAO': 'Trực tiếp chỉ đạo',
    'THAM_GIA': 'Tham gia', 
    'THAM_GIA_CHIEN_DAU': 'Tham gia chiến đấu',
    'KHOI_XUONG': 'Khởi xướng',
    'CHU_TRI': 'Chủ trì',
    'DOI_DAU': 'Đối đầu',
    'CHI_HUY_PHONG_THU': 'Chỉ huy phòng thủ',
    'DOC_TUYEN_NGON': 'Đọc bản Tuyên ngôn',

    # Nhóm Nhân vật - Tổ chức
    'THUOC_VE': 'Thành viên', 
    'LANH_DAO': 'Lãnh đạo', 
    'SANG_LAP': 'Sáng lập',

    # Nhóm Nhân vật - Quốc gia
    'DAI_DIEN_CHO': 'Đại diện cho', 
    'DUNG_DAU': 'Đứng đầu', 

    # Nhóm Tổ chức - Sự kiện / Quốc gia / Tổ chức khác
    'THAM_GIA_SU_KIEN': 'Tham gia sự kiện', 
    'TO_CHUC': 'Tổ chức',
    'LUC_LUONG_CHINH': 'Lực lượng nòng cốt',
    'LUC_LUONG_XAM_LUOC': 'Lực lượng xâm lược',
    'THUOC_QUOC_GIA': 'Thuộc quốc gia',
    'TRUC_THUOC': 'Trực thuộc',
    'HO_TRO': 'Hỗ trợ', 
    'HOAT_DONG_TAI': 'Hoạt động tại',
    'TIEN_THAN_CUA': 'Tiền thân của',

    # Nhóm Hiệp định - Các thực thể
    'KY_KET': 'Ký kết', 
    'DAM_PHAN': 'Đàm phán', 
    'THAM_GIA_KY': 'Tham gia ký kết', 

    # Nhóm Sự kiện - Sự kiện / Quốc gia
    'KET_THUC_SU_KIEN': 'Kết thúc sự kiện',
    'TIEN_DE_CHO': 'Tiền đề cho',
    'BUOC_NGOAT_DAN_DEN': 'Bước ngoặt dẫn đến',
    'KET_QUA_CUA': 'Kết quả của',
    'KHAI_SINH_RA': 'Khai sinh ra',
    'BAO_VE_DOC_LAP': 'Bảo vệ độc lập',
    'CHU_DONG_TIEN_CONG': 'Chủ động tiến công',
    'QUYET_CHIEN_LUOC': 'Quyết chiến chiến lược',
    'XAM_LUOC': 'Xâm lược',

    # Nhóm gắn kết với Thời Kỳ (Period)
    'THUOC_THOI_KY': 'Thuộc thời kỳ', 
    'MO_DAU_GIAI_DOAN': 'Mở đầu giai đoạn',
    'KET_THUC_GIAI_DOAN': 'Kết thúc giai đoạn',
    'CAN_THIEP_VAO': 'Can thiệp vào',
    'TON_TAI_TRONG': 'Tồn tại trong',
    'CAN_THIEP_TRONG': 'Can thiệp trong',
    'DO_HO_TRONG': 'Đô hộ trong',
    'XAM_LUOC_TRONG': 'Xâm lược trong',
    'HO_TRO_TRONG': 'Hỗ trợ trong',

    # Nhóm Nhân vật - Nhân vật 
    'LANH_DAO_CAP_TREN': 'Lãnh đạo / Cấp trên',
    'LANH_DAO_CAP_DUOI': 'Cấp dưới',
    'LANH_DAO_CAP_TREN_THAY_TRO': 'Thầy trò',
    'THAM_MUU_TRUONG_DUOI_QUYEN': 'Tham mưu trưởng',
    'CHI_HUY_CHIEN_SI': 'Chiến sĩ',
    'DONG_CHI': 'Đồng chí',
    'LANH_DAO_DONG_CHI': 'Lãnh đạo / Đồng chí',
    'DONG_CHI_COT_CAN': 'Đồng chí cốt cán',
    'DONG_CHI_CHI_HUY': 'Đồng chí / Chỉ huy',
    'DONG_CHI_CAP_DUOI': 'Đồng chí cấp dưới',
    'HOC_TRO_CONG_SU': 'Cộng sự / Học trò',
    'HOC_TRO_CU': 'Học trò cũ',
    'LANH_DAO_DONG_MINH': 'Đồng minh',
    'TIEN_BOI_CACH_MANG': 'Tiền bối cách mạng',
    'KE_NHIEM': 'Kế nhiệm',
    'CHUYEN_GIAO_QUYEN_LUC': 'Chuyển giao quyền lực',
    'PHO_TONG_THONG': 'Phó tổng thống',
    'DOI_DAU_BAT_SONG': 'Bắt sống',
    'DOI_LAP': 'Đối lập',
    'DOI_THU_CHINH_TRI': 'Đối thủ chính trị',
    'DOI_THU_DAM_PHAN': 'Đối thủ đàm phán',
    'LAT_DO': 'Lật đổ',
    'BI_LAT_DO': 'Bị lật đổ',
    'DONG_MINH_LAT_DO': 'Đồng minh lật đổ',
    'CHONG_DOI_CAP_TREN': 'Chống đối cấp trên',
    'LANH_DAO_BI_CHONG_DOI': 'Bị chống đối',
    'PHE_TRUAT': 'Phế truất',
    'BI_PHE_TRUAT': 'Bị phế truất',

    # NHÓM SỰ KIỆN - SỰ KIỆN 
    'TIEN_DE_CHO': 'Tiền đề cho',
    'BUOC_NGOAT_DAN_DEN': 'Bước ngoặt dẫn đến',
    'KET_QUA_CUA': 'Kết quả của',
    'NAM_TRONG': 'Nằm trong',
    'DIEN_BIEN_CUA': 'Diễn biến của',
    'KET_THUC_SU_KIEN': 'Kết thúc sự kiện',
    'KHOI_XUONG': 'Khởi xướng',
}

@admin_bp.context_processor
def inject_label_mapping():
    return dict(
        label_mapping={
            'NhanVat': 'Nhân vật',
            'SuKien': 'Sự kiện',
            'ToChuc': 'Tổ chức',
            'HiepDinh': 'Hiệp định',
            'QuocGia': 'Quốc gia',
            'ThoiKy': 'Thời kỳ',
            'Relationships': 'Mối quan hệ'
        },
    rel_mapping=RELATIONSHIP_TRANSLATIONS
    )

def format_vn_date(date_val):
    if not date_val or str(date_val).lower() in ['none', 'null', '']:
        return "?"
    
    date_str = str(date_val).strip()
    
    # Giữ nguyên nếu chỉ có 4 số (năm)
    if len(date_str) == 4 and date_str.isdigit():
        return date_str
        
    try:
        # Cắt lấy 10 ký tự đầu YYYY-MM-DD (phòng trường hợp có giờ phút giây phía sau)
        if len(date_str) >= 10:
            date_part = date_str[:10]
            dt = datetime.strptime(date_part, '%Y-%m-%d')
            return dt.strftime('%d/%m/%Y')
    except Exception:
        pass # Bỏ qua nếu lỗi format, trả về gốc
        
    return date_str

# ==================== ĐĂNG NHẬP & ĐĂNG XUẤT ====================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        with neo4j_service.driver.session() as db_session:
            result = db_session.run("MATCH (a:Admin {email: $email}) RETURN a.password as hash, a.name as name", {"email": email}).single()
            
            # Kiểm tra xem có email không, và mật khẩu giải mã có khớp không
            if result and check_password_hash(result['hash'], password):
                session['logged_in'] = True
                session['admin_name'] = result['name']
                session['admin_email'] = email
                return redirect(url_for('admin.person_admin_dashboard'))
                
        return render_template('admin/dangnhap.html', error="Email hoặc mật khẩu không đúng!")
    return render_template('admin/dangnhap.html')

# ==========================================================
# KHÔI PHỤC MẬT KHẨU QUA MÃ OTP
# ==========================================================

@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        with neo4j_service.driver.session() as db_session:
            result = db_session.run("MATCH (a:Admin {email: $email}) RETURN a.name as name", {"email": email}).single()
            
            if result:
                # Tạo mã OTP ngẫu nhiên gồm 6 chữ số
                otp_code = str(random.randint(100000, 999999))
                
                # Lưu thông tin xác thực vào Session (Hạn 10 phút) và đặt cờ otp_verified = False
                session['reset_password_email'] = email
                session['reset_password_otp'] = otp_code
                session['reset_password_expiry'] = datetime.now().timestamp() + 600
                session['otp_verified'] = False
                
                # Thiết lập nội dung Email
                msg = Message('Mã OTP khôi phục mật khẩu - Hệ thống Quản trị', 
                              sender=current_app.config['MAIL_USERNAME'], 
                              recipients=[email])
                msg.body = f"Chào {result['name']},\n\nBạn đã yêu cầu đặt lại mật khẩu cho tài khoản quản trị.\n\nMã OTP xác nhận của bạn là: {otp_code}\n\nMã này có hiệu lực trong vòng 10 phút. Vui lòng tuyệt đối không chia sẻ mã này cho bất kỳ ai khác."
                
                try:
                    mail.send(msg)
                    flash('Mã OTP khôi phục mật khẩu đã được gửi vào Email của bạn!', 'info')
                    # Chuyển hướng sang trang NHẬP MÃ OTP
                    return redirect(url_for('admin.forgot_password_verify'))
                except Exception as e:
                    flash(f'Lỗi gửi mail: Không thể kết nối dịch vụ SMTP. Chi tiết: {str(e)}', 'error')
            else:
                flash('Địa chỉ email này không tồn tại trong hệ thống tài khoản Admin!', 'error')
                
    return render_template('admin/forgot_password.html')


# BƯỚC 2: Trang nhập mã OTP và kiểm tra tính hợp lệ
@admin_bp.route('/forgot-password/verify', methods=['GET', 'POST'])
def forgot_password_verify():
    # Kiểm tra phòng hờ nếu người dùng chưa nhập email khôi phục trước đó
    if not session.get('reset_password_email'):
        flash('Vui lòng điền địa chỉ email cần nhận mã khôi phục trước!', 'error')
        return redirect(url_for('admin.forgot_password'))

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        session_otp = session.get('reset_password_otp')
        expiry_time = session.get('reset_password_expiry', 0)

        # Kiểm tra thời hạn hiệu lực của mã OTP
        if not session_otp or datetime.now().timestamp() > expiry_time:
            flash('Mã OTP đã hết hạn sử dụng. Vui lòng thực hiện gửi lại mã mới!', 'error')
            return redirect(url_for('admin.forgot_password'))

        # Kiểm tra độ chính xác của mã OTP
        if user_otp == session_otp:
            # Bật cờ cho phép đổi mật khẩu
            session['otp_verified'] = True
            flash('Xác thực OTP thành công! Vui lòng thiết lập mật khẩu mới.', 'success')
            # Chuyển hướng sang trang ĐỔI MẬT KHẨU
            return redirect(url_for('admin.reset_password_page'))
        else:
            flash('Mã OTP nhập vào không chính xác. Vui lòng kiểm tra lại hòm thư!', 'error')

    # Trả về giao diện chỉ có ô nhập OTP
    return render_template('admin/forgot_password_verify.html')


# BƯỚC 3: Trang nhập mật khẩu mới và lưu vào cơ sở dữ liệu
@admin_bp.route('/forgot-password/reset', methods=['GET', 'POST'])
def reset_password_page():
    # Khóa bảo mật: Nếu chưa nhập OTP thành công thì đẩy ngược về bước 1
    if not session.get('reset_password_email') or not session.get('otp_verified'):
        flash('Bạn cần phải xác minh mã OTP trước khi đổi mật khẩu!', 'error')
        return redirect(url_for('admin.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        target_email = session.get('reset_password_email')

        # Kiểm tra hai ô mật khẩu mới có trùng khớp không
        if new_password != confirm_password:
            flash('Mật khẩu nhập lại không khớp với mật khẩu mới!', 'error')
            return render_template('admin/reset_password.html')

        # Tiến hành mã hóa mật khẩu mới và cập nhật thẳng vào Neo4j
        hashed_password = generate_password_hash(new_password)
        with neo4j_service.driver.session() as db_session:
            db_session.run("MATCH (a:Admin {email: $email}) SET a.password = $new_pw", 
                           {"email": target_email, "new_pw": hashed_password})
        
        # Dọn dẹp sạch sẽ Session sau khi thành công
        session.pop('reset_password_email', None)
        session.pop('reset_password_otp', None)
        session.pop('reset_password_expiry', None)
        session.pop('otp_verified', None)
        
        flash('Cập nhật mật khẩu mới thành công! Bạn có thể tiến hành đăng nhập.', 'success')
        return redirect(url_for('admin.login'))

    # Trả về giao diện chỉ có 2 ô nhập mật khẩu
    return render_template('admin/reset_password.html')

@admin_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('user.index'))

# ==========================================================
# QUẢN LÝ THÔNG TIN TÀI KHOẢN (PROFILE)
# ==========================================================
@admin_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    
    current_email = session.get('admin_email')
    
    # Lấy thông tin hiện tại từ Database
    with neo4j_service.driver.session() as db_session:
        admin_node = db_session.run("MATCH (a:Admin {email: $email}) RETURN a", {"email": current_email}).single()
        if not admin_node: return "Lỗi: Không tìm thấy tài khoản", 404
        admin_data = dict(admin_node['a'])

    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        # Gom các thay đổi lại
        changes = {'name': new_name, 'email': new_email}
        if new_password:
            changes['password'] = generate_password_hash(new_password)

        # TẠO MÃ OTP 6 CHỮ SỐ NGẪU NHIÊN
        otp_code = str(random.randint(100000, 999999))

        # Lưu thông tin thay đổi và mã OTP vào Session để xác minh ở bước sau
        session['profile_otp'] = otp_code
        session['pending_profile_changes'] = changes
        session['otp_expiry'] = datetime.now().timestamp() + 600  # Hạn 10 phút

        # Gửi Email chứa mã OTP về Email hiện tại
        msg = Message('Mã OTP xác nhận thay đổi thông tin Admin',
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[current_email])
                      
        msg.body = f"Chào {admin_data.get('name')},\n\nBạn đang thực hiện yêu cầu thay đổi thông tin tài khoản quản trị.\n\nMã OTP xác nhận của bạn là: {otp_code}\n\nMã này có hiệu lực trong 10 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai khác."
        
        try:
            mail_ext = current_app.extensions.get('mail')
            mail_ext.send(msg)
            flash('Mã OTP đã được gửi đến Email của bạn. Vui lòng nhập mã để xác nhận!', 'info')
            return redirect(url_for('admin.verify_profile_otp'))
        except Exception as e:
            flash(f'Lỗi gửi mail: Không thể gửi mã OTP. Chi tiết: {str(e)}', 'error')
        
        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html', admin=admin_data)


@admin_bp.route('/profile/verify-otp', methods=['GET', 'POST'])
def verify_profile_otp():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        session_otp = session.get('profile_otp')
        expiry = session.get('otp_expiry', 0)
        
        # Kiểm tra thời hạn OTP
        if not session_otp or datetime.now().timestamp() > expiry:
            flash('Mã OTP đã hết hạn hoặc không tồn tại. Vui lòng thực hiện lại!', 'error')
            return redirect(url_for('admin.profile'))
            
        # Kiểm tra tính chính xác của OTP
        if user_otp == session_otp:
            changes = session.get('pending_profile_changes')
            current_email = session.get('admin_email')
            
            if changes and current_email:
                with neo4j_service.driver.session() as db_session:
                    if 'password' in changes:
                        db_session.run("""
                            MATCH (a:Admin {email: $current_email})
                            SET a.name = $name, a.email = $new_email, a.password = $password
                        """, {"current_email": current_email, "name": changes['name'], "new_email": changes['email'], "password": changes['password']})
                    else:
                        db_session.run("""
                            MATCH (a:Admin {email: $current_email})
                            SET a.name = $name, a.email = $new_email
                        """, {"current_email": current_email, "name": changes['name'], "new_email": changes['email']})
                
                # Cập nhật lại phiên đăng nhập hiện tại
                session['admin_email'] = changes['email']
                session['admin_name'] = changes['name']
                
                # Xóa sạch dữ liệu tạm trong session sau khi thành công
                session.pop('profile_otp', None)
                session.pop('pending_profile_changes', None)
                session.pop('otp_expiry', None)
                
                flash('Thông tin tài khoản của bạn đã được cập nhật thành công!', 'success')
                return redirect(url_for('admin.profile'))
        else:
            flash('Mã OTP không chính xác. Vui lòng kiểm tra lại!', 'error')
            
    return render_template('admin/verify_otp.html')

# ==================== ĐIỀU HƯỚNG MẶC ĐỊNH ====================
@admin_bp.route('/')
def admin_index():
    if not session.get('logged_in'):
        return redirect(url_for('admin.login'))
    # Chuyển hướng về trang Thống kê (Dashboard) thay vì trang Nhân vật
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): 
        return redirect(url_for('admin.login'))
    
    # Bộ từ điển chuyển đổi nhãn hệ thống sang tiếng Việt hiển thị trên giao diện
    
    with neo4j_service.driver.session() as db_session:
        stats = {}
        # Đếm số lượng tổng quát của từng loại thực thể
        labels = ['NhanVat', 'SuKien', 'ToChuc', 'HiepDinh', 'QuocGia', 'ThoiKy']
        for label in labels:
            res = db_session.run(f"MATCH (n:{label}) RETURN count(n) as total").single()
            stats[label] = res["total"] if res else 0

        # Đếm tổng số lượng tất cả mối quan hệ
        rel_res = db_session.run("MATCH ()-[r]->() RETURN count(r) as total").single()
        stats['Relationships'] = rel_res["total"] if rel_res else 0

        # Thống kê Nhân vật & Sự kiện theo từng Thời kỳ
        period_stats_query = """
            MATCH (t:ThoiKy)
            OPTIONAL MATCH (p:NhanVat)-[:THUOC_THOI_KY]->(t)
            WITH t, count(DISTINCT p) AS num_persons
            OPTIONAL MATCH (e:SuKien)-[:THUOC_THOI_KY]->(t)
            RETURN t.name AS period_name, 
                   num_persons, 
                   count(DISTINCT e) AS num_events, 
                   t.start_year AS start_year
            ORDER BY start_year ASC
        """
        period_stats = [dict(r) for r in db_session.run(period_stats_query)]

        # Đếm số lượng mối quan hệ của từng Node (Lấy Top 10)
        top_nodes_query = """
            MATCH (n)-[r]-()
            WHERE n.id IS NOT NULL AND labels(n)[0] IS NOT NULL
            RETURN coalesce(n.name, n.id) AS node_name, 
                   labels(n)[0] AS node_type, 
                   count(r) AS rel_count
            ORDER BY rel_count DESC
            LIMIT 10
        """
        top_nodes = [dict(r) for r in db_session.run(top_nodes_query)]

    return render_template('admin/dashboard.html', 
                           stats=stats, 
                           period_stats=period_stats, 
                           top_nodes=top_nodes) 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hàm bóc tách năm kể cả định dạng TCN
def parse_year(year_str):
    if not year_str: return None
    year_str = str(year_str).strip().upper()
    try:
        # Nếu có chữ TCN thì là số âm
        if "TCN" in year_str:
            num = re.sub(r'[^0-9]', '', year_str)
            return -int(num) if num else None
        
        # Nếu là YYYY-MM-DD
        if '-' in year_str:
            return int(year_str.split('-')[0])
            
        # Nếu là DD/MM/YYYY
        if '/' in year_str:
            return int(year_str.split('/')[-1])
            
        # Các trường hợp còn lại lấy số
        num = re.sub(r'[^0-9]', '', year_str)
        return int(num) if num else None
    except Exception:
        return None

# ==========================================================
# QUẢN LÝ NHÂN VẬT (personAdmin)
# ==========================================================
@admin_bp.route('/personAdmin')
def person_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (p:NhanVat) RETURN p.id as id, p.name as name, p.vai_tro as vai_tro, p.image_url as image_url ORDER BY p.name")
        persons = [dict(r) for r in result]
    return render_template('admin/personAdmin/list_nhanvat.html', persons=persons)

@admin_bp.route('/personAdmin/add')
def add_person_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/personAdmin/form_nhanvat.html', person=None)

@admin_bp.route('/personAdmin/edit/<person_id>')
def edit_person_page(person_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (p:NhanVat {id: $id}) RETURN p", {"id": person_id}).single()
        if not result: return "Không tìm thấy nhân vật", 404
        return render_template('admin/personAdmin/form_nhanvat.html', person=dict(result["p"]))
    
@admin_bp.route('/personAdmin/view/<person_id>')
def view_person_page(person_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (p:NhanVat {id: $id}) RETURN p", {"id": person_id}).single()
        if not result: return "Không tìm thấy nhân vật", 404
        
        rel_query = """
            MATCH (n {id: $id})-[r]-(m)
            RETURN startNode(r).id as source_id, coalesce(startNode(r).name) as source_name,
                   type(r) as rel_type, labels(startNode(r))[0] as source_type,
                   endNode(r).id as target_id, coalesce(endNode(r).name) as target_name, labels(endNode(r))[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(rel_query, {"id": person_id})]
        return render_template('admin/personAdmin/view_nhanvat.html', person=dict(result["p"]), relationships=relationships)

@admin_bp.route('/api/persons', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_persons():
    if not session.get('logged_in'): return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'GET':
                result = db_session.run("MATCH (p:NhanVat) RETURN p.id as id, p.name as name, p.vai_tro as vai_tro, p.image_url as image_url ORDER BY p.name")
                return jsonify({"success": True, "data": [dict(r) for r in result]})

            elif request.method in ['POST', 'PUT']:
                data = request.form.to_dict() 
                target_id = data.get('id', '')
                image_file = request.files.get('image')
                image_name = data.get('image_url')

                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                    save_path = os.path.join(current_app.root_path, 'static/images/persons')
                    os.makedirs(save_path, exist_ok=True)
                    image_file.save(os.path.join(save_path, filename))
                    image_name = filename

                # --- LOGIC TỰ ĐỘNG GẮN THỜI KỲ ---
                person_year = parse_year(data.get('ngay_sinh'))
                if person_year is None:
                    person_year = parse_year(data.get('ngay_mat'))

                auto_link_query = """
                    MATCH (p:NhanVat {id: $id}), (g:ThoiKy)
                    WHERE $person_year >= g.start_year AND $person_year <= g.end_year
                    MERGE (p)-[:THUOC_THOI_KY]->(g)
                """

                if request.method == 'POST':
                    # --- KIỂM TRA TRÙNG LẶP ---
                    check_dup = db_session.run(
                        "MATCH (p:NhanVat) WHERE toLower(p.name) = toLower($name) RETURN p", 
                        {"name": data.get('name', '').strip()}
                    ).single()
                    
                    if check_dup:
                        return jsonify({"success": False, "error": f"Nhân vật '{data.get('name')}' đã tồn tại trong hệ thống!"})
                    # --------------------------
                    new_id = f"person_{uuid.uuid4().hex[:8]}"
                    query = """
                        CREATE (p:NhanVat {
                            id: $id, name: $name, ten_day_du: $ten_day_du, vai_tro: $vai_tro,
                            ngay_sinh: $ngay_sinh, noi_sinh: $noi_sinh, ngay_mat: $ngay_mat,
                            noi_mat: $noi_mat, quoc_tich: $quoc_tich,
                            chuc_vu: $chuc_vu, nhiem_ky: $nhiem_ky, cuoc_doi: $cuoc_doi, image_url: $image_url
                        })
                    """
                    db_session.run(query, {**data, "id": new_id, "image_url": image_name})
                    
                    if person_year is not None:
                        db_session.run(auto_link_query, {"id": new_id, "person_year": person_year})
                        
                    return jsonify({"success": True, "message": "Thêm thành công!"})

                elif request.method == 'PUT':
                    if not target_id: return jsonify({"success": False, "error": "Thiếu ID"}), 400
                    
                    query = """
                        MATCH (p:NhanVat {id: $id}) 
                        SET p.name = $name, p.ten_day_du = $ten_day_du, p.vai_tro = $vai_tro,
                            p.ngay_sinh = $ngay_sinh, p.noi_sinh = $noi_sinh, p.ngay_mat = $ngay_mat,
                            p.noi_mat = $noi_mat, p.quoc_tich = $quoc_tich,
                            p.chuc_vu = $chuc_vu, p.nhiem_ky = $nhiem_ky, p.cuoc_doi = $cuoc_doi, p.image_url = $image_url
                    """
                    db_session.run(query, {**data, "id": target_id, "image_url": image_name})
                    
                    db_session.run("MATCH (p:NhanVat {id: $id})-[r:THUOC_THOI_KY]->(:ThoiKy) DELETE r", {"id": target_id})
                    if person_year is not None:
                        db_session.run(auto_link_query, {"id": target_id, "person_year": person_year})
                        
                    return jsonify({"success": True, "message": "Cập nhật thành công!"})

            elif request.method == 'DELETE':
                person_id = request.json.get('id')
                db_session.run("MATCH (p:NhanVat {id: $id}) DETACH DELETE p", {"id": person_id})
                return jsonify({"success": True, "message": "Xóa thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ==========================================================
# QUẢN LÝ SỰ KIỆN (eventAdmin)
# ==========================================================
@admin_bp.route('/eventAdmin')
def event_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (e:SuKien) RETURN e.id as id, e.name as name, e.start_time as start_time, e.end_time as end_time, e.image_url as image_url ORDER BY e.name")
        events = [dict(r) for r in result]
    return render_template('admin/eventAdmin/list_event.html', events=events)

@admin_bp.route('/eventAdmin/add')
def add_event_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/eventAdmin/form_event.html', event=None)

@admin_bp.route('/eventAdmin/edit/<event_id>')
def edit_event_page(event_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (e:SuKien {id: $id}) RETURN e", {"id": event_id}).single()
        if not result: return "Không tìm thấy sự kiện", 404
        return render_template('admin/eventAdmin/form_event.html', event=dict(result["e"]))

@admin_bp.route('/eventAdmin/view/<event_id>')
def view_event_page(event_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (e:SuKien {id: $id}) RETURN e", {"id": event_id}).single()
        if not result: return "Không tìm thấy sự kiện", 404
        
        rel_query = """
            MATCH (n {id: $id})-[r]-(m)
            RETURN startNode(r).id as source_id, coalesce(startNode(r).name) as source_name,
                   type(r) as rel_type, labels(startNode(r))[0] as source_type,
                   endNode(r).id as target_id, coalesce(endNode(r).name) as target_name, labels(endNode(r))[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(rel_query, {"id": event_id})]
        return render_template('admin/eventAdmin/view_event.html', event=dict(result["e"]), relationships=relationships)

@admin_bp.route('/api/events', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_events():
    if not session.get('logged_in'): return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'GET':
                result = db_session.run("MATCH (e:SuKien) RETURN e.id as id, e.name as name, e.locations as locations ORDER BY e.name")
                return jsonify({"success": True, "data": [dict(r) for r in result]})

            elif request.method in ['POST', 'PUT']:
                data = request.form.to_dict() 
                target_id = data.get('id', '') 
                
                # Lưu trực tiếp locations dưới dạng string (vì form truyền lên chuỗi)
                locations_str = data.get('locations', '')
                
                image_file = request.files.get('image')
                image_name = data.get('image_url')

                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                    save_path = os.path.join(current_app.root_path, 'static', 'images', 'events')
                    os.makedirs(save_path, exist_ok=True)
                    image_file.save(os.path.join(save_path, filename))
                    image_name = filename

                event_year = parse_year(data.get('start_time'))

                auto_link_query = """
                    MATCH (e:SuKien {id: $id}), (g:ThoiKy)
                    WHERE $event_year >= g.start_year AND $event_year <= g.end_year
                    MERGE (e)-[:THUOC_THOI_KY]->(g)
                """

                if request.method == 'POST':
                    # --- KIỂM TRA TRÙNG LẶP ---
                    check_dup = db_session.run(
                        "MATCH (e:SuKien) WHERE toLower(e.name) = toLower($name) RETURN e", 
                        {"name": data.get('name', '').strip()}
                    ).single()
                    
                    if check_dup:
                        return jsonify({"success": False, "error": f"Sự kiện '{data.get('name')}' đã tồn tại trong hệ thống!"})
                    # --------------------------
                    new_id = f"event_{uuid.uuid4().hex[:8]}"
                    query = """
                        CREATE (e:SuKien {
                            id: $id, name: $name, start_time: $start_time, end_time: $end_time,
                            locations: $locations, nguyen_nhan: $nguyen_nhan, ket_qua: $ket_qua,
                            y_nghia: $y_nghia, bai_hoc_kinh_nghiem: $bai_hoc_kinh_nghiem,
                            dien_bien: $dien_bien, image_url: $image_url
                        })
                    """
                    db_session.run(query, {**data, "id": new_id, "locations": locations_str, "image_url": image_name})
                    
                    if event_year is not None:
                        db_session.run(auto_link_query, {"id": new_id, "event_year": event_year}) 
                    
                    return jsonify({"success": True, "message": "Thêm sự kiện thành công!"})

                elif request.method == 'PUT':
                    if not target_id: return jsonify({"success": False, "error": "Thiếu ID"}), 400
                        
                    query = """
                        MATCH (e:SuKien {id: $id}) 
                        SET e.name = $name, e.start_time = $start_time, e.end_time = $end_time,
                            e.locations = $locations, e.nguyen_nhan = $nguyen_nhan, e.ket_qua = $ket_qua, 
                            e.y_nghia = $y_nghia, e.bai_hoc_kinh_nghiem = $bai_hoc_kinh_nghiem, 
                            e.dien_bien = $dien_bien, e.image_url = $image_url
                    """
                    db_session.run(query, {**data, "id": target_id, "locations": locations_str, "image_url": image_name})
                    
                    db_session.run("MATCH (e:SuKien {id: $id})-[r:THUOC_THOI_KY]->(:ThoiKy) DELETE r", {"id": target_id})
                    
                    if event_year is not None:
                        db_session.run(auto_link_query, {"id": target_id, "event_year": event_year})
                    
                    return jsonify({"success": True, "message": "Cập nhật sự kiện thành công!"})

            elif request.method == 'DELETE':
                event_id = request.json.get('id')
                db_session.run("MATCH (e:SuKien {id: $id}) DETACH DELETE e", {"id": event_id})
                return jsonify({"success": True, "message": "Xóa sự kiện thành công!"})
                
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================================
# QUẢN LÝ TỔ CHỨC (organizationAdmin)
# ==========================================================
@admin_bp.route('/organizationAdmin')
def organization_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (o:ToChuc) RETURN o.id as id, o.name as name, o.type as type, o.founded_year as founded_year ORDER BY o.name")
        organizations = [dict(r) for r in result]
    return render_template('admin/organizationAdmin/list_organization.html', organizations=organizations)

@admin_bp.route('/organizationAdmin/add')
def add_organization_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/organizationAdmin/form_organization.html', organization=None)

@admin_bp.route('/organizationAdmin/edit/<org_id>')
def edit_organization_page(org_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (o:ToChuc {id: $id}) RETURN o", {"id": org_id}).single()
        return render_template('admin/organizationAdmin/form_organization.html', organization=dict(result["o"])) if result else ("Không tìm thấy", 404)

@admin_bp.route('/organizationAdmin/view/<org_id>')
def view_organization_page(org_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (o:ToChuc {id: $id}) RETURN o", {"id": org_id}).single()
        if not result: return "Không tìm thấy tổ chức", 404
        
        rel_query = """
            MATCH (n {id: $id})-[r]-(m)
            RETURN startNode(r).id as source_id, coalesce(startNode(r).name) as source_name,
                   type(r) as rel_type, labels(startNode(r))[0] as source_type,
                   endNode(r).id as target_id, coalesce(endNode(r).name) as target_name, labels(endNode(r))[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(rel_query, {"id": org_id})]
        return render_template('admin/organizationAdmin/view_organization.html', organization=dict(result["o"]), relationships=relationships)

@admin_bp.route('/api/organizations', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_organizations():
    if not session.get('logged_in'): return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'GET':
                result = db_session.run("MATCH (o:ToChuc) RETURN o.id as id, o.name as name, o.type as type, o.founded_year as founded_year ORDER BY o.name")
                return jsonify({"success": True, "data": [dict(r) for r in result]})

            elif request.method in ['POST', 'PUT']:
                data = request.form.to_dict()

                if request.method == 'POST':
                    # --- KIỂM TRA TRÙNG LẶP ---
                    check_dup = db_session.run(
                        "MATCH (o:ToChuc) WHERE toLower(o.name) = toLower($name) RETURN o", 
                        {"name": data.get('name', '').strip()}
                    ).single()
                    
                    if check_dup:
                        return jsonify({"success": False, "error": f"Tổ chức '{data.get('name')}' đã tồn tại trong hệ thống!"})
                    # --------------------------
                    new_id = f"org_{uuid.uuid4().hex[:8]}"
                    query = """
                        CREATE (o:ToChuc {
                            id: $id, name: $name, type: $type, founded_year: $founded_year,
                             headquarters: $headquarters, description: $description
                        })
                    """
                    db_session.run(query, {**data, "id": new_id})
                    return jsonify({"success": True, "message": "Thêm tổ chức thành công!"})

                elif request.method == 'PUT':
                    org_id = data.get('id')
                    if not org_id: return jsonify({"success": False, "error": "Thiếu ID"}), 400
                    
                    query = """
                        MATCH (o:ToChuc {id: $id}) 
                        SET o.name = $name, o.type = $type, o.founded_year = $founded_year,
                            o.headquarters = $headquarters, o.description = $description
                    """
                    db_session.run(query, {**data, "id": org_id})
                    return jsonify({"success": True, "message": "Cập nhật tổ chức thành công!"})

            elif request.method == 'DELETE':
                org_id = request.json.get('id')
                db_session.run("MATCH (o:ToChuc {id: $id}) DETACH DELETE o", {"id": org_id})
                return jsonify({"success": True, "message": "Xóa tổ chức thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================================
# QUẢN LÝ QUỐC GIA (countryAdmin)
# ==========================================================
@admin_bp.route('/countryAdmin')
def country_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (c:QuocGia) RETURN c.id as id, c.name as name, c.capital as capital, c.region as region ORDER BY c.name")
        countries = [dict(r) for r in result]
    return render_template('admin/countryAdmin/list_country.html', countries=countries)

@admin_bp.route('/countryAdmin/add')
def add_country_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/countryAdmin/form_country.html', country=None)

@admin_bp.route('/countryAdmin/edit/<country_id>')
def edit_country_page(country_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (c:QuocGia {id: $id}) RETURN c", {"id": country_id}).single()
        return render_template('admin/countryAdmin/form_country.html', country=dict(result["c"])) if result else ("Không tìm thấy", 404)

@admin_bp.route('/countryAdmin/view/<country_id>')
def view_country_page(country_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (c:QuocGia {id: $id}) RETURN c", {"id": country_id}).single()
        if not result: return "Không tìm thấy quốc gia", 404
        
        rel_query = """
            MATCH (n {id: $id})-[r]-(m)
            RETURN startNode(r).id as source_id, coalesce(startNode(r).name) as source_name,
                   type(r) as rel_type, labels(startNode(r))[0] as source_type,
                   endNode(r).id as target_id, coalesce(endNode(r).name) as target_name, labels(endNode(r))[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(rel_query, {"id": country_id})]
        return render_template('admin/countryAdmin/view_country.html', country=dict(result["c"]), relationships=relationships)

@admin_bp.route('/api/countries', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_countries():
    if not session.get('logged_in'): return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'GET':
                result = db_session.run("MATCH (c:QuocGia) RETURN c.id as id, c.name as name, c.capital as capital, c.region as region ORDER BY c.name")
                return jsonify({"success": True, "data": [dict(r) for r in result]})

            elif request.method in ['POST', 'PUT']:
                data = request.form.to_dict()
                target_id = data.get('id', '')

                if request.method == 'POST':
                    # --- KIỂM TRA TRÙNG LẶP ---
                    check_dup = db_session.run(
                        "MATCH (c:QuocGia) WHERE toLower(c.name) = toLower($name) RETURN c", 
                        {"name": data.get('name', '').strip()}
                    ).single()
                    
                    if check_dup:
                        return jsonify({"success": False, "error": f"Quốc gia '{data.get('name')}' đã tồn tại trong hệ thống!"})
                    # --------------------------
                    new_id = f"country_{uuid.uuid4().hex[:8]}"
                    query = """
                        CREATE (c:QuocGia {
                            id: $id, name: $name, capital: $capital, region: $region,
                            description: $description
                        })
                    """
                    db_session.run(query, {**data, "id": new_id})
                    return jsonify({"success": True, "message": "Thêm quốc gia thành công!"})

                elif request.method == 'PUT':
                    if not target_id: return jsonify({"success": False, "error": "Thiếu ID"}), 400
                    
                    query = """
                        MATCH (c:QuocGia {id: $id}) 
                        SET c.name = $name, c.capital = $capital, c.region = $region,
                            c.description = $description
                    """
                    db_session.run(query, {**data, "id": target_id})
                    return jsonify({"success": True, "message": "Cập nhật quốc gia thành công!"})

            elif request.method == 'DELETE':
                country_id = request.json.get('id')
                db_session.run("MATCH (c:QuocGia {id: $id}) DETACH DELETE c", {"id": country_id})
                return jsonify({"success": True, "message": "Xóa quốc gia thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================================
# QUẢN LÝ HIỆP ĐỊNH (treatyAdmin)
# ==========================================================
@admin_bp.route('/treatyAdmin')
def treaty_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:

        query = """
            MATCH (t:HiepDinh) 
            RETURN t.id as id, t.name as name, t.signing_date as signing_date, t.location as location 
            ORDER BY toInteger(t.year) ASC
        """
        result = db_session.run(query)
        treaties = [dict(r) for r in result]
        
    return render_template('admin/treatyAdmin/list_treaty.html', treaties=treaties)

@admin_bp.route('/treatyAdmin/add')
def add_treaty_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/treatyAdmin/form_treaty.html', treaty=None)

@admin_bp.route('/treatyAdmin/edit/<treaty_id>')
def edit_treaty_page(treaty_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (t:HiepDinh {id: $id}) RETURN t", {"id": treaty_id}).single()
        return render_template('admin/treatyAdmin/form_treaty.html', treaty=dict(result["t"])) if result else ("Không tìm thấy", 404)

@admin_bp.route('/treatyAdmin/view/<treaty_id>')
def view_treaty_page(treaty_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (t:HiepDinh {id: $id}) RETURN t", {"id": treaty_id}).single()
        if not result: return "Không tìm thấy hiệp định", 404
        
        rel_query = """
            MATCH (n {id: $id})-[r]-(m)
            RETURN startNode(r).id as source_id, coalesce(startNode(r).name) as source_name,
                   type(r) as rel_type, labels(startNode(r))[0] as source_type,
                   endNode(r).id as target_id, coalesce(endNode(r).name) as target_name, labels(endNode(r))[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(rel_query, {"id": treaty_id})]
        return render_template('admin/treatyAdmin/view_treaty.html', treaty=dict(result["t"]), relationships=relationships)

@admin_bp.route('/api/treaties', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_treaties():
    if not session.get('logged_in'): return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'GET':
                result = db_session.run("MATCH (t:HiepDinh) RETURN t.id as id, t.name as name, t.signing_date as signing_date, t.location as location ORDER BY toInteger(t.year) ASC")
                return jsonify({"success": True, "data": [dict(r) for r in result]})

            elif request.method in ['POST', 'PUT']:
                data = request.form.to_dict()
                target_id = data.get('id', '')

                treaty_year = parse_year(data.get('year'))

                auto_link_query = """
                    MATCH (t:HiepDinh {id: $id}), (g:ThoiKy)
                    WHERE $treaty_year >= g.start_year AND $treaty_year <= g.end_year
                    MERGE (t)-[:THUOC_THOI_KY]->(g)
                """

                if request.method == 'POST':
                    # --- KIỂM TRA TRÙNG LẶP ---
                    check_dup = db_session.run(
                        "MATCH (t:HiepDinh) WHERE toLower(t.name) = toLower($name) RETURN t", 
                        {"name": data.get('name', '').strip()}
                    ).single()
                    
                    if check_dup:
                        return jsonify({"success": False, "error": f"Hiệp định '{data.get('name')}' đã tồn tại trong hệ thống!"})
                    # --------------------------
                    new_id = f"treaty_{uuid.uuid4().hex[:8]}"
                    query = """
                        CREATE (t:HiepDinh {
                            id: $id, name: $name, year: $year, signing_date: $signing_date,
                            location: $location,
                            description: $description, noi_dung_chinh: $noi_dung_chinh,
                            y_nghia: $y_nghia, bai_hoc_kinh_nghiem: $bai_hoc_kinh_nghiem
                        })
                    """
                    db_session.run(query, {**data, "id": new_id})
                    
                    if treaty_year is not None:
                        db_session.run(auto_link_query, {"id": new_id, "treaty_year": treaty_year}) 
                    return jsonify({"success": True, "message": "Thêm hiệp định thành công!"})

                elif request.method == 'PUT':
                    if not target_id: return jsonify({"success": False, "error": "Thiếu ID"}), 400
                        
                    query = """
                        MATCH (t:HiepDinh {id: $id}) 
                        SET t.name = $name, t.year = $year, t.signing_date = $signing_date,
                            t.location = $location,
                            t.description = $description, t.noi_dung_chinh = $noi_dung_chinh,
                            t.y_nghia = $y_nghia, t.bai_hoc_kinh_nghiem = $bai_hoc_kinh_nghiem
                    """
                    db_session.run(query, {**data, "id": target_id})
                    db_session.run("MATCH (t:HiepDinh {id: $id})-[r:THUOC_THOI_KY]->(:ThoiKy) DELETE r", {"id": target_id})
                    
                    if treaty_year is not None:
                        db_session.run(auto_link_query, {"id": target_id, "treaty_year": treaty_year}) 
                    return jsonify({"success": True, "message": "Cập nhật hiệp định thành công!"})

            elif request.method == 'DELETE':
                treaty_id = request.json.get('id')
                db_session.run("MATCH (t:HiepDinh {id: $id}) DETACH DELETE t", {"id": treaty_id})
                return jsonify({"success": True, "message": "Xóa hiệp định thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================================
# QUẢN LÝ MỐI QUAN HỆ (relationshipAdmin)
# ==========================================================
@admin_bp.route('/relationshipAdmin')
def relationship_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    
    with neo4j_service.driver.session() as db_session:
        query = """
            MATCH (a)-[r]->(b)
            WHERE a.id IS NOT NULL AND b.id IS NOT NULL
            RETURN a.id as source_id, coalesce(a.name, a.name) as source_name, labels(a)[0] as source_type,
                   type(r) as rel_type,
                   b.id as target_id, coalesce(b.name, b.name) as target_name, labels(b)[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(query)]
        rel_types = [r["type"] for r in db_session.run("CALL db.relationshipTypes() YIELD relationshipType as type")]

    return render_template('admin/relationshipAdmin/list_quanhe.html', relationships=relationships, rel_types=rel_types)

@admin_bp.route('/relationshipAdmin/add')
def add_relationship_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    pre_source_id = request.args.get('source_id', '')
    
    with neo4j_service.driver.session() as db_session:
        nodes = [dict(r) for r in db_session.run("MATCH (n) WHERE n.id IS NOT NULL RETURN n.id as id, coalesce(n.name, n.name) as name, labels(n)[0] as type ORDER BY type, name")]
        rel_types = [r["type"] for r in db_session.run("CALL db.relationshipTypes() YIELD relationshipType as type")]
        
    return render_template('admin/relationshipAdmin/form_quanhe.html', 
                           nodes=nodes, 
                           rel_types=rel_types, 
                           rel_data=None,
                           pre_source_id=pre_source_id)

@admin_bp.route('/api/relationships', methods=['POST', 'DELETE'])
def manage_relationships():
    if not session.get('logged_in'): return jsonify({"success": False}), 401
    
    data = request.json
    source_id = data.get('source_id')
    target_id = data.get('target_id')
    raw_rel_type = data.get('rel_type', '')
    rel_type = raw_rel_type.strip().upper().replace(' ', '_')

    # Bổ sung: Kiểm tra dữ liệu rỗng
    if not source_id or not target_id or not rel_type:
        return jsonify({"success": False, "error": "Vui lòng chọn đầy đủ 2 thực thể và loại quan hệ!"})

    # Bổ sung: Chặn việc tạo mối quan hệ vòng lặp (1 thực thể tự chỉ vào chính nó)
    if source_id == target_id:
        return jsonify({"success": False, "error": "Không thể tạo mối quan hệ tự chỉ vào chính nó!"})

    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'POST':
                
                # --- 1. KIỂM TRA TRÙNG LẶP ---
                check_query = f"""
                    MATCH (a {{id: $source_id}})-[r:{rel_type}]->(b {{id: $target_id}})
                    RETURN r
                """
                existing_rel = db_session.run(check_query, {"source_id": source_id, "target_id": target_id}).single()
                
                if existing_rel:
                    return jsonify({"success": False, "error": "Mối quan hệ này ĐÃ TỒN TẠI giữa 2 thực thể đã chọn!"})
                # -----------------------------

                # 2. TẠO MỐI QUAN HỆ MỚI NẾU CHƯA CÓ
                query = f"""
                    MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                    MERGE (a)-[r:{rel_type}]->(b)
                """
                db_session.run(query, {"source_id": source_id, "target_id": target_id})
                return jsonify({"success": True, "message": "Tạo mối quan hệ thành công!"})
                
            elif request.method == 'DELETE':
                query = f"""
                    MATCH (a {{id: $source_id}})-[r:{rel_type}]->(b {{id: $target_id}})
                    DELETE r
                """
                db_session.run(query, {"source_id": source_id, "target_id": target_id})
                return jsonify({"success": True, "message": "Đã xóa mối quan hệ!"})
                
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# ==========================================================
# QUẢN LÝ GIAI ĐOẠN / THỜI KỲ (periodAdmin)
# ==========================================================
@admin_bp.route('/periodAdmin')
def period_admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (g:ThoiKy) RETURN g.id as id, g.name as name, g.start_year as start_year, g.end_year as end_year ORDER BY g.start_year")
        periods = [dict(r) for r in result]
    return render_template('admin/periodAdmin/list_period.html', periods=periods)

@admin_bp.route('/periodAdmin/add')
def add_period_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/periodAdmin/form_period.html', period=None)

@admin_bp.route('/periodAdmin/edit/<period_id>')
def edit_period_page(period_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (g:ThoiKy {id: $id}) RETURN g", {"id": period_id}).single()
        return render_template('admin/periodAdmin/form_period.html', period=dict(result["g"])) if result else ("Không tìm thấy", 404)

@admin_bp.route('/periodAdmin/view/<period_id>')
def view_period_page(period_id):
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    with neo4j_service.driver.session() as db_session:
        result = db_session.run("MATCH (g:ThoiKy {id: $id}) RETURN g", {"id": period_id}).single()
        if not result: return "Không tìm thấy thời kỳ", 404
        
        rel_query = """
            MATCH (n)-[r]->(g:ThoiKy {id: $id})
            RETURN n.id as source_id, 
                   coalesce(n.name, n.name) as source_name,
                   type(r) as rel_type, labels(n)[0] as source_type,
                   g.id as target_id, 
                   coalesce(g.name, g.name) as target_name, 
                   labels(g)[0] as target_type
        """
        relationships = [dict(record) for record in db_session.run(rel_query, {"id": period_id})]
        return render_template('admin/periodAdmin/view_period.html', period=dict(result["g"]), relationships=relationships)

@admin_bp.route('/api/periods', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_periods():
    if not session.get('logged_in'): return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    try:
        with neo4j_service.driver.session() as db_session:
            if request.method == 'GET':
                result = db_session.run("MATCH (g:ThoiKy) RETURN g.id as id, g.name as name ORDER BY g.start_year")
                return jsonify({"success": True, "data": [dict(r) for r in result]})

            elif request.method in ['POST', 'PUT']:
                data = request.form.to_dict()
                target_id = data.get('id', '')
                
                # Quét lại tất cả Sự Kiện dựa trên năm để nối vào Thời Kỳ này
                auto_link_events_query = """
                    MATCH (e:SuKien), (g:ThoiKy {id: $id})
                    WHERE e.start_time IS NOT NULL AND trim(toString(e.start_time)) <> ""
                    WITH e, g, 
                         CASE 
                            WHEN toString(e.start_time) CONTAINS 'TCN' THEN -toInteger(replace(toString(e.start_time), 'TCN', ''))
                            WHEN toString(e.start_time) CONTAINS '-' THEN toInteger(split(toString(e.start_time), '-')[0])
                            WHEN toString(e.start_time) CONTAINS '/' THEN toInteger(last(split(toString(e.start_time), '/')))
                            ELSE toInteger(right(toString(e.start_time), 4))
                         END AS event_year
                    WHERE event_year IS NOT NULL AND event_year >= g.start_year AND event_year <= g.end_year
                    MERGE (e)-[:THUOC_THOI_KY]->(g)
                """
                
                # Quét lại tất cả Hiệp Định
                auto_link_treaties_query = """
                    MATCH (t:HiepDinh), (g:ThoiKy {id: $id})
                    WHERE t.year IS NOT NULL AND trim(toString(t.year)) <> ""
                    WITH t, g, 
                         CASE 
                            WHEN toString(t.year) CONTAINS 'TCN' THEN -toInteger(replace(toString(t.year), 'TCN', ''))
                            ELSE toInteger(t.year)
                         END AS treaty_year
                    WHERE treaty_year >= g.start_year AND treaty_year <= g.end_year
                    MERGE (t)-[:THUOC_THOI_KY]->(g)
                """
                
                # Lấy số năm từ Form của Admin (đã được định dạng TCN)
                start_year_str = data.get('start_year', '')
                end_year_str = data.get('end_year', '')
                
                start_y = parse_year(start_year_str) if start_year_str else 0
                end_y = parse_year(end_year_str) if end_year_str else 9999

                if request.method == 'POST':
                    new_id = f"period_{uuid.uuid4().hex[:8]}"
                    query = """
                        CREATE (g:ThoiKy {
                            id: $id, name: $name, start_year: $start_year, 
                            end_year: $end_year, description: $description, y_nghia: $y_nghia
                        })
                    """
                    db_session.run(query, {**data, "id": new_id, "start_year": start_y, "end_year": end_y})
                    db_session.run(auto_link_events_query, {"id": new_id})
                    db_session.run(auto_link_treaties_query, {"id": new_id})
                    return jsonify({"success": True, "message": "Thêm thời kỳ thành công!"})

                elif request.method == 'PUT':
                    if not target_id: return jsonify({"success": False, "error": "Thiếu ID để cập nhật!"}), 400
                        
                    query = """
                        MATCH (g:ThoiKy {id: $id}) 
                        SET g.name = $name, g.start_year = $start_year, 
                            g.end_year = $end_year, g.description = $description, g.y_nghia = $y_nghia
                    """
                    db_session.run(query, {**data, "id": target_id, "start_year": start_y, "end_year": end_y})
                    db_session.run("MATCH (n)-[r:THUOC_THOI_KY]->(g:ThoiKy {id: $id}) DELETE r", {"id": target_id})
                    db_session.run(auto_link_events_query, {"id": target_id})
                    db_session.run(auto_link_treaties_query, {"id": target_id})
                    return jsonify({"success": True, "message": "Cập nhật thời kỳ thành công!"})

            elif request.method == 'DELETE':
                period_id = request.json.get('id')
                db_session.run("MATCH (g:ThoiKy {id: $id}) DETACH DELETE g", {"id": period_id})
                return jsonify({"success": True, "message": "Xóa thời kỳ thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

# @admin_bp.route('/api/ai/extract-relation', methods=['POST'])
# def ai_extract_relation():
#     if not session.get('logged_in'): 
#         return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    
#     data = request.json
#     text_input = data.get('text', '')
    
#     if not text_input:
#         return jsonify({"success": False, "error": "Vui lòng nhập văn bản."})

#     # Lấy danh sách quan hệ đang có
#     with neo4j_service.driver.session() as db_session:
#         existing_types = [r["type"] for r in db_session.run("CALL db.relationshipTypes() YIELD relationshipType as type")]
    
#     # Câu lệnh (Prompt) cho AI đã gộp đầy đủ các rule
#     prompt = f"""
#     Bạn là một chuyên gia về Lịch sử Việt Nam. Nhiệm vụ của bạn là đọc một đoạn văn bản và trích xuất MỘT mối quan hệ lịch sử chính yếu dưới dạng JSON.
    
#     Các loại mối quan hệ ĐANG CÓ SẴN trong hệ thống: {existing_types}
    
#     Quy tắc trích xuất dữ liệu:
#     1. "source_name": Tên thực thể làm CHỦ NGỮ hoặc khởi xướng.
#     2. "target_name": Tên thực thể bị tác động, đích đến, hoặc nơi diễn ra.
#     3. "rel_type": Loại quan hệ. Hãy ƯU TIÊN SỬ DỤNG một trong các loại quan hệ đang có sẵn ở trên. Nếu không có cái nào phù hợp, bạn được phép TỰ TẠO MỚI (viết bằng CHỮ IN HOA, dùng DẤU GẠCH DƯỚI, không dấu tiếng Việt).

#     Yêu cầu trả về DUY NHẤT JSON theo đúng 3 key này.
    
#     Đoạn văn bản: "{text_input}"
#     """

#     try:
#         chat_completion = groq_client.chat.completions.create(
                #     messages=[{"role": "user", "content": prompt}],
                #     model="llama-3.1-8b-instant", 
                # )
        
#         # Parse JSON an toàn
#         result_data = json.loads(response.text)
        
#         return jsonify({
#             "success": True, 
#             "data": result_data
#         })
        
#     except Exception as e:
#         return jsonify({"success": False, "error": f"Lỗi AI: {str(e)}"}), 500

# ==========================================================
# QUẢN LÝ SAO LƯU & PHỤC HỒI (BACKUP / RESTORE EXCEL)
# ==========================================================
@admin_bp.route('/backupAdmin')
def backup_admin_page():
    if not session.get('logged_in'): return redirect(url_for('admin.login'))
    return render_template('admin/backup_admin.html')

@admin_bp.route('/api/backup/export', methods=['GET'])
def export_excel():
    if not session.get('logged_in'): return jsonify({"success": False}), 401
    try:
        output = io.BytesIO()
        column_orders = {
            'NhanVat': ['id', 'name', 'ten_day_du', 'ngay_sinh', 'noi_sinh', 'ngay_mat', 'noi_mat', 'quoc_tich', 'vai_tro', 'chuc_vu', 'nhiem_ky', 'cuoc_doi', 'image_url'],
            'SuKien': ['id', 'name', 'start_time', 'end_time', 'locations', 'dien_bien', 'nguyen_nhan', 'ket_qua', 'y_nghia', 'bai_hoc_kinh_nghiem', 'image_url'],
            'ToChuc': ['id', 'name', 'type', 'founded_year', 'headquarters', 'description'],
            'HiepDinh': ['id', 'name', 'year', 'signing_date', 'location', 'description', 'noi_dung_chinh', 'y_nghia', 'bai_hoc_kinh_nghiem'],
            'QuocGia': ['id', 'name', 'capital', 'region', 'description'],
            'ThoiKy': ['id', 'name', 'start_year', 'end_year', 'description', 'y_nghia'],
            'Relationships': ['source_id', 'source_label', 'target_id', 'target_label', 'relation']
        }
        long_text_columns = ['cuoc_doi', 'dien_bien', 'description', 'nguyen_nhan', 'ket_qua', 'y_nghia', 'bai_hoc_kinh_nghiem', 'noi_dung_chinh']

        with neo4j_service.driver.session() as db_session:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # 1. XUẤT CÁC THỰC THỂ (NODES)
                labels = ['NhanVat', 'SuKien', 'ToChuc', 'HiepDinh', 'QuocGia', 'ThoiKy']
                for label in labels:
                    res = db_session.run(f"MATCH (n:{label}) RETURN n")
                    data = [dict(r['n']) for r in res]
                    if data:
                        df = pd.DataFrame(data)
                        if label in column_orders:
                            cols = [c for c in column_orders[label] if c in df.columns]
                            df = df[cols + [c for c in df.columns if c not in cols]]
                        
                        for col in ['ngay_sinh', 'ngay_mat', 'start_time', 'end_time', 'signing_date']:
                            if col in df.columns: df[col] = df[col].apply(format_vn_date)

                        df.to_excel(writer, sheet_name=label, index=False)
                        # --- TRANG TRÍ VÀ CĂN CHỈNH ---
                        ws = writer.sheets[label]
                        
                        # Định dạng Header (Tô nền xanh đậm, chữ trắng)
                        for cell in ws[1]:
                            cell.font = Font(bold=True)
                            cell.alignment = Alignment(horizontal='center', vertical='center')

                        # Định dạng dữ liệu: Tự động xuống dòng (Wrap Text) và căn lề trên
                        for row in ws.iter_rows(min_row=2):
                            for cell in row:
                                cell.alignment = Alignment(wrap_text=True, vertical='top', horizontal='left')

                        # Thiết lập độ rộng cột (Chiều dài)
                        for col in ws.columns:
                            column_letter = col[0].column_letter
                            header_value = str(col[0].value)
                            
                            # Thiết lập độ rộng cột
                            if header_value in long_text_columns:
                                ws.column_dimensions[column_letter].width = 75 # Rất rộng cho tiểu sử
                            else:
                                ws.column_dimensions[column_letter].width = 25 # Rộng vừa cho các cột khác

                            # Áp dụng cho toàn bộ dữ liệu trong cột
                            for cell in col:
                                if cell.row > 1: # Bỏ qua header
                                    cell.alignment = Alignment(wrap_text=True, vertical='top', horizontal='left')

                # 2. XUẤT MỐI QUAN HỆ (EDGES) THEO CẤU TRÚC MỚI
                rel_res = db_session.run("""
                    MATCH (a)-[r]->(b) 
                    RETURN a.id as source_id, labels(a)[0] as source_label, 
                           b.id as target_id, labels(b)[0] as target_label, 
                           type(r) as relation
                """)
                df_rels = pd.DataFrame([dict(r) for r in rel_res])
                if not df_rels.empty:
                    df_rels = df_rels[['source_id', 'source_label', 'target_id', 'target_label', 'relation']]
                    df_rels.to_excel(writer, sheet_name='Relationships', index=False)
                    ws_rel = writer.sheets['Relationships']
                    for col in ws_rel.columns:
                        ws_rel.column_dimensions[col[0].column_letter].width = 25
                        for cell in col:
                            cell.alignment = Alignment(horizontal='left', vertical='top')

        output.seek(0)
        file_name = f"DuLieuLichSuVN_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return send_file(output, as_attachment=True, download_name=file_name, 
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return f"Lỗi xuất file: {str(e)}", 500

@admin_bp.route('/api/backup/import', methods=['POST'])
def import_excel():
    if not session.get('logged_in'): return jsonify({"success": False}), 401
    try:
        file = request.files.get('file')
        if not file or not file.filename.endswith('.xlsx'):
            return jsonify({"success": False, "error": "Định dạng file không hợp lệ"}), 400
        
        xls = pd.ExcelFile(file)
        node_labels = ['NhanVat', 'SuKien', 'ToChuc', 'HiepDinh', 'QuocGia', 'ThoiKy']
        
        with neo4j_service.driver.session() as db_session:
            # 1. Import Nodes
            for label in node_labels:
                if label in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=label).fillna('')
                    for _, row in df.iterrows():
                        props = row.to_dict()
                        db_session.run(f"MERGE (n:{label} {{id: $id}}) SET n += $props", 
                                       {"id": props['id'], "props": props})
            
            # 2. Import Relationships (source_id, source_label, target_id, target_label, relation)
            if 'Relationships' in xls.sheet_names:
                df_rels = pd.read_excel(xls, sheet_name='Relationships').fillna('')
                for _, row in df_rels.iterrows():
                    source_id = row['source_id']
                    target_id = row['target_id']
                    rel_type = str(row['relation']).strip().upper().replace(' ', '_')
                    
                    if source_id and target_id and rel_type:
                        # Dùng MERGE để tạo quan hệ, tránh trùng lặp
                        db_session.run(f"""
                            MATCH (a {{id: $s_id}}), (b {{id: $t_id}})
                            MERGE (a)-[r:{rel_type}]->(b)
                        """, {"s_id": source_id, "t_id": target_id})

        return jsonify({"success": True, "message": "Khôi phục dữ liệu thành công!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500