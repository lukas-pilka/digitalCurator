from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, SelectMultipleField, StringField, IntegerField
from wtforms.validators import DataRequired
import engine

class SearchForm(FlaskForm):
    exhibitionName = StringField('What do you want to name this exhibition?',render_kw={"placeholder": "Digital curator's choice"})
    searchedClassSelect = SelectMultipleField('Displayed motifs',
                                              choices=engine.getDetectedObjectsList(),
                                              validators=[DataRequired('Select the motifs that the artworks should display')]
                                              )
    comparisonClassSelect = SelectMultipleField('Displayed motifs for comparison (Use this option to plot a graph comparing the frequency of motifs across history.)',
                                                choices=engine.getDetectedObjectsList())
    dateFrom = IntegerField('From')
    dateTo = IntegerField('To')
    submit = SubmitField('Explore ' + str(engine.getGalleriesSum()['artworks count']) + ' artworks')