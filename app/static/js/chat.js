document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    if (!token) return window.location.href = "/";

    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const chatMessages = document.getElementById("chatMessages");
    const sessionList = document.getElementById("sessionList");

    let currentSessionId = null;

    // 🟢 Load all user sessions on load
    async function loadSessions() {
        try {
            const res = await fetch("/chat/sessions", {
                headers: { 
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Failed to load sessions');
            }

            sessionList.innerHTML = "";
            data.sessions.forEach((session) => {
                const li = document.createElement("li");
                li.className = 'session-item';
                li.textContent = session.title || "Default Session";
                li.onclick = () => loadMessages(session.id, session.title);
                if (session.id === currentSessionId) {
                    li.classList.add('active');
                }
                sessionList.appendChild(li);
            });
        } catch (err) {
            console.error('Error loading sessions:', err);
            alert('Failed to load sessions. Please try again.');
        }
    }

    // 🟢 Load messages of selected session
    async function loadMessages(sessionId, title) {
        try {
            if (!sessionId) return;
            
            currentSessionId = sessionId;
            document.getElementById("chatTitle").textContent = title || "Default Session";
            
            const res = await fetch(`/chat/message?session_id=${sessionId}`, {
                headers: { 
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.error || 'Failed to load messages');
            }

            chatMessages.innerHTML = "";
            data.messages.forEach((msg) => {
                const div = document.createElement("div");
                div.classList.add("message", msg.sender === "user" ? "user" : "bot");
                const sanitizedContent = escapeHtml(msg.content);
                div.innerHTML = sanitizedContent;
                chatMessages.appendChild(div);
            });
            
            // Scroll to bottom of messages
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (err) {
            console.error('Error loading messages:', err);
            alert('Failed to load messages. Please try again.');
        }
    }

    // 🟢 Send a new message
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const content = messageInput.value.trim();
        
        if (!content) {
            alert('Please enter a message');
            return;
        }
        
        if (!currentSessionId) {
            alert('Please select or create a chat session first');
            return;
        }

        try {
            messageInput.disabled = true;
            // First create a session if none exists
            if (!currentSessionId) {
                const sessionRes = await fetch("/chat/sessions", {
                    method: "POST",
                    headers: { 
                        Authorization: `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: "New Chat"
                    })
                });

                if (sessionRes.ok) {
                    const sessionData = await sessionRes.json();
                    currentSessionId = sessionData.session_id;
                }
            }

            const res = await fetch("/chat/message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ 
                    content: content
                })
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || 'Failed to send message');
            }

            messageInput.value = "";
            await loadMessages(currentSessionId, document.getElementById("chatTitle").textContent);
        } catch (err) {
            console.error('Error sending message:', err);
            alert(err.message || 'Failed to send message. Please try again.');
        } finally {
            messageInput.disabled = false;
            messageInput.focus();
        }
    });

    // 🟢 Create a new session
    document.getElementById("newSessionBtn").addEventListener("click", async () => {
        try {
            const button = document.getElementById("newSessionBtn");
            button.disabled = true;

            const res = await fetch("/chat/sessions", {
                method: "POST",
                headers: { 
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: "New Chat " + (new Date()).toLocaleDateString()
                })
            });

            if (!res.ok) {
                if (res.status === 404) {
                    throw new Error("Chat session creation is not available. Please try again later.");
                }
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || "Failed to create session");
            }

            const data = await res.json();
            await loadSessions();
            
            // If we got a session ID back, load it
            if (data.session_id) {
                loadMessages(data.session_id, data.title || "New Chat");
            }
        } catch (err) {
            console.error("Error creating session:", err);
            alert(err.message || "Network error while creating session. Please try again.");
        } finally {
            const button = document.getElementById("newSessionBtn");
            button.disabled = false;
        }
    });

    // 🟢 Load sessions on page load
    loadSessions();

    // Logout
    document.getElementById("logoutBtn").addEventListener("click", () => {
        localStorage.removeItem("token");
        window.location.href = "/";
    });

    // Add HTML escaping function for security
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
