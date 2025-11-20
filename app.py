from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, template_folder="suplementos_gym/templates")
app.secret_key = 'dev-secret'
# ---------------------- CONEXIÓN MONGO ----------------------
client = MongoClient('mongodb://localhost:27017/')
db = client['suplementos_gym']
productos_col = db['productos']
usuarios_col = db['usuarios']
pedidos_col = db['pedidos']

# ---------------------- FUNCIONES AUXILIARES ----------------------
def obtener_usuario():
    if 'user' in session:
        return usuarios_col.find_one({"_id": ObjectId(session['user']['_id'])})
    return None


def obtener_productos():
    productos_db = list(productos_col.find())
    productos_extra = [ ]
    return productos_db + productos_extra


def buscar_producto(producto_id):
    try:
        return productos_col.find_one({"_id": ObjectId(producto_id)})
    except:
        for p in obtener_productos():
            if str(p["_id"]) == str(producto_id):
                return p
    return None


# ---------------------- RUTAS PRINCIPALES ----------------------
@app.route('/')
def index():
    query = request.args.get('search', '')
    productos = obtener_productos()
    if query:
        productos = [p for p in productos if query.lower() in p['nombre'].lower()]
    return render_template('index.html', productos=productos, user=session.get('user'), current_year=datetime.now().year)


# ---------------------- REGISTRO ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if usuarios_col.find_one({"email": email}):
            return render_template('register.html', error="El correo ya está registrado")

        hashed = generate_password_hash(password)
        usuarios_col.insert_one({
            "nombre": nombre,
            "email": email,
            "password": hashed,
            "cart": []
        })
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------------- LOGIN ----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = usuarios_col.find_one({"email": email})
        if user and check_password_hash(user['password'], password):
            session['user'] = {"_id": str(user['_id']), "nombre": user['nombre'], "email": user['email']}
            return redirect(url_for('index'))
        return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')


# ---------------------- LOGOUT ----------------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


# ---------------------- DETALLE PRODUCTO ----------------------
@app.route('/producto/<producto_id>')
def producto_detalle(producto_id):
    producto = buscar_producto(producto_id)
    recomendados = [p for p in obtener_productos() if str(p["_id"]) != str(producto_id)]
    return render_template('product.html', producto=producto, productos=recomendados, user=session.get('user'))


# ---------------------- AGREGAR AL CARRITO ----------------------
@app.route('/agregar_carrito/<producto_id>', methods=['POST'])
def agregar_carrito(producto_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = obtener_usuario()

    # OBTENER CANTIDAD DESDE EL FORMULARIO
    cantidad = int(request.form.get('quantity', 1))

    carrito = user.get('cart', [])
    for item in carrito:
        if item['product_id'] == producto_id:
            item['quantity'] += cantidad
            break
    else:
        carrito.append({"product_id": producto_id, "quantity": cantidad})

    usuarios_col.update_one({"_id": user["_id"]}, {"$set": {"cart": carrito}})
    return redirect(url_for('cart'))



# ---------------------- CARRITO ----------------------
@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = obtener_usuario()
    cart_items = []
    total = 0

    for item in user.get('cart', []):
        producto = buscar_producto(item['product_id'])
        if producto:
            subtotal = producto['precio'] * item['quantity']
            total += subtotal
            producto['quantity'] = item['quantity']
            producto['subtotal'] = subtotal
            cart_items.append(producto)

    return render_template('cart.html', cart_items=cart_items, total=total, user=session.get('user'))


# ---------------------- ACTUALIZAR CANTIDAD ----------------------
@app.route('/update_cart/<product_id>', methods=['POST'])
def update_cart(product_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    nueva_cantidad = int(request.form.get('quantity', 1))
    user = obtener_usuario()
    carrito = user.get('cart', [])

    for item in carrito:
        if item['product_id'] == product_id:
            item['quantity'] = nueva_cantidad
            break

    usuarios_col.update_one({"_id": user["_id"]}, {"$set": {"cart": carrito}})
    return redirect(url_for('cart'))


# ---------------------- ELIMINAR PRODUCTO ----------------------
@app.route('/remove_from_cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    user = obtener_usuario()
    carrito = [item for item in user.get('cart', []) if item['product_id'] != product_id]
    usuarios_col.update_one({"_id": user["_id"]}, {"$set": {"cart": carrito}})
    return redirect(url_for('cart'))


# ---------------------- CHECKOUT ----------------------
@app.route('/checkout', methods=['GET'])
def checkout():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = obtener_usuario()
    cart_items = []
    total = 0

    for item in user.get('cart', []):
        producto = buscar_producto(item['product_id'])
        if producto:
            subtotal = producto['precio'] * item['quantity']
            total += subtotal
            producto['quantity'] = item['quantity']
            producto['subtotal'] = subtotal
            cart_items.append(producto)

    return render_template('checkout.html', cart_items=cart_items, total=total, user=session.get('user'))


# ---------------------- CONFIRMAR PEDIDO ----------------------
@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = obtener_usuario()
    nombre = request.form.get('nombre')
    direccion = request.form.get('direccion')
    metodo_pago = request.form.get('metodo_pago')

    cart_items = user.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))

    total = 0
    for item in cart_items:
        producto = buscar_producto(item['product_id'])
        if producto:
            total += producto['precio'] * item['quantity']

    pedidos_col.insert_one({
        "user_id": user["_id"],
        "nombre": nombre,
        "direccion": direccion,
        "metodo_pago": metodo_pago,
        "productos": cart_items,
        "total": total,
        "fecha": datetime.now()
    })

    usuarios_col.update_one({"_id": user["_id"]}, {"$set": {"cart": []}})

    return render_template('order_confirmation.html', user=session.get('user'))


# ---------------------- EJECUTAR APP ----------------------
if __name__ == '__main__':
    app.run(debug=True)



