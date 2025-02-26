// Alternar entre modo claro e escuro
const darkModeToggle = document.getElementById('darkModeToggle');
darkModeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
});

// Mostrar/ocultar senha
function togglePassword() {
    const senhaInput = document.getElementById('senha');
    const icon = document.querySelector('.fa-eye');
    if (senhaInput.type === 'password') {
        senhaInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        senhaInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Validação em tempo real
document.getElementById('username').addEventListener('input', function() {
    if (this.value.length < 3) {
        this.classList.add('is-invalid');
        document.getElementById('usernameError').style.display = 'block';
    } else {
        this.classList.remove('is-invalid');
        document.getElementById('usernameError').style.display = 'none';
    }
});

document.getElementById('senha').addEventListener('input', function() {
    if (this.value.length < 6) {
        this.classList.add('is-invalid');
        document.getElementById('senhaError').style.display = 'block';
    } else {
        this.classList.remove('is-invalid');
        document.getElementById('senhaError').style.display = 'none';
    }
});

// Animação de carregamento no botão de login
document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const loginButton = document.getElementById('loginButton');
    const loginText = document.getElementById('loginText');
    const loadingSpinner = document.getElementById('loadingSpinner');

    loginText.style.display = 'none';
    loadingSpinner.style.display = 'inline-block';
    loginButton.disabled = true;

    // Simula um tempo de carregamento
    setTimeout(function() {
        loginText.style.display = 'inline-block';
        loadingSpinner.style.display = 'none';
        loginButton.disabled = false;
        alert('Login realizado com sucesso!'); // Substitua por lógica real de login
    }, 2000); // Tempo de carregamento simulado
});

// Mensagem de boas-vindas dinâmica
const hour = new Date().getHours();
const welcomeMessage = document.getElementById('welcomeMessage');

if (hour < 12) {
    welcomeMessage.textContent = 'Bom dia! Faça login para continuar.';
} else if (hour < 18) {
    welcomeMessage.textContent = 'Boa tarde! Faça login para continuar.';
} else {
    welcomeMessage.textContent = 'Boa noite! Faça login para continuar.';
}