
####################### Modification for order history ######################

import streamlit as st
import pandas as pd
from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

def get_stock_quantity(product_id, stocks_df):
    stock = stocks_df[stocks_df['ProductID'] == product_id]['Quantity'].iloc[0] if not stocks_df[stocks_df['ProductID'] == product_id].empty else 0
    return float(stock)

def display_recommendations(recommendations, stocks_df):
    if recommendations.empty:
        st.info("No recommendations available")
        return
        
    st.subheader("Frequently Bought Together")
    cols = st.columns(5)
    for idx, (_, product) in enumerate(recommendations.iterrows()):
        with cols[idx]:
            stock_qty = get_stock_quantity(product['ProductID'], stocks_df)
            
            st.write(f"**{product['FamilyLevel2']}**")
            st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
            st.write(f"Price: ${product['avg_price']:.2f}")
            st.write(f"Stock: {stock_qty}")
            
            if stock_qty > 0:
                quantity = st.number_input("Quantity", min_value=1, max_value=int(stock_qty), 
                                        value=1, key=f"qty_{product['ProductID']}")
                if st.button("🛒", key=f"rec_add_{product['ProductID']}"):
                    if 'cart' not in st.session_state:
                        st.session_state.cart = []
                    st.session_state.cart.append({
                        'id': product['ProductID'],
                        'name': product['FamilyLevel2'],
                        'price': product['avg_price'],
                        'quantity': quantity
                    })
                    st.rerun()
            else:
                st.error("Out of stock")

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
    # Load stock data
    stocks_df = pd.read_csv('stocks_dataset.csv')
    
    if df.empty or stocks_df.empty:
        st.error("Unable to load data")
        return
    
    # Display cart contents in main area
    st.subheader("Cart Contents")
    
    total = 0
    updated_cart = []
    
    for item in st.session_state.cart:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        # Get current stock for this item
        current_stock = get_stock_quantity(item['id'], stocks_df)
        
        with col1:
            st.write(f"**{item['name']}**")
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
            if st.button("🗑️", key=f"main_remove_{item['id']}"):
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
    
    # Checkout button
    if st.button("Proceed to Checkout"):
        # Check final stock before confirming
        can_checkout = True
        for item in st.session_state.cart:
            current_stock = get_stock_quantity(item['id'], stocks_df)
            if current_stock < item['quantity']:
                st.error(f"Not enough stock for {item['name']}")
                can_checkout = False
                break
        
        if can_checkout:
            # Create order record
            order = {
                'order_id': len(st.session_state.get('orders', [])) + 1,
                'user_email': st.session_state.user_data['Email'],
                'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'items': [
                    {
                        'id': item['id'],
                        'name': item['name'],
                        'price': item['price'],
                        'quantity': item['quantity']
                    }
                    for item in st.session_state.cart
                ],
                'total': total
            }
            
            # Initialize orders list if it doesn't exist
            if 'orders' not in st.session_state:
                st.session_state.orders = []
            
            # Add order to history
            st.session_state.orders.append(order)

            st.balloons()
            st.success("Order confirmed! Thank you for your purchase. 🎉")
            
            # Display order summary
            st.subheader("Order Summary")
            st.write("Thank you for shopping with us! Here's what you ordered:")
            for item in st.session_state.cart:
                st.write(f"• {item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}")
            st.write(f"**Total Amount:** ${total:.2f}")
            
            # Clear the cart
            st.session_state.cart = []
            
            st.info("A confirmation email will be sent to your registered email address.")
            
            if st.button("Continue Shopping"):
                st.rerun()

if __name__ == "__main__":
    main()


########## with STOCK and confirmation ######################


# import streamlit as st
# import pandas as pd
# from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

# def get_stock_quantity(product_id, stocks_df):
#     stock = stocks_df[stocks_df['ProductID'] == product_id]['Quantity'].iloc[0] if not stocks_df[stocks_df['ProductID'] == product_id].empty else 0
#     return float(stock)

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
#                         'quantity': quantity
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
        
