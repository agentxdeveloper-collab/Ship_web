from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, HiddenField, TextAreaField
from wtforms.validators import DataRequired, URL, NumberRange, Optional

# 지역 공용 정의 (등록/수정/조회 모두에서 활용)
REGION_CHOICES = [
    ('', '지역을 선택하세요'),
    ('인천', '인천'),
    ('안산', '안산'),
    ('화성', '화성'),
    ('평택', '평택'),
    ('당진', '당진'),
    ('서산', '서산'),
    ('태안', '태안'),
    ('보령', '보령'),
    ('군산', '군산'),
    ('격포', '격포'),
    ('여수', '여수'),
    ('고흥', '고흥'),
]

class BoatRegistrationForm(FlaskForm):
    name = StringField('배 이름', validators=[DataRequired()])
    url = StringField('예약 페이지 URL', validators=[DataRequired(), URL()])
    city = SelectField('지역', validators=[DataRequired()], choices=REGION_CHOICES, coerce=str)
    port = SelectField('항구', validators=[DataRequired()], choices=[])
    note = TextAreaField('비고', validators=[Optional()])
    submit = SubmitField('등록하기')

class BoatEditForm(FlaskForm):
    id = HiddenField('ID')
    name = StringField('배 이름', validators=[DataRequired()])
    url = StringField('예약 페이지 URL', validators=[DataRequired(), URL()])
    city = SelectField('지역', validators=[DataRequired()], choices=REGION_CHOICES, coerce=str)
    port = SelectField('항구', validators=[DataRequired()], choices=[])
    note = TextAreaField('비고', validators=[Optional()])
    submit = SubmitField('수정하기')

class StatusCheckForm(FlaskForm):
    year = IntegerField('연도', validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    month = IntegerField('월', validators=[DataRequired(), NumberRange(min=1, max=12)])
    day = IntegerField('일', validators=[DataRequired(), NumberRange(min=1, max=31)])
    submit = SubmitField('조회하기')