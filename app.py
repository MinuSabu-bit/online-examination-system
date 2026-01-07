# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, g, abort
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-change-this'  # change for production
app.config['DATABASE'] = os.path.join(app.root_path, 'exam_system.db')

# ----------------- Database helpers ----------------- #
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL CHECK (correct_option IN ('A','B','C','D'))
    );
    ''')
    db.commit()

# Initialize DB automatically if missing (when app starts)
with app.app_context():
    init_db()

# ----------------- Utility ----------------- #
def get_question_or_404(q_id):
    question = get_db().execute(
        'SELECT * FROM questions WHERE question_id = ?', (q_id,)
    ).fetchone()
    if question is None:
        abort(404, f"Question id {q_id} doesn't exist.")
    return question

# ----------------- Routes (CRUD) ----------------- #

# READ (list all questions)
@app.route('/')
@app.route('/questions')
def list_questions():
    db = get_db()
    rows = db.execute('SELECT * FROM questions ORDER BY question_id DESC').fetchall()
    return render_template('list_questions.html', questions=rows)

# CREATE (add new question)
@app.route('/questions/add', methods=('GET', 'POST'))
def add_question():
    if request.method == 'POST':
        q_text = request.form.get('question_text', '').strip()
        a = request.form.get('option_a', '').strip()
        b = request.form.get('option_b', '').strip()
        c = request.form.get('option_c', '').strip()
        d = request.form.get('option_d', '').strip()
        correct = request.form.get('correct_option', '').strip().upper()
        error = None

        if not q_text:
            error = 'Question text is required.'
        elif not (a and b and c and d):
            error = 'All four options are required.'
        elif correct not in ('A', 'B', 'C', 'D'):
            error = 'Correct option must be A, B, C or D.'

        if error is None:
            db = get_db()
            db.execute(
                'INSERT INTO questions (question_text, option_a, option_b, option_c, option_d, correct_option) VALUES (?,?,?,?,?,?)',
                (q_text, a, b, c, d, correct)
            )
            db.commit()
            flash('Question added successfully!')
            return redirect(url_for('list_questions'))

        flash(error)

    return render_template('add_question.html')

# UPDATE (edit an existing question)
@app.route('/questions/<int:q_id>/edit', methods=('GET', 'POST'))
def edit_question(q_id):
    question = get_question_or_404(q_id)

    if request.method == 'POST':
        q_text = request.form.get('question_text', '').strip()
        a = request.form.get('option_a', '').strip()
        b = request.form.get('option_b', '').strip()
        c = request.form.get('option_c', '').strip()
        d = request.form.get('option_d', '').strip()
        correct = request.form.get('correct_option', '').strip().upper()
        error = None

        if not q_text:
            error = 'Question text is required.'
        elif not (a and b and c and d):
            error = 'All four options are required.'
        elif correct not in ('A', 'B', 'C', 'D'):
            error = 'Correct option must be A, B, C or D.'

        if error is None:
            db = get_db()
            db.execute('''
                UPDATE questions
                SET question_text=?, option_a=?, option_b=?, option_c=?, option_d=?, correct_option=?
                WHERE question_id=?
            ''', (q_text, a, b, c, d, correct, q_id))
            db.commit()
            flash('Question updated successfully!')
            return redirect(url_for('list_questions'))

        flash(error)

    return render_template('edit_question.html', question=question)

# DELETE (remove a question)
@app.route('/questions/<int:q_id>/delete', methods=('POST',))
def delete_question(q_id):
    # No separate confirmation page here — the button in the list does a POST
    db = get_db()
    db.execute('DELETE FROM questions WHERE question_id=?', (q_id,))
    db.commit()
    flash('Question deleted.')
    return redirect(url_for('list_questions'))

# ----------------- Run ----------------- #
if __name__ == '__main__':
    # debug=True for development (auto-reloads on changes)
    app.run(debug=True)
