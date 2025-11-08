import os
from flask import Flask, render_template, session, redirect, url_for, request, flash, render_template_string
import pandas as pd
from flask_mail import Mail, Message
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gajanankhakhra@gmail.com'
app.config['MAIL_PASSWORD'] = 'lufj csru dfnv nobq' 
# email_user = os.environ.get("EMAIL_USER")
# email_pass = os.environ.get("EMAIL_PASSWORD")

def get_cart_count():
    cart = session.get("cart", [])
    return sum(item["quantity"] for item in cart)

def load_products():
    df = pd.read_csv("static/products.csv")
    products = df.to_dict(orient="records")
    return products


@app.route('/')
def home():
    products = load_products()

    categories = defaultdict(list)
    for p in products:
        categories[p["category"]].append(p)

    cart = session.get("cart", [])
    cart_count = sum(item["quantity"] for item in cart)

    return render_template("index.html", categories=categories, cart_count=cart_count)


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    quantity = int(request.form.get("quantity", 1))
    products = load_products()
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return redirect(url_for("home"))

    cart = session.get("cart", [])

    for item in cart:
        if item["id"] == product_id:
            item["quantity"] += quantity
            break
    else:
        cart.append({
            "id": product["id"],
            "category": product["category"],
            "name": product["name"],
            "price": product["price"],
            "quantity": quantity
        })

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("home"))


@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/update_cart", methods=["POST"])
def update_cart():
    quantities = request.form.getlist("quantities")
    cart = session.get("cart", [])

    for product_id, qty in request.form.items():
        if product_id.startswith("quantities["):
            pid = product_id.split("[")[1].split("]")[0]
            for item in cart:
                if str(item["id"]) == pid:
                    item["quantity"] = int(qty)
                    break

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get("cart", [])
    cart = [item for item in cart if item["id"] != product_id]
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.route('/submit_order', methods=['POST'])
def submit_order():
    name = request.form.get('name')
    business_name = request.form.get('business_name')
    city = request.form.get('city')
    state = request.form.get('state')
    contact = request.form.get('contact')
    wholesale = 'Yes' if request.form.get('wholesale') else 'No'

    cart = session.get('cart', [])
    session['cart'] = []

    html_body = render_template_string("""
        <h2>🛍️ New Order Received</h2>
        <p><strong>Name:</strong> {{name}}</p>
        <p><strong>Business:</strong> {{business_name}}</p>
        <p><strong>City:</strong> {{city}}</p>
        <p><strong>State:</strong> {{state}}</p>
        <p><strong>Contact:</strong> {{contact}}</p>
        <p><strong>Wholesale:</strong> {{wholesale}}</p>
        <hr>
        <h4>🧾 Order Details</h4>
        <table border="1" cellpadding="6" cellspacing="0">
        <tr>
            <th>Category</th><th>Item</th><th>Qty</th><th>Price</th>
        </tr>
        {% for item in cart %}
        <tr>
            <td>{{ item.category }}</td>
            <td>{{ item.name }}</td>
            <td>{{ item.quantity }}</td>
            <td>₹{{ item.price }}</td>
        </tr>
        {% endfor %}
        </table>
        """, cart=cart, name=name, city=city, state=state, contact=contact, wholesale=wholesale, business_name=business_name)

    msg = Message(
        subject='New Order Received!',
        sender=app.config['MAIL_USERNAME'],
        recipients=['dedhiyanisarg16@gmail.com', 'dedhiyanirav07@gmail.com']
    )
    msg.html = html_body
    mail = Mail(app)
    mail.send(msg)

    flash("Order request submitted successfully! Our team will reach out to you shortly.", "success")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
