from django.db.models import (
    BigIntegerField, DO_NOTHING, ForeignKey, ManyToManyField, Model,
    SmallIntegerField, TextField)


# Elementary models

class Affiliation(Model):
    id = BigIntegerField(primary_key=True)
    normalized_name = TextField()
    display_name = TextField()

    class Meta:
        db_table = 'affiliations'
        managed = False


class Author(Model):
    id = BigIntegerField(primary_key=True)
    normalized_name = TextField()
    display_name = TextField()
    last_known_affiliation = ForeignKey(Affiliation,
                                        null=True, on_delete=DO_NOTHING)

    class Meta:
        db_table = 'authors'
        managed = False


class ConferenceSeries(Model):
    id = BigIntegerField(primary_key=True)
    normalized_name = TextField()
    display_name = TextField()

    class Meta:
        db_table = 'conference_series'
        managed = False


class FieldOfStudy(Model):
    id = BigIntegerField(primary_key=True)
    normalized_name = TextField()
    display_name = TextField()
    level = SmallIntegerField()

    class Meta:
        db_table = 'fields_of_study'
        managed = False


class Journal(Model):
    id = BigIntegerField(primary_key=True)
    normalized_name = TextField()
    display_name = TextField()

    class Meta:
        db_table = 'journals'
        managed = False


class Paper(Model):
    id = BigIntegerField(primary_key=True)
    title = TextField()
    year = SmallIntegerField(null=True)
    journal = ForeignKey(Journal, null=True, on_delete=DO_NOTHING)
    conference_series = ForeignKey(ConferenceSeries,
                                   null=True, on_delete=DO_NOTHING)
    # number_authors = SmallIntegerField(null=True)  # Not populated.
    author_set = ManyToManyField(
        Author, related_name='paper_set', through='UniqueAuthorship')
    field_of_study_set = ManyToManyField(
        FieldOfStudy, related_name='paper_set', through='PaperFieldStudied')
    citee_paper_set = ManyToManyField(
        'Paper',
        related_name='citor_paper_set', symmetrical=False,
        through='Citation', through_fields=('citor_paper', 'citee_paper'))

    class Meta:
        db_table = 'papers'
        managed = False


# Many-to-many relationships

class PaperFieldStudied(Model):
    paper = ForeignKey(Paper, on_delete=DO_NOTHING, related_name='+')
    field_of_study = ForeignKey(FieldOfStudy,
                                on_delete=DO_NOTHING, related_name='+')

    class Meta:
        db_table = 'paper_fields_studied'
        managed = False


class UniqueAuthorship(Model):
    paper = ForeignKey(Paper, on_delete=DO_NOTHING, related_name='+')
    author = ForeignKey(Author, on_delete=DO_NOTHING, related_name='+')

    class Meta:
        db_table = 'unique_authorships'
        managed = False


class Citation(Model):
    citor_paper = ForeignKey(Paper, on_delete=DO_NOTHING, related_name='+')
    citee_paper = ForeignKey(Paper, on_delete=DO_NOTHING, related_name='+')

    class Meta:
        db_table = 'citations'
        managed = False


# Leaving out for now. Django does not like composite primary keys!
# Options:
# - give it a surrogate key
# - this trick: https://stackoverflow.com/a/65404017

# class AuthorshipAffiliation(Model):
#     paper = ForeignKey(
#         Paper,
#         on_delete=DO_NOTHING, related_name='authorship_affiliation_set')
#     author = ForeignKey(
#         Author,
#         on_delete=DO_NOTHING, related_name='authorship_affiliation_set')
#     affiliation = ForeignKey(
#         Affiliation,
#         on_delete=DO_NOTHING, related_name='authorship_affiliation_set')

#     class Meta:
#         db_table = 'authorships'
#         managed = False
