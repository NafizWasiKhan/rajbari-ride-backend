/**
 * Zatra - Authentication Module
 * Handles login, signup, role management, and UI modals.
 */

const Auth = {
    token: localStorage.getItem('token'),
    role: localStorage.getItem('userRole'),

    init() {
        this.updateUI();
    },

    async login(username, password) {
        try {
            const response = await fetch('/api/users/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();
            if (response.ok) {
                this.setSession(data.token, data.user.profile.role);
                location.reload(); // Refresh to init correct dashboard
            } else {
                throw new Error(data.non_field_errors || "Invalid credentials");
            }
        } catch (error) {
            alert(error.message);
        }
    },

    async signup(username, email, password, role, phone_number) {
        try {
            const response = await fetch('/api/users/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username, email, password,
                    profile: { role, phone_number }
                })
            });
            const data = await response.json();
            if (response.ok) {
                this.setSession(data.token, data.user.profile.role);
                location.reload();
            } else {
                const errors = Object.values(data).flat().join('\n');
                throw new Error(errors || "Signup failed");
            }
        } catch (error) {
            alert(error.message);
        }
    },

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('userRole');
        location.reload();
    },

    setSession(token, role) {
        localStorage.setItem('token', token);
        localStorage.setItem('userRole', role);
        this.token = token;
        this.role = role;
    },

    showModal(type = 'login') {
        const modal = document.getElementById('auth-modal');
        const loginForm = document.getElementById('login-form');
        const signupForm = document.getElementById('signup-form');

        modal.style.display = 'flex';
        if (type === 'login') {
            loginForm.style.display = 'block';
            signupForm.style.display = 'none';
        } else {
            loginForm.style.display = 'none';
            signupForm.style.display = 'block';
        }
    },

    hideModal() {
        document.getElementById('auth-modal').style.display = 'none';
    },

    updateUI() {
        const authBtn = document.getElementById('auth-status-btn');
        if (this.token) {
            authBtn.innerHTML = `<i class="fas fa-sign-out-alt"></i> Logout`;
            authBtn.onclick = () => this.logout();
            // Show role in UI if needed
        } else {
            authBtn.innerHTML = `<i class="fas fa-user"></i> Login`;
            authBtn.onclick = () => this.showModal('login');
        }
    }
};

// Global handlers
window.toggleAuthTab = (type) => Auth.showModal(type);
window.handleLoginSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    Auth.login(fd.get('username'), fd.get('password'));
};
window.handleSignupSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    Auth.signup(fd.get('username'), fd.get('email'), fd.get('password'), fd.get('role'), fd.get('phone_number'));
};

document.addEventListener('DOMContentLoaded', () => Auth.init());
