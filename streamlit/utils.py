import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    try:
        if "df" not in st.session_state:
            st.session_state.df = pd.read_parquet('../final_df.parquet')
        return st.session_state.df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def show_cart_sidebar():
    with st.sidebar:
        st.title("🛒 Mon Panier")
        
        if 'cart' not in st.session_state:
            st.session_state.cart = []
        
        if not st.session_state.cart:
            st.write("Votre panier est vide!")
            total = 0
        else:
            total = 0
            for item in st.session_state.cart:
                with st.container():
                    st.write("---")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**{item['name']}**")
                        st.write(f"{item['price']:.2f}€")
                    with col2:
                        if st.button("🗑️", key=f"remove_{item['id']}"):
                            st.session_state.cart.remove(item)
                            st.rerun()
                    total += item['price']
            
            st.write("---")
            st.write(f"**Total: {total:.2f}€**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Vider", key="clear_cart"):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Commander", key="checkout"):  # Removed type="primary"
                    if not st.session_state.get('logged_in', False):
                        st.error("Veuillez vous connecter")
                    else:
                        st.switch_page("pages/2_🛒_Cart.py")