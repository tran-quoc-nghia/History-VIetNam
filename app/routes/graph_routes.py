from flask import Blueprint, jsonify
from app.services.neo4j_service import Neo4jService
from datetime import datetime 

graph_bp = Blueprint('graph', __name__)
neo4j_service = Neo4jService()

# Cấu hình màu sắc dùng chung cho toàn bộ đồ thị
GRAPH_COLORS = {
    'NhanVat': '#e74c3c', 'SuKien': '#f39c12', 
    'ToChuc': '#3498db', 'HiepDinh': '#9b59b6', 'QuocGia': "#9bafaa", 'ThoiKy': "#87ac0f"
}

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

    # Nhóm Nhân vật - Nhân vật
    'LANH_DAO_CAP_TREN': 'Lãnh đạo / Cấp trên',
    'LANH_DAO_CAP_TREN_THAY_TRO': 'Thầy trò',
    'THAM_MUU_TRUONG_DUOI_QUYEN': 'Tham mưu trưởng',
    'CHI_HUY_CHIEN_SI': 'Chiến sĩ',
    'DONG_CHI': 'Đồng chí',
    'LANH_DAO_DONG_CHI': 'Lãnh đạo / Đồng chí',
    'DONG_CHI_COT_CAN': 'Đồng chí cốt cán',
    'DONG_CHI_CHI_HUY': 'Đồng chí / Chỉ huy',
    'HOC_TRO_CONG_SU': 'Cộng sự / Học trò',
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
    'CHONG_DOI_CAP_TREN': 'Chống đối cấp trên',
    'LANH_DAO_BI_CHONG_DOI': 'Bị chống đối',
    'PHE_TRUAT': 'Phế truất',
    'BI_PHE_TRUAT': 'Bị phế truất',
}

# HÀM MỚI: Xử lý định dạng ngày tháng từ YYYY-MM-DD sang DD/MM/YYYY
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

def format_node(node, is_center=False):
    node_id = node.element_id
    node_type = list(node.labels)[0] if node.labels else 'Unknown'
    node_name =  node.get('name') or 'Không tên'
    
    props_table = '<div style="padding: 5px;">'
    props_table += '<table style="border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 12px; border: 1px solid #ddd;">'
    props_table += f'<tr><th colspan="2" style="background-color: #f2f2f2; padding: 8px; border: 1px solid #ddd; text-align: center;">Thông tin {node_type}</th></tr>'
    
    # Danh sách các trường được coi là "thời gian" để mang đi format
    date_fields = ['ngay_sinh', 'ngay_mat', 'start_time', 'end_time', 'signing_date', 'date']

    if node_type == 'NhanVat':
        thuoc_tinh_nhan_vat = {
            'name': 'Tên', 'ngay_sinh': 'Ngày sinh', 'ngay_mat': 'Ngày mất',
            'vai_tro': 'Vai trò', 'noi_sinh': 'Nơi sinh', 'noi_mat': 'Nơi mất', 'quoc_tich': 'Quốc tịch',
        }
        for key, label in thuoc_tinh_nhan_vat.items():
            if key in node and node[key]:
                val = format_vn_date(node[key]) if key in date_fields else node[key]
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{val}</td></tr>'
        
    elif node_type == 'SuKien':
        thuoc_tinh_su_kien = {
            'name': 'Tên', 'start_time': 'Ngày bắt đầu', 'end_time': 'Ngày kết thúc', 'locations': 'Địa điểm'
        }
        for key, label in thuoc_tinh_su_kien.items():
            if key in node and node[key]:
                val = format_vn_date(node[key]) if key in date_fields else node[key]
                # Xử lý riêng cho mảng locations nếu được lưu dạng mảng
                if key == 'locations' and isinstance(node[key], list):
                    val = ', '.join(node[key])
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{val}</td></tr>'

    elif node_type == 'ToChuc':
        thuoc_tinh_to_chuc = {
            'name': 'Tên', 'type': 'Loại tổ chức', 'founded_year': 'Năm thành lập', 'headquarters': 'Trụ sở/Địa bàn'
        }
        for key, label in thuoc_tinh_to_chuc.items():
            if key in node and node[key]:
                val = format_vn_date(node[key]) if key in date_fields else node[key]
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{val}</td></tr>'
    
    elif node_type == 'HiepDinh':   
        thuoc_tinh_hiep_dinh = {
            'name': 'Tên', 'signing_date': 'Ngày ký', 'location': 'Địa điểm ký kết',
        }
        for key, label in thuoc_tinh_hiep_dinh.items():
            if key in node and node[key]:
                val = format_vn_date(node[key]) if key in date_fields else node[key]
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{val}</td></tr>'

    elif node_type == 'QuocGia':
        thuoc_tinh_quoc_gia = {
            'name': 'Tên', 'quoc_tich': 'Quốc tịch', 'capital': 'Thủ đô', 'region': 'Khu vực',
        }
        for key, label in thuoc_tinh_quoc_gia.items():
            if key in node and node[key]:
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{node[key]}</td></tr>'
    
    elif node_type == 'ThoiKy':
        thuoc_tinh_giai_doan = {
            'name': 'Tên giai đoạn', 'start_year': 'Năm bắt đầu', 'end_year': 'Năm kết thúc'
        }
        for key, label in thuoc_tinh_giai_doan.items():
            if key in node and node[key]:
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{node[key]}</td></tr>'
        # Thêm ý nghĩa nhưng cắt bớt nếu quá dài để Popup đỡ bị chật
        if 'y_nghia' in node and node['y_nghia']:
            short_y_nghia = node['y_nghia'][:60] + '...' if len(node['y_nghia']) > 60 else node['y_nghia']
            props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">Ý nghĩa</td><td style="padding: 6px; border: 1px solid #ddd;">{short_y_nghia}</td></tr>'

    else:
        for key, value in node.items():
            if key not in ['id', 'element_id']:
                label = key.replace('_', ' ').capitalize()
                if key == 'name': label = "Tên"
                elif key == 'mo_ta' or key == 'description': label = "Mô tả"
                
                val = format_vn_date(value) if key in date_fields else value
                props_table += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa; white-space: nowrap;">{label}</td><td style="padding: 6px; border: 1px solid #ddd;">{val}</td></tr>'
                
    props_table += '</table></div>'
        
    return {
        'id': node_id,
        'real_id': node.get('id'),
        'label': str(node_name),
        'type': node_type,
        'title': props_table,
        'color': GRAPH_COLORS.get(node_type, '#95a5a6'),
        'size': 35 if is_center else 28,
        'borderWidth': 3 if is_center else 2,
        'font': {'size': 16 if is_center else 14, 'color': '#333', 'weight': 'bold' if is_center else 'normal'},
        'shadow': True
    }

