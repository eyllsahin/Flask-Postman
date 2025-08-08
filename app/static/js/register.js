
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem('token');
    if (token) {
       
        fetch('/chat/sessions', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (response.ok) {
               
                return fetch('/admin/users', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }).then(adminResponse => {
                    if (adminResponse.ok) {
                        window.location.href = '/admin';
                    } else {
                        window.location.href = '/chat';
                    }
                });
            } else {
                
                localStorage.removeItem('token');
            }
        }).catch(err => {
            
            localStorage.removeItem('token');
        });
    }
});

document.getElementById("registerForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirmPassword").value;

    if (password !== confirm) {
        alert("Passwords do not match.");
        return;
    }

    const response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password, confirm_password: confirm })
    });

    const data = await response.json();

    if (response.ok) {
        alert("Registration successful! You can now log in.");
        window.location.href = "/";
    } else {
        alert(data.error || "Registration failed.");
    }
});
