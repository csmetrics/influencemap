from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

flask_app = Flask(__name__)
flask_app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432"
db = SQLAlchemy(flask_app)
migrate = Migrate(flask_app, db)

# Elementary models

class Affiliation(db.Model):
    __tablename__ = 'affiliations'

    id = db.Column(db.BigInteger, primary_key=True)
    normalized_name = db.Column(db.String())
    display_name = db.Column(db.String())

    def __init__(self, id, normalized_name, display_name):
        self.id = id
        self.normalized_name = normalized_name
        self.display_name = display_name

    def __repr__(self):
        return f"<Affiliation {self.id}>"


class Author(db.Model):
    __tablename__ = 'authors'

    id = db.Column(db.BigInteger, primary_key=True)
    normalized_name = db.Column(db.String())
    display_name = db.Column(db.String())
    last_known_affiliation = db.Column(db.BigInteger, db.ForeignKey('affiliations.id'), nullable=True)

    def __init__(self, id, normalized_name, display_name, last_known_affiliation):
        self.id = id
        self.normalized_name = normalized_name
        self.display_name = display_name
        self.last_known_affiliation = None

    def __repr__(self):
        return f"<Authors {self.id}>"


class ConferenceSeries(db.Model):
    __tablename__ = 'conference_series'

    id = db.Column(db.BigInteger, primary_key=True)
    normalized_name = db.Column(db.String())
    display_name = db.Column(db.String())

    def __init__(self, id, normalized_name, display_name):
        self.id = id
        self.normalized_name = normalized_name
        self.display_name = display_name

    def __repr__(self):
        return f"<ConferenceSeries {self.id}>"


class FieldOfStudy(db.Model):
    __tablename__ = 'fields_of_study'

    id = db.Column(db.BigInteger, primary_key=True)
    normalized_name = db.Column(db.String())
    display_name = db.Column(db.String())
    level = db.Column(db.Integer)

    def __init__(self, id, normalized_name, display_name, level):
        self.id = id
        self.normalized_name = normalized_name
        self.display_name = display_name
        self.level = level

    def __repr__(self):
        return f"<FieldOfStudy {self.id}>"


class Journal(db.Model):
    __tablename__ = 'journals'

    id = db.Column(db.BigInteger, primary_key=True)
    normalized_name = db.Column(db.String())
    display_name = db.Column(db.String())

    def __init__(self, id, normalized_name, display_name):
        self.id = id
        self.normalized_name = normalized_name
        self.display_name = display_name

    def __repr__(self):
        return f"<Journal {self.id}>"



# Many-to-many relationships

authorships = db.Table('authorships',
    db.Column('paper_id', db.BigInteger, db.ForeignKey('papers.id')),
    db.Column('author_id', db.BigInteger, db.ForeignKey('authors.id')),
    db.Column('affiliation_id', db.BigInteger, db.ForeignKey('affiliations.id')),
    db.ForeignKeyConstraint(
        ('paper_id', 'author_id', 'affiliation_id'),
        ('authorships.paper_id', 'authorships.author_id', 'authorships.author_id')
    )
)

unique_authorships = db.Table('unique_authorships',
    db.Column('paper_id', db.BigInteger, db.ForeignKey('papers.id')),
    db.Column('author_id', db.BigInteger, db.ForeignKey('authors.id')),
    db.ForeignKeyConstraint(
        ('paper_id', 'author_id'),
        ('unique_authorships.paper_id', 'unique_authorships.author_id')
    )
)

paper_fields_studied = db.Table('paper_fields_studied',
    db.Column('paper_id', db.BigInteger, db.ForeignKey('papers.id')),
    db.Column('field_of_study_id', db.BigInteger, db.ForeignKey('fields_of_study.id')),
    db.ForeignKeyConstraint(
        ('paper_id', 'field_of_study_id'),
        ('paper_fields_studied.paper_id', 'paper_fields_studied.field_of_study_id')
    )
)
citations = db.Table('citations',
    db.Column('citor_paper_id', db.BigInteger, db.ForeignKey('papers.id')),
    db.Column('citee_paper_id', db.BigInteger, db.ForeignKey('papers.id')),
    db.ForeignKeyConstraint(
        ('citor_paper_id', 'citee_paper_id'),
        ('citations.citor_paper_id', 'citations.citee_paper_id')
    )
)

class Paper(db.Model):
    __tablename__ = 'papers'

    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String())
    year = db.Column(db.Integer, nullable=True)
    journal = db.Column(db.BigInteger, db.ForeignKey('journals.id'), nullable=True)
    conference_series = db.Column(db.BigInteger, db.ForeignKey('conference_series.id'), nullable=True)
    number_authors = db.Column(db.Integer, nullable=True)

    author_set = db.relationship('authors', secondary=unique_authorships, backref='paper_set')
    field_of_study_set = db.relationship('fields_of_study', secondary=paper_fields_studied, backref='paper_set')
    citee_paper_set = db.relationship('papers', secondary=citations, backref='citor_paper_set')
    citor_paper_set = db.relationship('papers', secondary=citations, backref='citee_paper_set')

    def __init__(self, id, title):
        self.id = id
        self.title = title

    def __repr__(self):
        return f"<Paper {self.id}>"



def search(type, name):
    print(type, name)
    pass
