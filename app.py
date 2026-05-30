from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, abort
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'gryffin_secret_spell'
BASE_PATH = os.path.abspath("do_not_open")

def init_users_db():
    if not os.path.exists('users.db'):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        users = [
            ('harry', 'expelliarmus'),
            ('hermione', 'lumos'),
            ('ron', 'eat_chicken'),
            ('voldemort', 'avada')
        ]
        c.executemany('INSERT INTO users (username, password) VALUES (?, ?)', users)
        conn.commit()
        conn.close()
        print("[+] users.db created with test users.")
    else:
        print("[✓] users.db already exists.")

    os.makedirs('flags', exist_ok=True)
    os.makedirs('hidden', exist_ok=True)

    if not os.path.exists('flags/real_flag_slytherin.txt'):
        with open('flags/real_flag_slytherin.txt', 'w') as f:
            f.write("real_flag_slytherin=Sly{serpent_clever_9}\n")

    with open('flags/fake_flags.txt', 'w') as f:
        f.write("sly!{nothing_to_see_here}\nsly!{wrong_path_try_again}\nsly!{decoy_flag_123}\n")

    with open('hidden/raven_hint.txt', 'w') as f:
        f.write("Riddle Answer Username: eagle_eye\nPassword: wisdom42\n")

    with open('hidden/snake_den.txt', 'w') as f:
        f.write("Username: sly_sneak\nPassword: pureblood123\n")

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()
        house = (request.form.get('house') or '').strip().lower()

        if house == 'gryffindor':
            try:
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
                print(f"[DEBUG] Executing query: {query}")
                cursor.execute(query)
                result = cursor.fetchone()
                if result:
                    return redirect(url_for('house_gryffindor'))
                else:
                    error = "🧨 Incorrect credentials!"
            except sqlite3.Error as e:
                error = f"🔥 Suspicious input detected! {e}"
            finally:
                conn.close()

        elif house == 'ravenclaw':
            if username == 'eagle_eye' and password == 'wisdom42':
                return redirect(url_for('ravenclaw_task'))
            else:
                error = "❌ Wrong credentials for Ravenclaw."

        elif house == 'hufflepuff':
            if username == 'badger' and password == 'cupcake':
                return redirect(url_for('hufflepuff_task'))
            else:
                error = "🧁 Try again..."

        elif house == 'slytherin':
            if username == '' and password == '':
                return redirect(url_for('slytherin_task'))
            else:
                error = "🪄 Use your brain to make it colourful!"

        else:
            error = "❓ Unknown house."

    return render_template('login.html', error=error)

@app.route('/house_gryffindor', methods=['GET', 'POST'])
def house_gryffindor():
    popup_token = "R3J5MTIz"
    flag_found = False
    real_flag = "Gry{bravery_is_123}"

    if request.method == 'POST':
        decoded = request.form.get('decoded', '').strip()
        if decoded == popup_token:
            session['gryffindor'] = True
            flag_found = True

    return render_template('house_gryffindor.html', flag_found=flag_found, flag_value=real_flag if flag_found else None, popup_token=popup_token)

@app.route('/ravenclaw', methods=['GET', 'POST'])
def ravenclaw_task():
    if request.method == 'POST':
        token = request.form.get('challenge_token')
        if token and token.strip().lower() == 'echo':
            session['ravenclaw'] = True
            return jsonify({'flag': 'Rav{wit_and_wisdom_42}'})
    return render_template('house_ravenclaw.html')

@app.route('/hufflepuff', methods=['GET', 'POST'])
def hufflepuff_task():
    result = None
    show_flags = False

    if request.method == 'POST':
        answer = request.form.get('puzzle_answer', '').strip().lower()
        if answer == 'loyalty':
            show_flags = True
            session['hufflepuff'] = True
        else:
            result = "❌ Incorrect! A true Hufflepuff must be precise."

    return render_template('house_hufflepuff.html', result=result, show_flags=show_flags)

@app.route('/slytherin')
def slytherin_task():
    file = request.args.get('file')
    flag_found = False
    error = None
    content = None

    if file:
        try:
            requested_path = os.path.realpath(os.path.join(BASE_PATH, file))
            if not requested_path.startswith(BASE_PATH):
                raise Exception("⛔ Access denied! Directory traversal blocked.")
            if not os.path.isfile(requested_path):
                raise Exception("📁 No such file exists.")
            with open(requested_path, 'r') as f:
                content = f.read()
                if "Sly{" in content:
                    session['slytherin'] = True
                    flag_found = True
        except Exception as e:
            error = str(e)

    return render_template('house_slytherin.html', content=content, error=error, flag_found=flag_found)

@app.route('/final_chamber', methods=['GET', 'POST'])
def final_chamber():
    required_flags = {
        'gryffindor': 'Gry{bravery_is_123}',
        'ravenclaw': 'Rav{wit_and_wisdom_42}',
        'hufflepuff': 'Huf{loyal_and_true}',
        'slytherin': 'Sly{serpent_clever_9}'
    }

    # Check if user completed all houses
    if not all(session.get(house) for house in required_flags):
        return render_template('not_unlocked.html')

    real_flag = None
    error = None

    if request.method == 'POST':
        user_flags = {
            'gryffindor': request.form.get('gryffindor', '').strip(),
            'ravenclaw': request.form.get('ravenclaw', '').strip(),
            'hufflepuff': request.form.get('hufflepuff', '').strip(),
            'slytherin': request.form.get('slytherin', '').strip()
        }

        # Debug print
        print("User Submitted Flags:", user_flags)

        all_correct = all(user_flags[house] == required_flags[house] for house in required_flags)

        if all_correct:
            real_flag = "Arc{united_magic_four}"
        else:
            error = "❌ One or more flags are incorrect. Double check and try again."

    return render_template('final_chamber.html', real_flag=real_flag, error=error)


@app.route('/snake_den/<filename>')
def serve_slytherin_hint(filename):
    try:
        return send_from_directory('hidden', filename)
    except:
        return "🛑 File not found!", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/hidden/<path:filename>')
def serve_hidden_file(filename):
    try:
        return send_from_directory('hidden', filename)
    except FileNotFoundError:
        abort(404)

@app.route('/hidden/')
def list_hidden():
    files = os.listdir('hidden')
    return '<br>'.join(files)

@app.errorhandler(403)
def time_up(e):
    return render_template('time_up.html', message=str(e)), 403

if __name__ == '__main__':
    init_users_db()
    app.run(debug=True)
