// Validação simples para login e criar conta
(function(){
  function q(id){ return document.getElementById(id); }

  /* Helpers */
  function isEmail(value){
    return /\S+@\S+\.\S+/.test(value);
  }

  /* CREATE ACCOUNT */
  var createForm = q('createForm');
  if(createForm){
    var name = q('name');
    var email = q('email');
    var pwd = q('password');
    var confirm = q('passwordConfirm');
    var btn = q('createBtn');

    function validateCreate(){
      var ok = true;
      q('nameError').textContent = '';
      q('emailError').textContent = '';
      q('passwordError').textContent = '';
      q('confirmError').textContent = '';

      if(!name.value.trim()){ q('nameError').textContent = 'Por favor informe seu nome.'; ok = false; }
      if(!isEmail(email.value)){ q('emailError').textContent = 'Email inválido.'; ok = false; }
      if(pwd.value.length < 6){ q('passwordError').textContent = 'A senha precisa ter pelo menos 6 caracteres.'; ok = false; }
      if(pwd.value !== confirm.value){ q('confirmError').textContent = 'As senhas não coincidem.'; ok = false; }

      btn.disabled = !ok;
    }

    [name,email,pwd,confirm].forEach(function(el){ if(el) el.addEventListener('input', validateCreate); });

    createForm.addEventListener('submit', function(e){
      e.preventDefault();
      validateCreate();
      if(!btn.disabled){
        // Aqui você pode integrar com API ou redirecionar
        alert('Conta criada (simulação) — enviar dados ao servidor.');
      }
    });
  }

  /* LOGIN */
  var loginForm = q('loginForm');
  if(loginForm){
    var le = q('loginEmail');
    var lp = q('loginPassword');
    var lb = q('loginBtn');

    function validateLogin(){
      q('loginEmailError').textContent = '';
      q('loginPasswordError').textContent = '';
      var ok = true;
      if(!isEmail(le.value)){ q('loginEmailError').textContent = 'Email inválido.'; ok = false; }
      if(lp.value.length < 6){ q('loginPasswordError').textContent = 'Senha inválida.'; ok = false; }
      lb.disabled = !ok;
    }

    [le,lp].forEach(function(el){ if(el) el.addEventListener('input', validateLogin); });

    loginForm.addEventListener('submit', function(e){
      e.preventDefault();
      validateLogin();
      if(!lb.disabled){
        // Simular login
        alert('Login efetuado (simulação) — autenticar no servidor.');
      }
    });
  }
})();
