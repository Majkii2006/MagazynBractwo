from flask import Flask, render_template, url_for, redirect, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField, DateField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import os 
from email.mime.text import MIMEText
import smtplib


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SECRET_KEY'] = '967f38b36fbe26a1ab35b4bd6db7e6f1'

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#Dekorator, który umożliwi wejście pod url tylko dla zalogowanych użytkowników
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


#===================Konfiguracja wysyłania email=====================





#======================================================================


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))






#Linijka na dole powoduje, że python znajduje katalog instance i tam moze sobie utworzyć bazę
#inaczej to nie działa i nie da sie utworzyć bazy danych poleceniem db.create_all()
app.app_context().push()



class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable = False)
    password = db.Column(db.String(80), nullable = False)



class RegistrationForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nazwa użytkownika"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Hasło"})
    submit = SubmitField("Zarejestruj")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nazwa użytkownika"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Hasło"})
    submit = SubmitField("Zaloguj")



@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username = form.username.data, password = hashed_password )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                flash(f'Pomyślnie zalogowano, masz otwartą sesję dla {form.username.data}', 'success')
                return redirect(url_for('home_page'))
            else:
                flash("Wpisane hasło jest niepoprawne!", 'danger')
                return render_template('login.html', form=form)

        flash("Wpisana nazwa użytkownika jest niepoprawna!", 'danger')
        
    return render_template('login.html', form=form)

@app.route('/logout', methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for('login'))




class AddNewItemForm(FlaskForm):
     name = StringField('Nazwa', validators=[DataRequired(), Length(min=2, max=30)])
     category = StringField('Kategoria', validators=[DataRequired(), Length(min=2, max=30)])
     amount = IntegerField('Ilość', validators=[DataRequired()])
     localization = StringField('Lokalizacja', validators=[DataRequired(), Length(min=2, max=30)])
     notes = StringField('Uwagi')
     submit = SubmitField('Dodaj')
     

class AddNewPersonForm(FlaskForm):
    name = StringField('Imię', validators=[DataRequired(), Length(min=2, max=30)])
    surname = StringField('Nazwisko', validators=[DataRequired(), Length(min=2, max=30)])
    phone = StringField('Numer Telefonu', validators=[DataRequired(), Length(min=12, max=12)], default="+48")
    submit = SubmitField('Dodaj')


class AddNewRequest(FlaskForm):
    name = StringField('Imię', validators=[DataRequired()])
    surname = StringField('Nazwisko', validators=[DataRequired()])
    purpose = StringField('Cel wypożyczenia', validators=[DataRequired(), Length(min=2, max=80)])
    date_from = DateField('Od kiedy', format='%Y-%m-%d')
    date_to = DateField('Do kiedy', format='%Y-%m-%d')
    special_code = PasswordField('Kod zabezpieczający', validators=[DataRequired()])
    submit = SubmitField('Wyślij')
    

@app.route('/takerequest')
def take_request():
    items = Item.query.all()
    return render_template('take_request.html', items=items)

@app.route('/takerequestnext', methods=['POST'])
def take_request_next():
    items = Item.query.all()
    rental_request=[]
    for item in items:
        field_name = f"item_{item.id}"
        quantity = int(request.form.get(field_name, 0))

        if quantity>0:
            rental_request.append({"id": item.id, "name": item.name, "category": item.category, "amount": quantity})
            session['rental_request'] = rental_request

    return redirect('/takerequest/form')


@app.route('/takerequest/form', methods=["POST", "GET"])
def take_request_form():
    form = AddNewRequest()

    if form.validate_on_submit():

        name = form.name.data
        surname = form.surname.data
        purpose = form.purpose.data
        date_from = form.date_from.data
        date_to = form.date_to.data

        if form.special_code.data.lower() == "braczo":
            rental_request_person = []
            rental_request_person.append({"name": name, "surname": surname, "purpose": purpose, "date_from": date_from, "date_to": date_to})
            session['rental_request_person'] = rental_request_person
            print(rental_request_person)
            print(session.get('rental_request', []))

            body = ""
            for person in rental_request_person:
                body += (
                    f"Imię: {person['name']}\n"
                    f"Nazwisko: {person['surname']}\n"
                    f"Przeznaczenie: {person['purpose']}\n"
                    f"Od kiedy: {person['date_from']}\n"
                    f"Do kiedy: {person['date_to']}\n"
                )
            myEmail = 'magazynzdhbractwo@gmail.com'
            michael_email = 'michal.zadlo2020@gmail.com'
            cris_email = 'k.skupniewicz1@gmail.com'
            igantius_email = 'ignacy.wilkk@gmail.com'
            smtp_server = 'smtp.gmail.com'
            smtp_port = 587
            items = session.get('rental_request', [])
            body += "\nLista:\n"
            for item in items:
                body += f"{item['id']} - {item['name']} x{item['amount']}\n"

            msg = MIMEText(body, _charset="utf-8")
            msg['Subject'] = f'Nowe Wypożyczenie od {person['name']} {person['surname']}'
            msg['From'] = myEmail
            msg['To'] = ", ".join([cris_email, michael_email, igantius_email])


            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(myEmail, 'jmbeginrxugatvjc')

            server.send_message(msg)
            server.quit()


            flash('Wysłano prośbę o wypożyczenie, skontaktujemy się z tobą w najbliższym czasie.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Wpisałeś zły kod kontrolny', 'danger')
            return redirect(url_for('take_request_form'))

    return render_template('take_request_form.html', form=form)


    
