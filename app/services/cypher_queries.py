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
            
            Quy tắc bắt buộc:
            1. Tự động sửa lỗi chính tả, TỰ ĐỘNG THÊM DẤU tiếng Việt nếu người dùng viết không dấu (VD: "vo nguyen giap" -> "Võ Nguyên Giáp").
            2. TUYỆT ĐỐI GIỮ NGUYÊN các con số hoặc ký hiệu ở cuối tên (VD: "Võ Nguyên Giáp 1" thì bắt buộc phải trả về "Võ Nguyên Giáp 1", không được xóa số 1).
            3. Trả về DUY NHẤT một chuỗi JSON hợp lệ theo định dạng.
            
            Ví dụ:
            - Hỏi 'võ thị sáu bị bắt khi nào': {{"type": "person_info", "person_name": "Võ Thị Sáu"}}
            - Hỏi 'chức vụ của võ nguyên giáp 1 là gì': {{"type": "person_info", "person_name": "Võ Nguyên Giáp 1"}}
            - Hỏi 'quang trung 2 tham gia trận nào': {{"type": "person_battles", "person_name": "Quang Trung 2"}}
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
            WHERE toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name)
               OR toLower(p.name) CONTAINS toLower($name) OR toLower(p.ten_day_du) CONTAINS toLower($name)
            WITH p
            ORDER BY CASE WHEN toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
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
                    WHEN 'TRUC_TIEP_CHI_DAO' THEN 'Trực tiếp chỉ đạo'
                    WHEN 'THAM_GIA' THEN 'Tham gia'
                    WHEN 'THAM_GIA_CHIEN_DAU' THEN 'Tham gia chiến đấu'
                    WHEN 'CHI_HUY_PHONG_THU' THEN 'Chỉ huy phòng thủ'
                    WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                    WHEN 'CHU_TRI' THEN 'Chủ trì'
                    WHEN 'DOC_TUYEN_NGON' THEN 'Đọc bản Tuyên ngôn'
                    WHEN 'DOI_DAU' THEN 'Đối đầu'
                    ELSE type(r)
                END as role
            ORDER BY e.start_time
        """

    @staticmethod
    def get_battle_participants(battle_name):
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) = toLower($name) OR toLower(e.name) CONTAINS toLower($name)
            WITH e
            ORDER BY CASE WHEN toLower(e.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
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
                    WHEN 'TRUC_TIEP_CHI_DAO' THEN 'Trực tiếp chỉ đạo'
                    WHEN 'THAM_GIA' THEN 'Tham gia'
                    WHEN 'THAM_GIA_CHIEN_DAU' THEN 'Tham gia chiến đấu'
                    WHEN 'CHI_HUY_PHONG_THU' THEN 'Chỉ huy phòng thủ'
                    WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                    WHEN 'CHU_TRI' THEN 'Chủ trì'
                    WHEN 'DOC_TUYEN_NGON' THEN 'Đọc bản Tuyên ngôn'
                    WHEN 'DOI_DAU' THEN 'Đối đầu'
                    ELSE type(r)
                END as role
            ORDER BY 
                CASE WHEN type(r) IN ['CHI_HUY', 'CHI_DAO', 'TRUC_TIEP_CHI_DAO', 'CHU_TRI'] THEN 1 
                     WHEN type(r) IN ['KHOI_XUONG', 'DOC_TUYEN_NGON'] THEN 2 
                     WHEN type(r) IN ['THAM_GIA', 'THAM_GIA_CHIEN_DAU', 'CHI_HUY_PHONG_THU'] THEN 3
                     WHEN type(r) = 'DOI_DAU' THEN 4
                     ELSE 5 
                END
        """

    @staticmethod
    def get_event_location(event_name):
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) = toLower($name) OR toLower(e.name) CONTAINS toLower($name)
            WITH e
            ORDER BY CASE WHEN toLower(e.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
            RETURN 
                e.name as event_name,
                e.start_time as start_time,
                COALESCE(e.locations, 'Chưa rõ địa điểm') as locations,
                e.description as description
        """

    @staticmethod
    def get_event_cause_result(event_name):
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) = toLower($name) OR toLower(e.name) CONTAINS toLower($name)
            WITH e
            ORDER BY CASE WHEN toLower(e.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
            RETURN 
                e.name as event_name,
                COALESCE(e.dien_bien, 'Đang cập nhật') as dien_bien,
                COALESCE(e.nguyen_nhan, 'Đang cập nhật') as nguyen_nhan,
                COALESCE(e.ket_qua, 'Đang cập nhật') as ket_qua,
                COALESCE(e.y_nghia, 'Đang cập nhật') as y_nghia,
                COALESCE(e.bai_hoc_kinh_nghiem, 'Đang cập nhật') as bai_hoc_kinh_nghiem
        """

    @staticmethod
    def get_treaty_participants(treaty_name):
        return """
            MATCH (t:HiepDinh)
            WHERE toLower(t.name) = toLower($name) OR toLower(t.name) CONTAINS toLower($name)
            WITH t
            ORDER BY CASE WHEN toLower(t.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
            OPTIONAL MATCH (p:NhanVat)-[:DAM_PHAN|THAM_GIA_KY]-(t)
            OPTIONAL MATCH (c:QuocGia)-[:THAM_GIA_KY]-(t)
            RETURN 
                t.name as treaty_name,
                t.signing_date as signing_date,
                collect(DISTINCT p.name) as negotiators,
                collect(DISTINCT c.name) as countries
        """

    @staticmethod
    def get_period_events(period_name):
        return """
            MATCH (tk:ThoiKy)
            WHERE toLower(tk.name) = toLower($name) OR toLower(tk.name) CONTAINS toLower($name)
            WITH tk
            ORDER BY CASE WHEN toLower(tk.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
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
            WHERE toLower(o.name) = toLower($name) OR toLower(o.name) CONTAINS toLower($name)
            WITH o
            ORDER BY CASE WHEN toLower(o.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
            OPTIONAL MATCH (p:NhanVat)-[r:THUOC_VE|LANH_DAO|SANG_LAP]-(o)
            RETURN 
                o.name as org_name,
                p.name as person_name,
                p.vai_tro as person_role,
                p.chuc_vu as chuc_vu,
                type(r) as relation,
                CASE type(r)
                    WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                    WHEN 'THUOC_VE' THEN 'Thành viên'
                    WHEN 'SANG_LAP' THEN 'Sáng lập'
                    ELSE type(r)
                END as role_name
        """
    
    @staticmethod
    def get_person_organizations(person_name):
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name)
               OR toLower(p.name) CONTAINS toLower($name) OR toLower(p.ten_day_du) CONTAINS toLower($name)
            WITH p
            ORDER BY CASE WHEN toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
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
    
    @staticmethod
    def get_entity_detail(label, property_name, name):
        """Lấy thông tin 1 node: Ưu tiên khớp chính xác 100%, nếu không có mới tìm gần đúng"""
        return f"""
            MATCH (n:{label})
            WHERE toLower(n.{property_name}) = toLower($name) 
               OR toLower(n.{property_name}) CONTAINS toLower($name)
            RETURN n
            ORDER BY 
                CASE 
                    WHEN toLower(n.{property_name}) = toLower($name) THEN 0 
                    ELSE 1 
                END ASC
            LIMIT 1
        """

    @staticmethod
    def get_all_persons():
        return """
            MATCH (tk:ThoiKy)
            OPTIONAL MATCH (p:NhanVat)-[:THUOC_THOI_KY]->(tk)
            WITH tk, p
            ORDER BY p.name
            RETURN 
                tk.id as period_id,
                tk.name as period_name,
                tk.start_year as period_start_year,
                tk.end_year as period_end_year,
                collect(CASE WHEN p IS NOT NULL THEN {
                    id: p.id,
                    name: p.name,
                    ten_day_du: p.ten_day_du,
                    ngay_sinh: p.ngay_sinh,
                    noi_sinh: p.noi_sinh,
                    ngay_mat: p.ngay_mat,
                    noi_mat: p.noi_mat,
                    quoc_tich: p.quoc_tich,
                    vai_tro: p.vai_tro,
                    chuc_vu: p.chuc_vu,
                    nhiem_ky: p.nhiem_ky,
                    cuoc_doi: p.cuoc_doi,
                    image_url: p.image_url
                } END) as persons
            ORDER BY tk.id
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
    def get_person_detail_with_relations():
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) = toLower($name)
            RETURN 
                p {.id, .name, .ten_day_du, .ngay_sinh, .noi_sinh, .ngay_mat, .noi_mat, 
                   .quoc_tich, .vai_tro, .chuc_vu, .nhiem_ky, .cuoc_doi, .image_url} as person,
                [(p)-[re]-(e:SuKien) | {
                    name: e.name, start_time: e.start_time, end_time: e.end_time, ket_qua: e.ket_qua, relation: type(re),
                    role: CASE type(re)
                        WHEN 'CHI_HUY' THEN 'Chỉ huy'
                        WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                        ELSE type(re) END
                }] as events,
                [(p)-[ro]-(o:ToChuc) | {
                    name: o.name, type: o.type, founded_year: o.founded_year,
                    role: CASE type(ro)
                        WHEN 'THUOC_VE' THEN 'Thành viên'
                        WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'SANG_LAP' THEN 'Sáng lập'
                        ELSE type(ro) END
                }] as organizations,
                [(p)-[rc]-(c:QuocGia) | {
                    name: c.name, relation: type(rc),
                    role: CASE type(rc)
                        WHEN 'DAI_DIEN_CHO' THEN 'Đại diện cho'
                        WHEN 'DUNG_DAU' THEN 'Lãnh đạo'
                        WHEN 'THUOC_QUOC_GIA' THEN 'Thuộc quốc gia'
                        ELSE type(rc) END
                }] as countries
            LIMIT 1
        """

    @staticmethod
    def get_event_detail_with_relations():
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) = toLower($name)
            RETURN 
                e {.id, .name, .start_time, .end_time, .dien_bien, .nguyen_nhan, 
                   .ket_qua, .y_nghia, .bai_hoc_kinh_nghiem, .image_url, .locations} as event,
                [(e)-[rp]-(p:NhanVat) | {
                    name: p.name, vai_tro: p.vai_tro, relation: type(rp),
                    role: CASE type(rp)
                        WHEN 'CHI_HUY' THEN 'Chỉ huy'
                        WHEN 'CHI_DAO' THEN 'Chỉ đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'KHOI_XUONG' THEN 'Khởi xướng'
                        ELSE type(rp) END
                }] as persons,
                [(e)-[ro]-(o:ToChuc) | {
                    name: o.name, type: o.type, founded_year: o.founded_year,
                    role: CASE type(ro)
                        WHEN 'THAM_GIA_SU_KIEN' THEN 'Tham gia'
                        WHEN 'TO_CHUC' THEN 'Tổ chức'
                        ELSE type(ro) END
                }] as organizations,
                [(e)-[rt:THUOC_THOI_KY]->(g:ThoiKy) | {
                    name: g.name, start_year: g.start_year, end_year: g.end_year
                }] as periods
            LIMIT 1
        """
    
    @staticmethod
    def get_organization_detail_with_relations():
        return """
            MATCH (o:ToChuc)
            WHERE toLower(o.name) = toLower($name)
            RETURN 
                o {.id, .name, .type, .founded_year, .headquarters, .description} as organization,
                [(o)-[rm]-(p:NhanVat) | {
                    name: p.name, vai_tro: p.vai_tro, chuc_vu: p.chuc_vu, relation: type(rm),
                    role: CASE type(rm)
                        WHEN 'THUOC_VE' THEN 'Thành viên'
                        WHEN 'LANH_DAO' THEN 'Lãnh đạo'
                        WHEN 'THAM_GIA' THEN 'Tham gia'
                        WHEN 'SANG_LAP' THEN 'Người sáng lập'
                        ELSE type(rm) END
                }] as members,
                [(o)-[rc]-(c:QuocGia) | {
                    name: c.name, cap_do: c.cap_do, relation: type(rc),
                    role: CASE type(rc)
                        WHEN 'DAI_DIEN_CHO' THEN 'Đại diện cho'
                        WHEN 'DUNG_DAU' THEN 'Lãnh đạo'
                        WHEN 'THUOC_QUOC_GIA' THEN 'Trực thuộc'
                        WHEN 'HO_TRO' THEN 'Hỗ trợ'
                        ELSE type(rc) END
                }] as countries
            LIMIT 1
        """

    @staticmethod
    def get_treaty_detail_with_relations():
        return """
            MATCH (t:HiepDinh)
            WHERE toLower(t.name) = toLower($name)
            RETURN 
                t {.id, .name, .year, .signing_date, .location, .description, .noi_dung_chinh, .y_nghia, .bai_hoc_kinh_nghiem} as treaty,
                [(t)-[rp]-(p:NhanVat) | {
                    name: p.name, relation: type(rp),
                    role: CASE type(rp) WHEN 'KY_KET' THEN 'Người ký' WHEN 'DAM_PHAN' THEN 'Người đàm phán' ELSE type(rp) END
                }] as persons,
                [(t)-[rc]-(c:QuocGia) | {
                    name: c.name, relation: type(rc),
                    role: CASE type(rc) WHEN 'THAM_GIA_KY' THEN 'Tham gia ký kết' ELSE type(rc) END
                }] as countries,
                [(t)-[re]-(e:SuKien) | {
                    name: e.name, start_time: e.start_time, relation: type(re),
                    role: CASE type(re) WHEN 'KET_THUC_SU_KIEN' THEN 'Kết thúc sự kiện' ELSE type(re) END
                }] as events
            LIMIT 1
        """

    @staticmethod
    def get_country_detail_with_relations():
        return """
            MATCH (c:QuocGia)
            WHERE toLower(c.name) = toLower($name)
            RETURN 
                c {.id, .name, .capital, .region, .description} as country,
                [(c)-[rp]-(p:NhanVat) | {
                    name: p.name, relation: type(rp),
                    role: CASE type(rp) WHEN 'DUNG_DAU' THEN 'Lãnh đạo' WHEN 'DAI_DIEN_CHO' THEN 'Đại diện' ELSE type(rp) END
                }] as persons,
                [(c)-[re]-(e:SuKien) | {
                    name: e.name, start_time: e.start_time, relation: type(re),
                    role: CASE type(re) WHEN 'THAM_GIA' THEN 'Tham gia' WHEN 'KHOI_XUONG' THEN 'Khởi xướng' ELSE type(re) END
                }] as events,
                [(c)-[ro]-(o:ToChuc) | {
                    name: o.name, relation: type(ro),
                    role: CASE type(ro) WHEN 'THUOC_QUOC_GIA' THEN 'Tổ chức trực thuộc' ELSE type(ro) END
                }] as organizations
            LIMIT 1
        """

    @staticmethod
    def get_period_detail_with_relations():
        return """
            MATCH (g:ThoiKy)
            WHERE toLower(g.name) = toLower($name)
            RETURN 
                g {.id, .name, .start_year, .end_year, .description, .y_nghia} as period,
                [(g)-[:THUOC_THOI_KY]-(e:SuKien) | {
                    name: e.name, start_time: e.start_time, end_time: e.end_time, locations: e.locations
                }] as events,
                [(p:NhanVat)-[:THUOC_THOI_KY]->(g) | {
                    name: p.name, vai_tro: p.vai_tro
                }] as persons
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
        return """
            MATCH (p:NhanVat)
            WHERE toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name)
               OR toLower(p.name) CONTAINS toLower($name) OR toLower(p.ten_day_du) CONTAINS toLower($name)
            WITH p
            ORDER BY CASE WHEN toLower(p.name) = toLower($name) OR toLower(p.ten_day_du) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
            MATCH (p)-[r]-(p2:NhanVat)
            RETURN 
                p.name as person_name,
                p2.name as related_person,
                type(r) as relation,
                CASE type(r)
                    WHEN 'LANH_DAO_CAP_TREN' THEN 'Lãnh đạo / Cấp trên'
                    WHEN 'LANH_DAO_CAP_DUOI' THEN 'Cấp dưới'
                    WHEN 'LANH_DAO_CAP_TREN_THAY_TRO' THEN 'Thầy trò'
                    WHEN 'THAM_MUU_TRUONG_DUOI_QUYEN' THEN 'Tham mưu trưởng'
                    WHEN 'CHI_HUY_CHIEN_SI' THEN 'Chiến sĩ'
                    WHEN 'DONG_CHI' THEN 'Đồng chí'
                    WHEN 'LANH_DAO_DONG_CHI' THEN 'Lãnh đạo / Đồng chí'
                    WHEN 'DONG_CHI_COT_CAN' THEN 'Đồng chí cốt cán'
                    WHEN 'DONG_CHI_CHI_HUY' THEN 'Đồng chí / Chỉ huy'
                    WHEN 'DONG_CHI_CAP_DUOI' THEN 'Đồng chí cấp dưới'
                    WHEN 'HOC_TRO_CONG_SU' THEN 'Cộng sự / Học trò'
                    WHEN 'HOC_TRO_CU' THEN 'Học trò cũ'
                    WHEN 'LANH_DAO_DONG_MINH' THEN 'Đồng minh'
                    WHEN 'TIEN_BOI_CACH_MANG' THEN 'Tiền bối cách mạng'
                    WHEN 'KE_NHIEM' THEN 'Kế nhiệm'
                    WHEN 'CHUYEN_GIAO_QUYEN_LUC' THEN 'Chuyển giao quyền lực'
                    WHEN 'PHO_TONG_THONG' THEN 'Phó tổng thống'
                    WHEN 'DOI_DAU' THEN 'Đối đầu'
                    WHEN 'DOI_DAU_BAT_SONG' THEN 'Bắt sống'
                    WHEN 'DOI_LAP' THEN 'Đối lập'
                    WHEN 'DOI_THU_CHINH_TRI' THEN 'Đối thủ chính trị'
                    WHEN 'DOI_THU_DAM_PHAN' THEN 'Đối thủ đàm phán'
                    WHEN 'LAT_DO' THEN 'Lật đổ'
                    WHEN 'BI_LAT_DO' THEN 'Bị lật đổ'
                    WHEN 'DONG_MINH_LAT_DO' THEN 'Đồng minh lật đổ'
                    WHEN 'CHONG_DOI_CAP_TREN' THEN 'Chống đối cấp trên'
                    WHEN 'LANH_DAO_BI_CHONG_DOI' THEN 'Lãnh đạo bị chống đối'
                    WHEN 'PHE_TRUAT' THEN 'Phế truất'
                    WHEN 'BI_PHE_TRUAT' THEN 'Bị phế truất'
                    ELSE type(r)
                END as relation_name
            LIMIT 30
        """

    @staticmethod
    def get_event_relations(event_name):
        return """
            MATCH (e:SuKien)
            WHERE toLower(e.name) = toLower($name) OR toLower(e.name) CONTAINS toLower($name)
            WITH e
            ORDER BY CASE WHEN toLower(e.name) = toLower($name) THEN 0 ELSE 1 END ASC
            LIMIT 1
            
            MATCH (e)-[r]-(e2:SuKien)
            RETURN 
                e.name as event_name,
                e2.name as related_event,
                e2.start_time as time,
                type(r) as relation,
                CASE type(r)
                    WHEN 'TIEN_DE_CHO' THEN 'Tiền đề cho'
                    WHEN 'BUOC_NGOAT_DAN_DEN' THEN 'Bước ngoặt dẫn đến'
                    WHEN 'CHAM_NGOI_CHO' THEN 'Châm ngòi cho'
                    WHEN 'KET_QUA_CUA' THEN 'Kết quả của'
                    WHEN 'NAM_TRONG' THEN 'Nằm trong'
                    WHEN 'DIEN_BIEN_CUA' THEN 'Diễn biến của'
                    WHEN 'KET_THUC_SU_KIEN' THEN 'Kết thúc'
                    ELSE type(r)
                END as relation_name
            LIMIT 15
        """