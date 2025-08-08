document.addEventListener("DOMContentLoaded", () => {
    
    const token = localStorage.getItem("token");
    const cookieToken = getCookie('token');
    
    if (!token && !cookieToken) {
        console.log("No authentication found, redirecting to login page");
        clearAllAuth();
        forceRedirectToLogin();
        return;
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    function clearAllAuth() {
        localStorage.removeItem('token');
        sessionStorage.clear();
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
    }

    function forceRedirectToLogin() {
       
        history.replaceState(null, null, '/login');
        window.location.replace("/login");
    }
    
    
    function getCurrentToken() {
        return localStorage.getItem("token") || cookieToken;
    }
    
    
    if (window.location.pathname === '/chat' && (!token && !cookieToken)) {
        clearAllAuth();
        forceRedirectToLogin();
        return;
    }
    
    
    
    console.log("Token found in localStorage, continuing with chat page");

  
    history.pushState(null, null, window.location.href);
    window.onpopstate = function (event) {
        console.log("Back button pressed, checking auth");
        const currentToken = localStorage.getItem("token");
        if (!currentToken) {
            
            window.location.replace("/login");
        } else {
            
            history.pushState(null, null, window.location.href);
        }
    };

   
    window.addEventListener("popstate", () => {
        console.log("Popstate event triggered, checking auth");
        const token = localStorage.getItem("token");
        if (!token) {
            window.location.replace("/login");
        } else {
           
            history.pushState(null, null, window.location.href);
        }
    });

    
    window.addEventListener('pageshow', function(event) {
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
            console.log("Token expired during session, redirecting to login");
            clearAllAuth();
            window.location.replace("/login");
        }
    }, 3300000); 

  
    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const chatMessages = document.getElementById("chatMessages");
    const sessionList = document.getElementById("sessionList");
    const chatTitle = document.getElementById("chatTitle");
    const newSessionBtn = document.getElementById("newSessionBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const modeSelect = document.getElementById("modeSelect");

   
    let currentSessionId = null;

   
    function applyTheme(selectedMode, saveToStorage = true) {
        const chatTitle = document.getElementById("chatTitle");
        const sidebarTitle = document.querySelector('.sidebar h2');
        const body = document.body;
        const html = document.documentElement;
        const fairies = document.querySelectorAll('.fairy');
        
        body.classList.remove('lucifer-mode', 'eren-mode');
        html.classList.remove('lucifer-mode', 'eren-mode');
        
        if (selectedMode === "lucifer") {
            
            body.classList.add('lucifer-mode');
            html.classList.add('lucifer-mode');
            chatTitle.textContent = "😈 Lucifer's Hell 😈";
            if (sidebarTitle) {
                sidebarTitle.textContent = "😈 Lucifer's Hell 😈";
            }
            messageInput.placeholder = "What is it you truly desire?";
            
           
            fairies.forEach(fairy => {
                fairy.style.display = 'none';
            });
           
            const fireEffects = document.querySelector('.fire-effects');
            if (fireEffects) {
                fireEffects.style.display = 'block';
            }
            
            
            const thornDecoration = document.querySelector('.thorn-decoration');
            if (thornDecoration) {
                thornDecoration.style.display = 'block';
            }
            
        } else if (selectedMode === "eren") {
            console.log("Applying Eren mode...");
            body.classList.add('eren-mode');
            html.classList.add('eren-mode');
            console.log("Eren mode classes added. Body classes:", body.className);
            console.log("HTML classes:", html.className);
            chatTitle.textContent = " Path to Freedom ";
            if (sidebarTitle) {
                sidebarTitle.textContent = " Path to Freedom ";
            }
            messageInput.placeholder = "What do you seek beyond these walls?";
            
            
            fairies.forEach(fairy => {
                fairy.style.display = 'none';
            });
            
            
            const fireEffects = document.querySelector('.fire-effects');
            if (fireEffects) {
                fireEffects.style.display = 'none';
            }
            
            
            const thornDecoration = document.querySelector('.thorn-decoration');
            if (thornDecoration) {
                thornDecoration.style.display = 'none';
            }
            
        } else {
            
            chatTitle.textContent = "✧ Fraude's Realm ✧";
            if (sidebarTitle) {
                sidebarTitle.textContent = "✧ Fraude Realms ✧";
            }
            messageInput.placeholder = "Cast your message into the magical realm...";
            
            
            fairies.forEach(fairy => {
                fairy.style.display = 'block';
            });
            
            
            const fireEffects = document.querySelector('.fire-effects');
            if (fireEffects) {
                fireEffects.style.display = 'none';
            }
            
            
            const thornDecoration = document.querySelector('.thorn-decoration');
            if (thornDecoration) {
                thornDecoration.style.display = 'none';
            }
        }
        
       
        if (saveToStorage) {
            localStorage.setItem('selectedMode', selectedMode);
        }
    }

    
    modeSelect.addEventListener('change', function() {
        const selectedMode = this.value;
        applyTheme(selectedMode, true);
    });

    
    async function loadSessions() {
        try {
            
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
            
           
            data.sessions.forEach((session) => {
                const li = document.createElement("li");
                li.className = 'session-item';
                
                const sessionDiv = document.createElement("div");
                sessionDiv.className = "session-content";
                
               
                const titleDiv = document.createElement("div");
                titleDiv.className = "session-title";
                titleDiv.textContent = session.title || "Default Session";
                
                const dateDiv = document.createElement("div");
                dateDiv.className = "session-date";
                
                
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

    
        messageInput.value = '';
        messageInput.disabled = true;
        
        try {
            const userDiv = document.createElement("div");
            userDiv.classList.add("message", "user");
            userDiv.textContent = content;
            chatMessages.appendChild(userDiv);


            // Add loading message with mode-specific text
            const loadingDiv = document.createElement("div");
            loadingDiv.className = "loading-message";
            const selectedMode = modeSelect.value;
            console.log(`🔄 Creating loading message for ${selectedMode} mode`);
            
            if (selectedMode === "lucifer") {
                loadingDiv.textContent = "The Devil is contemplating your words...";
            } else if (selectedMode === "eren") {
                loadingDiv.textContent = "Eren considers your words with burning conviction...";
            } else {
                loadingDiv.textContent = "Fraude weaves through your thoughts...";
            }
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;


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
                    
                    console.log(`📤 Sending message to backend for ${modeSelect.value} mode:`, {
                        content: content.substring(0, 50) + "...",
                        session_id: currentSessionId,
                        mode: modeSelect.value
                    });
                    
                    // Add timeout for faster response handling
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
                    
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
                        }),
                        signal: controller.signal
                    });

                    clearTimeout(timeoutId);
                    console.log(`📨 Response status: ${res.status} for ${modeSelect.value} mode`);
                    const data = await res.json();
                    console.log(`📦 Response data received for ${modeSelect.value} mode:`, {
                        status: data.status,
                        reply_length: data.chatbot_reply?.length,
                        session_title: data.session_title,
                        mode: data.mode
                    });
                    if (res.ok) {
                        console.log(`✅ Response received for ${modeSelect.value} mode:`, data.chatbot_reply?.substring(0, 50) + "...");
                        
                        // Remove loading message immediately
                        const loadingMessage = chatMessages.querySelector('.loading-message');
                        if (loadingMessage) {
                            loadingMessage.remove();
                        }

                        const botDiv = document.createElement("div");
                        botDiv.classList.add("message", "bot");
                        
                        // Apply mode-specific styling
                        if (modeSelect.value === "eren") {
                            console.log("🎨 Applying Eren mode styling to bot message");
                            // Ensure Eren styling is properly applied
                            botDiv.classList.add("eren-mode-message");
                        }
                        
                        // Format response with proper line breaks and code highlighting
                        let formattedResponse = data.chatbot_reply
                            .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                                return `<pre><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
                            })
                            .replace(/`([^`]+)`/g, '<code>$1</code>')
                            .replace(/\n\s*[-•]\s+([^\n]+)/g, '\n• $1')
                            .replace(/\n/g, '<br>'); // Convert single line breaks to <br>
                        
                        botDiv.innerHTML = formattedResponse;
                        chatMessages.appendChild(botDiv);
                        
                        // Force immediate DOM update and scroll - multiple methods for reliability
                        botDiv.offsetHeight; // Force reflow
                        
                        // Use multiple scroll approaches for immediate response
                        setTimeout(() => {
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }, 0);
                        
                        requestAnimationFrame(() => {
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                            
                            // Double-check that the message is visible
                            const messageRect = botDiv.getBoundingClientRect();
                            const containerRect = chatMessages.getBoundingClientRect();
                            
                            if (messageRect.bottom > containerRect.bottom) {
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        });
                        
                        if (typeof hljs !== 'undefined') {
                            hljs.highlightAll();
                        }
                        
                        
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                        
                  
                        if (data.session_title && data.session_title !== "Untitled Chat") {
                            console.log(`📝 Updating session title: ${data.session_title}`);
                            const titleElement = document.getElementById("chatTitle");
                            titleElement.textContent = data.session_title;
                            
                           
                            titleElement.offsetHeight;
                            
                            
                            const activeSession = document.querySelector('.session-item.active .session-title');
                            if (activeSession) {
                                activeSession.textContent = data.session_title;
                            }
                        }
                        
                        
                        if (sessionWasCreated || data.session_title) {
                            console.log(`🔄 Reloading sessions for ${modeSelect.value} mode`);
                            setTimeout(() => {
                                loadSessions();
                            }, 100); 
                        }
                        
                        console.log(`✅ Message displayed successfully for ${modeSelect.value} mode`);
                        return; 
                    } else {
                        throw new Error(data.error || "Failed to send message");
                    }
                } catch (error) {
                    lastError = error;
                    retryCount++;
                    
                    console.log(`⚠️ Error in attempt ${retryCount}: ${error.message}`);
                    
                    
                    if (error.name === 'AbortError') {
                        console.log('⏰ Request timeout - server is slow');
                        lastError = new Error('Response timed out. The server is taking too long to respond.');
                    }
                    
                    if (retryCount <= maxRetries) {
                        
                        const loadingMessage = chatMessages.querySelector('.loading-message');
                        if (loadingMessage) {
                            if (modeSelect.value === "eren") {
                                loadingMessage.textContent = `Retry ${retryCount}/${maxRetries}: Breaking through the barriers...`;
                            } else if (modeSelect.value === "lucifer") {
                                loadingMessage.textContent = `Retry ${retryCount}/${maxRetries}: The Devil doesn't give up easily...`;
                            } else {
                                loadingMessage.textContent = `Retry ${retryCount}/${maxRetries}: The serpent gathers its thoughts...`;
                            }
                        }
                        
                        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
                    }
                }
            }
            
            
            throw lastError;
        } catch (err) {
            console.error("Error:", err);
            
            
            const loadingMessage = chatMessages.querySelector('.loading-message');
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            
            const errorDiv = document.createElement("div");
            errorDiv.classList.add("message", "bot", "error");
            errorDiv.textContent = err.message || "Something went wrong. Please try again.";
            chatMessages.appendChild(errorDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } finally {
            
            messageInput.disabled = false;
            messageInput.focus();
        }
    });


    async function loadMessages(sessionId, title) {
        try {
            if (!sessionId) return;
            
            console.log(`📥 Loading messages for session ${sessionId} with title: ${title}`);
            
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

            console.log(`📨 Loaded ${data.messages.length} messages for session ${sessionId}`);
            chatMessages.innerHTML = "";
            
            data.messages.forEach((msg, index) => {
                console.log(`📝 Processing message ${index + 1}: ${msg.sender} in ${msg.mode || 'fraude'} mode`);
                
                const div = document.createElement("div");
                div.classList.add("message", msg.sender === "user" ? "user" : "bot");
                
              
                if (msg.mode === "eren" && msg.sender === "bot") {
                    div.classList.add("eren-mode-message");
                }
                
                if (msg.sender === "bot") {
                    let formattedContent = msg.content
                        .replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                            return `<pre><code class="language-${lang || ''}">${code.trim()}</code></pre>`;
                        })
                        .replace(/`([^`]+)`/g, '<code>$1</code>')
                        .replace(/\n\s*[-•]\s+([^\n]+)/g, '\n• $1')
                        .replace(/\n/g, '<br>');
                    
                    div.innerHTML = formattedContent;
                } else {
                    div.innerHTML = msg.content.replace(/\n/g, '<br>');
                }
                chatMessages.appendChild(div);
            });
            
        
            if (typeof hljs !== 'undefined') {
                hljs.highlightAll();
            }
            
    
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            console.log(`✅ Messages loaded successfully for session ${sessionId}`);
        } catch (err) {
            console.error('Error loading messages:', err);
            alert(err.message || 'Failed to load messages');
        }
    }


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
            currentSessionId = data.session_id;
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


    logoutBtn.addEventListener("click", async () => {
        console.log('Logout function called from chat');
        
        try {
            const currentToken = getCurrentToken();
            if (currentToken) {
  
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
        

        localStorage.removeItem("token");
        localStorage.removeItem("selectedMode"); 
        sessionStorage.clear();
        
    
        document.cookie.split(";").forEach(function(c) { 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        });
        
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => {
                    caches.delete(name);
                });
            });
        }
        
        
        console.log('Redirecting to login from chat...');
        window.history.replaceState(null, null, "/login");
        window.location.replace("/login"); 
    });

    
    loadSessions();
    
    
    const cleanupStorage = () => {
        const savedMode = localStorage.getItem('selectedMode');
        if (savedMode && savedMode !== 'fraude' && savedMode !== 'lucifer' && savedMode !== 'eren') {
            console.log('Removing invalid mode from localStorage:', savedMode);
            localStorage.removeItem('selectedMode');
        }
    };
    
    cleanupStorage();

    const initializeTheme = () => {
       
        const savedMode = localStorage.getItem('selectedMode');
        
        console.log('Retrieved savedMode from localStorage:', savedMode);
        
        let modeToUse = 'fraude'; 
        
        if (savedMode === 'lucifer') {
            modeToUse = 'lucifer';
        } else if (savedMode === 'eren') {
            modeToUse = 'eren';
        }
        
        console.log('Initializing theme with mode:', modeToUse);

        modeSelect.value = modeToUse;
  
        applyTheme(modeToUse, !savedMode);
    };
    

    initializeTheme();
});
