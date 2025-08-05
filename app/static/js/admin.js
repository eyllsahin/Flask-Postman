document.addEventListener('DOMContentLoaded', () => {
    const sessionList = document.getElementById('sessionList');
    const pageInfo = document.getElementById('pageInfo');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    let currentPage = 1;
    const limit = 10;

    // Safely format date strings for display
    function formatDate(dateStr) {
        try {
            // Check if it's already a valid date string format
            if (!dateStr) return 'N/A';
            
            // Try to format the date - if it's a simple YYYY-MM-DD string, display it directly
            if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                return dateStr;
            }
            
            // Otherwise try to create a Date object and format it
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) {
                return dateStr; // Just return the original string if it's not a valid date
            }
            return date.toLocaleString();
        } catch (e) {
            console.error('Date formatting error:', e);
            return dateStr; // Return the original string in case of errors
        }
    }

    if (!localStorage.getItem('token')) {
        window.location.href = '/login';
        return;
    }

    async function loadSessions(page = 1) {
        try {
            const response = await fetch(`/admin/sessions?page=${page}&limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.error || "You are not authorized.");
                return;
            }

            sessionList.innerHTML = '';
            data.sessions.forEach(session => {
                const div = document.createElement('div');
                div.classList.add('message');
                div.innerHTML = `
                    <strong>ID:</strong> ${session.id} |
                    <strong>User:</strong> ${session.username} |
                    <strong>Title:</strong> ${session.title || 'N/A'} |
                    <strong>Active:</strong> ${session.is_active ? 'Yes' : 'No'}<br>
                    <small>${formatDate(session.created_at)}</small>
                `;
                sessionList.appendChild(div);
            });

            pageInfo.textContent = `Page ${data.page} of ${data.total_pages}`;
            currentPage = data.page;

            prevPageBtn.disabled = currentPage <= 1;
            nextPageBtn.disabled = currentPage >= data.total_pages;

        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) loadSessions(currentPage - 1);
    });

    nextPageBtn.addEventListener('click', () => {
        loadSessions(currentPage + 1);
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    });

    loadSessions();
});
