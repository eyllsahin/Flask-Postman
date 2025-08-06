document.addEventListener("DOMContentLoaded", () => {
    // Ultra-enhanced security checks
    const token = localStorage.getItem("token");
    const cookieToken = getCookie('token');
    
    if (!token && !cookieToken) {
        console.log("No authentication found, redirecting to login page");
        clearAllAuth();
        forceRedirectToLogin();
        return;
    }

    // Function to get cookie value
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Function to clear all authentication
    function clearAllAuth() {
        localStorage.removeItem('token');
        sessionStorage.clear();
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
    }

    // Function to force redirect (prevents back navigation)
    function forceRedirectToLogin() {
        // Clear browser history and redirect
        history.replaceState(null, null, '/login');
        window.location.replace("/login");
    }
    
    // Helper function to get current valid token
    function getCurrentToken() {
        return localStorage.getItem("token") || cookieToken;
    }
    
    // Immediately check if we're on an unauthorized page
    if (window.location.pathname === '/chat' && (!token && !cookieToken)) {
        clearAllAuth();
        forceRedirectToLogin();
        return;
    }
    
    // Note: Token validation will be done when sessions are loaded, no need for separate validation here
    
    console.log("Token found in localStorage, continuing with chat page");

    // Ultra-strong security: Prevent back navigation after logout
    history.pushState(null, null, window.location.href);
    window.onpopstate = function (event) {
        console.log("Back button pressed, checking auth");
        const currentToken = localStorage.getItem("token");
        if (!currentToken) {
            // If no token, force redirect to login
            window.location.replace("/login");
        } else {
            // If token exists, push state again to prevent back navigation
            history.pushState(null, null, window.location.href);
        }
    };

    // Additional popstate listener for extra security
    window.addEventListener("popstate", () => {
        console.log("Popstate event triggered, checking auth");
        const token = localStorage.getItem("token");
        if (!token) {
            window.location.replace("/login");
        } else {
            // Push state again to prevent going back
            history.pushState(null, null, window.location.href);
        }
    });

    // Security: Prevent back navigation after logout
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            // Page was restored from cache (user pressed back button)
            const currentToken = localStorage.getItem("token");
            if (!currentToken) {
                // No token means user logged out, prevent access
                window.location.replace("/login");
            }
        }
    });

    // Security: Check token validity periodically (token lasts 1 hour, check every 55 minutes)
    setInterval(() => {
        const currentToken = localStorage.getItem("token");
        if (!currentToken) {
            console.log("Token expired during session, redirecting to login");
            clearAllAuth();
            window.location.replace("/login");
        }
    }, 3300000); // Check every 55 minutes (3300000ms) - 5 min buffer before 1-hour expiry

    // Get DOM elements
    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const chatMessages = document.getElementById("chatMessages");
    const sessionList = document.getElementById("sessionList");
    const chatTitle = document.getElementById("chatTitle");
    const newSessionBtn = document.getElementById("newSessionBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const modeSelect = document.getElementById("modeSelect");

    // Initialize session state
    let currentSessionId = null;

    // Function to apply theme without saving
    function applyTheme(selectedMode, saveToStorage = true) {
        const chatTitle = document.getElementById("chatTitle");
        const sidebarTitle = document.querySelector('.sidebar h2');
        const body = document.body;
        const html = document.documentElement;
        const fairies = document.querySelectorAll('.fairy');
        
        if (selectedMode === "lucifer") {
            // Switch to Lucifer theme
            body.classList.add('lucifer-mode');
            html.classList.add('lucifer-mode');
            chatTitle.textContent = "😈 Lucifer's Hell 😈";
            if (sidebarTitle) {
                sidebarTitle.textContent = "😈 Lucifer's Hell 😈";
            }
            messageInput.placeholder = "What is it you truly desire?";
            
            // Hide fairies
            fairies.forEach(fairy => {
                fairy.style.display = 'none';
            });
            
            // Show fire effects
            const fireEffects = document.querySelector('.fire-effects');
            if (fireEffects) {
                fireEffects.style.display = 'block';
            }
            
            // Show thorn decorations
            const thornDecoration = document.querySelector('.thorn-decoration');
            if (thornDecoration) {
                thornDecoration.style.display = 'block';
            }
            
        } else {
            // Switch back to Fraude theme
            body.classList.remove('lucifer-mode');
            html.classList.remove('lucifer-mode');
            chatTitle.textContent = "✧ Fraude's Realm ✧";
            if (sidebarTitle) {
                sidebarTitle.textContent = "✧ Fraude Realms ✧";
            }
            messageInput.placeholder = "Cast your message into the magical realm...";
            
            // Show fairies
            fairies.forEach(fairy => {
                fairy.style.display = 'block';
            });
            
            // Hide fire effects
            const fireEffects = document.querySelector('.fire-effects');
            if (fireEffects) {
                fireEffects.style.display = 'none';
            }
            
            // Hide thorn decorations
            const thornDecoration = document.querySelector('.thorn-decoration');
            if (thornDecoration) {
                thornDecoration.style.display = 'none';
            }
        }
        
        // Save to localStorage for persistence
        if (saveToStorage) {
            localStorage.setItem('selectedMode', selectedMode);
        }
    }

    // Handle mode changes
    modeSelect.addEventListener('change', function() {
        const selectedMode = this.value;
        applyTheme(selectedMode, true);
    });

    // Load all sessions function
    async function loadSessions() {
        try {
            // Get current token (it might have changed)
            const currentToken = localStorage.getItem("token") || cookieToken;
            
            if (!currentToken) {
                console.log("No token available for loading sessions");
                window.location.replace("/login");
                return;
            }
            
            console.log("Loading sessions with token:", currentToken.substring(0, 10) + "...");
            
            const res = await fetch("/chat/sessions", {
                headers: { 
                    Authorization: `Bearer ${currentToken}`,
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
            
            // Sessions are already sorted by created_at DESC from the API
            // Display them in the order received (newest first)
            data.sessions.forEach((session) => {
                const li = document.createElement("li");
                li.className = 'session-item';
                
                const sessionDiv = document.createElement("div");
                sessionDiv.className = "session-content";
                
                // Create session title with date
                const titleDiv = document.createElement("div");
                titleDiv.className = "session-title";
                titleDiv.textContent = session.title || "Default Session";
                
                const dateDiv = document.createElement("div");
                dateDiv.className = "session-date";
                
                // Format the date to include time
                const sessionDate = new Date(session.created_at);
                const formattedDate = sessionDate.toLocaleDateString() + ' ' + 
                                    sessionDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                dateDiv.textContent = formattedDate;
                
                sessionDiv.appendChild(titleDiv);
                sessionDiv.appendChild(dateDiv);
                sessionDiv.onclick = () => loadMessages(session.id, session.title);
                
                const deleteBtn = document.createElement("button");
                deleteBtn.className = "delete-session-btn";
                deleteBtn.innerHTML = "🗑️";
                deleteBtn.onclick = async (e) => {
                    e.stopPropagation();
                    if (confirm('Are you sure you want to delete this chat session?')) {
                        try {
                            const currentToken = getCurrentToken();
                            if (!currentToken) {
                                window.location.replace("/login");
                                return;
                            }
                            
                            const res = await fetch(`/chat/sessions/${session.id}`, {
                                method: 'DELETE',
                                headers: { Authorization: `Bearer ${currentToken}` }
                            });
                            
                            if (!res.ok) {
                                const data = await res.json();
                                throw new Error(data.error || 'Failed to delete session');
                            }
                            
                            await loadSessions(); // Refresh to update the session list
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

            // Add loading message based on mode
            const loadingDiv = document.createElement("div");
            loadingDiv.className = "loading-message";
            const selectedMode = modeSelect.value;
            if (selectedMode === "lucifer") {
                loadingDiv.textContent = "The Devil is contemplating your words...";
            } else {
                loadingDiv.textContent = "Fraude weaves through your thoughts...";
            }
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // If no session, create one
            let sessionWasCreated = false;
            if (!currentSessionId) {
                const currentToken = getCurrentToken();
                if (!currentToken) {
                    window.location.replace("/login");
                    return;
                }
                
                const sessionRes = await fetch("/chat/sessions", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${currentToken}`
                    },
                    body: JSON.stringify({ title: "New Chat" })
                });

                if (!sessionRes.ok) {
                    throw new Error("Failed to create session");
                }

                const sessionData = await sessionRes.json();
                currentSessionId = sessionData.session_id;
                document.getElementById("chatTitle").textContent = sessionData.title;
                sessionWasCreated = true;
                
                // Immediately refresh sessions to show the new one
                await loadSessions();
            }

            
            let retryCount = 0;
            const maxRetries = 2;
            let lastError;
            
            while (retryCount <= maxRetries) {
                try {
                    const currentToken = getCurrentToken();
                    if (!currentToken) {
                        window.location.replace("/login");
                        return;
                    }
                    
                    const res = await fetch("/chat/message", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${currentToken}`
                        },
                        body: JSON.stringify({
                            content: content,
                            session_id: currentSessionId,
                            mode: modeSelect.value
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
                        
                        // Only refresh session list if a new session was created
                        if (sessionWasCreated) {
                            await loadSessions();
                        }
                        
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
            
            const currentToken = getCurrentToken();
            if (!currentToken) {
                window.location.replace("/login");
                return;
            }
            
            currentSessionId = sessionId;
            chatTitle.textContent = title || "Default Session";
            
            const res = await fetch(`/chat/message?session_id=${sessionId}&limit=100`, {
                headers: { 
                    Authorization: `Bearer ${currentToken}`,
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
            
            const currentToken = getCurrentToken();
            if (!currentToken) {
                window.location.replace("/login");
                return;
            }
            
            const res = await fetch("/chat/sessions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentToken}`
                },
                body: JSON.stringify({
                    title: "New Chat " + (new Date()).toLocaleDateString() + " " + 
                           (new Date()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                })
            });

            if (!res.ok) {
                throw new Error("Could not create new session");
            }

            const data = await res.json();
            currentSessionId = data.id;
            chatTitle.textContent = data.title;
            chatMessages.innerHTML = "";
            await loadSessions(); // Refresh to show the new session
        } catch (err) {
            console.error("Error:", err);
            alert(err.message || "Could not create new session");
        } finally {
            newSessionBtn.disabled = false;
        }
    });

    // Handle logout
    logoutBtn.addEventListener("click", async () => {
        console.log('Logout function called from chat');
        
        try {
            const currentToken = getCurrentToken();
            if (currentToken) {
                // Call logout endpoint to clear server-side session
                await fetch("/logout", {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${currentToken}`,
                        "Content-Type": "application/json"
                    }
                });
            }
        } catch (err) {
            console.log("Logout request failed, but continuing with client-side cleanup");
        }
        
        // Clear client-side tokens and saved preferences
        localStorage.removeItem("token");
        localStorage.removeItem("selectedMode"); // Also clear theme preference
        sessionStorage.clear();
        
        // Clear cookies more thoroughly
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
        
        // Clear any cached data
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    caches.delete(name);
                });
            });
        }
        
        // Prevent back navigation to logged-in pages
        console.log('Redirecting to login from chat...');
        window.history.replaceState(null, null, "/login");
        window.location.replace("/login"); // Use replace to prevent back navigation
    });

    // Load sessions on page load
    loadSessions();
    
    // Clean up any corrupted localStorage values
    const cleanupStorage = () => {
        const savedMode = localStorage.getItem('selectedMode');
        if (savedMode && savedMode !== 'fraude' && savedMode !== 'lucifer') {
            console.log('Removing invalid mode from localStorage:', savedMode);
            localStorage.removeItem('selectedMode');
        }
    };
    
    cleanupStorage();
    
    // Initialize theme based on saved preference - ensure fraude is always default
    const initializeTheme = () => {
        // Get saved mode from localStorage, but ensure fraude is the fallback
        const savedMode = localStorage.getItem('selectedMode');
        
        console.log('Retrieved savedMode from localStorage:', savedMode);
        
        // Default to fraude if nothing is saved or if invalid value
        let modeToUse = 'fraude'; // Always start with fraude as default
        
        if (savedMode === 'lucifer') {
            modeToUse = 'lucifer';
        }
        
        console.log('Initializing theme with mode:', modeToUse);
        
        // Set the select value without triggering change event
        modeSelect.value = modeToUse;
        
        // Apply the theme and save the preference if it wasn't saved before
        applyTheme(modeToUse, !savedMode);
    };
    
    // Initialize theme immediately when DOM elements are available
    initializeTheme();
});
