# app.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os   
from datetime import datetime

app = Flask(__name__, template_folder='template')
app.secret_key = 'your_secret_key'  # Ändern Sie dies in der Produktion!


# connect to the Database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

#  Tables for register

#  Restaurants
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Restaurants (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        username TEXT NOT NULL,
        address TEXT NOT NULL,
        description TEXT,
        image_path TEXT,
        password_hash TEXT NOT NULL,
        opening_time TIME  NOT NULL,
        closing_time TIME  NOT NULL,
        delivery_radius TEXT
    )
''')


#  Clients
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Clients (
        id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        username TEXT NOT NULL,
        address TEXT NOT NULL,
        postal_code INTEGER  NOT NULL,
        password_hash TEXT NOT NULL
    )
''')
#  Menu Items
cursor.execute('''
    CREATE TABLE IF NOT EXISTS MenuItems (
        id INTEGER PRIMARY KEY,
        restaurant_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price FLOAT NOT NULL,
        image_path TEXT,
        FOREIGN KEY(restaurant_id) REFERENCES Restaurants(id)
    )
''')
# order table 
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Orders (
        id INTEGER PRIMARY KEY,
        client_id INTEGER NOT NULL,
        restaurant_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price FLOAT NOT NULL,
        notes TEXT,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status Text,
        FOREIGN KEY(client_id) REFERENCES Clients(id),
        FOREIGN KEY(restaurant_id) REFERENCES Restaurants(id),
        FOREIGN KEY(item_id) REFERENCES MenuItems(id)
    )
