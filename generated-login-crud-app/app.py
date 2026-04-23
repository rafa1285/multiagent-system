from flask import Flask, jsonify, request

app = Flask(__name__)

HTML = """<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Login + CRUD Clientes</title>
  <style>
    body { font-family: Segoe UI, Tahoma, sans-serif; background: #f2f6fb; margin: 0; }
    .wrap { max-width: 920px; margin: 24px auto; padding: 0 12px; }
    .card { background: #fff; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,.08); padding: 16px; margin-bottom: 12px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    input, button { padding: 9px; border-radius: 8px; border: 1px solid #ccd; }
    button { border: none; background: #0d5f7a; color: #fff; font-weight: 600; cursor: pointer; }
    .hidden { display: none; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    th, td { border-bottom: 1px solid #eee; text-align: left; padding: 8px; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"card\" id=\"login\">
      <h2>Login</h2>
      <p>Demo: <b>admin</b> / <b>admin123</b></p>
      <div class=\"grid\">
        <input id=\"u\" placeholder=\"Usuario\" />
        <input id=\"p\" type=\"password\" placeholder=\"Password\" />
      </div>
      <div style=\"margin-top:8px\">
        <button onclick=\"login()\">Entrar</button>
        <span id=\"loginMsg\" style=\"color:#b00020\"></span>
      </div>
    </div>

    <div class=\"card hidden\" id=\"app\">
      <h2>CRUD Clientes</h2>
      <div class=\"grid\">
        <input id=\"n\" placeholder=\"Nombre\" />
        <input id=\"e\" placeholder=\"Email\" />
        <input id=\"t\" placeholder=\"Telefono\" />
        <input id=\"c\" placeholder=\"Ciudad\" />
      </div>
      <div style=\"margin-top:8px\">
        <button onclick=\"saveCustomer()\">Guardar</button>
        <button onclick=\"clearForm()\" style=\"background:#666\">Limpiar</button>
      </div>
      <table>
        <thead><tr><th>Nombre</th><th>Email</th><th>Telefono</th><th>Ciudad</th><th>Acciones</th></tr></thead>
        <tbody id=\"rows\"></tbody>
      </table>
    </div>
  </div>

  <script>
    const KEY = 'customers_v1';
    let editing = null;

    function login() {
      const u = document.getElementById('u').value.trim();
      const p = document.getElementById('p').value.trim();
      if (u === 'admin' && p === 'admin123') {
        document.getElementById('login').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');
        render();
      } else {
        document.getElementById('loginMsg').textContent = 'Credenciales invalidas';
      }
    }

    function list() {
      return JSON.parse(localStorage.getItem(KEY) || '[]');
    }

    function saveList(items) {
      localStorage.setItem(KEY, JSON.stringify(items));
    }

    function validate(c) {
      if (!c.name || c.name.length < 2) return 'Nombre invalido';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.email)) return 'Email invalido';
      if (!/^\+?[0-9\-\s]{7,20}$/.test(c.phone)) return 'Telefono invalido';
      if (!c.city) return 'Ciudad obligatoria';
      return '';
    }

    function clearForm() {
      editing = null;
      document.getElementById('n').value = '';
      document.getElementById('e').value = '';
      document.getElementById('t').value = '';
      document.getElementById('c').value = '';
    }

    function saveCustomer() {
      const customer = {
        id: editing || crypto.randomUUID(),
        name: document.getElementById('n').value.trim(),
        email: document.getElementById('e').value.trim(),
        phone: document.getElementById('t').value.trim(),
        city: document.getElementById('c').value.trim(),
      };

      const err = validate(customer);
      if (err) {
        alert(err);
        return;
      }

      const items = list();
      const idx = items.findIndex(x => x.id === customer.id);
      if (idx >= 0) items[idx] = customer; else items.push(customer);
      saveList(items);
      clearForm();
      render();
    }

    function editCustomer(id) {
      const c = list().find(x => x.id === id);
      if (!c) return;
      editing = id;
      document.getElementById('n').value = c.name;
      document.getElementById('e').value = c.email;
      document.getElementById('t').value = c.phone;
      document.getElementById('c').value = c.city;
    }

    function deleteCustomer(id) {
      saveList(list().filter(x => x.id !== id));
      render();
    }

    function render() {
      const body = document.getElementById('rows');
      body.innerHTML = '';
      list().forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML =
          `<td>${c.name}</td><td>${c.email}</td><td>${c.phone}</td><td>${c.city}</td>` +
          `<td><button onclick=\"editCustomer('${c.id}')\">Editar</button> ` +
          `<button style=\"background:#b00020\" onclick=\"deleteCustomer('${c.id}')\">Eliminar</button></td>`;
        body.appendChild(tr);
      });
    }
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    return HTML


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
