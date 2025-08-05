document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    if (!token) {
        console.log("No token found, redirecting to login page");
        return window.location.href = "/";
    }
    
    console.log("Token found in localStorage, continuing with chat page");

    // Get DOM elements
    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const chatMessages = document.getElementById("chatMessages");
    const sessionList = document.getElementById("sessionList");
    const chatTitle = document.getElementById("chatTitle");
    const newSessionBtn = document.getElementById("newSessionBtn");
    const logoutBtn = document.getElementById("logoutBtn");

    // Initialize session state
    let currentSessionId = null;

    // Load all sessions function
    async function loadSessions() {
        try {
            console.log("Loading sessions with token:", token.substring(0, 10) + "...");
            
            const res = await fetch("/chat/sessions", {
                headers: { 
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!res.ok) {
                console.error('Failed to load sessions:', res.status, res.statusText);
                throw new Error(`Failed to load sessions: ${res.status} ${res.statusText}`);
            }

            const data = await res.json();
            console.log("Sessions loaded successfully:", data);
            sessionList.innerHTML = "";
            
            data.sessions.forEach((session) => {
                const li = document.createElement("li");
                li.className = 'session-item';
                
                const sessionDiv = document.createElement("div");
                sessionDiv.className = "session-content";
                sessionDiv.textContent = session.title || "Default Session";
                sessionDiv.onclick = () => loadMessages(session.id, session.title);
                
                const deleteBtn = document.createElement("button");
                deleteBtn.className = "delete-session-btn";
                deleteBtn.innerHTML = "🗑️";
                deleteBtn.onclick = async (e) => {
                    e.stopPropagation();
                    if (confirm('Are you sure you want to delete this chat session?')) {
                        try {
                            const res = await fetch(`/chat/sessions/${session.id}`, {
                                method: 'DELETE',
                                headers: { Authorization: `Bearer ${token}` }
                            });
                            
                            if (!res.ok) {
                                const data = await res.json();
                                throw new Error(data.error || 'Failed to delete session');
                            }
                            
                            await loadSessions();
                            if (session.id === currentSessionId) {
                                chatMessages.innerHTML = "";
                                currentSessionId = null;
                                chatTitle.textContent = "Select a chat";
                            }
                        } catch (err) {
                            console.error('Error deleting session:', err);
                            alert(err.message || 'Failed to delete session');
                        }
                    }
                };
                
                li.appendChild(sessionDiv);
                li.appendChild(deleteBtn);
                
                if (session.id === currentSessionId) {
                    li.classList.add('active');
                }
                sessionList.appendChild(li);
            });
        } catch (err) {
            console.error('Error loading sessions:', err);
            alert(err.message || 'Failed to load sessions');
        }
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const content = messageInput.value.trim();
        if (!content) return;

        // Clear input immediately and disable it
        messageInput.value = '';
        messageInput.disabled = true;
        
        try {
            // Add user message immediately to UI
            const userDiv = document.createElement("div");
            userDiv.classList.add("message", "user");
            userDiv.textContent = content;
            chatMessages.appendChild(userDiv);

            // Add loading message
            const loadingDiv = document.createElement("div");
            loadingDiv.className = "loading-message";
            loadingDiv.textContent = "Fraude weaves through your thoughts...";
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // If no session, create one
            if (!currentSessionId) {
                const sessionRes = await fetch("/chat/sessions", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({ title: "New Chat" })
                });

                if (!sessionRes.ok) {
                    throw new Error("Failed to create session");
                }

                const sessionData = await sessionRes.json();
                currentSessionId = sessionData.session_id;
                document.getElementById("chatTitle").textContent = sessionData.title;
            }

            // Send message with retry logic
            let retryCount = 0;
            const maxRetries = 2;
            let lastError;
            
            while (retryCount <= maxRetries) {
                try {
                    const res = await fetch("/chat/message", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            content: content,
                            session_id: currentSessionId
                        })
                    });

                    const data = await res.json();
                    if (res.ok) {
                        // Remove loading message
                        const loadingMessage = chatMessages.querySelector('.loading-message');
                        if (loadingMessage) {
                            loadingMessage.remove();
                        }

                        const botDiv = document.createElement("div");
                        botDiv.classList.add("message", "bot");
                        
                        // Format the response with markdown-like syntax
                        let formattedResponse = data.chatbot_reply
                            .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                                return `<pre><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
                            })
                            .replace(/`([^`]+)`/g, '<code>$1</code>')
                            .replace(/\n\s*[-•]\s+([^\n]+)/g, '\n• $1')
                            .replace(/\n\n/g, '<br><br>');
                        
                        botDiv.innerHTML = formattedResponse;
                        chatMessages.appendChild(botDiv);
                        
                        // Apply syntax highlighting to new content
                        if (typeof hljs !== 'undefined') {
                            hljs.highlightAll();
                        }
                        
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                        
                        await loadSessions();  // Refresh session list
                        return; // Success, exit the retry loop
                    } else {
                        throw new Error(data.error || "Failed to send message");
                    }
                } catch (error) {
                    lastError = error;
                    retryCount++;
                    
                    if (retryCount <= maxRetries) {
                        // Update loading message to show retry
                        const loadingMessage = chatMessages.querySelector('.loading-message');
                        if (loadingMessage) {
                            loadingMessage.textContent = `Retry ${retryCount}/${maxRetries}: The serpent gathers its thoughts...`;
                        }
                        // Wait before retrying (exponential backoff)
                        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
                    }
                }
            }
            
            // If we get here, all retries failed
            throw lastError;
        } catch (err) {
            console.error("Error:", err);
            
            // Remove loading message if there was an error
            const loadingMessage = chatMessages.querySelector('.loading-message');
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            // Show error message in chat
            const errorDiv = document.createElement("div");
            errorDiv.classList.add("message", "bot", "error");
            errorDiv.textContent = err.message || "Something went wrong. Please try again.";
            chatMessages.appendChild(errorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } finally {
            // Always re-enable and focus the input
            messageInput.disabled = false;
            messageInput.focus();
        }
    });


    async function loadMessages(sessionId, title) {
        try {
            if (!sessionId) return;
            
            currentSessionId = sessionId;
            chatTitle.textContent = title || "Default Session";
            
            const res = await fetch(`/chat/message?session_id=${sessionId}&limit=100`, {
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
                
                // Format bot messages with markdown-like syntax
                if (msg.sender === "bot") {
                    let formattedContent = msg.content
                        .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                            return `<pre><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
                        })
                        .replace(/`([^`]+)`/g, '<code>$1</code>')
                        .replace(/\n\s*[-•]\s+([^\n]+)/g, '\n• $1')
                        .replace(/\n\n/g, '<br><br>');
                    
                    div.innerHTML = formattedContent;
                } else {
                    div.innerHTML = msg.content.replace(/\n/g, '<br>');
                }
                chatMessages.appendChild(div);
            });
            
            // Apply syntax highlighting to all loaded content
            if (typeof hljs !== 'undefined') {
                hljs.highlightAll();
            }
            
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } catch (err) {
            console.error('Error loading messages:', err);
            alert(err.message || 'Failed to load messages');
        }
    }

    // Create a new session
    newSessionBtn.addEventListener("click", async () => {
        try {
            newSessionBtn.disabled = true;
            const res = await fetch("/chat/sessions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    title: "New Chat " + (new Date()).toLocaleDateString()
                })
            });

            if (!res.ok) {
                throw new Error("Could not create new session");
            }

            const data = await res.json();
            currentSessionId = data.id;
            chatTitle.textContent = data.title;
            chatMessages.innerHTML = "";
            await loadSessions();
        } catch (err) {
            console.error("Error:", err);
            alert(err.message || "Could not create new session");
        } finally {
            newSessionBtn.disabled = false;
        }
    });

    // Handle logout
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("token");
        window.location.href = "/";
    });

    // Load sessions on page load
    loadSessions();
});
