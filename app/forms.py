from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    searchedItem = SelectField(u'Object you are interested in:',
                               choices=[('book', 'book'), ('crown', 'crown'), ('woman', 'woman')])
    submit = SubmitField('Search many artworks')