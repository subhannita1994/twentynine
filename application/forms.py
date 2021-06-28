from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, ValidationError


class StartGameForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    team = SelectField('Team', choices=[('red', 'Red'), ('blue', 'Blue')], validators=[DataRequired()])
    game_id = StringField('Game ID')
    submitJoin = SubmitField('Join Game')
    submitCreate = SubmitField('Create Game')

