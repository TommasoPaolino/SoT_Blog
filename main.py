from flask import render_template, url_for, redirect, flash
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from flask_login import UserMixin
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField
from wtforms.validators import Length, DataRequired, Email, EqualTo, ValidationError
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pythonping import ping
import os
from werkzeug.utils import secure_filename
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup


#CREAZIONE APP E DATABASE  --------------------------------------------------------------------------------------------------------------


app = Flask(__name__)


app.config['SECRET_KEY'] = '35f76991980ac9d1ec403f4391108054ae9ce824'
# Occhio al triplo slash
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'
WTF_CSRF_ENABLED = False
app.config['MAX_CONTENT_LENGTH'] = 2048 * 2048
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'static'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)



# dichiarazione delle tabelle

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(30), nullable=False,
                           default="default.png")
    posts = db.relationship('Post', backref="author", lazy=True)

    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    post_content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.id}', '{self.title}', '{self.date_posted}', '{self.user_id}')"
    
class Risposte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_answer = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    answer_content = db.Column(db.Text, nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_link = db.Column(db.String(200),  nullable=False)

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_comment = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    comment_content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)

#creazione db
with app.app_context():
    db.create_all()
conn = engine.connect()
#----------------------------------------------------------------------------------------------------------------------



#FUNZIONI -------------------------------------------------------------------------------------------------------------------

def save_image_file(image_file_obj):
    image_file_obj.save(os.path.join(os.getcwd(), 
                             "static", "images", secure_filename(image_file_obj.filename)))
    
    return secure_filename(image_file_obj.filename)

def html_code(url):

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
    LANGUAGE = "en-US,en;q=0.5"

    # Si dà lo user agent per determinare il browser (e quindi la disposizione dell'html)
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html = session.get(url)
    # create a new soup
    soup = BeautifulSoup(html.text, "html.parser")  #trasforma l'html in una sorta di contenitore dati (JSON, XML e etc.)
    return(soup)

def immagini_pagina(url):

    driver = webdriver.Firefox()
    driver.get(url)
    for i in [1000]:
        driver.execute_script(f"window.scrollTo(0, {i})")
        time.sleep(2)
    

    immagini = []
    for a in driver.find_elements(By.XPATH, "//*[name()='image']"):
        if(a.get_attribute('xlink:href')!= None):
            immagini.append(str(a.get_attribute('xlink:href')))


    driver.quit()
    return immagini
# ------------------------------------------------------------------------------------------------------------------------------



#WEB SCRAPING ---------------------------------------------------------------------------------------------------------

try:
    page  = str(ping("66.22.238.135")).split("\r")[0]  #ip del server di gioco di Sea of thieves a cui mi collego per controllare lo stato del server
    if("Reply" in page and  float(page.split(" ")[6].rsplit("ms")[0])< 800):
        terzo = True
    else:
        terzo = False
except:
    terzo = False


url = "https://www.seaofthieves.com/it/news" #Link da cui estraggo le news del gioco
url2 = "https://steamcharts.com/app/1172620" #Link da cui estraggo i dati statistici sul gioco
soup = html_code(url)
titoli = soup.findAll("h3", attrs={"class" : "article-panel__title heading-h2 variant-small-caps"})
paragrafi = soup.findAll("p", attrs={"class" : "article-panel__snippet"})
links = soup.findAll("a", attrs={"class" : "article-panel align-left"})
date = []
esistenti = []
with app.app_context():
    try:
        database = Page.query.all()
        for esistente in database:
            esistenti.append(esistente.page_link)
    except:
        pass
        

for link in links:
    soup = html_code(link["href"])
    stringa = soup.findAll("div", attrs={"class" : "article-meta article__block grid-item span-10 push-1 align-center transform-uppercase"})[0].findAll("p")[1].text
    date.append(stringa[stringa.index("il")+2:])
    if(link["href"] not in esistenti):
        pagina = Page(page_link = str(link["href"]),)
        with app.app_context():
            db.session.add(pagina)
            db.session.commit()

posts = []
for i in range(len(titoli)):
    posts.append({"fonte" : url ,"link": links[i]["href"] , "title": titoli[i].text, "content": paragrafi[i].text, "date": date[i]}) #creo i miei post sulla home

soup = html_code(url2)
primo = soup.find("div", attrs={"class": "app-stat"}).find("span", attrs={"class": "num"}).text
secondo = datetime.strptime(soup.find("div", attrs={"class": "app-stat"}).find("abbr")["title"], '%Y-%m-%dT%H:%M:%SZ').strftime('%d/%m/%Y %H:%M:%S')

statistiche = {"attuale": primo, "data": secondo, "attivita" : terzo}  #creo le statistiche da mostrare nella home



#VARIABILI GLOBALI -----------------------------------------------------------------------------------------------------------------

global immagini
immagini = {}
# -------------------------------------------------------------------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# FORMS ------------------------------------------------------------------------------------------------------------------------------
class PostForm(FlaskForm):
    titolo = StringField('Titolo', validators=[
                           Length(min=1, max=200), DataRequired()])
    domanda = StringField('Domanda', validators=[
                           Length(min=1, max=200), DataRequired()])
    submit = SubmitField('Pubblica')

