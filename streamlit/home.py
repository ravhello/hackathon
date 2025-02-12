import streamlit as st
import pandas as pd
from utils import load_data, show_cart_sidebar, CATEGORY_EMOJIS
from sklearn.preprocessing import MinMaxScaler
from models.recommender import Recommender, get_personalized_recommendations, get_generic_recommendations

# Page config
st.set_page_config(
    page_title="Sport Marketplace",
    page_icon="🏃",
    layout="wide"
)


def main():
    show_cart_sidebar()
    
    st.title("🏃 Sport Marketplace")
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.error("Unable to load data")
        return
    
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        user = st.session_state.user_data
        st.write(f"Welcome {user['Email']}!")
        products = get_personalized_recommendations(df, user)
        st.subheader("Personalized Recommendations for You")
    else:
        products = get_generic_recommendations(df)
        st.subheader("Popular Products")
    
    # Display products in a grid
    if not products.empty:
        # Create a container for all products
        for idx, (_, product) in enumerate(products.iterrows()):
            if idx % 3 == 0:
                cols = st.columns(3)
            
            with cols[idx % 3]:
                st.write("---")
                st.write(f"**{product['FamilyLevel2']}**")
                st.write(f"{CATEGORY_EMOJIS[product['Category']]} | {product['Universe']}")
                st.write(f"Price: ${product['avg_price']:.2f}")
                
                if st.button("🛒", key=f"add_{product['ProductID']}"):
                    if 'cart' not in st.session_state:
                        st.session_state.cart = []
                    st.session_state.cart.append({
                        'id': product['ProductID'],
                        'name': product['FamilyLevel2'],
                        'price': product['avg_price']
                    })
                    st.rerun()
    else:
        st.warning("No products available at the moment.")

if __name__ == "__main__":
    main()
