import streamlit as st
import pandas as pd
from utils import load_data, get_frequently_bought_together, CATEGORY_EMOJIS

def display_recommendations(recommendations):
    if recommendations.empty:
        st.info("No recommendations available")
        return
        
    st.subheader("Frequently Bought Together")
    cols = st.columns(5)
    for idx, (_, product) in enumerate(recommendations.iterrows()):
        with cols[idx]:
            st.write(f"**{product['FamilyLevel2']}**")
            st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
            st.write(f"Price: ${product['avg_price']:.2f}")
            if st.button("🛒", key=f"rec_add_{product['ProductID']}"):
                if 'cart' not in st.session_state:
                    st.session_state.cart = []
                st.session_state.cart.append({
                    'id': product['ProductID'],
                    'name': product['FamilyLevel2'],
                    'price': product['avg_price']
                })
                st.rerun()


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
    
    if df.empty:
        st.error("Unable to load data")
        return
    
    # Display cart contents in main area
    st.subheader("Cart Contents")
    
    total = 0
    for item in st.session_state.cart:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{item['name']}**")
        with col2:
            st.write(f"${item['price']:.2f}")
        with col3:
            if st.button("🗑️", key=f"main_remove_{item['id']}"):
                st.session_state.cart.remove(item)
                st.rerun()
        total += item['price']
    
    st.write("---")
    st.write(f"**Total: ${total:.2f}**")
    
    # Add recommendations
    product_ids = [item['id'] for item in st.session_state.cart]
    recommendations = get_frequently_bought_together(df, product_ids)
    display_recommendations(recommendations)
    
    # Checkout button
    if st.button("Proceed to Checkout"):
        # Add payment processing logic here
        st.success("Order confirmed! Thank you for your purchase.")
        st.session_state.cart = []
        st.rerun()

if __name__ == "__main__":
    main()
