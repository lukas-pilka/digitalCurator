from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, SelectMultipleField
import engine

class SearchForm(FlaskForm):
    searchedClassSelect = SelectMultipleField(u'Object you are interested in:',
                                          choices=engine.getDetectedObjectsList())
    submit = SubmitField('Search many artworks')