#         with col1:
#             st.write(f"**{item['name']}**")
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
#         # Vérifier le stock final avant de confirmer
#         can_checkout = True
#         for item in st.session_state.cart:
#             current_stock = get_stock_quantity(item['id'], stocks_df)
#             if current_stock < item['quantity']:
#                 st.error(f"Not enough stock for {item['name']}")
#                 can_checkout = False
#                 break
        
#         if can_checkout:
#             # Add payment processing logic here
#             # Update stock in database here
#             st.balloons()  # Add some fun animation
#             st.success("Order confirmed! Thank you for your purchase. 🎉")
            
#             # Display order summary
#             st.subheader("Order Summary")
#             st.write("Thank you for shopping with us! Here's what you ordered:")
#             for item in st.session_state.cart:
#                 st.write(f"• {item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}")
#             st.write(f"**Total Amount:** ${total:.2f}")
            
#             # Clear the cart
#             st.session_state.cart = []
            
#             # Add a message about confirmation email
#             st.info("A confirmation email will be sent to your registered email address.")
            
#             # Add a button to continue shopping
#             if st.button("Continue Shopping"):
#                 st.rerun()

# if __name__ == "__main__":
#     main()



#################### With STOCK ############################


# import streamlit as st
# import pandas as pd
# from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

# def get_stock_quantity(product_id, stocks_df):
#     stock = stocks_df[stocks_df['ProductID'] == product_id]['Quantity'].iloc[0] if not stocks_df[stocks_df['ProductID'] == product_id].empty else 0
#     return float(stock)  # Convert to float as I see decimal numbers in your data

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
#                         'quantity': quantity
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
        
#         with col1:
#             st.write(f"**{item['name']}**")
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
#         # Vérifier le stock final avant de confirmer
#         can_checkout = True
#         for item in st.session_state.cart:
#             current_stock = get_stock_quantity(item['id'], stocks_df)
#             if current_stock < item['quantity']:
#                 st.error(f"Not enough stock for {item['name']}")
#                 can_checkout = False
#                 break
        
#         if can_checkout:
#             # Add payment processing logic here
#             # Update stock in database here
#             st.success("Order confirmed! Thank you for your purchase.")
#             st.session_state.cart = []
#             st.rerun()

# if __name__ == "__main__":
#     main()









################## Without STOCK ########################


# import streamlit as st
# import pandas as pd
# from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS



# def display_recommendations(recommendations):
#     if recommendations.empty:
#         st.info("No recommendations available")
#         return
        
#     st.subheader("Frequently Bought Together")
#     cols = st.columns(5)
#     for idx, (_, product) in enumerate(recommendations.iterrows()):
#         with cols[idx]:
#             st.write(f"**{product['FamilyLevel2']}**")
#             st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
#             st.write(f"Price: ${product['avg_price']:.2f}")
#             if st.button("🛒", key=f"rec_add_{product['ProductID']}"):
#                 if 'cart' not in st.session_state:
#                     st.session_state.cart = []
#                 st.session_state.cart.append({
#                     'id': product['ProductID'],
#                     'name': product['FamilyLevel2'],
#                     'price': product['avg_price']
#                 })
#                 st.rerun()


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
    
#     if df.empty:
#         st.error("Unable to load data")
#         return
    
#     # Display cart contents in main area
#     st.subheader("Cart Contents")
    
#     total = 0
#     for item in st.session_state.cart:
#         col1, col2, col3 = st.columns([3, 1, 1])
#         with col1:
#             st.write(f"**{item['name']}**")
#         with col2:
#             st.write(f"${item['price']:.2f}")
#         with col3:
#             if st.button("🗑️", key=f"main_remove_{item['id']}"):
#                 st.session_state.cart.remove(item)
#                 st.rerun()
#         total += item['price']
    
#     st.write("---")
#     st.write(f"**Total: ${total:.2f}**")
    
#     # Add recommendations
#     product_ids = [item['id'] for item in st.session_state.cart]
#     recommendations = get_frequently_bought_together(df, product_ids)
#     display_recommendations(recommendations)
    
#     # Checkout button
#     if st.button("Proceed to Checkout"):
#         # Add payment processing logic here
#         st.success("Order confirmed! Thank you for your purchase.")
#         st.session_state.cart = []
#         st.rerun()

# if __name__ == "__main__":
#     main()
