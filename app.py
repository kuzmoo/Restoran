from flask import Flask, render_template, request, session, redirect, url_for, flash, current_app
import os
from werkzeug.utils import secure_filename
from functools import wraps

from flask_mysqldb import MySQL
import yaml
import hashlib

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.jinja_env.add_extension('jinja2.ext.do')
# flask_bootstrap.Bootstrap(app)

with open('db.yaml') as f:
    db = yaml.safe_load(f)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get('admin') != 1:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        korisnicko_ime = request.form['korisnicko_ime']
        ime_prezime = request.form['ime_prezime']
        email = request.form['email']
        sifra = request.form['sifra']
        
        hashed_sifra = hashlib.sha256(sifra.encode()).hexdigest()
      
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM login WHERE korisnicko_ime = %s OR email = %s", (korisnicko_ime, email))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Korisničko ime ili email već postoje', 'error')
            return redirect(url_for('register'))
        else:
            cur.execute("INSERT INTO login (korisnicko_ime, ime_prezime, email, sifra) VALUES (%s, %s, %s, %s)",
                        (korisnicko_ime, ime_prezime, email, hashed_sifra))
            mysql.connection.commit()
            cur.close()
            
            session['korisnicko_ime'] = korisnicko_ime
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        korisnicko_ime = request.form['korisnicko_ime']
        sifra = request.form['sifra']
        
        hashed_sifra = hashlib.sha256(sifra.encode()).hexdigest()
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM login WHERE korisnicko_ime = %s AND sifra = %s",
                    (korisnicko_ime, hashed_sifra))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session['korisnicko_ime'] = korisnicko_ime
            if 'admin' in [col[0] for col in cur.description]:
                admin_index = [col[0] for col in cur.description].index('admin')
                session['admin'] = user[admin_index]
            else:
                session['admin'] = False
            
            if session['admin']:
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Pogrešno korisničko ime ili šifra')
    
    return render_template('login.html')

@app.route('/')
def home():
    if 'korisnicko_ime' in session:
        korisnicko_ime = session['korisnicko_ime']
        return render_template('home.html', korisnicko_ime=korisnicko_ime)
    else:
        return redirect(url_for('login'))

@app.route('/odjava')
def odjava():
    session.pop('korisnicko_ime', None)
    return redirect(url_for('login'))


@app.route('/dodaj_jelo', methods=['GET', 'POST'])
@admin_required
def dodaj_jelo():
    if 'naziv' in request.form:
        naziv = request.form['naziv']
        opis = request.form['opis']
        cijena = request.form['cijena']
        slika = request.files['slika']

        if 'slika' not in request.files:
            flash('Niste odabrali sliku', 'error')
            return redirect(url_for('jelovnik'))

        slika = request.files['slika']
        if slika.filename == '':
            flash('Niste odabrali sliku', 'error')
            return redirect(url_for('jelovnik'))

        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not allowed_file(slika.filename, allowed_extensions):
            flash('Dozvoljeni formati slika su JPG, JPEG, PNG i GIF', 'error')
            return redirect(url_for('jelovnik'))

        filename = secure_filename(slika.filename)
        slika.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO jelovnik (naziv, opis, cijena, slika) VALUES (%s, %s, %s, %s)",
                    (naziv, opis, cijena, filename))
        mysql.connection.commit()
        cur.close()

        flash('Jelo uspješno dodato', 'success')
        return redirect(url_for('jelovnik'))
    return render_template('dodaj_jelo.html')

@app.route('/jelovnik')
def jelovnik():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, naziv, opis, cijena, slika FROM jelovnik")
    jela = []
    rows = cur.fetchall()
    for row in rows:
        jelo = {
            'id': row[0],
            'naziv': row[1],
            'opis': row[2],
            'cijena': row[3],
            'slika': row[4]
        }
        jela.append(jelo)
    cur.close()
    return render_template('jelovnik.html', jela=jela)

