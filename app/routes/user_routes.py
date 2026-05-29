import os
import urllib.parse
from flask import Blueprint, render_template, jsonify, request
from flask.cli import load_dotenv
from app.services.cypher_queries import CypherQueries
from app.services.neo4j_service import Neo4jService
import unicodedata
import re
from groq import Groq
import json
from app.routes.graph_routes import RELATIONSHIP_TRANSLATIONS

load_dotenv()

user_bp = Blueprint('user', __name__)
neo4j_service = Neo4jService()

# ==================== FILTER FUNCTIONS ====================

@user_bp.app_template_filter('urlencode')
def urlencode_filter(s):
    import urllib.parse
    return urllib.parse.quote(s) if s else ''

@user_bp.app_template_filter('slugify')
def slugify_filter(value):
    if not value: return ''
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(c for c in value if not unicodedata.combining(c)).lower()
    value = value.replace('đ', 'd')
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')

# ==================== MAIN PAGES & NATURAL QUERY ====================
@user_bp.route('/')
def index():
    return render_template('index.html')

@user_bp.route('/tracuu')
def tracuu():
    return render_template('tracuu.html')

def build_network_graph(center_name, center_type, target_type, items, target_key, rel_key, default_rel):
    """Hàm generic xây dựng đồ thị cho Q&A có hỗ trợ hover Popup, link chuyển trang và dịch tiếng Việt"""
    colors = {'NhanVat': '#e74c3c', 'SuKien': '#f39c12', 
              'ToChuc': '#3498db', 'HiepDinh': '#9b59b6', 'QuocGia': '#9bafaa', 'ThoiKy': "#87ac0f"}  
    graph = {"nodes": [], "edges": []}
    node_ids = set()
    
    # Map type sang slug URL để click chuyển trang
    type_to_url = {
        'NhanVat': 'person', 'SuKien': 'event', 'ToChuc': 'organization', 
        'HiepDinh': 'treaty', 'QuocGia': 'country', 'ThoiKy': 'period'
    }

    # Hàm nội bộ để tạo HTML Tooltip (title) giả lập giống format_node
    def build_tooltip(name, entity_type, extra_info=None, extra_label="Thông tin phụ"):
        html = '<div style="padding: 5px;">'
        html += '<table style="border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 12px; border: 1px solid #ddd;">'
        html += f'<tr><th colspan="2" style="background-color: #f2f2f2; padding: 8px; border: 1px solid #ddd; text-align: center;">Thông tin {entity_type}</th></tr>'
        html += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa;">Tên</td><td style="padding: 6px; border: 1px solid #ddd;">{name}</td></tr>'
        if extra_info:
            html += f'<tr><td style="padding: 6px; border: 1px solid #ddd; font-weight: bold; background: #fafafa;">{extra_label}</td><td style="padding: 6px; border: 1px solid #ddd;">{extra_info}</td></tr>'
        html += '</table></div>'
        return html

    # Xác định chính xác tên Node trung tâm
    if items:
        if center_type == 'SuKien': center_name = items[0].get('battle_name', center_name)
        elif center_type == 'ToChuc': center_name = items[0].get('org_name', center_name)
        elif center_type == 'NhanVat': center_name = items[0].get('person_name', center_name) 
        elif center_type == 'ThoiKy': center_name = items[0].get('period_name', center_name)
        elif center_type == 'HiepDinh': center_name = items[0].get('treaty_name', center_name)
        elif center_type == 'QuocGia': center_name = items[0].get('country_name', center_name)
    
    # Tạo node trung tâm
    center_slug_url = f"/{type_to_url.get(center_type, 'person')}/detail/{urllib.parse.quote(center_name)}"
    graph["nodes"].append({
        'id': center_name, 
        'label': center_name, 
        'type': center_type, 
        'color': colors.get(center_type), 
        'size': 35, 
        'font': {'size': 16, 'weight': 'bold'},
        'title': build_tooltip(center_name, center_type),
        'url': center_slug_url
    })
    node_ids.add(center_name)
    
    for item in items:
        target_name = item.get(target_key)
        if target_name and target_name not in node_ids:
            target_slug_url = f"/{type_to_url.get(target_type, 'person')}/detail/{urllib.parse.quote(target_name)}"
            
            # Lấy thêm thông tin phụ
            extra_info = item.get('person_role') or item.get('time') or item.get('description') or ""
            extra_label = "Vai trò" if target_type == "NhanVat" else "Chi tiết"

            graph["nodes"].append({
                'id': target_name, 
                'label': target_name, 
                'type': target_type, 
                'color': colors.get(target_type), 
                'size': 28,
                'title': build_tooltip(target_name, target_type, str(extra_info)[:100] + "..." if len(str(extra_info)) > 100 else extra_info, extra_label),
                'url': target_slug_url
            })
            node_ids.add(target_name)
            
            # Xử lý Label (Nhãn trên mũi tên)
            raw_rel = item.get('relation', '')
            vietnamese_label = RELATIONSHIP_TRANSLATIONS.get(raw_rel, item.get(rel_key, default_rel))

            # --- ĐỊNH HƯỚNG MŨI TÊN CHUẨN XÁC ---
            from_node = center_name
            to_node = target_name

            # Quy tắc 1: Nhân vật là chủ thể hành động -> trỏ tới các thực thể khác
            if center_type == target_type:
                pass 
            # Quy tắc 1: Nhân vật là chủ thể hành động -> trỏ tới các thực thể khác
            elif target_type == 'NhanVat':
                from_node, to_node = target_name, center_name
            # Quy tắc 2: Sự kiện luôn trỏ về Thời kỳ (SuKien -[THUOC_THOI_KY]-> ThoiKy)
            elif center_type == 'ThoiKy' and target_type == 'SuKien':
                from_node, to_node = target_name, center_name
            # Quy tắc 3: Tổ chức là chủ thể -> trỏ tới Sự kiện / Hiệp định
            elif target_type == 'ToChuc' and center_type in ['SuKien', 'HiepDinh']:
                from_node, to_node = target_name, center_name

            graph["edges"].append({
                'from': from_node, 
                'to': to_node, 
                'label': vietnamese_label, 
                'arrows': 'to'
            })
                
    return graph

