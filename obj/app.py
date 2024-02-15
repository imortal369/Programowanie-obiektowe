from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pandas as pd


app = Flask(__name__)
app.secret_key = 'sekretny klucz'  # Klucz sekretny dla sesji

def generate_plot():
    #Importowanie danych z pliku pojazdy.csv
    pojazdy = pd.read_csv('pojazdy.csv')
    #Ustalenie wymiarów wykresu
    plt.figure(figsize=(12, 7))
    #Tytuł wykresu
    plt.title('Ilość pojazdów w 2023 z podziałaem na klasy emisji')
    #Opis dla osi x
    plt.xlabel('Miesiąc')
    #Opis dla osi Y
    plt.ylabel('Ilość pojazdów')
    #Generowanie lini na wykresie dla kądej kategori euro
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro 0 lub nieokreślona"], label='Euro 0 lub nieokreślona')
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro I"], label='Euro I', marker='.')
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro II"], label='Euro II', marker='.')
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro III"], label='Euro III', marker='.')
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro IV"], label='Euro IV', marker='.')
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro V"], label='Euro V', marker='.')
    plt.plot(pojazdy["Miesiąc"],pojazdy["Euro VI"], label='Euro VI', marker='.')
    #Pozycjonowanie legendy i przezroczystości jej tła
    legenda = plt.legend(loc='lower left',framealpha=0.2)
    #Rozmiar tekstu legendy
    plt.setp(legenda.texts, size=5)
    #Dodanie siatki do wykresu
    plt.grid()
    # Zapisz wykres do obiektu BytesIO w formacie png
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Konwertuj obrazek do base64
    img_base64 = base64.b64encode(img.getvalue()).decode()

    return img_base64


def create_table():
    # Połączenie z bazą danych
    conn = sqlite3.connect('users.db')
    # Utworzenie tabeli użytkowników, jeśli nie istnieje
    conn.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT PRIMARY KEY NOT NULL,
             password_hash TEXT NOT NULL);''')
    # Zakończenie połączenia z bazą danych
    conn.close()


def hash_password(password):
    # Funkcja zwracająca zaszyfrowane hasło
    return hashlib.sha256(password.encode()).hexdigest()



@app.route('/')
def home():
    if 'username' in session:
        # Generuj wykres
        plot = generate_plot()

        # Przekaż wykres do szablonu HTML
        return render_template('home.html', username=session["username"], plot=plot)
    return 'Witaj! <a href="/login">Zaloguj</a> lub <a href="/register">Zarejestruj się</a>'




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #Wymogi do długości loginu i hasła
        if len(username) < 5:
            return render_template('register.html', registration_failed=True)
        if len(password) < 8:
            return render_template('register.html', registration_failed=True)
        
        # Połączenie z bazą danych
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Sprawdzenie, czy użytkownik o podanej nazwie już istnieje
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return render_template('register.html', registration_failed=True)
        else:
            # Zaszyfrowanie hasła
            hashed_password = hash_password(password)
            # Wstawienie danych użytkownika do bazy danych
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
            
            # Zatwierdzenie zmian i zamknięcie połączenia z bazą danych
            conn.commit()
            conn.close()
            
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Połączenie z bazą danych
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Pobranie zaszyfrowanego hasła użytkownika z bazy danych
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        if user_data:
            hashed_password = user_data[0]
            # Sprawdzenie poprawności hasła
            if hashed_password == hash_password(password):
                session['username'] = username
                return redirect(url_for('home'))
        
        # Zatwierdzenie zmian i zamknięcie połączenia z bazą danych
        conn.commit()
        conn.close()
        
        return render_template('login.html', login_failed=True)
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    create_table()
    app.run(debug=True)