@graph_bp.route('/api/graph/<path:name>')
def get_graph_data(name):
    """Lấy dữ liệu đồ thị - CHỈ lấy node chính và các node liên quan trực tiếp"""
    try:
        with neo4j_service.driver.session() as session:
            query = """
                MATCH (start) WHERE start.name = $name
                OPTIONAL MATCH (start)-[r]-(connected) WHERE connected IS NOT NULL
                RETURN start, collect(DISTINCT connected) as connected_nodes, collect(DISTINCT r) as relationships
            """
            record = session.run(query, {"name": name}).single()
            
            if not record or not record.get("start"):
                return jsonify({"success": False, "error": "Không tìm thấy node", "nodes": [], "edges": []})
            
            main_node = record["start"]
            nodes_dict = {main_node.element_id: format_node(main_node, is_center=True)}
            edges = []
            seen_edges = set()
            
            for node in (record["connected_nodes"] or []):
                if node.element_id not in nodes_dict:
                    nodes_dict[node.element_id] = format_node(node)
                    
            for rel in (record["relationships"] or []):
                from_id, to_id = rel.start_node.element_id, rel.end_node.element_id
                if from_id in nodes_dict and to_id in nodes_dict:
                    edge_key = tuple(sorted([from_id, to_id]))
                    if edge_key not in seen_edges:
                        vietnamese_label = RELATIONSHIP_TRANSLATIONS.get(rel.type, rel.type)
                        edges.append({
                            'from': from_id, 'to': to_id,
                            'label': vietnamese_label, 'arrows': 'to',
                            'font': {'size': 12, 'align': 'middle', 'background': 'white', 'strokeWidth': 2},
                            'color': {'color': '#95a5a6', 'highlight': '#2a5298', 'hover': '#2a5298'},
                            'smooth': {'type': 'continuous', 'roundness': 0.5}, 'width': 2
                        })
                        seen_edges.add(edge_key)
            
            return jsonify({"success": True, "nodes": list(nodes_dict.values()), "edges": edges})
            
    except Exception as e:
        print(f"Graph error: {e}")
        return jsonify({"success": False, "error": str(e), "nodes": [], "edges": []})

@graph_bp.route('/api/graph/person-battles/<path:name>')
def get_person_battles_graph(name):
    """Lấy dữ liệu đồ thị cho nhân vật và các trận chiến liên quan """
    try:
        with neo4j_service.driver.session() as session:
            query = """
                MATCH (p:NhanVat) 
                WHERE toLower(toString(p.name)) CONTAINS toLower(toString($name))
                OPTIONAL MATCH (p)-[r]-(e:SuKien) WHERE toLower(toString(e.name)) CONTAINS 'trận' OR toLower(toString(e.name)) CONTAINS 'chiến dịch'
                RETURN p, collect(DISTINCT e) as battles
            """
            record = session.run(query, {"name": name}).single()
            if not record or not record.get("p"):
                return jsonify({"success": False, "nodes": [], "edges": []})
            
            nodes_dict = {}
            edges = []
            
            person = record["p"]
            nodes_dict[person.element_id] = format_node(person, is_center=True)
            
            battles = [b for b in record["battles"] if b]
            for battle in battles:
                b_id = battle.element_id
                if b_id not in nodes_dict:
                    nodes_dict[b_id] = format_node(battle)
                edges.append({'from': person.element_id, 'to': b_id, 'label': 'THAM_GIA', 'arrows': 'to'})
            
            return jsonify({"success": True, "nodes": list(nodes_dict.values()), "edges": edges})
            
    except Exception as e:
        print(f"Graph error: {e}")
        return jsonify({"success": False, "nodes": [], "edges": []})
    
