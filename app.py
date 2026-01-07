from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length
import phonenumbers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SECRET_KEY'] = '967f38b36fbe26a1ab35b4bd6db7e6f1'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


#Linijka na dole powoduje, że python znajduje katalog instance i tam moze sobie utworzyć bazę
#inaczej to nie działa i nie da sie utworzyć bazy danych poleceniem db.create_all()
app.app_context().push()

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

    
@app.route("/login")



@app.route("/")
@app.route("/home")
def home_page():
    return render_template('home.html')

@app.route("/magazine")
def magazine_page():
    items = Item.query.all()   
    
    return render_template('magazine.html', items=items)

@app.route("/magazine/add", methods =['GET', 'POST'])
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





@app.route("/persons")
def persons_page():
    persons = Person.query.all()
    return render_template('persons.html', persons=persons)




@app.route("/persons/add", methods=['POST', 'GET'])
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
            return redirect(url_for('persons_page'))
        except:
            flash(f'Wystąpił błąd, prawdopodobnie istnieje już taka osoba w bazie.', 'danger')
            return redirect(url_for('magazine_page_add'))
      

    return render_template('add_person.html', title="Add New Person", add_person_form=add_person_form)



@app.route("/rentals")
def rentals_page():
    return render_template('rentals.html')





if __name__ == '__main__':
    app.run(debug=True)