// ==================== TIỆN ÍCH ====================

// Highlight text với từ khóa tìm kiếm
function highlightText(text, keyword) {
    if (!text || !keyword) return text;
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

// Hiển thị lỗi trong một element
function showError(element, message) {
    if (!element) return;
    element.innerHTML = `
        <div class="error-message" style="color: #c00; padding: 20px; text-align: center;">
            <i class="fas fa-exclamation-circle"></i> ${message}
        </div>
    `;
}

// Hiển thị loading
function showLoading(element) {
    if (!element) return;
    element.innerHTML = `
        <div class="loading" style="text-align: center; padding: 30px;">
            <i class="fas fa-spinner fa-spin"></i> Đang tải...
        </div>
    `;
}

// Escape HTML để tránh XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Debounce function để tránh gọi API quá nhiều
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatVNTime(dateStr) {
    if (!dateStr || dateStr === 'None' || dateStr === 'null') return "?";
    
    // Nếu dữ liệu chỉ có năm (ví dụ: "1890" hoặc 1890) thì giữ nguyên
    if (String(dateStr).length === 4 && !isNaN(dateStr)) {
        return dateStr;
    }

    // Xử lý chuỗi Date (VD: "1954-05-07" hoặc "1954-05-07T00:00:00")
    try {
        // Tách bỏ phần giờ (nếu có) và chỉ lấy YYYY-MM-DD
        let datePart = String(dateStr).split('T')[0]; 
        if (datePart.includes('-')) {
            let parts = datePart.split('-');
            if (parts.length === 3) {
                // parts[0] = YYYY, parts[1] = MM, parts[2] = DD
                return `${parts[2]}/${parts[1]}/${parts[0]}`;
            }
        }
    } catch (e) {
        console.error("Lỗi parse ngày:", e);
    }
    
    // Nếu không parse được, trả về nguyên gốc
    return dateStr;
}

// Export các hàm ra global

window.highlightText = highlightText;
window.showError = showError;
window.showLoading = showLoading;
window.escapeHtml = escapeHtml;
window.debounce = debounce;
window.formatVNTime = formatVNTime;