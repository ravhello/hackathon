################################ Modern Structure only for frequently bought ################################

import streamlit as st
import pandas as pd
from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

def get_stock_quantity(product_id, stocks_df):
    stock = stocks_df[stocks_df['ProductID'] == product_id]['Quantity'].iloc[0] if not stocks_df[stocks_df['ProductID'] == product_id].empty else 0
    return float(stock)

def get_product_universe(product_id, df):
    universe = df[df['ProductID'] == product_id]['Universe'].iloc[0] if not df[df['ProductID'] == product_id].empty else 'N/A'
    return universe

def display_recommendations(recommendations, stocks_df):
    st.markdown("""
    <style>
    .recommendation-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }

    .recommendation-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    .product-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1a1a1a;
        margin-bottom: 0.8rem;
        min-height: 2.6em;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .product-category {
        font-size: 0.9rem;
        color: #666;
        background-color: #f8f9fa;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 0.8rem;
    }

    .product-price {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2E7D32;
        margin-bottom: 0.8rem;
    }

    .out-of-stock {
        color: #dc3545;
        font-weight: bold;
        padding: 0.5rem;
        text-align: center;
        background-color: #ffe6e6;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    if recommendations.empty:
        st.info("No recommendations available")
        return
        
    st.subheader("📦 Frequently Bought Together")
    
    cols = st.columns(4)
    for idx, (_, product) in enumerate(recommendations.head(4).iterrows()):
        with cols[idx]:
            stock_qty = get_stock_quantity(product['ProductID'], stocks_df)
            
            st.markdown(f"""
            <div class="recommendation-card">
                <div class="product-title">{product['FamilyLevel2']}</div>
                <div class="product-category">
                    {CATEGORY_EMOJIS[product['Category']]} {product['Universe']}
                </div>
                <div class="product-price">${product['avg_price']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if stock_qty > 0:
                quantity = st.number_input(
                    "Quantity", 
                    min_value=1, 
                    max_value=int(stock_qty),
                    value=1, 
                    key=f"qty_{product['ProductID']}"
                )
                if st.button("Add to Cart 🛒", key=f"add_{product['ProductID']}"):
                    if 'cart' not in st.session_state:
                        st.session_state.cart = []
                    st.session_state.cart.append({
                        'id': product['ProductID'],
                        'name': product['FamilyLevel2'],
                        'price': product['avg_price'],
                        'quantity': quantity,
                        'universe': product['Universe']
                    })
                    st.rerun()
            else:
                st.markdown('<div class="out-of-stock">Out of Stock</div>', 
                          unsafe_allow_html=True)

def main():
    if not st.session_state.get('logged_in', False):
        st.error("Please login to access your cart")
        return
        
    st.title("🛒 Cart")
    
    if not st.session_state.get('cart', []):
        st.write("Your cart is empty!")
        return
        
    # Load data
    df = load_data()
    stocks_df = pd.read_csv('stocks_dataset.csv')
    
    if df.empty or stocks_df.empty:
        st.error("Unable to load data")
        return
    
    st.subheader("Cart Contents")
    
    total = 0
    updated_cart = []
    
    for item in st.session_state.cart:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        current_stock = get_stock_quantity(item['id'], stocks_df)
        
        if 'universe' not in item or item['universe'] == 'N/A':
            item['universe'] = get_product_universe(item['id'], df)
        
        with col1:
            st.write(f"**{item['name']}**")
            st.write(f"*{item['universe']}*")
        with col2:
            st.write(f"${item['price']:.2f}")
        with col3:
            if current_stock > 0:
                new_quantity = st.number_input("Qty", 
                                            min_value=1,
                                            max_value=int(current_stock),
                                            value=item.get('quantity', 1),
                                            key=f"cart_qty_{item['id']}")
                item['quantity'] = new_quantity
            else:
                st.error("Out of stock")
                new_quantity = 0
        with col4:
            st.write(f"${item['price'] * item['quantity']:.2f}")
        with col5:
            if st.button("🗑️", key=f"remove_{item['id']}"):
                continue
        
        total += item['price'] * item['quantity']
        updated_cart.append(item)
    
    st.session_state.cart = updated_cart
    
    st.write("---")
    st.write(f"**Total: ${total:.2f}**")
    
    # Add recommendations
    product_ids = [item['id'] for item in st.session_state.cart]
    recommendations = get_frequently_bought_together(df, product_ids)
    display_recommendations(recommendations, stocks_df)
    
    if st.button("Proceed to Checkout"):
        can_checkout = True
        for item in st.session_state.cart:
            current_stock = get_stock_quantity(item['id'], stocks_df)
            if current_stock < item['quantity']:
                st.error(f"Not enough stock for {item['name']}")
                can_checkout = False
                break
        
        if can_checkout:
            order = {
                'order_id': len(st.session_state.get('orders', [])) + 1,
                'user_email': st.session_state.user_data['Email'],
                'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'items': [
                    {
                        'id': item['id'],
                        'name': item['name'],
                        'price': item['price'],
                        'quantity': item['quantity'],
                        'universe': item['universe']
                    }
                    for item in st.session_state.cart
                ],
                'total': total
            }
            
            if 'orders' not in st.session_state:
                st.session_state.orders = []
            
            st.session_state.orders.append(order)
            
            st.balloons()
            st.success("Order confirmed! Thank you for your purchase. 🎉")
            
            st.subheader("Order Summary")
            st.write("Thank you for shopping with us! Here's what you ordered:")
            for item in st.session_state.cart:
                st.write(f"• {item['quantity']}x {item['name']} ({item['universe']}) - ${item['price'] * item['quantity']:.2f}")
            st.write(f"**Total Amount:** ${total:.2f}")
            
            st.session_state.cart = []
            
            st.info("A confirmation email will be sent to your registered email address.")
            
            if st.button("Continue Shopping"):
                st.switch_page("1_🏠_Home.py")

if __name__ == "__main__":
    main()




# ################################ Modern structure ################################

# import streamlit as st
# import pandas as pd
# from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

# # Add custom CSS for card styling
# st.markdown("""
# <style>
# .cart-card {
#     background-color: white;
#     border: 1px solid #e0e0e0;
#     border-radius: 10px;
#     padding: 1.5rem;
#     margin: 1rem 0;
#     box-shadow: 0 2px 4px rgba(0,0,0,0.1);
# }

# .cart-item {
#     border: 1px solid #e0e0e0;
#     border-radius: 8px;
#     padding: 1rem;
#     margin: 0.5rem 0;
#     background-color: white;
#     box-shadow: 0 2px 4px rgba(0,0,0,0.05);
#     transition: transform 0.2s ease, box-shadow 0.2s ease;
# }

# .cart-item:hover {
#     transform: translateY(-2px);
#     box-shadow: 0 4px 8px rgba(0,0,0,0.1);
# }

# .product-name {
#     font-size: 1.1rem;
#     font-weight: bold;
#     color: #1a1a1a;
#     margin-bottom: 0.25rem;
# }

# .product-universe {
#     font-size: 0.9rem;
#     color: #666;
#     padding: 0.25rem 0.5rem;
#     background-color: #f8f9fa;
#     border-radius: 4px;
#     display: inline-block;
# }

# .price-tag {
#     font-size: 1.2rem;
#     font-weight: bold;
#     color: #2E7D32;
# }

# .recommendation-card {
#     background-color: white;
#     border: 1px solid #e0e0e0;
#     border-radius: 10px;
#     padding: 1rem;
#     margin: 0.5rem;
#     box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#     transition: transform 0.2s ease;
#     height: 100%;
# }

# .recommendation-card:hover {
#     transform: translateY(-5px);
#     box-shadow: 0 4px 8px rgba(0,0,0,0.2);
# }

# .total-section {
#     background-color: #f8f9fa;
#     padding: 1.5rem;
#     border-radius: 10px;
#     margin-top: 1.5rem;
#     border: 1px solid #e0e0e0;
# }

# .checkout-btn {
#     background-color: #1976D2;
#     color: white;
#     padding: 0.75rem 1.5rem;
#     border-radius: 5px;
#     border: none;
#     width: 100%;
#     font-size: 1.1rem;
#     margin-top: 1rem;
#     cursor: pointer;
#     transition: background-color 0.3s ease;
# }

# .checkout-btn:hover {
#     background-color: #1565C0;
# }

# .stock-info {
#     color: #666;
#     font-size: 0.9rem;
#     margin-top: 0.5rem;
# }

# .out-of-stock {
#     color: #dc3545;
#     font-weight: bold;
# }

# .stButton button {
#     width: 100%;
# }

# div[data-testid="stHorizontalBlock"] {
#     gap: 1rem;
#     padding: 0.5rem;
# }
# </style>
# """, unsafe_allow_html=True)

# def get_stock_quantity(product_id, stocks_df):
#     stock = stocks_df[stocks_df['ProductID'] == product_id]['Quantity'].iloc[0] if not stocks_df[stocks_df['ProductID'] == product_id].empty else 0
#     return float(stock)

# def get_product_universe(product_id, df):
#     universe = df[df['ProductID'] == product_id]['Universe'].iloc[0] if not df[df['ProductID'] == product_id].empty else 'N/A'
#     return universe

# def display_recommendations(recommendations, stocks_df):
#     if recommendations.empty:
#         st.info("No recommendations available")
#         return
        
#     st.subheader("📦 Frequently Bought Together")
#     cols = st.columns(4)
#     for idx, (_, product) in enumerate(recommendations.head(4).iterrows()):
#         with cols[idx]:
#             stock_qty = get_stock_quantity(product['ProductID'], stocks_df)
            
#             st.markdown(f"""
#             <div class="recommendation-card">
#                 <div class="product-name">{product['FamilyLevel2']}</div>
#                 <div class="product-universe">{CATEGORY_EMOJIS[product['Category']]} {product['Universe']}</div>
#                 <div class="price-tag">${product['avg_price']:.2f}</div>
#                 <div class="stock-info">Stock: {int(stock_qty)}</div>
#             </div>
#             """, unsafe_allow_html=True)
            
#             if stock_qty > 0:
#                 quantity = st.number_input("Quantity", min_value=1, max_value=int(stock_qty), 
#                                         value=1, key=f"qty_{product['ProductID']}")
#                 if st.button("Add to Cart 🛒", key=f"rec_add_{product['ProductID']}"):
#                     if 'cart' not in st.session_state:
#                         st.session_state.cart = []
#                     st.session_state.cart.append({
#                         'id': product['ProductID'],
#                         'name': product['FamilyLevel2'],
#                         'price': product['avg_price'],
#                         'quantity': quantity,
#                         'universe': product['Universe']
#                     })
#                     st.rerun()
#             else:
#                 st.markdown('<div class="out-of-stock">Out of stock</div>', unsafe_allow_html=True)

# def main():
#     if not st.session_state.get('logged_in', False):
#         st.error("Please login to access your cart")
#         return
        
#     st.title("🛒 Shopping Cart")
    
#     if not st.session_state.get('cart', []):
#         st.write("Your cart is empty!")
#         return
        
#     # Load data
#     df = load_data()
#     stocks_df = pd.read_csv('stocks_dataset.csv')
    
#     if df.empty or stocks_df.empty:
#         st.error("Unable to load data")
#         return
    
#     total = 0
#     updated_cart = []
    
#     st.markdown('<div class="cart-card">', unsafe_allow_html=True)
    
#     for item in st.session_state.cart:
#         current_stock = get_stock_quantity(item['id'], stocks_df)
        
#         if 'universe' not in item or item['universe'] == 'N/A':
#             item['universe'] = get_product_universe(item['id'], df)
        
#         st.markdown(f"""
#         <div class="cart-item">
#             <div class="product-name">{item['name']}</div>
#             <div class="product-universe">{item['universe']}</div>
#         """, unsafe_allow_html=True)
        
#         col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
#         with col1:
#             st.markdown(f'<div class="price-tag">${item["price"]:.2f}</div>', unsafe_allow_html=True)
            
#         with col2:
#             if current_stock > 0:
#                 new_quantity = st.number_input("Quantity", 
#                                             min_value=1,
#                                             max_value=int(current_stock),
#                                             value=item.get('quantity', 1),
#                                             key=f"cart_qty_{item['id']}")
#                 item['quantity'] = new_quantity
#             else:
#                 st.markdown('<div class="out-of-stock">Out of stock</div>', unsafe_allow_html=True)
#                 new_quantity = 0
                
#         with col3:
#             st.markdown(f'<div class="price-tag">Subtotal: ${item["price"] * item["quantity"]:.2f}</div>', 
#                        unsafe_allow_html=True)
            
#         with col4:
#             if st.button("🗑️", key=f"main_remove_{item['id']}"):
#                 continue
        
#         st.markdown('</div>', unsafe_allow_html=True)
        
#         total += item['price'] * item['quantity']
#         updated_cart.append(item)
    
#     st.markdown('</div>', unsafe_allow_html=True)
    
#     st.session_state.cart = updated_cart
    
#     # Total section
#     st.markdown(f"""
#     <div class="total-section">
#         <h3>Order Summary</h3>
#         <div class="price-tag">Total: ${total:.2f}</div>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # Add recommendations
#     product_ids = [item['id'] for item in st.session_state.cart]
#     recommendations = get_frequently_bought_together(df, product_ids)
#     display_recommendations(recommendations, stocks_df)
    
#     # Checkout section
#     if st.button("Proceed to Checkout", type="primary"):
#         can_checkout = True
#         for item in st.session_state.cart:
#             current_stock = get_stock_quantity(item['id'], stocks_df)
#             if current_stock < item['quantity']:
#                 st.error(f"Not enough stock for {item['name']}")
#                 can_checkout = False
#                 break
        
#         if can_checkout:
#             order = {
#                 'order_id': len(st.session_state.get('orders', [])) + 1,
#                 'user_email': st.session_state.user_data['Email'],
#                 'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'items': [
#                     {
#                         'id': item['id'],
#                         'name': item['name'],
#                         'price': item['price'],
#                         'quantity': item['quantity'],
#                         'universe': item['universe']
#                     }
#                     for item in st.session_state.cart
#                 ],
#                 'total': total
#             }
            
#             if 'orders' not in st.session_state:
#                 st.session_state.orders = []
            
#             st.session_state.orders.append(order)

#             st.balloons()
#             st.success("Order confirmed! Thank you for your purchase. 🎉")
            
#             st.subheader("Order Summary")
#             st.write("Thank you for shopping with us! Here's what you ordered:")
#             for item in st.session_state.cart:
#                 st.write(f"• {item['quantity']}x {item['name']} ({item['universe']}) - ${item['price'] * item['quantity']:.2f}")
#             st.write(f"**Total Amount:** ${total:.2f}")
            
#             st.session_state.cart = []
            
#             st.info("A confirmation email will be sent to your registered email address.")
            
#             if st.button("Continue Shopping"):
#                 st.switch_page("1_🏠_Home.py")

# if __name__ == "__main__":
#     main()



################################ Old strcuture ################################

# import streamlit as st
# import pandas as pd
# from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

# def get_stock_quantity(product_id, stocks_df):
#     stock = stocks_df[stocks_df['ProductID'] == product_id]['Quantity'].iloc[0] if not stocks_df[stocks_df['ProductID'] == product_id].empty else 0
#     return float(stock)

# def get_product_universe(product_id, df):
#     universe = df[df['ProductID'] == product_id]['Universe'].iloc[0] if not df[df['ProductID'] == product_id].empty else 'N/A'
#     return universe

# def display_recommendations(recommendations, stocks_df):
#     if recommendations.empty:
#         st.info("No recommendations available")
#         return
        
#     st.subheader("Frequently Bought Together")
#     cols = st.columns(5)
#     for idx, (_, product) in enumerate(recommendations.iterrows()):
#         with cols[idx]:
#             stock_qty = get_stock_quantity(product['ProductID'], stocks_df)
            
#             st.write(f"**{product['FamilyLevel2']}**")
#             st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
#             st.write(f"Price: ${product['avg_price']:.2f}")
#             st.write(f"Stock: {stock_qty}")
            
#             if stock_qty > 0:
#                 quantity = st.number_input("Quantity", min_value=1, max_value=int(stock_qty), 
#                                         value=1, key=f"qty_{product['ProductID']}")
#                 if st.button("🛒", key=f"rec_add_{product['ProductID']}"):
#                     if 'cart' not in st.session_state:
#                         st.session_state.cart = []
#                     st.session_state.cart.append({
#                         'id': product['ProductID'],
#                         'name': product['FamilyLevel2'],
#                         'price': product['avg_price'],
#                         'quantity': quantity,
#                         'universe': product['Universe']
#                     })
#                     st.rerun()
#             else:
#                 st.error("Out of stock")

# def main():
#     if not st.session_state.get('logged_in', False):
#         st.error("Please login to access your cart")
#         return
        
#     st.title("🛒 Cart")
    
#     if not st.session_state.get('cart', []):
#         st.write("Your cart is empty!")
#         return
        
#     # Load data
#     df = load_data()
#     # Load stock data
#     stocks_df = pd.read_csv('stocks_dataset.csv')
    
#     if df.empty or stocks_df.empty:
#         st.error("Unable to load data")
#         return
    
#     # Display cart contents in main area
#     st.subheader("Cart Contents")
    
#     total = 0
#     updated_cart = []
    
#     for item in st.session_state.cart:
#         col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
#         # Get current stock for this item
#         current_stock = get_stock_quantity(item['id'], stocks_df)
        
#         # Get or update universe information
#         if 'universe' not in item or item['universe'] == 'N/A':
#             item['universe'] = get_product_universe(item['id'], df)
        
#         with col1:
#             st.write(f"**{item['name']}**")
#             st.write(f"*{item['universe']}*")
#         with col2:
#             st.write(f"${item['price']:.2f}")
#         with col3:
#             if current_stock > 0:
#                 new_quantity = st.number_input("Qty", 
#                                             min_value=1,
#                                             max_value=int(current_stock),
#                                             value=item.get('quantity', 1),
#                                             key=f"cart_qty_{item['id']}")
#                 item['quantity'] = new_quantity
#             else:
#                 st.error("Out of stock")
#                 new_quantity = 0
#         with col4:
#             st.write(f"${item['price'] * item['quantity']:.2f}")
#         with col5:
#             if st.button("🗑️", key=f"main_remove_{item['id']}"):
#                 continue
        
#         total += item['price'] * item['quantity']
#         updated_cart.append(item)
    
#     st.session_state.cart = updated_cart
    
#     st.write("---")
#     st.write(f"**Total: ${total:.2f}**")
    
#     # Add recommendations
#     product_ids = [item['id'] for item in st.session_state.cart]
#     recommendations = get_frequently_bought_together(df, product_ids)
#     display_recommendations(recommendations, stocks_df)
    
#     # Checkout button
#     if st.button("Proceed to Checkout"):
#         # Check final stock before confirming
#         can_checkout = True
#         for item in st.session_state.cart:
#             current_stock = get_stock_quantity(item['id'], stocks_df)
#             if current_stock < item['quantity']:
#                 st.error(f"Not enough stock for {item['name']}")
#                 can_checkout = False
#                 break
        
#         if can_checkout:
#             # Create order record
#             order = {
#                 'order_id': len(st.session_state.get('orders', [])) + 1,
#                 'user_email': st.session_state.user_data['Email'],
#                 'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'items': [
#                     {
#                         'id': item['id'],
#                         'name': item['name'],
#                         'price': item['price'],
#                         'quantity': item['quantity'],
#                         'universe': item['universe']
#                     }
#                     for item in st.session_state.cart
#                 ],
#                 'total': total
#             }
            
#             # Initialize orders list if it doesn't exist
#             if 'orders' not in st.session_state:
#                 st.session_state.orders = []
            
#             # Add order to history
#             st.session_state.orders.append(order)

#             st.balloons()
#             st.success("Order confirmed! Thank you for your purchase. 🎉")
            
#             # Display order summary
#             st.subheader("Order Summary")
#             st.write("Thank you for shopping with us! Here's what you ordered:")
#             for item in st.session_state.cart:
#                 st.write(f"• {item['quantity']}x {item['name']} ({item['universe']}) - ${item['price'] * item['quantity']:.2f}")
#             st.write(f"**Total Amount:** ${total:.2f}")
            
#             # Clear the cart
#             st.session_state.cart = []
            
#             st.info("A confirmation email will be sent to your registered email address.")
            
#             if st.button("Continue Shopping"):
#                 # Navigate to home while keeping the session
#                 st.switch_page("1_🏠_Home.py")
                

# if __name__ == "__main__":
#     main()
