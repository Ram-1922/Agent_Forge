from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import users_col
from pymongo import errors

def register_user(username, email, password):
    """
    Creates a new user account. Hashes the password for security.
    """
    try:
        # Check if user already exists
        if users_col.find_one({"username": username}):
            print("❌ Error: Username already exists. Please choose another.")
            return False
            
        if users_col.find_one({"email": email}):
            print("❌ Error: Email already registered.")
            return False

        # Hash the password (NEVER store plain text passwords)
        hashed_password = generate_password_hash(password)

        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now()
        }
        
        users_col.insert_one(new_user)
        print(f"✅ Success: Account created for '{username}'. Welcome aboard!")
        return True

    except errors.PyMongoError as e:
        print(f"❌ Database Error (Registration): {e}")
        return False

def login_user(username, password):
    """
    Verifies credentials and logs the user in.
    Returns the username if successful, None if failed.
    """
    try:
        user = users_col.find_one({"username": username})
        
        if not user:
            print("❌ Error: User not found.")
            return None
            
        # Check if the provided password matches the stored hash
        if check_password_hash(user['password'], password):
            print(f"🔓 Login successful! Welcome back, {username}.")
            return user['username']
        else:
            print("❌ Error: Incorrect password.")
            return None

    except errors.PyMongoError as e:
        print(f"❌ Database Error (Login): {e}")
        return None