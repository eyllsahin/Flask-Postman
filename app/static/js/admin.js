document.addEventListener('DOMContentLoaded', () => {
    if (!localStorage.getItem('token')) {
        window.location.href = '/login';
        return;
    }

    history.pushState(null, null, window.location.href);
    window.addEventListener("popstate", () => {
        const token = localStorage.getItem("token");
        if (!token) {
            window.location.replace("/login");
        } else {
            history.pushState(null, null, window.location.href);
        }
    });

    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            const currentToken = localStorage.getItem("token");
            if (!currentToken) {
                window.location.replace("/login");
            }
        }
    });

    setInterval(() => {
        const currentToken = localStorage.getItem("token");
        if (!currentToken) {
            window.location.href = "/login";
        }
    }, 3000000);

    const sessionList = document.getElementById('sessionList');
    const pageInfo = document.getElementById('pageInfo');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    let currentPage = 1;
    const limit = 10;

    function formatDate(dateStr) {
        try {
            if (!dateStr) return 'N/A';
            if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                return dateStr;
            }
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return dateStr;
            return date.toLocaleString();
        } catch (e) {
            console.error('Date formatting error:', e);
            return dateStr;
        }
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

    logoutBtn.addEventListener('click', async () => {
        try {
            await fetch("/logout", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${localStorage.getItem('token')}`,
                    "Content-Type": "application/json"
                }
            });
        } catch (err) {
            console.log("Logout request failed, but continuing with client-side cleanup");
        }

        localStorage.removeItem('token');
        sessionStorage.clear();

        document.cookie.split(";").forEach(function (c) {
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });

        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    caches.delete(name);
                });
            });
        }

        window.history.replaceState(null, null, "/login");
        window.location.replace('/login');
    });

    loadSessions();

    const modal = document.getElementById('chatModal');
    const closeBtn = document.querySelector('.close');

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.classList.remove('modal-open');
        }
    });

    window.openChatModal = function () {
        modal.style.display = 'block';
        document.body.classList.add('modal-open');
    };

    function recalculatePageHeight() {
        document.documentElement.style.overflow = 'auto';
        document.body.style.overflow = 'visible';
        document.body.style.height = 'auto';
        document.documentElement.style.height = 'auto';

        const adminContainer = document.querySelector('.admin-container');
        if (adminContainer) {
            adminContainer.style.maxHeight = 'none';
            adminContainer.style.height = 'auto';
        }

        const height = Math.max(
            document.body.scrollHeight,
            document.body.offsetHeight,
            document.documentElement.clientHeight,
            document.documentElement.scrollHeight,
            document.documentElement.offsetHeight
        );

        document.body.style.minHeight = height + 'px';

        window.dispatchEvent(new Event('resize'));
    }

    const observer = new MutationObserver((mutations) => {
        let shouldRecalculate = false;

        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (let node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        shouldRecalculate = true;
                        break;
                    }
                }
            } else if (mutation.type === 'attributes') {
                if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
                    shouldRecalculate = true;
                }
            }
        });

        if (shouldRecalculate) {
            clearTimeout(window.heightRecalcTimeout);
            window.heightRecalcTimeout = setTimeout(recalculatePageHeight, 100);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });

    document.addEventListener('click', (event) => {
        if (event.target.matches('button, .btn, .expand, .view, .show, .toggle') ||
            event.target.closest('button, .btn, .expand, .view, .show, .toggle')) {
            setTimeout(() => {
                recalculatePageHeight();
            }, 300);
        }
    });

    window.resetScrollRange = function () {
        recalculatePageHeight();
    };

    recalculatePageHeight();
});