class RispostaForm(FlaskForm):
    risposta = StringField('Rispondi', validators=[
                           Length(min=1, max=200), DataRequired()])
    submit = SubmitField('Pubblica')

class RegistrationForm(FlaskForm):

    username = StringField('Username', validators=[
                           Length(min=2, max=30), DataRequired()])
    email = StringField('Email', validators=[
                        Length(min=2, max=100), Email(), DataRequired()])
    password = PasswordField('Password', validators=[
                             Length(min=8, max=100), DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[Length(min=8, max=100),
                                                 DataRequired(),
                                                 EqualTo('password')])
    submit = SubmitField('Register Now!')
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already registered')

class ResetForm(FlaskForm):
    email = StringField('Email', validators=[
        Length(min=2, max=100), Email(), DataRequired()])
    submit = SubmitField('Send email!')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already registered')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
                        Length(min=2, max=100), Email(), DataRequired()])
    password = PasswordField('Password', validators=[
                             Length(min=8, max=100), DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class UpdateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        Length(min=2, max=30), DataRequired()])
    email = StringField('Email', validators=[
        Length(min=2, max=100), Email(), DataRequired()])
    image_file = FileField()

    submit = SubmitField('Update Your Profile!')


    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already registered')
#--------------------------------------------------------------------------------------------------------------------------

#ROUTES --------------------------------------------------------------------------------------------------------------------------------------- 

#ROUTES WEBSCRAPING
@app.route("/")
@app.route("/home") #permette di visualizzare le ultime notizie sul gioco e le statistiche(numero di giocatori , attività del server e etc.)
def home():
    immagine = []
    try:
        immagine = os.path.join("static", "images", current_user.image_file)
    except:
        pass
    return render_template("home.html", title="Home Page", posts=posts, statistiche = statistiche, numero=8, 
                           immagine = immagine)
@app.route("/pagina", methods=[ 'GET', 'POST']) #questa route permette di visualizzare l'articolo specifico su cui si è cliccato nella home
def pagina():
    
    form = RispostaForm()
    global immagini
    
    if request.method == 'POST':
        stringa_post = request.form.get('link').replace("\'", "")
        print(stringa_post)
        id= int(db.session.execute(db.select(Page).filter_by(page_link=stringa_post)).scalar_one().id)
        if(current_user.is_authenticated):
            if form.validate_on_submit():
                    answer = Comments(
                    date_comment = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S"),
                    comment_content = form.risposta.data,
                    page_id = id,
                    user_id = current_user.id
                    )
                    db.session.add(answer)
                    db.session.commit()
                    flash(f"Il tuo commento è stato pubblicato", category="success")
                    return redirect(f"/pagina?link='{stringa_post}'")
        else:
            flash(f"Devi fare il login per poter commentare !", category="danger")
            return redirect(f"/pagina?link='{stringa_post}'")
        
    
    
    
    if request.method == 'GET':
    
        stringa= request.args.get('link').replace("\'", "")        
        id= int(db.session.execute(db.select(Page).filter_by(page_link=stringa)).scalar_one().id)
        risposte = []

        for risposta in db.session.execute(db.select(Comments).filter_by(page_id=id)).scalars():
            dizionario = {"date_answer": risposta.date_comment, "comment_content": risposta.comment_content,
                      "username": db.session.execute(db.select(User).filter_by(id=risposta.user_id)).scalar_one().username}
            risposte.append(dizionario)
            

        
       
        
    
        if(stringa not in list(immagini.keys())):
            immagini[stringa] = []
            while len(immagini[stringa])==0:
                immagini[stringa] = immagini_pagina(stringa)
        else:
            while len(immagini[stringa])==0:
                immagini[stringa] = immagini_pagina(stringa)



        
        soup = html_code(stringa)
        titolo = soup.find("h1", attrs= {"class": "article__content-title article__block grid-item span-10 push-1"}).text

        soup = html_code(stringa)
        p = soup.find_all("div", attrs ={"class" : "article__text-block article__block grid-item span-10 push-1"})
        lista = []
        for div in p:
            for paragrafo in div.findAll("p"):
                lista.append(paragrafo)
        immagine = []
        try:
            immagine = os.path.join("static", "images", current_user.image_file)
        except:
            pass
   

        return render_template("pagina.html", link=stringa, title="Articolo", numero=16, paragrafi = lista, titolo_articolo = titolo, immagini = immagini[stringa],
                               form = form, risposte = risposte, immagine = immagine, link_utilizzato = stringa)


