function createFairies(count) {
    const container = document.body;
    for (let i = 0; i < count; i++) {
        const fairy = document.createElement('div');
        fairy.className = 'fairy';

        fairy.style.left = `${Math.random() * 100}vw`;
        fairy.style.top = `${Math.random() * 100}vh`;
        fairy.style.animationDelay = `${Math.random() * 5}s`;

        container.appendChild(fairy);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    createFairies(15);

    const form = document.getElementById("loginForm");
    const submitBtn = form.querySelector("button[type='submit']");

    // Optional: Add error container
    let errorElem = document.createElement("p");
    errorElem.id = "loginError";
    errorElem.style.color = "tomato";
    errorElem.style.textAlign = "center";
    errorElem.style.marginTop = "10px";
    form.appendChild(errorElem);

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Clear previous error
        errorElem.textContent = "";

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        submitBtn.disabled = true;
        submitBtn.textContent = "Logging in...";

        try {
            const res = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (res.ok) {
                // Store token in localStorage
                localStorage.setItem('token', data.token);
                console.log("Token stored in localStorage");
                
                // The server also sets it as a cookie as a backup
                window.location.href = data.redirect;
            } else {
                errorElem.textContent = data.error || "Invalid email or password";
            }

        } catch (err) {
            console.error(err);
            errorElem.textContent = "An unexpected error occurred.";
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Enter the Realm";
        }
    });
});
