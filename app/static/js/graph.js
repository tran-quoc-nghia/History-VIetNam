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
            hover: true, // Cho phép hover
            tooltipDelay: 200 // Thời gian trễ khi hiện bảng thông tin (ms)
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
    graphNetwork.on("click", function (params) {
        // Nếu người dùng click trúng 1 node (mảng nodes có phần tử)
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const clickedNode = nodes.get(nodeId); // Lấy dữ liệu của node được click từ DataSet

            if (clickedNode && clickedNode.type) {
                // 1. Ánh xạ Loại Node (Neo4j) sang entity_type (để khớp với hàm generic_detail)
                let entityType = '';
                switch (clickedNode.type) {
                    case 'NhanVat': entityType = 'person'; break;
                    case 'SuKien': entityType = 'event'; break;
                    case 'ToChuc': entityType = 'organization'; break;
                    case 'HiepDinh': entityType = 'treaty'; break;
                    case 'QuocGia': entityType = 'country'; break;
                    case 'ThoiKy': entityType = 'period'; break;
                    default: return; // Bỏ qua nếu không xác định được loại
                }

                // 2. Chuyển hướng trang (Điều hướng URL)
                const url = `/${entityType}/detail/${encodeURIComponent(clickedNode.label)}`;
                
                // Chuyển sang trang mới
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

// Export functions - gán vào window để có thể gọi từ HTML
window.drawGraph = drawGraph;
window.loadGraphData = loadGraphData;