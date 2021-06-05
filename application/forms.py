from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, ValidationError


class StartGameForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    team = SelectField('Team', choices=[('red', 'Red'), ('blue', 'Blue')], validators=[DataRequired()])
    gameid = StringField('Game ID')
    submitJoin = SubmitField('Join Game')
    submitCreate = SubmitField('Create Game')

    def validate_gameid(self, gameid):
        if self.submitJoin.data and len(self.gameid.data.strip()) == 0:
            raise ValidationError('Game ID must be entered to join a game')
