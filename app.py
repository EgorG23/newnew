from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import re

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host="db",
        database="phonebook",
        user="admin",
        password="admin"
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM contacts ORDER BY full_name;')
    contacts = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', contacts=contacts)

@app.route('/add', methods=['POST'])
def add():
    full_name = request.form['full_name'].strip()
    phone_number = request.form['phone_number'].strip()
    note = request.form['note'].strip()

    # Валидация
    if not full_name:
        return "Поле 'ФИО' обязательно для заполнения!", 400
    
    if not re.fullmatch(r'^\+?[0-9]{10,15}$', phone_number):
        return "Номер должен содержать 10-15 цифр и может начинаться с +", 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO contacts (phone_number, full_name, note) VALUES (%s, %s, %s)',
            (phone_number, full_name, note)
        )
        conn.commit()
    except psycopg2.IntegrityError:
        return "Контакт с таким номером уже существует!", 400
    except Exception as e:
        return f"Ошибка: {str(e)}", 500
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/edit/<old_phone>', methods=['POST'])
def edit(old_phone):
    new_phone = request.form['phone_number'].strip()
    full_name = request.form['full_name'].strip()
    note = request.form['note'].strip()

    # Валидация
    if not full_name:
        return "Поле 'ФИО' обязательно для заполнения!", 400
    
    if not re.fullmatch(r'^\+?[0-9]{10,15}$', new_phone):
        return "Номер должен содержать 10-15 цифр и может начинаться с +", 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Если номер изменился
        if new_phone != old_phone:
            cur.execute('DELETE FROM contacts WHERE phone_number = %s', (old_phone,))
        
        cur.execute(
            'INSERT INTO contacts (phone_number, full_name, note) VALUES (%s, %s, %s) '
            'ON CONFLICT (phone_number) DO UPDATE SET full_name = EXCLUDED.full_name, note = EXCLUDED.note',
            (new_phone, full_name, note)
        )
        conn.commit()
    except Exception as e:
        return f"Ошибка: {str(e)}", 500
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete/<phone_number>')
def delete(phone_number):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM contacts WHERE phone_number = %s', (phone_number,))
        conn.commit()
    except Exception as e:
        return f"Ошибка: {str(e)}", 500
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
