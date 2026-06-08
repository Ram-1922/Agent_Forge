import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

# Import your Custom AI Platform Modules
from auth import register_user, login_user
from builder import create_agent_blueprint
from executor import run_agent
from database import list_all_agents, get_agent_history
from database import list_all_agents, get_agent_history, delete_agent_blueprint
from database import list_all_agents, get_agent_history, get_user_email

app = Flask(__name__)
app.secret_key = "infynd_hackathon_super_secret_key" # Keep this safe!

# Configure Upload Folders
if not os.path.exists('credentials.json'):
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        with open('credentials.json', 'w') as f:
            f.write(creds_json)
UPLOAD_FOLDER = 'uploads'
os.makedirs(os.path.join(UPLOAD_FOLDER, 'builders'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'executors'), exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ==========================================
# 1. AUTHENTICATION (Login / Register)
# ==========================================
@app.route('/', methods=['GET', 'POST'])
def login_page():
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            username = request.form.get('username')
            password = request.form.get('password')
            user = login_user(username, password)
            if user:
                session['username'] = user
                return redirect(url_for('dashboard'))
            flash("Authentication failed. Check credentials.", "error")
                
        elif action == 'register':
            username = request.form.get('reg_username')
            email = request.form.get('reg_email')
            password = request.form.get('reg_password')
            if register_user(username, email, password):
                flash("Core Initialized. You may now Sign In.", "success")
            else:
                flash("Registration failed. ID or Email conflict.", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Session terminated securely.", "success")
    return redirect(url_for('login_page'))

# ==========================================
# 2. COMMAND CENTER (Dashboard)
# ==========================================
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html', username=session['username'])

# ==========================================
# 3. AGENT STUDIO (Architect Module)
# ==========================================
@app.route('/build', methods=['GET', 'POST'])
def build_agent():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    result = None
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        ref_file = request.files.get('reference_file')
        
        file_path = None
        if ref_file and ref_file.filename != '':
            filename = secure_filename(ref_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'builders', filename)
            ref_file.save(file_path)

        # Call the Architect Logic (builder.py)
        # RECTIFIED: Ensure your builder.py function matches these arguments
        try:
            blueprint = create_agent_blueprint(prompt, file_path)
            if blueprint:
                result = blueprint
            else:
                flash("Architect Error: Could not generate blueprint.", "error")
        except TypeError as e:
            flash(f"System Argument Error: {str(e)}", "error")
            print(f"ERROR: You must update create_agent_blueprint in builder.py! {e}")

    return render_template('agent_builder.html', result=result)

# ==========================================
# 4. DEPLOYMENT (Executor Module)
# ==========================================
@app.route('/run', methods=['GET', 'POST'])
def execute_agent():
    if 'username' not in session:
        return redirect(url_for('login_page'))

    # Fetch agent names AND their tools for the dynamic UI
    from database import agents_col
    agents_cursor = list(agents_col.find({}, {"agent_name": 1, "tools": 1, "_id": 0}))
    agents_list = [a['agent_name'] for a in agents_cursor]
    
    # Create a dictionary mapping: {"Agent Name": ["email", "doc_writer"]}
    agent_tools_map = {a['agent_name']: a.get('tools', []) for a in agents_cursor}

    result = None

    if request.method == 'POST':
        agent_name = request.form.get('agent_name')
        user_prompt = request.form.get('prompt') 
        is_authorized = request.form.get('auth_checkbox') == 'on'
        data_file = request.files.get('reference_file')
        
        # Grab ALL dynamic inputs
        app_password = request.form.get('app_password')
        sheet_link = request.form.get('sheet_link')
        doc_link = request.form.get('doc_link')
        slide_link = request.form.get('slide_link')
        
        user_email = get_user_email(session['username'])
        
        file_path = None
        if data_file and data_file.filename != '':
            filename = secure_filename(data_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'executors', filename)
            data_file.save(file_path)

        if agent_name:
            result = run_agent(
                agent_name=agent_name, 
                file_paths=[file_path] if file_path else [], 
                auto_approve=is_authorized, 
                current_username=session['username'],
                user_instructions=user_prompt,
                sender_email=user_email,
                sender_password=app_password,
                sheet_link=sheet_link,
                doc_link=doc_link,
                slide_link=slide_link
            )
            # ... (keep the rest of the flash messaging the same)
            if result and result.get('status') == 'success':
                flash(f"Deployment successful for {agent_name}.", "success")
            else:
                flash("Agent Loop Error: check logs below.", "error")
        else:
            flash("Please select an agent to run.", "error")

    # Pass the JSON map to the HTML template
    return render_template('agent_executor.html', agents=agents_list, agent_tools_json=json.dumps(agent_tools_map), result=result)

@app.route('/manage', methods=['GET', 'POST'])
def manage_agents():
    if 'username' not in session:
        return redirect(url_for('login_page'))
        
    if request.method == 'POST':
        agent_to_delete = request.form.get('delete_agent')
        if agent_to_delete:
            if delete_agent_blueprint(agent_to_delete):
                flash(f"Agent '{agent_to_delete}' terminated successfully.", "success")
            else:
                flash("Failed to delete agent.", "error")
                
    agents = list_all_agents()
    return render_template('manage_agents.html', agents=agents)

if __name__ == '__main__':
    print("\n" + "—"*50)
    print("🚀 AGENT OS: ONLINE")
    print("🔗 LOCAL ACCESS: http://127.0.0.1:5000")
    print("—"*50 + "\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)