from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime, date
import uuid

app = Flask(__name__)

# Data file path
DATA_FILE = 'todos.json'

def load_todos():
    """Load todos from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_todos(todos):
    """Save todos to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(todos, f, indent=2, default=str)

def get_todos_for_date(selected_date):
    """Get todos for a specific date, sorted with completed tasks at the end"""
    todos = load_todos()
    date_todos = todos.get(selected_date, [])
    # Sort todos: incomplete tasks first, then completed tasks
    return sorted(date_todos, key=lambda x: (x.get('completed', False), x.get('created_at', '')))

@app.route('/')
def index():
    """Main page with calendar view"""
    selected_date = request.args.get('date', str(date.today()))
    todos = get_todos_for_date(selected_date)
    
    # Get all dates that have todos for calendar highlighting
    all_todos = load_todos()
    dates_with_todos = list(all_todos.keys())
    
    return render_template('index.html', 
                         todos=todos,
                         selected_date=selected_date,
                         dates_with_todos=dates_with_todos)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    """Add a new todo item"""
    data = request.get_json() if request.is_json else request.form
    task = data.get('task', '').strip()
    selected_date = data.get('date', str(date.today()))
    
    if not task:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Task cannot be empty'})
        return redirect(url_for('index', date=selected_date))
    
    todos = load_todos()
    if selected_date not in todos:
        todos[selected_date] = []
    
    new_todo = {
        'id': str(uuid.uuid4()),
        'task': task,
        'completed': False,
        'created_at': datetime.now().isoformat()
    }
    
    todos[selected_date].append(new_todo)
    save_todos(todos)
    
    if request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('index', date=selected_date))

@app.route('/toggle_todo', methods=['POST'])
def toggle_todo():
    """Toggle todo completion status"""
    data = request.get_json()
    todo_id = data.get('id')
    selected_date = data.get('date')
    
    todos = load_todos()
    if selected_date in todos:
        for todo in todos[selected_date]:
            if todo['id'] == todo_id:
                todo['completed'] = not todo['completed']
                todo['completed_at'] = datetime.now().isoformat() if todo['completed'] else None
                break
        
        # Re-sort the todos for this date (completed tasks move to end)
        todos[selected_date] = sorted(todos[selected_date], 
                                    key=lambda x: (x.get('completed', False), x.get('created_at', '')))
    
    save_todos(todos)
    return jsonify({'success': True})

@app.route('/delete_todo', methods=['POST'])
def delete_todo():
    """Delete a todo item"""
    data = request.get_json()
    todo_id = data.get('id')
    selected_date = data.get('date')
    
    todos = load_todos()
    if selected_date in todos:
        todos[selected_date] = [todo for todo in todos[selected_date] if todo['id'] != todo_id]
        
        if not todos[selected_date]:  # Remove date key if no todos left
            del todos[selected_date]
    
    save_todos(todos)
    return jsonify({'success': True})

@app.route('/edit_todo', methods=['POST'])
def edit_todo():
    """Edit a todo item"""
    data = request.get_json()
    todo_id = data.get('id')
    new_task = data.get('task', '').strip()
    selected_date = data.get('date')
    
    if not new_task:
        return jsonify({'success': False, 'error': 'Task cannot be empty'})
    
    todos = load_todos()
    if selected_date in todos:
        for todo in todos[selected_date]:
            if todo['id'] == todo_id:
                todo['task'] = new_task
                todo['updated_at'] = datetime.now().isoformat()
                break
    
    save_todos(todos)
    return jsonify({'success': True})


