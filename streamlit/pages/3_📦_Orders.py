import streamlit as st
import pandas as pd
from utils import load_data, show_cart_sidebar

st.set_page_config(
    page_title="Past Orders",
    page_icon="📦",
    layout="wide"
)

def display_order_details(order):
    st.write(f"**Order #{order['order_id']}**")
    st.write(f"Date: {order['date']}")
    st.write("Items:")
    for item in order['items']:
        st.write(f"• {item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}")
    st.write(f"**Total: ${order['total']:.2f}**")
    st.write("---")

def main():
    if not st.session_state.get('logged_in', False):
        st.error("Please login to view your orders")
        return

    show_cart_sidebar()
    
    st.title("📦 Your Orders")

    # Initialize orders in session state if not exists
    if 'orders' not in st.session_state:
        st.session_state.orders = []

    if not st.session_state.orders:
        st.info("You haven't placed any orders yet.")
        if st.button("Start Shopping"):
            st.switch_page("Home.py")
    else:
        # Filter orders for current user
        user_email = st.session_state.user_data['Email']
        user_orders = [order for order in st.session_state.orders 
                      if order['user_email'] == user_email]

        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            ["Most Recent", "Oldest First", "Price (High to Low)", "Price (Low to High)"]
        )

        # Apply sorting
        filtered_orders = user_orders.copy()
        
        if sort_by == "Most Recent":
            filtered_orders.sort(key=lambda x: x['date'], reverse=True)
        elif sort_by == "Oldest First":
            filtered_orders.sort(key=lambda x: x['date'])
        elif sort_by == "Price (High to Low)":
            filtered_orders.sort(key=lambda x: x['total'], reverse=True)
        elif sort_by == "Price (Low to High)":
            filtered_orders.sort(key=lambda x: x['total'])

        # Display orders
        for order in filtered_orders:
            with st.container():
                display_order_details(order)

        # Add download option
        if st.button("Download Order History"):
            # Convert orders to DataFrame
            orders_df = pd.DataFrame([
                {
                    'Order ID': order['order_id'],
                    'Date': order['date'],
                    'Total': order['total'],
                    'Items': ', '.join([f"{item['quantity']}x {item['name']}" for item in order['items']])
                }
                for order in filtered_orders
            ])
            
            # Convert DataFrame to CSV
            csv = orders_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "order_history.csv",
                "text/csv",
                key='download-csv'
            )

if __name__ == "__main__":
    main()



################# With date filter #################




# import streamlit as st
# import pandas as pd
# from utils import load_data, show_cart_sidebar

# st.set_page_config(
#     page_title="Past Orders",
#     page_icon="📦",
#     layout="wide"
# )

# def display_order_details(order):
#     st.write(f"**Order #{order['order_id']}**")
#     st.write(f"Date: {order['date']}")
#     st.write("Items:")
#     for item in order['items']:
#         st.write(f"• {item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}")
#     st.write(f"**Total: ${order['total']:.2f}**")
#     st.write("---")

# def main():
#     if not st.session_state.get('logged_in', False):
#         st.error("Please login to view your orders")
#         return

#     show_cart_sidebar()
    
#     st.title("📦 Your Orders")

#     # Initialize orders in session state if not exists
#     if 'orders' not in st.session_state:
#         st.session_state.orders = []

#     if not st.session_state.orders:
#         st.info("You haven't placed any orders yet.")
#         if st.button("Start Shopping"):
#             st.switch_page("Home.py")
#     else:
#         # Filter orders for current user
#         user_email = st.session_state.user_data['Email']
#         user_orders = [order for order in st.session_state.orders 
#                       if order['user_email'] == user_email]

#         # Add filter options
#         col1, col2 = st.columns([2, 2])
#         with col1:
#             # Date range filter
#             date_range = st.date_input(
#                 "Filter by date range",
#                 value=(min(pd.to_datetime([order['date'] for order in user_orders])),
#                       max(pd.to_datetime([order['date'] for order in user_orders]))),
#                 key="date_range"
#             )
        
#         with col2:
#             # Sort options
#             sort_by = st.selectbox(
#                 "Sort by",
#                 ["Most Recent", "Oldest First", "Price (High to Low)", "Price (Low to High)"]
#             )

#         # Apply filters and sorting
#         filtered_orders = user_orders.copy()
        
#         # Date filter
#         filtered_orders = [
#             order for order in filtered_orders
#             if date_range[0] <= pd.to_datetime(order['date']).date() <= date_range[1]
#         ]

#         # Sorting
#         if sort_by == "Most Recent":
#             filtered_orders.sort(key=lambda x: x['date'], reverse=True)
#         elif sort_by == "Oldest First":
#             filtered_orders.sort(key=lambda x: x['date'])
#         elif sort_by == "Price (High to Low)":
#             filtered_orders.sort(key=lambda x: x['total'], reverse=True)
#         elif sort_by == "Price (Low to High)":
#             filtered_orders.sort(key=lambda x: x['total'])

#         # Display orders
#         for order in filtered_orders:
#             with st.container():
#                 display_order_details(order)

#         # Add download option
#         if st.button("Download Order History"):
#             # Convert orders to DataFrame
#             orders_df = pd.DataFrame([
#                 {
#                     'Order ID': order['order_id'],
#                     'Date': order['date'],
#                     'Total': order['total'],
#                     'Items': ', '.join([f"{item['quantity']}x {item['name']}" for item in order['items']])
#                 }
#                 for order in filtered_orders
#             ])
            
#             # Convert DataFrame to CSV
#             csv = orders_df.to_csv(index=False)
#             st.download_button(
#                 "Download CSV",
#                 csv,
#                 "order_history.csv",
#                 "text/csv",
#                 key='download-csv'
#             )

# if __name__ == "__main__":
#     main()