@app.route('/izmijeni_jelo/<int:jelo_id>', methods=['GET', 'POST'])
@admin_required
def izmijeni_jelo(jelo_id):

    jelo_data = {}

    if request.method == 'POST':
        naziv = request.form['naziv']
        opis = request.form['opis']
        cijena = request.form['cijena']
        slika = request.files['slika']
        if slika.filename != '':
            allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
            if not allowed_file(slika.filename, allowed_extensions):
                flash('Dozvoljeni formati slika su JPG, JPEG, PNG i GIF', 'error')
                return redirect(url_for('jelovnik'))

            filename = secure_filename(slika.filename)
            slika.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT slika FROM jelovnik WHERE id = %s", (jelo_id,))
            jelo = cur.fetchone()
            cur.close()
            if jelo:
                filename = jelo[0]
            else:
                filename = None

        cur = mysql.connection.cursor()
        cur.execute("UPDATE jelovnik SET naziv = %s, opis = %s, cijena = %s, slika = %s WHERE id = %s",
                    (naziv, opis, cijena, filename, jelo_id))
        mysql.connection.commit()
        cur.close()

        flash('Jelo uspješno izmijenjeno', 'success')
        return redirect(url_for('jelovnik'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, naziv, opis, cijena, slika FROM jelovnik WHERE id = %s", (jelo_id,))
    jelo = cur.fetchone()
    cur.close()

    if jelo:
        jelo_data = {
            'id': jelo[0],
            'naziv': jelo[1],
            'opis': jelo[2],
            'cijena': jelo[3],
            'slika': jelo[4]
        }
        return render_template('izmijeni_jelo.html', jelo=jelo_data)
    else:
        flash('Jelo nije pronađeno', 'error')
        return redirect(url_for('jelovnik'))

@app.route('/obrisi_jelo/<int:jelo_id>', methods=['GET', 'POST'])
@admin_required
def obrisi_jelo(jelo_id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT slika FROM jelovnik WHERE id = %s", (jelo_id,))
        jelo = cur.fetchone()
        if jelo:
            filename = jelo[0]
            if filename:
                upload_folder = app.config['UPLOAD_FOLDER']
                if isinstance(upload_folder, bytes):
                    upload_folder = upload_folder.decode()
                filename = filename.decode()  
                filepath = os.path.join(upload_folder, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            cur.execute("DELETE FROM jelovnik WHERE id = %s", (jelo_id,))
            mysql.connection.commit()
            cur.close()
            flash('Jelo uspješno obrisano', 'success')
            return redirect(url_for('jelovnik'))
        else:
            flash('Jelo nije pronađeno', 'error')
            return redirect(url_for('jelovnik'))
    
    return render_template('obrisi_jelo.html', jelo_id=jelo_id)

@app.route('/rezervacija', methods=['GET', 'POST'])
def rezervacija():
    if request.method == 'POST':
        ime_prezime = request.form['name']
        email = request.form['email']
        broj_telefona = request.form['phone']
        datum = request.form['date']
        vrijeme = request.form['time']
        broj_gostiju = request.form['guests']
        poruka = request.form['message']
        tip_rezervacije = request.form['reservationType']
        login_id = request.form['login_id']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO rezervacija (ime_prezime, email, broj_telefona, datum, vrijeme, broj_gostiju, poruka, tip_rezervacije, login_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (ime_prezime, email, broj_telefona, datum, vrijeme, broj_gostiju, poruka, tip_rezervacije, session.get('login_id')))
        mysql.connection.commit()
        cur.close()
        
        flash('Rezervacija uspješno poslana', 'success')
        return redirect(url_for('rezervacija'))
    
    if 'korisnicko_ime' in session:
        korisnicko_ime = session['korisnicko_ime']
        cur = mysql.connection.cursor()
        cur.execute("SELECT email, ime_prezime, id FROM login WHERE korisnicko_ime = %s", (korisnicko_ime,))
        user = cur.fetchone()
        cur.close()
        if user:
            email = user[0]
            ime_prezime = user[1]
            login_id = user[2]
        else:
            email = ''
            ime_prezime = ''
            login_id = None
    else:
        email = ''
        ime_prezime = ''
        login_id = None

    return render_template('rezervacija.html', email=email, ime_prezime=ime_prezime, login_id=login_id)

@app.route('/rezervacije')
@admin_required
def prikazi_rezervacije():
    cur = mysql.connection.cursor()
    cur.execute("SELECT ime_prezime, email, broj_telefona, datum, vrijeme, broj_gostiju, poruka, tip_rezervacije FROM rezervacija")
    rezervacije = cur.fetchall()
    cur.close()
    return render_template('rezervacije.html', rezervacije=rezervacije)

@app.route('/recenzija', methods=['GET', 'POST'])
def recenzija():
    if request.method == 'POST':
        ime_prezime = request.form['ime_prezime']
        email = request.form['email']
        poruka = request.form['poruka']
        ocjena = int(request.form['ocjena'])
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO recenzija (ime_prezime, email, poruka, ocjena, login_id) VALUES (%s, %s, %s, %s, %s)",
                    (ime_prezime, email, poruka, ocjena, session.get('login_id')))
        mysql.connection.commit()
        cur.close()
        
        flash('Recenzija uspješno poslata', 'success')
        return redirect(url_for('recenzija'))

    if 'korisnicko_ime' in session:
        korisnicko_ime = session['korisnicko_ime']
        cur = mysql.connection.cursor()
        cur.execute("SELECT email, ime_prezime FROM login WHERE korisnicko_ime = %s", (korisnicko_ime,))
        user = cur.fetchone()
        cur.close()
        if user is not None:
            email = user[0]
            ime_prezime = user[1]
        else:
            email = ''
            ime_prezime = ''

    else:
        email = ''
        ime_prezime = ''

    return render_template('recenzija.html', email=email, ime_prezime=ime_prezime)

@app.route('/recenzije')
@admin_required
def prikazi_recenzije():
    cur = mysql.connection.cursor()
    cur.execute("SELECT ime_prezime, email, poruka, ocjena FROM recenzija")
    recenzije = cur.fetchall()
    cur.close()
    return render_template('recenzije.html', recenzije=recenzije)



@app.route('/kontakt', methods=['GET', 'POST'])
def kontakt():
    if request.method == 'POST':
        ime_prezime = request.form['ime_prezime']
        email = request.form['email']
        naslov = request.form['naslov']
        poruka = request.form['poruka']
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO kontakt (ime_prezime, email, naslov, poruka, login_id) VALUES (%s, %s, %s, %s, %s)",
                    (ime_prezime, email, naslov, poruka, session.get('login_id')))
        mysql.connection.commit()
        cur.close()
        
        flash('Poruka uspješno poslana', 'success')
        return redirect(url_for('kontakt'))
    
    if 'korisnicko_ime' in session:
        korisnicko_ime = session['korisnicko_ime']
        cur = mysql.connection.cursor()
        cur.execute("SELECT email, ime_prezime FROM login WHERE korisnicko_ime = %s", (korisnicko_ime,))
        user = cur.fetchone()
        cur.close()
        if user is not None:
            email = user[0]
            ime_prezime = user[1]
        else:
            email = ''
            ime_prezime = ''

    else:
        email = ''
        ime_prezime = ''

    return render_template('kontakt.html', email=email, ime_prezime=ime_prezime)


@app.route('/kontakti')
@admin_required
def kontakti():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, ime_prezime, email, naslov, poruka FROM kontakt")
    kontakti = cur.fetchall()
    cur.close()
    return render_template('kontakti.html', kontakti=kontakti)

@app.route('/onama')
def onama():
    return render_template('onama.html')


@app.route('/dodaj_konobara', methods=['GET', 'POST'])
@admin_required
def dodaj_konobara():
    if request.method == 'POST':
        ime_prezime = request.form['ime_prezime']
        pozicija = request.form['pozicija']
        slika = request.files['slika']

        if 'slika' not in request.files:
            flash('Niste odabrali sliku', 'error')
            return redirect(url_for('dodaj_konobara'))

        slika = request.files['slika']

        if slika.filename == '':
            flash('Niste odabrali sliku', 'error')
            return redirect(url_for('dodaj_konobara'))

        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not allowed_file(slika.filename, allowed_extensions):
            flash('Dozvoljeni formati slika su JPG, JPEG, PNG i GIF', 'error')
            return redirect(url_for('dodaj_konobara'))

        filename = secure_filename(slika.filename)
        slika.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO radnici (ime_prezime, pozicija, slika) VALUES (%s, %s, %s)",
                    (ime_prezime, pozicija, filename))
        mysql.connection.commit()
        cur.close()

        flash('Konobar uspješno dodan', 'success')
        return redirect(url_for('radnici'))

    return render_template('dodaj_konobara.html')

@app.route('/radnici')
def radnici():
    cur = mysql.connection.cursor()
    cur.execute("SELECT ime_prezime, pozicija, slika FROM radnici")
    radnici = cur.fetchall()
    cur.close()
    return render_template('radnici.html', radnici=radnici)


@app.route('/admin/panel')
@admin_required
def admin_panel():
    return render_template('admin_panel.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404





def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'image')
if __name__ == '__main__':
    app.run(debug=True)