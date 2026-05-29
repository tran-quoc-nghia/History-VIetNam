"""
Thư viện các truy vấn Cypher mẫu cho hệ thống hỏi đáp lịch sử
"""
import json
from groq import Groq
import os

class CypherQueries:
    """Lớp chứa các truy vấn Cypher và xử lý câu hỏi tự nhiên bằng AI"""
    
    # ==================== XỬ LÝ CÂU HỎI TỰ NHIÊN BẰNG GEMINI/GROQ ====================
    @staticmethod
    def parse_natural_query(query_text):
        """Dùng Groq AI để phân tích ý định câu hỏi"""
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            
            prompt = f"""
            Phân tích câu hỏi lịch sử sau: "{query_text}"
            
            Nhiệm vụ: Xác định loại câu hỏi (type) và trích xuất từ khóa chính.
            Các loại (type) hợp lệ và key tương ứng: 
            - "person_battles": Hỏi nhân vật này tham gia trận nào (Key: "person_name")
            - "battle_participants": Hỏi ai tham gia trận này/sự kiện này (Key: "battle_name")
            - "organization_members": Hỏi ai ở trong tổ chức này (Key: "org_name")
            - "person_organizations": Hỏi nhân vật này tham gia tổ chức nào (Key: "person_name")
            - "event_time": Hỏi sự kiện diễn ra khi nào (Key: "event_name")
            - "event_location": Hỏi sự kiện diễn ra ở đâu (Key: "event_name")
            - "event_cause_result": Hỏi nguyên nhân, kết quả, ý nghĩa sự kiện (Key: "event_name")
            - "person_info": Hỏi thông tin, tiểu sử, cuộc đời, gia đình, HOẶC BẤT KỲ CHI TIẾT CỤ THỂ NÀO VỀ NHÂN VẬT (ví dụ: bị bắt, học ở đâu, mất năm nào) (Key: "person_name")
            - "treaty_participants": Hỏi những ai/quốc gia nào tham gia ký kết hiệp định (Key: "treaty_name")
            - "period_events": Hỏi về các sự kiện trong một thời kỳ/giai đoạn (Key: "period_name")
            - "period_info": Hỏi thông tin chi tiết về một thời kỳ (mô tả, ý nghĩa, năm bắt đầu, năm kết thúc) (Key: "period_name")
            - "treaty_info": Hỏi thông tin về một hiệp định (nội dung, ngày ký, ý nghĩa) (Key: "treaty_name")
            - "organization_info": Hỏi thông tin về một tổ chức (loại hình, năm thành lập, vai trò) (Key: "org_name")
            - "country_info": Hỏi thông tin về một quốc gia (thủ đô, khu vực, mô tả) (Key: "country_name")
            - "general_qa": Hỏi các chi tiết cụ thể nằm trong mô tả, diễn biến, cuộc đời, kết quả, ý nghĩa (Key: "keyword")
            - "person_relations": Hỏi về mối quan hệ của nhân vật này với các nhân vật khác (ai là kẻ thù, đồng đội, vợ/chồng, cha con) (Key: "person_name")
            - "event_relations": Hỏi sự kiện này liên quan/dẫn đến/là tiền đề/là kết quả của sự kiện nào khác (Key: "event_name")
            - "search": Nếu không thuộc các loại trên (Key: "keyword")
            
            Quy tắc bắt buộc:
            1. Tự động sửa lỗi chính tả, viết hoa đúng chuẩn tên riêng.
            2. Trả về DUY NHẤT một chuỗi JSON hợp lệ theo định dạng.
            
            Ví dụ:
            - Hỏi 'võ thị sáu bị bắt khi nào': {{"type": "person_info", "person_name": "Võ Thị Sáu"}}
            - Hỏi 'đại tướng võ nguyên giáp có mấy người con': {{"type": "person_info", "person_name": "Võ Nguyên Giáp"}}
            - Hỏi 'ai tham gia chiến dịch điện biên phủ': {{"type": "battle_participants", "battle_name": "Điện Biên Phủ"}}
            - Hỏi 'thời kỳ phong kiến độc lập có ý nghĩa gì': {{"type": "period_info", "period_name": "Thời kỳ Phong kiến độc lập"}}
            - Hỏi 'hiệp định paris được ký khi nào': {{"type": "treaty_info", "treaty_name": "Hiệp định Paris"}}
            - Hỏi 'đảng cộng sản việt nam ra đời năm bao nhiêu': {{"type": "organization_info", "org_name": "Đảng Cộng sản Việt Nam"}}
            - Hỏi 'ai đã đọc bản tuyên ngôn độc lập': {{"type": "general_qa", "keyword": "tuyên ngôn độc lập"}}
            - Hỏi 'bác hồ ra đi tìm đường cứu nước ở bến cảng nào': {{"type": "general_qa", "keyword": "tìm đường cứu nước"}}
            - Hỏi 'ai là đối thủ của lý thường kiệt': {{"type": "person_relations", "person_name": "Lý Thường Kiệt"}}
            - Hỏi 'sự kiện nào là tiền đề cho chiến dịch điện biên phủ': {{"type": "event_relations", "event_name": "Điện Biên Phủ"}}
            """
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Bạn là hệ thống trích xuất dữ liệu. Luôn luôn trả về định dạng JSON hợp lệ."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.1-8b-instant", 
                temperature=0.1,
                response_format={"type": "json_object"} 
            )
            
            response_text = chat_completion.choices[0].message.content
            parsed_data = json.loads(response_text)
            
            print(f">>> Groq parsed: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            print(">>> Lỗi phân tích Intent Groq:", str(e))
            words = query_text.split()
            fallback_keyword = " ".join(words[:3]) if len(words) >= 3 else query_text
            return {"type": "search", "keyword": fallback_keyword}
    
    # ==================== TRUY VẤN NEO4J DÀNH CHO Q&A CHATBOT ====================
    
    @staticmethod
    def get_person_battles(person_name):
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) CONTAINS toLower($name) 
               OR toLower(p.ten_day_du) CONTAINS toLower($name)
            MATCH (p)-[r]-(e:SuKien)
            RETURN 
                p.name as person_name,
                e.name as battle_name,
                e.start_time as time,
                e.end_time as end_time,
                e.description as description,
                e.ket_qua as result,
                type(r) as relation,
                CASE type(r)
                    WHEN 'CHI_HUY' THEN 'Chỉ huy'
                    WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                    WHEN 'THAM_GIA' THEN 'Tham gia'
                    WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                    ELSE type(r)
                END as role
            ORDER BY e.start_time
        """

    @staticmethod
    def get_battle_participants(battle_name):
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) CONTAINS toLower($name)
            OPTIONAL MATCH (p:NhanVat)-[r]-(e)
            RETURN 
                e.name as battle_name,
                e.start_time as time,
                e.description as description,
                p.name as person_name,
                p.vai_tro as person_role,
                type(r) as relation,
                CASE type(r)
                    WHEN 'CHI_HUY' THEN 'Chỉ huy'
                    WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                    WHEN 'THAM_GIA' THEN 'Tham gia'
                    WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                    ELSE type(r)
                END as role
            ORDER BY 
                CASE WHEN type(r) = 'CHI_HUY' THEN 1 
                     WHEN type(r) = 'CHI_DAO' THEN 2 
                     WHEN type(r) = 'THAM_GIA' THEN 3
                     WHEN type(r) = 'KHOI_XUONG' THEN 4
                     ELSE 5 
                END
        """

    @staticmethod
    def get_event_location(event_name):
        """Lấy thông tin địa điểm của sự kiện"""
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) CONTAINS toLower($name)
            RETURN 
                e.name as event_name,
                e.start_time as start_time,
                COALESCE(e.locations, 'Chưa rõ địa điểm') as locations,
                e.description as description
            LIMIT 1
        """

    @staticmethod
    def get_event_cause_result(event_name):
        """Lấy diễn biến, nguyên nhân, kết quả, ý nghĩa của sự kiện"""
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) CONTAINS toLower($name)
            RETURN 
                e.name as event_name,
                COALESCE(e.dien_bien, 'Đang cập nhật') as dien_bien,
                COALESCE(e.nguyen_nhan, 'Đang cập nhật') as nguyen_nhan,
                COALESCE(e.ket_qua, 'Đang cập nhật') as ket_qua,
                COALESCE(e.y_nghia, 'Đang cập nhật') as y_nghia,
                COALESCE(e.bai_hoc_kinh_nghiem, 'Đang cập nhật') as bai_hoc_kinh_nghiem
            LIMIT 1
        """

    @staticmethod
    def get_treaty_participants(treaty_name):
        """Tìm các bên tham gia đàm phán, ký kết hiệp định"""
        return """
            MATCH (t:HiepDinh)
            WHERE toLower(t.name) CONTAINS toLower($name)
            OPTIONAL MATCH (p:NhanVat)-[:DAM_PHAN|THAM_GIA_KY]-(t)
            OPTIONAL MATCH (c:QuocGia)-[:THAM_GIA_KY]-(t)
            RETURN 
                t.name as treaty_name,
                t.signing_date as signing_date,
                collect(DISTINCT p.name) as negotiators,
                collect(DISTINCT c.name) as countries
            LIMIT 1
        """

    @staticmethod
    def get_period_events(period_name):
        """Lấy các sự kiện thuộc một thời kỳ lịch sử"""
        return """
            MATCH (tk:ThoiKy)
            WHERE toLower(tk.name) CONTAINS toLower($name)
            MATCH (e:SuKien)-[r:THUOC_THOI_KY]->(tk)
            RETURN 
                tk.name as period_name,
                e.name as event_name,
                e.start_time as start_time,
                e.end_time as end_time,
                CASE type(r)
                    WHEN 'THUOC_THOI_KY' THEN 'Thuộc thời kỳ'
                    ELSE type(r)
                END as relation
            ORDER BY e.start_time
        """
        
    @staticmethod
    def get_person_related_entities(person_name):
        """Lấy tất cả các thực thể liên quan đến một nhân vật (sự kiện, tổ chức, quốc gia, thời kỳ)"""
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) CONTAINS toLower($name) 
               OR toLower(p.ten_day_du) CONTAINS toLower($name)
            OPTIONAL MATCH (p)-[r]-(e:SuKien)
            OPTIONAL MATCH (p)-[r2]-(o:ToChuc)
            OPTIONAL MATCH (p)-[r3]-(c:QuocGia)
            OPTIONAL MATCH (p)-[r4]-(tk:ThoiKy)
            RETURN 
                p.name as person_name,
                collect(DISTINCT {type: 'SuKien', name: e.name, relation: type(r)}) +
                collect(DISTINCT {type: 'ToChuc', name: o.name, relation: type(r2)}) +
                collect(DISTINCT {type: 'QuocGia', name: c.name, relation: type(r3)}) +
                collect(DISTINCT {type: 'ThoiKy', name: tk.name, relation: type(r4)}) as related_entities
            LIMIT 1
        """
    
    @staticmethod
    def get_event_related_entities(event_name):
        """Lấy tất cả các thực thể liên quan đến một sự kiện"""
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) CONTAINS toLower($name)
            OPTIONAL MATCH (e)-[r]-(p:NhanVat)
            OPTIONAL MATCH (e)-[r2]-(o:ToChuc)
            OPTIONAL MATCH (e)-[r3]-(c:QuocGia)
            OPTIONAL MATCH (e)-[r4:THUOC_THOI_KY]->(tk:ThoiKy)
            RETURN 
                e.name as event_name,
                collect(DISTINCT {type: 'NhanVat', name: p.name, relation: type(r)}) +
                collect(DISTINCT {type: 'ToChuc', name: o.name, relation: type(r2)}) +
                collect(DISTINCT {type: 'QuocGia', name: c.name, relation: type(r3)}) +
                collect(DISTINCT {type: 'ThoiKy', name: tk.name, relation: type(r4)}) as related_entities
            LIMIT 1
        """
    
    # ==================== TÌM KIẾM TỪ KHÓA MẶC ĐỊNH ====================
    
    @staticmethod
    def search_by_keyword(keyword):
        return """
            MATCH (n)
            WHERE toLower(toString(n.name)) CONTAINS toLower($keyword) 
               OR toLower(toString(n.cuoc_doi)) CONTAINS toLower($keyword)
               OR toLower(toString(n.description)) CONTAINS toLower($keyword)
            RETURN 
               COALESCE(n.name, n.ten_day_du, 'Chưa có tên') as name,
               labels(n)[0] as type,
               CASE 
                   WHEN 'NhanVat' IN labels(n) THEN n.vai_tro
                   WHEN 'SuKien' IN labels(n) THEN n.dien_bien
                   WHEN 'ToChuc' IN labels(n) THEN n.type
                   ELSE COALESCE(n.description, '')
               END as info
            ORDER BY name
            LIMIT 50
        """
    
    @staticmethod
    def get_organization_members(org_name):
        return """
            MATCH (o:ToChuc)
            WHERE toLower(o.name) CONTAINS toLower($name)
            OPTIONAL MATCH (p:NhanVat)-[r:THUOC_VE|LANH_DAO]-(o)
            RETURN 
                o.name as org_name,
                p.name as person_name,
                p.vai_tro as person_role,
                p.chuc_vu as chuc_vu,
                type(r) as relation,
                CASE type(r)
                    WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                    WHEN 'THUOC_VE' THEN 'Thành viên'
                    ELSE type(r)
                END as role_name
        """
    
    @staticmethod
    def get_person_organizations(person_name):
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) CONTAINS toLower($name) 
               OR toLower(p.ten_day_du) CONTAINS toLower($name)
            MATCH (p)-[r]-(o:ToChuc)
            RETURN 
                p.name as person_name,
                o.name as org_name,
                o.type as org_type,
                p.vai_tro as role,
                type(r) as relation,
                CASE type(r)
                    WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                    WHEN 'THUOC_VE' THEN 'Thành viên'
                    WHEN 'SANG_LAP' THEN 'Sáng lập'
                    ELSE type(r)
                END as relation_name
        """
    
    # ==================== TRUY VẤN DÀNH CHO GIAO DIỆN VIEW/DETAIL ====================
    # (Đã tối ưu hóa DISTINCT để tránh lặp dữ liệu)
    
    @staticmethod
    def get_entity_detail(label, property_name, name):
        """Dùng cho các truy vấn đơn giản: Lấy thông tin 1 node"""
        return f"""
            MATCH (n:{label})
            WHERE toLower(n.{property_name}) CONTAINS toLower($name)
            RETURN n
            LIMIT 1
        """

    @staticmethod
    def get_persons_by_period():
        return """
            MATCH (tk:ThoiKy)
            OPTIONAL MATCH (p:NhanVat)-[:THUOC_THOI_KY]->(tk)
            OPTIONAL MATCH (p)-[:DAI_DIEN_CHO|DUNG_DAU|THUOC_QUOC_GIA]-(c:QuocGia)
            WITH tk, p, collect(DISTINCT c.name) as side
            ORDER BY p.name
            RETURN 
                tk.id as period_id,
                tk.name as period_name,
                tk.start_year as period_start_year,
                tk.end_year as period_end_year,
                collect(CASE WHEN p IS NOT NULL THEN {
                    id: p.id,
                    name: p.name,
                    ngay_sinh: p.ngay_sinh,
                    ngay_mat: p.ngay_mat,
                    vai_tro: p.vai_tro,
                    image_url: p.image_url,
                    side: side
                } END) as persons
            ORDER BY tk.id
        """

    @staticmethod
    def get_all_persons():
        return """
            MATCH (p:NhanVat)
            OPTIONAL MATCH (p)-[:DAI_DIEN_CHO|DUNG_DAU]-(c:QuocGia)
            RETURN 
                p.name as name,
                p.ten_day_du as ten_day_du,
                p.ngay_sinh as ngay_sinh,
                p.noi_sinh as noi_sinh,
                p.ngay_mat as ngay_mat,
                p.noi_mat as noi_mat,
                p.quoc_tich as quoc_tich,
                p.vai_tro as vai_tro,
                p.chuc_vu as chuc_vu,
                p.nhiem_ky as nhiem_ky,
                p.cuoc_doi as cuoc_doi,
                p.image_url as image_url,
                collect(DISTINCT c.name) as side
            ORDER BY p.name
        """
    
    @staticmethod
    def get_all_events():
        return """
            MATCH (tk:ThoiKy)
            OPTIONAL MATCH (e:SuKien)-[:THUOC_THOI_KY]->(tk)
            
            // Xử lý bóc tách Năm ra thành số để sắp xếp chuẩn xác
            WITH tk, e, 
                 CASE 
                    WHEN toString(e.start_time) CONTAINS 'TCN' THEN -toInteger(replace(toString(e.start_time), 'TCN', ''))
                    WHEN toString(e.start_time) CONTAINS '-' THEN toInteger(split(toString(e.start_time), '-')[0])
                    WHEN toString(e.start_time) CONTAINS '/' THEN toInteger(last(split(toString(e.start_time), '/')))
                    ELSE toInteger(right(toString(e.start_time), 4))
                 END AS sort_year
                 
            // Sắp xếp ưu tiên theo năm (từ quá khứ đến hiện tại), nếu trùng năm thì xếp theo start_time
            ORDER BY sort_year ASC, e.start_time ASC
            
            RETURN 
                tk.id as period_id,
                tk.name as period_name,
                tk.start_year as period_start_year,
                tk.end_year as period_end_year,
                collect(CASE WHEN e IS NOT NULL THEN {
                    id: e.id,
                    name: e.name,
                    start_time: e.start_time,
                    end_time: e.end_time,
                    dien_bien: e.dien_bien,
                    nguyen_nhan: e.nguyen_nhan,
                    ket_qua: e.ket_qua,
                    y_nghia: e.y_nghia,
                    bai_hoc_kinh_nghiem: e.bai_hoc_kinh_nghiem,
                    image_url: e.image_url,
                    locations: e.locations
                } END) as events
            ORDER BY tk.id
        """
    
    @staticmethod
    def get_all_organizations():
        return """
            MATCH (o:ToChuc)
            RETURN o.id as id, o.name as name, o.type as type, o.founded_year as founded_year,
                    o.headquarters as headquarters, o.description as description
            ORDER BY o.name
        """
    
    @staticmethod
    def get_all_treaties():
        return """
            MATCH (t:HiepDinh)
            RETURN t.id as id, t.name as name, t.year as year, t.signing_date as signing_date,
                   t.location as location, t.description as description, t.noi_dung_chinh as noi_dung_chinh,
                   t.y_nghia as y_nghia, t.bai_hoc_kinh_nghiem as bai_hoc_kinh_nghiem
            ORDER BY t.year DESC
        """
    
    @staticmethod
    def get_all_countries():
        return """
            MATCH (c:QuocGia)
            RETURN c.id as id, c.name as name, c.capital as capital, c.region as region, c.description as description
            ORDER BY c.name
        """
    
    @staticmethod
    def get_all_periods():
        return """
            MATCH (tk:ThoiKy)
            RETURN tk.id as id, tk.name as name, tk.start_year as start_year, tk.end_year as end_year,
                   tk.description as description, tk.y_nghia as y_nghia
            ORDER BY tk.id
        """
    
    @staticmethod
    def get_person_detail_with_relations(person_name):
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name)
            OPTIONAL MATCH (p)-[:DAI_DIEN_CHO|DUNG_DAU|THUOC_QUOC_GIA]-(c:QuocGia)
            OPTIONAL MATCH (p)-[:THUOC_VE|LANH_DAO|THAM_GIA|SANG_LAP]-(o:ToChuc)
            OPTIONAL MATCH (p)-[r:CHI_HUY|CHI_DAO|THAM_GIA|KHOI_XUONG|DOC_TUYEN_NGON]-(e:SuKien)
            RETURN
                p {.name, .ten_day_du, .ngay_sinh, .noi_sinh, .ngay_mat, .noi_mat, 
                   .quoc_tich, .vai_tro, .chuc_vu, .nhiem_ky, .cuoc_doi, .image_url} as person,
                collect(DISTINCT c.name) as countries,
                collect(DISTINCT o.name) as organizations,
                collect(DISTINCT {
                    event: e.name,
                    relation: type(r),
                    role: CASE type(r)
                        WHEN 'CHI_HUY' THEN 'Chỉ huy'
                        WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                        WHEN 'DOC_TUYEN_NGON' THEN 'Đọc bản Tuyên ngôn'
                        ELSE type(r) 
                    END,
                    time: e.start_time
                }) as events
            LIMIT 1
        """
    
    @staticmethod
    def get_event_detail_with_relations(event_name):
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) = toLower($name)
            OPTIONAL MATCH (p:NhanVat)-[r]-(e)
            OPTIONAL MATCH (o:ToChuc)-[r2:THAM_GIA_SU_KIEN|TO_CHUC|KET_QUA_CUA]-(e)
            RETURN 
                e {.name, .start_time, .end_time, .dien_bien, .nguyen_nhan, 
                   .ket_qua, .y_nghia, .bai_hoc_kinh_nghiem, .image_url, .locations} as event,
                collect(DISTINCT {
                    person: p.name,
                    relation: type(r),
                    role: p.vai_tro
                }) as participants,
                collect(DISTINCT {
                    organization: o.name,
                    relation: type(r2)
                }) as organizations
            LIMIT 1
        """
    
    def search_all_attributes(keyword):
        """
        Quét từ khóa trên toàn bộ các thuộc tính chứa văn bản dài 
        của NhanVat (cuoc_doi) và SuKien (dien_bien, nguyen_nhan, ket_qua, y_nghia)
        """
        return """
            MATCH (n)
            WHERE toLower(toString(n.name)) CONTAINS toLower($keyword)
               OR toLower(toString(n.cuoc_doi)) CONTAINS toLower($keyword)
               OR toLower(toString(n.dien_bien)) CONTAINS toLower($keyword)
               OR toLower(toString(n.y_nghia)) CONTAINS toLower($keyword)
               OR toLower(toString(n.ket_qua)) CONTAINS toLower($keyword)
               OR toLower(toString(n.nguyen_nhan)) CONTAINS toLower($keyword)
            RETURN 
               labels(n)[0] as type,
               COALESCE(n.name, n.ten_day_du, 'Không rõ') as name,
               COALESCE(n.cuoc_doi, '') as cuoc_doi,
               COALESCE(n.dien_bien, '') as dien_bien,
               COALESCE(n.nguyen_nhan, '') as nguyen_nhan,
               COALESCE(n.ket_qua, '') as ket_qua,
               COALESCE(n.y_nghia, '') as y_nghia
            ORDER BY name
            LIMIT 5
        """
    
    @staticmethod
    def get_person_relations(person_name):
        """Lấy mối quan hệ giữa Nhân vật và Nhân vật (Ví dụ: Cấp trên, đồng chí, đối đầu, lật đổ...)"""
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) CONTAINS toLower($name) OR toLower(p.ten_day_du) CONTAINS toLower($name)
            MATCH (p)-[r]-(p2:NhanVat)
            RETURN 
                p.name as person_name,
                p2.name as related_person,
                type(r) as relation,
                CASE type(r)
                    // Nhóm quan hệ Lãnh đạo - Cấp dưới
                    WHEN 'LANH_DAO_CAP_TREN' THEN 'Lãnh đạo / Cấp trên'
                    WHEN 'LANH_DAO_CAP_DUOI' THEN 'Cấp dưới'
                    WHEN 'LANH_DAO_CAP_TREN_THAY_TRO' THEN 'Thầy trò'
                    WHEN 'THAM_MUU_TRUONG_DUOI_QUYEN' THEN 'Tham mưu trưởng'
                    WHEN 'CHI_HUY_CHIEN_SI' THEN 'Chiến sĩ'
                    
                    // Nhóm quan hệ Đồng chí - Cộng sự
                    WHEN 'DONG_CHI' THEN 'Đồng chí'
                    WHEN 'LANH_DAO_DONG_CHI' THEN 'Lãnh đạo / Đồng chí'
                    WHEN 'DONG_CHI_COT_CAN' THEN 'Đồng chí cốt cán'
                    WHEN 'DONG_CHI_CHI_HUY' THEN 'Đồng chí / Chỉ huy'
                    WHEN 'DONG_CHI_CAP_DUOI' THEN 'Đồng chí cấp dưới'
                    WHEN 'HOC_TRO_CONG_SU' THEN 'Cộng sự / Học trò'
                    WHEN 'HOC_TRO_CU' THEN 'Học trò cũ'
                    WHEN 'LANH_DAO_DONG_MINH' THEN 'Đồng minh'
                    
                    // Nhóm quan hệ Kế thừa - Chuyển giao
                    WHEN 'TIEN_BOI_CACH_MANG' THEN 'Tiền bối cách mạng'
                    WHEN 'KE_NHIEM' THEN 'Kế nhiệm'
                    WHEN 'CHUYEN_GIAO_QUYEN_LUC' THEN 'Chuyển giao quyền lực'
                    WHEN 'PHO_TONG_THONG' THEN 'Phó tổng thống'
                    
                    // Nhóm quan hệ Đối đầu - Xung đột
                    WHEN 'DOI_DAU' THEN 'Đối đầu'
                    WHEN 'DOI_DAU_BAT_SONG' THEN 'Bắt sống'
                    WHEN 'DOI_LAP' THEN 'Đối lập'
                    WHEN 'DOI_THU_CHINH_TRI' THEN 'Đối thủ chính trị'
                    WHEN 'DOI_THU_DAM_PHAN' THEN 'Đối thủ đàm phán'
                    
                    // Nhóm quan hệ Lật đổ - Chống đối
                    WHEN 'LAT_DO' THEN 'Lật đổ'
                    WHEN 'BI_LAT_DO' THEN 'Bị lật đổ'
                    WHEN 'DONG_MINH_LAT_DO' THEN 'Đồng minh lật đổ'
                    WHEN 'CHONG_DOI_CAP_TREN' THEN 'Chống đối cấp trên'
                    WHEN 'LANH_DAO_BI_CHONG_DOI' THEN 'Lãnh đạo bị chống đối'
                    WHEN 'PHE_TRUAT' THEN 'Phế truất'
                    WHEN 'BI_PHE_TRUAT' THEN 'Bị phế truất'
                    
                    // Fallback
                    ELSE type(r)
                END as relation_name
            LIMIT 30
        """

    @staticmethod
    def get_event_relations(event_name):
        """Lấy mối quan hệ giữa Sự kiện và Sự kiện (Ví dụ: Tiền đề, kết quả, bước ngoặt)"""
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) CONTAINS toLower($name)
            MATCH (e)-[r]-(e2:SuKien)
            RETURN 
                e.name as event_name,
                e2.name as related_event,
                e2.start_time as time,
                type(r) as relation,
                CASE type(r)
                    WHEN 'TIEN_DE_CHO' THEN 'Tiền đề cho'
                    WHEN 'BUOC_NGOAT_DAN_DEN' THEN 'Bước ngoặt dẫn đến'
                    WHEN 'KET_QUA_CUA' THEN 'Kết quả của'
                    WHEN 'NAM_TRONG' THEN 'Nằm trong'
                    WHEN 'DIEN_BIEN_CUA' THEN 'Diễn biến của'
                    WHEN 'KET_THUC_SU_KIEN' THEN 'Kết thúc'
                    ELSE type(r)
                END as relation_name
            LIMIT 15
        """

    # ==================== CÂU HỎI GỢI Ý CHO CHAT AI (CẬP NHẬT) ====================
    
    @staticmethod
    def get_suggested_questions():
        """Trả về danh sách câu hỏi gợi ý cho Chat AI bám sát các Intent đã định nghĩa"""
        return [
            # battle_participants
            "Ai là người chỉ huy trận Bạch Đằng năm 938?",
            "Những nhân vật nào tham gia Chiến dịch Hồ Chí Minh?",
            
            # event_location
            "Trận Ngọc Hồi Đống Đa diễn ra ở đâu?",
            
            # event_cause_result
            "Nguyên nhân và kết quả của sự kiện Vịnh Bắc Bộ là gì?",
            
            # organization_members
            "Những nhân vật lịch sử nào thuộc Vương triều Trần?",
            
            # person_organizations
            "Chủ tịch Hồ Chí Minh đã tham gia và sáng lập những tổ chức nào?",
            
            # event_time
            "Cách mạng tháng Tám diễn ra vào thời gian nào?",
            
            # treaty_participants
            "Những ai đã tham gia đàm phán Hiệp định Paris?",
            
            # person_info
            "Cho tôi biết thông tin tiểu sử của Hưng Đạo Đại Vương Trần Quốc Tuấn?",
            
            # period_events
            "Kể tên các sự kiện diễn ra trong Thời kỳ Phong kiến độc lập?",
            
            # period_info (mới)
            "Thời kỳ Bắc thuộc và Chống Bắc thuộc kéo dài bao lâu và có ý nghĩa gì?",
            
            # treaty_info (mới)
            "Hiệp định Genève có nội dung chính là gì?",
            
            # organization_info (mới)
            "Đảng Cộng sản Việt Nam được thành lập năm nào và vai trò là gì?",
            
            # country_info (mới)
            "Quốc gia Đại Việt có thủ đô ở đâu và tồn tại trong thời kỳ nào?",
            
            # search
            "Ý nghĩa lịch sử của phong trào Đồng Khởi là gì?"

            # person_relations
            "Trần Hưng Đạo có mối quan hệ như thế nào với Trần Quang Khải?",

            # event_relations
            "Sự kiện Vịnh Bắc Bộ là tiền đề dẫn đến sự kiện nào?",
        ]