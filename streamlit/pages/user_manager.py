import pandas as pd

class UserManager:
    def __init__(self):
        self.users = pd.DataFrame(columns=['UserID', 'Email', 'Password', 'Age', 'Gender', 'Country'])
        
    def add_user(self, email, password, age, gender, country):
        user_id = len(self.users) + 1
        new_user = pd.DataFrame({
            'UserID': [user_id],
            'Email': [email],
            'Password': [password],
            'Age': [age],
            'Gender': [gender],
            'Country': [country]
        })
        self.users = pd.concat([self.users, new_user], ignore_index=True)
        return user_id

    def verify_user(self, email, password):
        user = self.users[
            (self.users['Email'] == email) & 
            (self.users['Password'] == password)
        ]
        if not user.empty:
            return user.iloc[0]
        return None