''')


# Save Tables and Closing database
conn.commit()
conn.close()



#  the main page 
@app.route('/')
def welcome():
    print("Reached the welcome route")
    return render_template('main.html')

#  choosing between Client or Restaurant
@app.route('/handle-choice', methods=['POST'])
def handle_choice():
    role = request.form.get('role')

    if role == 'client':
        return redirect(url_for('client_login'))
    elif role == 'restaurant':
        return redirect(url_for('restaurant_login'))
    

#  route for client-login 
@app.route('/client-login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # connect to Database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # calling client's data
        cursor.execute("SELECT * FROM Clients WHERE username=?", (username,))
        client = cursor.fetchone()

        # Checking the username and Password is correct?
        if client and check_password_hash(client[6], password):
            session['client_id'] = client[0]
            return redirect(url_for('client_main'))
        
    return render_template('client_login.html')



#  route for restaurant-login
@app.route('/restaurant-login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # connect to Database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Calling of Restaurant data
        cursor.execute("SELECT * FROM Restaurants WHERE username=?", (username,))
        restaurant = cursor.fetchone()

        # Checking the username and Password is correct?
        
        if restaurant and check_password_hash(restaurant[6], password):
            session['restaurant_id'] = restaurant[0]

            return redirect(url_for('restaurant_main'))
        print("Login successful. Redirecting to restaurant_main.")


    return render_template('restaurant_login.html')


@app.route('/restaurant-main')
def restaurant_main():
    if 'restaurant_id' in session:
        restaurant_id = session['restaurant_id']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Fetch necessary information for the dashboard
        cursor.execute("SELECT id, name FROM Restaurants WHERE id=?", (restaurant_id,))
        restaurant = cursor.fetchone()

        conn.close()

        restaurant_info = None  # Default value in case the restaurant is not found or there's an issue
        if restaurant:
            restaurant_info = {
                'id': restaurant[0],
                'name': restaurant[1],
            }
            session['restaurant_name'] = restaurant_info['name']

        return render_template('restaurant_main.html', restaurant_info=restaurant_info)
    
    return redirect(url_for('restaurant_login'))



@app.route('/client-register', methods=['GET', 'POST'])
def client_register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        address = request.form.get('address')
        postal_code = request.form.get('postal_code')
        password = request.form.get('password')

        # Hash password
        password_hash = generate_password_hash(password)

        # connect to Database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            # Adding Client's data to the table Clients
            cursor.execute("INSERT INTO Clients (first_name, last_name, username, address, postal_code, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
                           (first_name, last_name, username, address, postal_code, password_hash))

            # Save the Data and Closing the connection with data
            conn.commit()
            conn.close()
        except Exception as e:
            # Print or log the exception for debugging
            print(f"Error: {e}")

        return redirect(url_for('client_login'))

    return render_template('client_register.html')



#route for restaurant-register
@app.route('/restaurant-register', methods=['GET', 'POST'])
def restaurant_register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        address = request.form['address']
        description = request.form['description']
        image_path = request.form['image_path']
        password = request.form['password']
        opening_time = request.form['opening_time']
        closing_time = request.form['closing_time']
        delivery_radius = request.form['delivery_radius']

        # Split the comma-separated string into a list of permissible postal codes
        delivery_radius_list = [code.strip() for code in delivery_radius.split('/n')]

        # Convert the list to a comma-separated string for storage in the database
        delivery_radius_str = ','.join(delivery_radius_list)

        # Hash password
        password_hash = generate_password_hash(password)

        # connect to Database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        
        cursor.execute("INSERT INTO Restaurants (name, address, username, description, image_path, password_hash, opening_time, closing_time, delivery_radius) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (name, address, username, description, image_path, password_hash, opening_time, closing_time, delivery_radius or ''))



        # Save the Data and Closing the connection with data
        conn.commit()
        conn.close()

        
        return redirect(url_for('restaurant_login'))
    return render_template('restaurant_register.html')


#  Menu View
@app.route('/restaurant-menu', methods=['GET'])
def restaurant_menu():
    if session.get('restaurant_id'):
        restaurant_id = session['restaurant_id']

        # Connect to the Database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Calling to the menu Items of Restaurant
        cursor.execute("SELECT * FROM MenuItems WHERE restaurant_id=?", (restaurant_id,))
        menu_items = cursor.fetchall()

        # Debugging: Print the retrieved menu items
        print(f"Retrieved menu items: {menu_items}")

        # closing connection
        conn.close()

        return render_template('restaurant_menu.html', menu_items=menu_items)

    return redirect(url_for('restaurant_login'))




@app.route('/add-item', methods=['GET', 'POST'])
def add_menu_item():
    if 'restaurant_id' in session:
        file_path = None  # Initialize file_path
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']

         

            
            restaurant_id = session['restaurant_id']

            # connect to database
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            cursor.execute("INSERT INTO MenuItems (name, description, price, image_path, restaurant_id) VALUES (?, ?, ?, ?, ?)",
                           (name, description, price, file_path, restaurant_id))

            # save and close the connection
            conn.commit()
            conn.close()

            flash('Item was added to Item.', 'success')

        return render_template('add_menu_item.html')

    return redirect(url_for('restaurant_menu'))

#  Remove the item from the menu
@app.route('/remove-item/<int:item_id>', methods=['GET'])
def remove_menu_item(item_id):
    if 'restaurant_id' in session:
        # Connect to database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # remove the Item from database
        cursor.execute("DELETE FROM MenuItems WHERE id=?", (item_id,))

        # save and close the connection
        conn.commit()
        conn.close()

        flash('Item wurde von der Speisekarte entfernt.', 'success')

        return redirect(url_for('restaurant_menu'))

    return redirect(url_for('restaurant_main'))


#  Editing the Item 
@app.route('/edit-item/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    if 'restaurant_id' in session:
        # Connect to database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Initialize file_path with None
        file_path = None

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']

            

            # Update item in database
            cursor.execute("UPDATE MenuItems SET name=?, description=?, price=?, image_path=? WHERE id=?",
                           (name, description, price, file_path, item_id))

            # save and close the connection 
            conn.commit()
            conn.close()

            flash('Item was updated.', 'success')
            return redirect(url_for('restaurant_menu'))

        # Retrieve information about the item and display it in the form
        cursor.execute("SELECT * FROM MenuItems WHERE id=?", (item_id,))
        menu_item = cursor.fetchone()

        # close the connection
        conn.close()

        return render_template('edit_menu_item.html', menu_item=menu_item)

    return redirect(url_for('restaurant-main'))

# for filter restaurants depend on postal code and opening-time 
def query_restaurants_by_postal_code(postal_code):
    # Connect to the database and retrieve restaurants based on postal code
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()

        current_time = datetime.now().time()

        # Adjust the query according to your Restaurants table structure
        cursor.execute("SELECT * FROM Restaurants")
        restaurants = cursor.fetchall()

        filtered_restaurants = []

        for restaurant in restaurants:
            # Assuming the delivery radius is in the 10th column
            delivery_radius_str = restaurant[9]
            delivery_radius_list = [code.strip() for code in delivery_radius_str.replace('\r\n', ',').split(',')]


            # opening and closing times
            opening_time_str = restaurant[7]
            closing_time_str = restaurant[8]

            opening_time = datetime.strptime(opening_time_str, '%H:%M').time()
            closing_time = datetime.strptime(closing_time_str, '%H:%M').time()

            # Check if the user's postal code is in the delivery radius
            if postal_code in delivery_radius_list and opening_time <= current_time <= closing_time:
                filtered_restaurants.append(restaurant)
            

    return filtered_restaurants


# show the items of the restaurants
def query_menu_items_by_restaurant_id(restaurant_id):
    # Connect to the database and retrieve menu items based on restaurant ID
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()

        # Adjust the query according to your MenuItems table structure
        cursor.execute("SELECT * FROM MenuItems WHERE restaurant_id=?", (restaurant_id,))
        menu_items = cursor.fetchall()

    return menu_items

# Route to display the details of a specific restaurant
@app.route('/restaurant/<int:restaurant_id>', methods=['GET'])
def restaurant_detail(restaurant_id):
    if 'client_id' in session:
        # Query the database to get information about the selected restaurant
        restaurant = query_restaurant_by_id(restaurant_id)
        menu_items = query_menu_items_by_restaurant_id(restaurant_id)
        if restaurant:
            return render_template('restaurant_detail.html', restaurant=restaurant, menu_items=menu_items)
    return redirect(url_for('client_login'))

# Client-id
def get_client_by_id(client_id):
    # Connect to the database and retrieve the user by ID
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Adjust the query according to your Clients table structure
    cursor.execute("SELECT * FROM Clients WHERE id=?", (client_id,))
    client = cursor.fetchone()

    # Close the database connection
    conn.close()

    return client




# Restaurant-id
def query_restaurant_by_id(restaurant_id):
    # Connect to the database and retrieve restaurant information based on ID
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()

        # Adjust the query according to your Restaurants table structure
        cursor.execute("SELECT * FROM Restaurants WHERE id=?", (restaurant_id,))
        restaurant = cursor.fetchone()

    return restaurant

# Main for the User
@app.route('/client-main')
def client_main():
    if 'client_id' in session:
        client_id = session['client_id']
        # Assuming you have a User model with a postal_code field
        client = get_client_by_id(client_id)

        # Debugging: Print relevant information for the user
        print(f"Client ID: {client_id}")
        print(f"Client Data: {client}")

        if client:
            client_postal_code = client[5] if client and len(client) > 4 else None

            # Debugging: Print relevant information for the user's postal code
            print(f"Client's Original Postal Code: {client_postal_code}")

            # Normalize user's postal code to contain only digits
            normalized_client_postal_code = ''.join(filter(str.isdigit, str(client_postal_code)))

            # Debugging: Print relevant information for the normalized user's postal code
            print(f"Client's Normalized Postal Code: {normalized_client_postal_code}")

            # Query restaurants based on user postal code and opening times
            restaurants = query_restaurants_by_postal_code(normalized_client_postal_code)
            return render_template('client_main.html', client=client, restaurants=restaurants)


    return redirect(url_for('client_login'))


# Funktion zum Abrufen der Menüelemente für ein bestimmtes Restaurant aus der Datenbank
def get_menu_items(restaurant_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()


    # Datenbankabfrage, um die Menüelemente für das angegebene Restaurant abzurufen
    cursor.execute("SELECT * FROM MenuItems WHERE restaurant_id=?", (restaurant_id,))
    menu_items = cursor.fetchall()

    conn.close()
    return menu_items
# calling item details to history 
def get_menu_item_details(item_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM MenuItems WHERE id=?", (item_id,))
    menu_item = cursor.fetchone()

    return menu_item

# Assuming you have a function to get details of all ordered items for an order
def get_ordered_items(order_id):
    # connect to database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()   

        # Assuming your Orders table has a column named id as the primary key
    cursor.execute("SELECT * FROM Orders WHERE id=?", (order_id,))
    order = cursor.fetchone()

    ordered_items = []
    if order:
        # Access tuple elements by index
        item_id = order[3]
        quantity = order[4]

        # Fetch menu item details using the item_id
        menu_item = get_menu_item_details(item_id)

        # Create a dictionary with item details and quantity
        ordered_item = {
            'name': menu_item[2],
            'price': menu_item[4],
            'quantity': quantity,
        }

        ordered_items.append(ordered_item)

    return ordered_items

# client-history
def get_client_orders(client_id):
    # connect to database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM Orders WHERE client_id=? ORDER BY
            CASE
                WHEN status = 'In Progress' THEN 1
                WHEN status = 'Completed' THEN 2
                WHEN status = 'Cancelled' THEN 3
                ELSE 4
            END,
            order_date DESC""", (client_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders


# showing the client_order_history
@app.route('/client_order_history')
def client_order_history():
    if 'client_id' in session:
        client_id = session['client_id']
        orders = get_client_orders(client_id)
        orders_with_status = []

        for order in orders:
            order_id = order[0]
            status = get_order_status(order_id)  
            ordered_items = get_ordered_items(order_id)
            orders_with_status.append((order, status, ordered_items))

        return render_template('client_order_history.html', orders_with_status=orders_with_status)

    return redirect(url_for('client_login'))


# Restaurant_Order_history
@app.route('/restaurant_order_history')
def restaurant_order_history():
    if 'restaurant_id' in session:
        restaurant_id = session['restaurant_id']
        orders = get_restaurant_order_history(restaurant_id)

        orders_with_items = []

        for order in orders:
            order_id = order[0]
            status = get_order_status(order_id)
            ordered_items = get_ordered_items(order_id)

            order_with_items = {
                'order_details': order,  # Assuming order is a list or tuple
                'ordered_items': ordered_items
            }

            orders_with_items.append((status, order_with_items))

        return render_template('restaurant_order_history.html', orders_with_items=orders_with_items)

    return redirect(url_for('restaurant_login'))


def get_order_status(order_id):
    conn = sqlite3.connect('database.db')  # Replace with your actual database name
    cursor = conn.cursor()

    # Assuming your Orders table has columns 'id' and 'status'
    cursor.execute("SELECT status FROM Orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()

    # Close the database connection
    conn.close()

    if result:
        return result[0]  # Assuming the status is in the first column of the result
    else:
        return "Order Status Not Found"



# restaurant_order
def get_restaurant_order_history(restaurant_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT *
        FROM Orders
        WHERE restaurant_id = ?
        ORDER BY
            CASE
                WHEN status = 'In Progress' THEN 1
                WHEN status = 'Completed' THEN 2
                WHEN status = 'Cancelled' THEN 3
                ELSE 4
            END,
            order_date DESC""", (restaurant_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders


# update order status in datebase for cart and order in restaurant
def update_order_status_in_db(order_id, new_status):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Update the order status in the Orders table
    cursor.execute("UPDATE Orders SET status = ? WHERE id = ?", (new_status, order_id))

    # Commit the changes
    conn.commit()

    # Close the database connection
    conn.close()





@app.route('/restaurant/<int:restaurant_id>/menu')
def restaurant_menu_client(restaurant_id):
    if 'client_id' in session:
        # Hier rufen Sie die Menüelemente für das angegebene Restaurant ab
        restaurant = query_restaurant_by_id(restaurant_id)
        menu_items = get_menu_items(restaurant_id)
        return render_template('restaurant_menu_client.html', restaurant=restaurant, menu_items=menu_items)
    else:
        # Wenn der Benutzer nicht angemeldet ist, leiten Sie ihn zur Anmeldung weiter
        return redirect(url_for('client_login'))


# add the item to the card 
@app.route('/add_to_cart/<int:restaurant_id>/<int:item_id>', methods=['POST'])
def add_to_cart(restaurant_id, item_id):
    if 'client_id' in session:
        client_id = session['client_id']
        quantity = int(request.form.get('quantity', 1))

        # Connect to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve menu item details
        cursor.execute("SELECT * FROM MenuItems WHERE id=?", (item_id,))
        menu_item = cursor.fetchone()

        if menu_item:
            # Add item to the client's cart in the session
            cart_key = f"cart_{client_id}"
            cart = session.get(cart_key, [])
            cart.append({
                'restaurant_id': restaurant_id,
                'item_id': item_id,
                'name': menu_item[2],
                'price': menu_item[4],
                'quantity': quantity,
            })
            session[cart_key] = cart

            flash(f'{quantity} {menu_item[2]} added to your cart.', 'success')

        # Close the database connection
        conn.close()

    return redirect(url_for('restaurant_menu_client', restaurant_id=restaurant_id))

# Calculate the total price 
def calculate_total_price(cart_items):
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return total_price






#  Cart Overview 
@app.route('/cart_overview', methods=['GET', 'POST'])
def cart_overview():
    if 'client_id' in session:
        client_id = session['client_id']

        # Connect to the database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Retrieve cart items from the session
        cart_key = f"cart_{client_id}"
        cart = session.get(cart_key, [])

        # Fetch menu item details for items in the cart
        cart_items = []
        total_price = 0
        for item in cart:
            cursor.execute("SELECT * FROM MenuItems WHERE id=?", (item['item_id'],))
            menu_item = cursor.fetchone()
            if menu_item:
                total_price += menu_item[4] * item['quantity']
                # view cart-items in the html 
                cart_items.append({
                    'id': item['item_id'],  # Add item id to identify items uniquely
                    'name': menu_item[2],
                    'price': menu_item[4],
                    'quantity': item['quantity'],
                })

        # Handle updates, removals, and submit
        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'update':
                item_id = int(request.form.get('item_id'))
                new_quantity = int(request.form.get('quantity'))
                
                # Update the quantity in the session
                for item in cart:
                    if item['item_id'] == item_id:
                        item['quantity'] = new_quantity
                        break

                flash('Cart updated successfully!', 'success')

            elif action == 'remove':
                item_id = int(request.form.get('item_id'))
                
                # Remove the item from the cart in the session
                cart = [item for item in cart if item['item_id'] != item_id]

                flash('Item removed from the cart!', 'success')

            elif action == 'submit':
                additional_notes = request.form.get('additional_notes')
                

                # Check if the cart is not empty
                if cart:
                    # Fetch restaurant_id based on the items in the cart
                    restaurant_id = get_restaurant_id_for_cart(cart)

                    # Insert the order into the Orders table
                    cursor.executemany('''
                        INSERT INTO Orders (client_id, restaurant_id, item_id, quantity, notes, total_price, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', [(client_id, restaurant_id, item['item_id'], item['quantity'], additional_notes,  total_price, 'In Progress') for item in cart])

                    # Commit the changes to the database
                    conn.commit()

                    # Fetch the order_id after inserting into the Orders table
                    order_id = cursor.lastrowid

                    # Clear the cart in the session
                    session.pop(cart_key, None)

                    

                    flash('Order submited successfully!', 'success')
                else:
                    flash('Your cart is empty. Add items before Submit an order.', 'error')

                # Redirect to the thank you page after placing an order
                return redirect(url_for('cart_overview'))

            # Save the updated cart back to the session
            session[cart_key] = cart

            # Redirect to avoid form resubmission on refresh
            return redirect(url_for('cart_overview'))

        # Close the database connection
        conn.close()

        return render_template('cart_overview.html', cart_items=cart_items, total_price=total_price)

    return redirect(url_for('client_login'))


# get the restaurant_id in the cart 
def get_restaurant_id_for_cart(cart):
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # Check if the cart is not empty
        if cart:
            first_item_id = cart[0]['item_id']

            # Fetch restaurant_id based on the items in the cart
            cursor.execute("SELECT restaurant_id FROM MenuItems WHERE id=?", (first_item_id,))
            restaurant_id = cursor.fetchone()[0]

            return restaurant_id
        else:
            return None
    finally:
        # Close the database connection in the finally block
        conn.close()


# Updated Flask route
@app.route('/update_order_status_route', methods=['POST'])
def update_order_status_route():
    if 'restaurant_id' in session:
        restaurant_id = session['restaurant_id']

        order_id = request.form.get('order_id')
        if isinstance(order_id, tuple):
            order_id = order_id[0]

        try:
            order_id = int(order_id)
        except ValueError:
            return "Invalid order ID"    
        new_status = request.form.get('new_status')

        update_order_status_in_db(order_id, new_status)
        flash('Order status updated successfully!', 'success')

        return redirect(url_for('restaurant_order_history'))

    return redirect(url_for('client_login'))




if __name__ == '__main__':
    app.run(debug=True, port=5001)