#ROUTES DEL FORUM
@app.route("/new_post", methods=['POST', 'GET']) #questa route permette di visualizzare i post pubblicati dagli utenti 
@login_required
def new_post():
    database = Post.query.all()
    domande = []
    for domanda in database:
        domande.append({"id":domanda.id, "title": domanda.title, "content": domanda.post_content, "date": domanda.date_posted, "autore": load_user(domanda.user_id).username})
    try:
        form = PostForm()
        if form.validate_on_submit():
            post = Post(title = form.titolo.data,
                date_posted = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S"),
                post_content = form.domanda.data,
                user_id = current_user.id
                )
            db.session.add(post)
            db.session.commit()
            flash("Il post è stato pubblicato", category="success")
            return redirect("/new_post") 
    except:
        flash('Login necessario', category='danger')
        return redirect("/new_post")
    
    immagine = []
    try:
        immagine = os.path.join("static", "images", current_user.image_file)
    except:
        pass
    else:
        return render_template("new_post.html", title="Forum", form = form, numero = 12, posts=domande, immagine=immagine)
    

@app.route("/new_answer", methods=['POST', 'GET']) #questa route permette di visualizzare le risposte pubblicate dagli utenti 
@login_required
def new_answer():
    form = RispostaForm()
    if request.method == 'POST':
        id_post = int(request.form.get('post_id').replace("\'", ""))
        print("ID : " , id_post)
        if form.validate_on_submit():
                answer = Risposte(
                    date_answer = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"%Y-%m-%d %H:%M:%S"),
                    answer_content = form.risposta.data,
                    post_id = id_post,
                    user_id = current_user.id
                    )
                db.session.add(answer)
                db.session.commit()
                flash(f"La risposta è stata pubblicata", category="success")
                return redirect(f"/new_answer?post='{id_post}'")
        

    if request.method == 'GET':  
        
        id= int(request.args.get('post').replace("\'", ""))

        post = db.session.execute(db.select(Post).filter_by(id=id)).scalar_one()
        autore = db.session.execute(db.select(User).filter_by(id=post.user_id)).scalar_one()
        risposte = []
    
        for risposta in db.session.execute(db.select(Risposte).filter_by(post_id=post.id)).scalars():
            dizionario = {"date_answer": risposta.date_answer, "answer_content": risposta.answer_content,
                        "username": db.session.execute(db.select(User).filter_by(id=risposta.user_id)).scalar_one().username}
            risposte.append(dizionario)

  

    immagine = []
    try:
        immagine = os.path.join("static", "images", current_user.image_file)
    except:
        pass

    return render_template(f"new_answer.html", title="Forum", form = form, numero = 12, post = post,
                            autore = autore.username, risposte = risposte, immagine = immagine, id=id)
    

#ROUTES DELL'UTENTE
@app.route("/login", methods=['POST', 'GET']) #route di login
def login():
    
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        candidate = form.password.data
        if user and bcrypt.check_password_hash(user.password, candidate):
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome {user.username}', category='success')
            return redirect('home')

        else:
            flash('Wrong email or password', category='danger')
            return redirect('login')
    else:
        
        return render_template("login.html", title="Login Page", numero = 4, form=form)


@app.route("/register", methods=['POST', 'GET']) #route di registrazione
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        password = form.password.data
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
                username=form.username.data,
                    password=pw_hash,
                    email=form.email.data)

        db.session.add(user)
        db.session.commit()

        flash(f"Your account has been created {form.username.data}", category="success")
        return redirect('/login')

    return render_template("register.html", title="Register Page", form=form, numero= 6)


@app.route("/logout") #route di logout
@login_required
def logout():
    logout_user()
    flash(f'Logged Out', category='info')
    return redirect('/home')

@app.route("/user_account") #route del profilo utente
@login_required
def user_account():
    image_file = url_for(
        'static', filename=f"images/{current_user.image_file}")
    
    immagine = []
    try:
        immagine = os.path.join("static", "images", current_user.image_file)
    except:
        pass

    return render_template("user_account.html", title=f"{current_user.username} page",
                           image_file=image_file, immagine = immagine)

@app.route("/user_account/edit", methods=['POST', 'GET']) #route del profilo utente per modificarlo
@login_required
def edit_user_account():
    image_file = url_for(
        'static', filename=f"images/{current_user.image_file}")

    form = UpdateUserForm()

    if form.validate_on_submit():

        updated = False
        if form.image_file.data:
            print(form.image_file.data)
            new_image_file_name = save_image_file(
                form.image_file.data)
            current_user.image_file = new_image_file_name
            updated = True

        if current_user.username != form.username.data:
            current_user.username = form.username.data
            updated = True

        if current_user.email != form.email.data:
            current_user.email = form.email.data
            updated = True
        if updated:
            db.session.commit()

        flash(
            f"Your account has been updated {form.username.data}", category="success")
        return redirect(url_for('user_account'))
    else:

        form.username.data = current_user.username
        form.email.data = current_user.email
    
    immagine = []
    try:
        immagine = os.path.join("static", "images", current_user.image_file)
    except:
            pass

    return render_template("edit_user_account.html", title=f"{current_user.username} update page",
                           image_file=image_file, form=form, numero=4, immagine = immagine)



app.run(host='0.0.0.0', port=5000, debug=True) #Esecuzione flask 