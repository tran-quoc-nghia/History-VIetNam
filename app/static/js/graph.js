// Biến toàn cục
let graphNetwork = null;
window.currentGraphData = null;

// Vẽ đồ thị
function drawGraph(data, centerNodeName, containerId = 'graphContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (graphNetwork !== null) {
        graphNetwork.destroy();
        graphNetwork = null;
    }

    const nodes = new vis.DataSet(data.nodes);
    const edges = new vis.DataSet(data.edges);

    const options = {
        nodes: {
            shape: 'dot',
            size: 20,
            font: { size: 12 }
        },
        interaction: {
            hover: true, 
            tooltipDelay: 200
        },
        configure: {
            enabled: false
        },
        physics: {
            enabled: true,
            stabilization: {
                enabled: true,
                iterations: 100,
                updateInterval: 25,
                fit: true
            },
            barnesHut: {
                gravitationalConstant: -3000,
                centralGravity: 0.3,
                springLength: 150,
                springConstant: 0.04,
                damping: 0.09,
                avoidOverlap: 0.5
            },
            solver: 'barnesHut'
        },
        height: '100%',
        width: '100%'
    };

    graphNetwork = new vis.Network(container, { nodes, edges }, options);
    
    graphNetwork.on("doubleClick", function (params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const clickedNode = nodes.get(nodeId); 

            if (clickedNode && clickedNode.type) {
                // Kiểm tra xem người dùng đang ở trang Admin hay trang User
                const isAdmin = window.location.pathname.startsWith('/admin');
                let url = '';

                if (isAdmin) {
                    // ==========================================
                    // 1. ĐIỀU HƯỚNG DÀNH CHO TRANG ADMIN
                    // ==========================================
                    let adminEntity = '';
                    switch (clickedNode.type) {
                        case 'NhanVat': adminEntity = 'personAdmin'; break;
                        case 'SuKien': adminEntity = 'eventAdmin'; break;
                        case 'ToChuc': adminEntity = 'organizationAdmin'; break;
                        case 'HiepDinh': adminEntity = 'treatyAdmin'; break;
                        case 'QuocGia': adminEntity = 'countryAdmin'; break;
                        case 'ThoiKy': adminEntity = 'periodAdmin'; break;
                        default: return; 
                    }
                    
                    // Admin dùng ID hệ thống (VD: person_xxxx). Nếu graph API có truyền real_id thì lấy, nếu không lấy label tạm.
                    const targetId = clickedNode.real_id || clickedNode.id; 
                    url = `/admin/${adminEntity}/view/${encodeURIComponent(targetId)}`;

                } else {
                    // ==========================================
                    // 2. ĐIỀU HƯỚNG DÀNH CHO TRANG USER 
                    // ==========================================
                    let userEntity = '';
                    switch (clickedNode.type) {
                        case 'NhanVat': userEntity = 'person'; break;
                        case 'SuKien': userEntity = 'event'; break;
                        case 'ToChuc': userEntity = 'organization'; break;
                        case 'HiepDinh': userEntity = 'treaty'; break;
                        case 'QuocGia': userEntity = 'country'; break;
                        case 'ThoiKy': userEntity = 'period'; break;
                        default: return; 
                    }
                    
                    // User dùng Tên (Label)
                    url = `/${userEntity}/detail/${encodeURIComponent(clickedNode.label)}`;
                }

                // Thực hiện chuyển trang
                window.location.href = url;
            }
        }
    });

    // Tự động fit đồ thị sau khi vẽ
    graphNetwork.once('stabilized', () => graphNetwork.fit());
}

// Tải dữ liệu đồ thị
function loadGraphData(entityName, depth = 1, callback) {
    const container = document.getElementById('graphContainer');
    if (container) {
        container.innerHTML = '<div class="graph-loading"><i class="fas fa-spinner fa-spin"></i> Đang tải đồ thị...</div>';
    }
    
    fetch(`/api/graph/${encodeURIComponent(entityName)}`)
        .then(res => res.json())
        .then(data => {
            if (callback) callback(data);
            else if (data.success && data.nodes.length > 0) {
                drawGraph(data, entityName);
            } else if (container && !data.success) {
                container.innerHTML = '<div class="graph-empty">Không có dữ liệu đồ thị</div>';
            }
        })
        .catch(error => {
            console.error('Lỗi tải đồ thị:', error);
            if (container) {
                container.innerHTML = '<div class="graph-error">Lỗi tải dữ liệu đồ thị</div>';
            }
        });
}

// Export functions
window.drawGraph = drawGraph;
window.loadGraphData = loadGraphData;