class Rentals(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    person_name = db.Column(db.String(30))
    person_surname = db.Column(db.String(30))
    item_name = db.Column(db.String(30))
    item_category = db.Column(db.String(30))
    item_localization = db.Column(db.String(30))
    item_amount = db.Column(db.Integer())

@app.route('/rentals/confirm', methods=['POST'])
@login_required
def confirm_rentals():
    name = session.get('selected_person_name')
    surname = session.get('selected_person_surname')

    items = Item.query.all()

    for item in items:
        field_name = f"item_{item.id}"
        quantity = int(request.form.get(field_name, 0))

        if quantity>0:
            rental = Rentals(person_name = name, person_surname= surname, item_name = item.name, item_category=item.category, item_localization=item.localization, item_amount=quantity)
            db.session.add(rental)

            item.amount = item.amount-quantity
    
    db.session.commit()

    flash("Wypożyczenie zostało utworzone pomyślnie", 'success')
    return redirect(url_for('rentals_page'))



@app.route("/rentals")
@login_required
def rentals_page():
    rentals = Rentals.query.all()
    if rentals != []:
        return render_template('rentals.html', rentals=rentals)
    else:
        return render_template('rentals_if_empty.html')


@app.route('/rentals/return/<int:id>', methods=["POST", "GET"])
@login_required
def return_rentals_page(id):
    rental = Rentals.query.get_or_404(id)

    item = Item.query.filter_by(name=rental.item_name).first()

    if item:
        item.amount = item.amount + int(rental.item_amount)
    
    db.session.delete(rental)
    db.session.commit()

    flash("Wypożyczenie zostało zwrócone", "warning")
    return redirect(url_for('rentals_page'))



class Person(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    name = db.Column(db.String(length=30), nullable = False)
    surname = db.Column(db.String(length=30), nullable = False)
    phone = db.Column(db.String(length=12), nullable = False, unique = True)

    def __repr__(self):
        return f"{self.name}"


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    category = db.Column(db.String(length=30), nullable=False)
    amount = db.Column(db.Integer(), nullable=True)
    localization = db.Column(db.String(length=30), nullable=False)
    notes = db.Column(db.String(length=60), nullable=True)

    def __repr__(self):
        return f"{self.name}"

    




@app.route("/")
@app.route("/home")
@login_required
def home_page():
    return render_template('home.html')

@app.route("/magazine")
@login_required
def magazine_page():
    items = Item.query.all()   
    
    return render_template('magazine.html', items=items)


@app.route('/magazineview')
def magazine_view():
    items = Item.query.all()
    return render_template('magazine_view_only.html', items = items)

@app.route("/magazine/add", methods =['GET', 'POST'])
@login_required
def magazine_page_add():
    add_item_form = AddNewItemForm()
    if add_item_form.validate_on_submit():
        name = add_item_form.name.data
        category = add_item_form.category.data
        amount = add_item_form.amount.data
        localization = add_item_form.localization.data
        notes = add_item_form.notes.data

        try:
            new_item = Item(name=name, category=category, amount=amount, localization=localization, notes=notes)
            db.session.add(new_item)
            db.session.commit()
            flash(f'Dodano nowy rekord o nazwie {add_item_form.name.data}', 'success')
            return redirect(url_for('magazine_page'))
        except: 
            flash(f'Wystąpił błąd, prawdopodobnie istnieje już taka rzecz w bazie.', 'danger')
            return redirect(url_for('person_page_add'))
            
    return render_template('add_item.html', title='Add New Item', add_item_form=add_item_form)


@app.route('/magazine/delete/<int:id>')
@login_required
def magazine_page_delete(id):
    item_to_delete = Item.query.get_or_404(id)

    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        flash("Sprzęt pomyślnie usunięty z bazy danych", 'success')
        return redirect(url_for('magazine_page'))
    except:
        flash("Wystąpił problem przy usuwaniu tego sprzętu", "danger")
        return redirect(url_for('magazine_page'))
    

@app.route('/magazine/edit/<int:id>', methods=['POST', 'GET'])
@login_required
def magazine_page_edit(id):
    form = AddNewItemForm()
    item_to_update = Item.query.get_or_404(id)

    if request.method == "POST" and form.validate_on_submit():
        item_to_update.name = form.name.data
        item_to_update.category = form.category.data
        item_to_update.amount = form.amount.data
        item_to_update.localization = form.localization.data
        item_to_update.notes = form.notes.data

        try:
            db.session.commit()
            flash("Pomyślnie zaktualizowano sprzęt", "success")
            return redirect(url_for('magazine_page'))
        except:
            flash("Nie udało się zaktualizować sprzętu, spróbuj ponownie później")

    else:
        form.name.data = item_to_update.name
        form.category.data = item_to_update.category
        form.amount.data = item_to_update.amount
        form.localization.data = item_to_update.localization
        form.notes.data = item_to_update.notes
        return render_template('edit_item.html', add_item_form = form, item_to_update=item_to_update)








@app.route("/persons")
@login_required
def persons_page():
    persons = Person.query.all()
    return render_template('persons.html', persons=persons)




@app.route("/persons/add", methods=['POST', 'GET'])
@login_required
def person_page_add():
    add_person_form = AddNewPersonForm()
    if add_person_form.validate_on_submit():
        name = add_person_form.name.data
        surname = add_person_form.surname.data
        phone = add_person_form.phone.data
        
        try:
            new_person = Person(name=name, surname=surname, phone=phone)
            db.session.add(new_person)
            db.session.commit()
            flash(f'Dodano nową osobę o imieniu {add_person_form.name.data}', 'success')
            return redirect(url_for('persons_page'))
        except:
            flash(f'Wystąpił błąd, prawdopodobnie istnieje już taka osoba w bazie.', 'danger')
            return redirect(url_for('magazine_page_add'))
      

    return render_template('add_person.html', title="Add New Person", add_person_form=add_person_form)


@app.route('/persons/delete/<int:id>')
@login_required
def person_page_delete(id):
    person_to_delete=Person.query.get_or_404(id)

    try:
        db.session.delete(person_to_delete)
        db.session.commit()
        flash("Osoba pomyślnie usunięta z bazy danych", 'success')
        return redirect(url_for('persons_page'))
    except:
        flash("Wystąpił problem przy usuwaniu tej osoby", "danger")
        return redirect(url_for('persons_page'))
    



@app.route('/persons/edit/<int:id>', methods=['POST', 'GET'])
@login_required
def person_page_edit(id):
    person_to_update = Person.query.get_or_404(id)
    form = AddNewPersonForm()

    if request.method == 'POST' and form.validate_on_submit():
        person_to_update.name = form.name.data
        person_to_update.surname = form.surname.data
        person_to_update.phone = form.phone.data

        try:
            db.session.commit()
            flash("Dane osoby zostały zaktualizowane", 'success')
            return redirect(url_for('persons_page'))
        except:
            flash("Nie udało się zaktualizować osoby", 'danger')

    else:
        form.name.data = person_to_update.name
        form.surname.data = person_to_update.surname
        form.phone.data = person_to_update.phone

    return render_template(
        'edit_person.html',
        add_person_form=form,
        person_to_update=person_to_update
    )


@app.route('/persons/choose/<int:id>', methods=['GET'])
@login_required
def choose_person_page(id):
    person = Person.query.get_or_404(id)

    session['selected_person_id'] = person.id
    session['selected_person_name'] = person.name
    session['selected_person_surname'] = person.surname

    return redirect(url_for('choose_item_list'))



@app.route('/persons/choose', methods=['GET'])
@login_required
def choose_person_list():
    persons = Person.query.all()
    return render_template('rental_person_choose.html', persons=persons)





@app.route("/magazine/choose", methods=['GET'])
@login_required
def choose_item_list():
    items = Item.query.all()
    return render_template('rental_magazine_choose.html', items=items)





if __name__ == '__main__':
    app.run(debug=True)