# ==================== HÀM FIX LỖI JSON DATETIME ====================
def parse_neo4j_data(data):
    """Hàm đệ quy xử lý các object của Neo4j (DateTime, Date, Node) sang kiểu Python chuẩn để jsonify không bị lỗi"""
    if data is None:
        return None
    # Xử lý các object có chứa thời gian
    if hasattr(data, 'isoformat'):
        return data.isoformat()
    if isinstance(data, list):
        return [parse_neo4j_data(item) for item in data]
    if isinstance(data, dict):
        return {key: parse_neo4j_data(value) for key, value in data.items()}
    # Xử lý nếu data trả về là một Neo4j Node nguyên bản thay vì các field
    if hasattr(data, 'items') and hasattr(data, 'labels'):
        return {key: parse_neo4j_data(value) for key, value in dict(data).items()}
    # Nếu là các object khác không thể serialize, ép kiểu về string
    if not isinstance(data, (str, int, float, bool, type(None))):
        return str(data)
    return data
# ===================================================================

QUERY_DISPATCHER = {
    # --- Các truy vấn phức tạp (trả về danh sách/nhiều dữ liệu) ---
    "person_battles": CypherQueries.get_person_battles,
    "battle_participants": CypherQueries.get_battle_participants,
    "organization_members": CypherQueries.get_organization_members,
    "person_organizations": CypherQueries.get_person_organizations,
    "period_events": CypherQueries.get_period_events,
    "person_related_entities": CypherQueries.get_person_related_entities,
    "event_related_entities": CypherQueries.get_event_related_entities,
    "treaty_participants": CypherQueries.get_treaty_participants,
    "person_relations": CypherQueries.get_person_relations,
    "event_relations": CypherQueries.get_event_relations,
    
    # --- Các hàm lấy thông tin chi tiết (Lấy node cụ thể) ---
    "event_time": lambda name: CypherQueries.get_entity_detail("SuKien", "name", name),
    "person_info": lambda name: CypherQueries.get_entity_detail("NhanVat", "name", name),
    "event_location": lambda name: CypherQueries.get_event_location(name),
    "event_cause_result": lambda name: CypherQueries.get_event_cause_result(name),
    "period_info": lambda name: CypherQueries.get_entity_detail("ThoiKy", "name", name),
    "treaty_info": lambda name: CypherQueries.get_entity_detail("HiepDinh", "name", name),
    "organization_info": lambda name: CypherQueries.get_entity_detail("ToChuc", "name", name),
    "country_info": lambda name: CypherQueries.get_entity_detail("QuocGia", "name", name),
    
    # --- Các hàm tìm kiếm/QA chung ---
    "general_qa": CypherQueries.search_all_attributes,
    "search": CypherQueries.search_by_keyword
}

