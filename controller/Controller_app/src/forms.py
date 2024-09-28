# This file defines all the forms used in this app #

# Imports #
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired





# Forms #
class ScanForm(FlaskForm): 
    ip = StringField('IP Adress or Range',
                       validators=[DataRequired()])
    scan_type = SelectField("Scan Type", choices=[('-sS', 'Syn Scan'), 
                                                  ('-sV', 'Version Scan'), 
                                                  ('-O', 'System Scan'), 
                                                  ('-sF', 'Fin Scan'), 
                                                  ('-sU', 'UDP Scan'), 
                                                  ('-sT', 'Connect Scan')])
    no_ping = BooleanField("No Ping")
    randomize_hosts = BooleanField("Randomize Hosts")
    fragment_packets = BooleanField("Fragment Packets")
    submit = SubmitField('Scan')

class JohnForm(FlaskForm):
    file = FileField('File with Hashes', validators=[DataRequired()])
    format = SelectField('Hash Format', choices=[('descrypt', 'Descrypt'), 
                                                 ('bsdicrypt', 'Bsdicrypt'),
                                                 ('md5crypt', 'MD5crypt'),
                                                 ('bcrypt', 'BCrypt'),
                                                 ('lm', 'LM'),
                                                 ('afs', 'AFS'),
                                                 ('tripcode', 'Tripcode')])
    attack_type = SelectField('Attack Type', choices=[('dictionary', 'Dictionary'), 
                                                      ('bruteforce', 'Bruteforce')])
    dictionary = FileField('Dictionary File')
    submit = SubmitField('Crack')