@user_bp.route('/api/query/natural')
def query_natural():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"success": False, "error": "Vui lòng nhập câu hỏi"})
    
    try:
        # 1. AI phân tích intent
        parsed = CypherQueries.parse_natural_query(q)
        intent = parsed.get("type")
        param_keys = [k for k in parsed.keys() if k != "type"]
        param_val = parsed.get(param_keys[0]) if param_keys else q
        
        # 2. Thực thi truy vấn qua Dispatcher
        query_func = QUERY_DISPATCHER.get(intent)
        if not query_func:
            return jsonify({"success": False, "error": f"Intent '{intent}' chưa được cấu hình."})
        
        with neo4j_service.driver.session() as session:
            query_str = query_func(param_val) if callable(query_func) else query_func
            raw_data = session.run(query_str, {"name": param_val, "keyword": param_val})
            results = parse_neo4j_data([dict(r) for r in raw_data])
            
        # 3. Kiểm tra dữ liệu (Early Return nếu không có kết quả)
        if not results:
            return jsonify({
                "success": True,
                "answer": "Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở dữ liệu lịch sử.",
                "data": [],
                "graph": {"nodes": [], "edges": []}
            })

        # 4. Tạo đồ thị (Graph Data) - Tự động hóa dựa trên intent
        # Bạn có thể mở rộng logic này để build đồ thị cho nhiều intent hơn
        graph_data = {"nodes": [], "edges": []}
        if intent == "person_battles":
            graph_data = build_network_graph(param_val, 'NhanVat', 'SuKien', results, 'battle_name', 'role', 'Tham gia')
        elif intent == "battle_participants":
            graph_data = build_network_graph(param_val, 'SuKien', 'NhanVat', results, 'person_name', 'role', 'Tham gia')
        elif intent == "organization_members":
            # Đổi 'role' -> 'role_name' cho chuẩn với get_organization_members
            graph_data = build_network_graph(param_val, 'ToChuc', 'NhanVat', results, 'person_name', 'role_name', 'Thành viên')
        elif intent == "person_organizations":
            graph_data = build_network_graph(param_val, 'NhanVat', 'ToChuc', results, 'org_name', 'relation_name', 'Tham gia')
        elif intent == "period_events":
            # Đổi 'result' -> 'relation' để lấy đúng nhãn "Thuộc thời kỳ"
            graph_data = build_network_graph(param_val, 'ThoiKy', 'SuKien', results, 'event_name', 'relation', 'Thuộc thời kỳ')
        elif intent == "treaty_participants":
            graph_data = build_network_graph(param_val, 'HiepDinh', 'NhanVat', results, 'person_name', 'role', 'Tham gia ký')
        elif intent == "person_relations":
            graph_data = build_network_graph(param_val, 'NhanVat', 'NhanVat', results, 'related_person', 'relation_name', 'Liên quan')
        elif intent == "event_relations":
            graph_data = build_network_graph(param_val, 'SuKien', 'SuKien', results, 'related_event', 'relation_name', 'Liên quan')
        
        # Bỏ qua vẽ đồ thị nếu chỉ có 1 node (Không có cạnh nối)
        if len(graph_data.get("nodes", [])) <= 1:
            graph_data = {"nodes": [], "edges": []}

        # 5. Sử dụng Groq AI để viết câu trả lời tự nhiên
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        prompt = f"""
        Bạn là một chuyên gia lịch sử Việt Nam. 
        Người dùng hỏi: "{q}"
        Dữ liệu từ database: {json.dumps(results, ensure_ascii=False)}
        Nhiệm vụ: Trả lời ngắn gọn, đúng trọng tâm bằng Markdown.
        """
        
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant", 
            )
            natural_answer = chat_completion.choices[0].message.content
        except Exception:
            natural_answer = generate_fallback_answer(results, q, intent)

        return jsonify({
            "success": True, 
            "query": q, 
            "answer": natural_answer,
            "data": results,
            "graph": graph_data
        })
        
    except Exception as e:
        print(f">>> LỖI API Natural: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

def generate_fallback_answer(results, question, intent=None):
    """Tạo câu trả lời thủ công khi AI bị lỗi"""
    if not results:
        return "Xin lỗi, tôi không tìm thấy thông tin phù hợp."
    
    answer_parts = []
    
    # Xử lý theo intent để biết cách parse results
    if intent == "person_battles":
        answer_parts.append(f"**Các trận chiến/sự kiện tham gia:**")
        for item in results[:10]:
            battle_name = item.get('battle_name', 'Không rõ')
            role = item.get('role', 'Tham gia')
            time = item.get('time', '')
            answer_parts.append(f"- {battle_name} ({role})" + (f" - {time}" if time else ""))
    
    elif intent == "battle_participants":
        battle_name = results[0].get('battle_name', 'sự kiện') if results else 'sự kiện'
        answer_parts.append(f"**Những người tham gia {battle_name}:**")
        for item in results[:10]:
            person_name = item.get('person_name', 'Không rõ')
            role = item.get('role', 'Tham gia')
            answer_parts.append(f"- {person_name} ({role})")
    
    elif intent == "organization_members":
        org_name = results[0].get('org_name', 'tổ chức') if results else 'tổ chức'
        answer_parts.append(f"**Thành viên của {org_name}:**")
        for item in results[:10]:
            person_name = item.get('person_name', 'Không rõ')
            role = item.get('role_name', 'Thành viên')
            answer_parts.append(f"- {person_name} ({role})")
    
    elif intent == "person_organizations":
        person_name = results[0].get('person_name', 'người này') if results else 'người này'
        answer_parts.append(f"**Các tổ chức {person_name} tham gia:**")
        for item in results:
            org_name = item.get('org_name', 'Không rõ')
            relation = item.get('relation_name', 'Tham gia')
            answer_parts.append(f"- {org_name} ({relation})")
    
    elif intent in ["person_info", "event_info", "period_info", "treaty_info", "organization_info", "country_info"]:
        # Các intent lấy thông tin chi tiết thường trả về 1 record
        if results:
            item = results[0]
            # Lấy tên từ bất kỳ key nào có chứa 'name'
            name = next((v for k, v in item.items() if 'name' in k.lower() and v), 'Không rõ')
            answer_parts.append(f"**{name}**")
            
            # Hiển thị tất cả các trường có dữ liệu
            for key, value in item.items():
                if value and key not in ['name', 'type'] and not key.startswith('_'):
                    # Format key cho dễ đọc
                    display_key = key.replace('_', ' ').title()
                    if isinstance(value, str) and len(value) > 200:
                        value = value[:200] + '...'
                    answer_parts.append(f"- **{display_key}**: {value}")
    
    elif intent == "period_events":
        period_name = results[0].get('period_name', 'thời kỳ này') if results else 'thời kỳ này'
        answer_parts.append(f"**Các sự kiện trong {period_name}:**")
        for item in results[:10]:
            event_name = item.get('event_name', 'Không rõ')
            start_time = item.get('start_time', '')
            result = item.get('result', '')
            answer_parts.append(f"- {event_name}" + (f" ({start_time})" if start_time else "") + (f" - Kết quả: {result}" if result else ""))
    
    elif intent == "event_location":
        if results:
            item = results[0]
            event_name = item.get('event_name', 'Sự kiện')
            locations = item.get('locations', 'Chưa rõ địa điểm')
            answer_parts.append(f"**Địa điểm diễn ra {event_name}:** {locations}")
    
    elif intent == "event_cause_result":
        if results:
            item = results[0]
            event_name = item.get('event_name', 'Sự kiện')
            answer_parts.append(f"**{event_name}**")
            if item.get('nguyen_nhan'):
                answer_parts.append(f"- **Nguyên nhân**: {item['nguyen_nhan'][:300]}...")
            if item.get('dien_bien'):
                answer_parts.append(f"- **Diễn biến**: {item['dien_bien'][:300]}...")
            if item.get('ket_qua'):
                answer_parts.append(f"- **Kết quả**: {item['ket_qua'][:300]}...")
            if item.get('y_nghia'):
                answer_parts.append(f"- **Ý nghĩa**: {item['y_nghia'][:300]}...")
    
    elif intent == "general_qa" or intent == "search":
        answer_parts.append(f"**Kết quả tìm kiếm:**")
        for item in results[:10]:
            item_name = item.get('name', 'Không rõ')
            item_type = item.get('type', 'Không rõ') if 'type' in item else ''
            answer_parts.append(f"- **{item_name}** {f'({item_type})' if item_type else ''}")
            
            # Hiển thị thêm thông tin nếu có
            for field in ['cuoc_doi', 'dien_bien', 'y_nghia', 'ket_qua', 'nguyen_nhan']:
                if item.get(field):
                    value = item[field][:200] + '...' if len(str(item[field])) > 200 else item[field]
                    answer_parts.append(f"  - {field.replace('_', ' ').title()}: {value}")
                    break  # Chỉ hiển thị 1 field dài nhất
    
    if not answer_parts:
        return f"Tôi tìm thấy một số dữ liệu liên quan đến '{question}', nhưng không thể hiển thị chi tiết."
    
    return "\n".join(answer_parts)

# ==================== API_FULL_QUERIES - CẬP NHẬT ĐẦY ĐỦ THÔNG TIN ====================
API_FULL_QUERIES = {
    'persons': CypherQueries.get_all_persons(),
    'organizations': CypherQueries.get_all_organizations(),
    'events': CypherQueries.get_all_events(),
    'treaties': CypherQueries.get_all_treaties(),
    'countries': CypherQueries.get_all_countries(),
    'periods': CypherQueries.get_all_periods()
}

# ==================== ROUTE GỘP CHO CÁC TRANG LIST ====================
@user_bp.route('/<entity_type>/list')
def generic_list(entity_type):
    """Gộp routes danh sách và truyền dữ liệu trực tiếp vào Template (SSR)"""
    valid_types = ['person', 'event', 'organization', 'treaty', 'country', 'period']
    if entity_type not in valid_types:
        return "Không tìm thấy", 404

    with neo4j_service.driver.session() as session:
        if entity_type == 'person':
            periods = parse_neo4j_data([dict(r) for r in session.run(CypherQueries.get_persons_by_period())])
            return render_template('person/list.html', periods=periods)
        elif entity_type == 'event':
            events = parse_neo4j_data([dict(r) for r in session.run(CypherQueries.get_all_events())])
            return render_template('event/list.html', events=events)

    return render_template(f'{entity_type}/list.html')


# ==================== ROUTE GỘP CHO CÁC TRANG CHI TIẾT ====================
@user_bp.route('/<entity_type>/detail/<path:name>')
def generic_detail(entity_type, name):
    """Định tuyến các trang chi tiết tùy theo thực thể (Cập nhật full Relationships)"""
    with neo4j_service.driver.session() as session:
        params = {"name": name.lower()}
        
        if entity_type == 'person':
            p = session.run("MATCH (p:NhanVat) WHERE toLower(p.name) = $name RETURN p", params).single()
            if not p: return "Không tìm thấy", 404
            
            exact_name = dict(p["p"]).get('name')
            
            events = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (p:NhanVat)-[r]-(e:SuKien) 
                WHERE p.name = $exact_name 
                RETURN e.name as name, e.start_time as start_time, e.end_time as end_time, 
                       e.ket_qua as ket_qua, type(r) as relation,
                       CASE type(r)
                           WHEN 'CHI_HUY' THEN 'Chỉ huy'
                           WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                           WHEN 'THAM_GIA' THEN 'Tham gia'
                           WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                           ELSE type(r)
                       END as role
                ORDER BY e.start_time
            """, {"exact_name": exact_name})])
            
            orgs = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (p:NhanVat)-[r]-(o:ToChuc) 
                WHERE p.name = $exact_name 
                RETURN o.name as name, o.type as type, o.founded_year as founded_year,
                    CASE type(r)
                        WHEN 'THUOC_VE' THEN 'Thành viên'
                        WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'SANG_LAP' THEN 'Sáng lập'
                        ELSE type(r)
                    END as role
            """, {"exact_name": exact_name})])
            
            countries = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (p:NhanVat)-[r]-(c:QuocGia) 
                WHERE p.name = $exact_name 
                RETURN c.name as name, type(r) as relation,
                    CASE type(r)
                        WHEN 'DAI_DIEN_CHO' THEN 'Đại diện cho'
                        WHEN 'DUNG_DAU' THEN 'Lãnh đạo'
                        WHEN 'THUOC_QUOC_GIA' THEN 'Thuộc quốc gia'
                        ELSE type(r)
                    END as role
            """, {"exact_name": exact_name})])
            
            return render_template('person/detail.html', person=dict(p["p"]), events=events, organizations=orgs, countries=countries)
            
        elif entity_type == 'event':
            e = session.run("MATCH (e:SuKien) WHERE toLower(e.name) = $name RETURN e", params).single()
            if not e: return "Không tìm thấy", 404
            
            exact_name = dict(e["e"]).get('name')
            
            persons = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (e:SuKien)-[r]-(p:NhanVat) 
                WHERE e.name = $exact_name
                RETURN p.name as name, p.vai_tro as vai_tro, type(r) as relation,
                    CASE type(r)
                        WHEN 'CHI_HUY' THEN 'Chỉ huy'
                        WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                        ELSE type(r)
                    END as role
            """, {"exact_name": exact_name})])

            periods = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (e:SuKien)-[r:THUOC_THOI_KY]->(g:ThoiKy) 
                WHERE e.name = $exact_name
                RETURN g.name as name, g.start_year as start_year, g.end_year as end_year
            """, {"exact_name": exact_name})])
        
            orgs = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (o:ToChuc)-[r]-(e:SuKien)
                WHERE e.name = $exact_name
                RETURN o.name as name, o.type as type, o.founded_year as founded_year, 
                    CASE type(r)
                        WHEN 'THAM_GIA_SU_KIEN' THEN 'Tham gia'
                        WHEN 'TO_CHUC' THEN 'Tổ chức'
                        ELSE type(r)
                    END as role
            """, {"exact_name": exact_name})])
            return render_template('event/detail.html', event=dict(e["e"]), persons=persons, organizations=orgs, periods=periods)
            
        elif entity_type == 'organization':
            o = session.run("MATCH (o:ToChuc) WHERE toLower(o.name) = $name RETURN o", params).single()
            if not o: return "Không tìm thấy", 404
            exact_name = dict(o["o"]).get('name') 
            
            members = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (p:NhanVat)-[r]-(o:ToChuc) 
                WHERE o.name = $exact_name 
                RETURN p.name as name, p.vai_tro as vai_tro, p.chuc_vu as chuc_vu,
                    CASE type(r)
                        WHEN 'THUOC_VE' THEN 'Thành viên'
                        WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'SANG_LAP' THEN 'Người sáng lập'
                        ELSE type(r)
                    END as role
            """, {"exact_name": exact_name})])
            
            countries = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (o:ToChuc)-[r]-(c:QuocGia)
                WHERE o.name = $exact_name
                RETURN c.name as name, c.cap_do as cap_do,
                    CASE type(r)
                        WHEN 'DAI_DIEN_CHO' THEN 'Đại diện cho'
                        WHEN 'DUNG_DAU' THEN 'Lãnh đạo'
                        WHEN 'THUOC_QUOC_GIA' THEN 'Trực thuộc'
                        WHEN 'HO_TRO' THEN 'Hỗ trợ'
                        ELSE type(r)
                    END as role
            """, {"exact_name": exact_name})])
            return render_template('organization/detail.html', organization=dict(o["o"]), members=members, countries=countries)

        elif entity_type == 'treaty':
            t = session.run("MATCH (t:HiepDinh) WHERE toLower(t.name) = $name RETURN t", params).single()
            if not t: return "Không tìm thấy", 404
            exact_name = dict(t["t"]).get('name') 

            # Lấy người ký, quốc gia tham gia và sự kiện liên quan của Hiệp Định
            persons = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (t:HiepDinh)-[r]-(p:NhanVat) WHERE t.name = $exact_name 
                RETURN p.name as name, CASE type(r) WHEN 'KY_KET' THEN 'Người ký' WHEN 'DAM_PHAN' THEN 'Người đàm phán' ELSE type(r) END as role
            """, {"exact_name": exact_name})])

            countries = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (t:HiepDinh)-[r]-(c:QuocGia) WHERE t.name = $exact_name 
                RETURN c.name as name, CASE type(r) WHEN 'THAM_GIA_KY' THEN 'Tham gia ký kết' ELSE type(r) END as role
            """, {"exact_name": exact_name})])

            events = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (t:HiepDinh)-[r]-(e:SuKien) WHERE t.name = $exact_name 
                RETURN e.name as name, e.start_time as start_time, CASE type(r) WHEN 'KET_THUC_SU_KIEN' THEN 'Kết thúc sự kiện' ELSE type(r) END as role
            """, {"exact_name": exact_name})])

            return render_template('treaty/detail.html', treaty=dict(t["t"]), persons=persons, countries=countries, events=events)
            
        elif entity_type == 'country':
            c = session.run("MATCH (c:QuocGia) WHERE toLower(c.name) = $name RETURN c", params).single()
            if not c: return "Không tìm thấy", 404
            exact_name = dict(c["c"]).get('name') 

            # Lấy lãnh đạo, sự kiện và tổ chức của Quốc gia
            persons = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (c:QuocGia)-[r]-(p:NhanVat) WHERE c.name = $exact_name 
                RETURN p.name as name, CASE type(r) WHEN 'DUNG_DAU' THEN 'Lãnh đạo' WHEN 'DAI_DIEN_CHO' THEN 'Đại diện' ELSE type(r) END as role
            """, {"exact_name": exact_name})])

            events = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (c:QuocGia)-[r]-(e:SuKien) WHERE c.name = $exact_name 
                RETURN e.name as name, e.start_time as start_time, CASE type(r) WHEN 'THAM_GIA' THEN 'Tham gia' WHEN 'KHOI_XUONG' THEN 'Khởi xướng' ELSE type(r) END as role
            """, {"exact_name": exact_name})])

            orgs = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (c:QuocGia)-[r]-(o:ToChuc) WHERE c.name = $exact_name 
                RETURN o.name as name, CASE type(r) WHEN 'THUOC_QUOC_GIA' THEN 'Tổ chức trực thuộc' ELSE type(r) END as role
            """, {"exact_name": exact_name})])

            return render_template('country/detail.html', country=dict(c["c"]), persons=persons, events=events, organizations=orgs)
            
        elif entity_type == 'period':
            g = session.run("MATCH (g:ThoiKy) WHERE toLower(g.name) = $name RETURN g", params).single()
            if not g: return "Không tìm thấy", 404
            
            exact_name = dict(g["g"]).get('name')
            
            events = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (e:SuKien)-[r:THUOC_THOI_KY]-(g:ThoiKy) 
                WHERE g.name = $exact_name 
                RETURN e.name as name, e.start_time as start_time, e.end_time as end_time, e.locations as locations
                ORDER BY e.start_time
            """, {"exact_name": exact_name})])

            persons = parse_neo4j_data([dict(r) for r in session.run("""
                MATCH (p:NhanVat)-[r:THUOC_THOI_KY]->(g:ThoiKy)
                WHERE g.name = $exact_name
                RETURN p.name as name, p.vai_tro as vai_tro
                ORDER BY p.name
            """, {"exact_name": exact_name})])

            return render_template('period/detail.html', period=dict(g["g"]), events=events, persons=persons)

        return "Không tìm thấy", 404

# ==================== API LẤY FULL DANH SÁCH ====================
@user_bp.route('/api/<entity_type>/full')
def api_entities_full(entity_type):
    """Gộp API lấy Full danh sách thành 1 API động duy nhất"""
    if entity_type not in API_FULL_QUERIES:
        return jsonify({"success": False, "error": "Invalid entity type"}), 400
        
    try:
        with neo4j_service.driver.session() as session:
            result = session.run(API_FULL_QUERIES[entity_type])
            return jsonify({
                "success": True,
                entity_type: [parse_neo4j_data(dict(record)) for record in result]
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== API THỐNG KÊ, TÌM KIẾM, GỢI Ý ====================
@user_bp.route('/api/stats')
def get_stats():
    try:
        with neo4j_service.driver.session() as session:
            stats = {r["type"]: r["count"] for r in session.run("MATCH (n) RETURN labels(n)[0] as type, count(n) as count")}
            stats["relations"] = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@user_bp.route('/api/search')
def search():
    keyword = request.args.get('q', '')
    if len(keyword) < 2: return jsonify({"success": True, "results": []})
    try:
        with neo4j_service.driver.session() as session:
            results = [dict(r) for r in session.run(CypherQueries.search_by_keyword(keyword))]
        return jsonify({"success": True, "results": parse_neo4j_data(results)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@user_bp.route('/api/suggestions')
def get_suggestions():
    keyword = request.args.get('q', '').strip()
    if len(keyword) < 2: return jsonify({"success": True, "suggestions": []})
    try:
        with neo4j_service.driver.session() as session:
            query = """
                MATCH (n) 
                WHERE toLower(n.name) CONTAINS toLower($k) 
                RETURN CASE WHEN n.name IS NOT NULL THEN n.name ELSE n.name END as name, 
                       labels(n)[0] as type 
                LIMIT 10
            """
            suggestions = [dict(r) for r in session.run(query, {"k": keyword})]
        return jsonify({"success": True, "suggestions": parse_neo4j_data(suggestions)})
    except Exception as e:
        return jsonify({"success": False, "suggestions": []})