# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from forum.models import Thread
from users.models import Student
from skills.models import SkillHistory, Skill
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime


# Create your models here.

class CollaborativeSettings(models.Model):
    """ Constant : The default distance"""
    DEFAULT_DISTANCE = 5
    """ Integer to make computation easier """
    distance = models.IntegerField(default=DEFAULT_DISTANCE)


class PostalCode(models.Model):
    postal_code = models.PositiveIntegerField(default=0)
    longitude = models.FloatField(default=0)
    latitude = models.FloatField(default=0)

    def __unicode__(self):
        return str(self.postal_code)

    class Meta:
        ordering = ['postal_code']


class StudentCollaborator(models.Model):
    # Simple way to extend the user model :
    #  https://docs.djangoproject.com/en/dev/topics/auth/customizing/#extending-the-existing-user-model
    user = models.OneToOneField(Student, on_delete=models.CASCADE)
    """" postal code : link to a PostalCode object"""
    postal_code = models.ForeignKey(PostalCode, null=True)
    """" Flag to inform if the user has activated the system for himself """
    collaborative_tool = models.BooleanField(default=False)
    """ The default settings for this user """
    settings = models.OneToOneField(CollaborativeSettings, on_delete=models.CASCADE, null=True)

    """ For the admin page """

    def __unicode__(self):
        return self.user.__unicode__()

    """" skills mastered by the user"""

    def get_mastered_skills(self):
        return SkillHistory.objects.filter(student=self.user, value="acquired").values_list('skill__id', flat=True)

    """ skills not mastered but already tested once in an examination """

    def get_unmastered_skills(self):
        return SkillHistory.objects.filter(student=self.user, value='not acquired').values_list('skill__id', flat=True)

    def launch_help_request(self, settings):
        return HelpRequest.objects.create(
            student=self.user,
            settings=settings
        )

    def launched_help_request_list(self):
        return HelpRequest.objects.filter(student=self.user)

    def replied_help_request_list(self):
        return HelpRequest.objects.filter(tutor=self.user)

    def change_settings(self, new_settings):
        self.settings = new_settings
        self.save()

    """ https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone """
    """ Signals: create an StudentCollaborator object when a user is created """

    @receiver(post_save, sender=Student)
    def create_student_collaborator_profile(sender, instance, created, **kwargs):
        if created:
            """ On crée effectivement notre profile """
            StudentCollaborator.objects.create(
                user=instance,
                collaborative_tool=False
            )


class HelpRequest(models.Model):
    """ Constants : Help request statuses """
    CLOSED = "Closed"
    OPEN = "Open"
    ACCEPTED = u"Accepted"
    PENDING = u"Pending"
    """ date and hour of creation """
    timestamp = models.DateTimeField(default=datetime.now)

    """ The settings for this Help Request """
    settings = models.ForeignKey(CollaborativeSettings)

    """ The conversation """
    thread = models.ForeignKey(Thread, null=True)

    """ The current state of the request """
    requestStatus = (
        (CLOSED, u"Cloturé"),
        (OPEN, "Ouverte"),
        (ACCEPTED, u"Accepté"),
        (PENDING, u"Expirée"),
    )
    state = models.CharField(max_length=20, null=False, choices=requestStatus, default=OPEN)
    """ The skill or group of skills linked to this request """
    skill = models.ManyToManyField(Skill)
    """ The student who is offering his help; not set when the help request if created """
    tutor = models.ForeignKey(Student, null=True, related_name="%(class)s_tutor")
    """ The student asking for help """
    student = models.ForeignKey(Student)

    """ The comment left at the closure of the help request """
    """ By default , an automatic message from the system """
    DEFAULT_COMMENT = u"Fermé par le système"
    comment = models.CharField(max_length=255, null=True)

    """ The existing categories for a closure """
    CLOSED_BY_SYSTEM = "SYSTEM_CLOSED"
    CANNOT_HELP = "CANNOT_HELP"
    TRIED_TO_HELP = "TRIED_TO_HELP"
    CLOSED_BY_USER = "USER_CLOSED"

    closedCategories = (
        (CLOSED_BY_USER, u"Fermé par le demandeur d'aide"),
        (CLOSED_BY_SYSTEM, u"Cloturé par le système"),
        (CANNOT_HELP, u"Ne sait pas aider"),
        (TRIED_TO_HELP, u"A aidé dans la mesure du possible")
    )
    """ The reason why the help request was closed """
    closedReason = models.CharField(max_length=255, null=True, choices=closedCategories)

    """ Enables to respond to an open help request """

    def reply_to_unanswered_help_request(self, user):
        """ The student who responds is the tutor """
        self.tutor = user
        """ Status shifts to accepted """
        self.state = HelpRequest.ACCEPTED

        """ We create the thread between the two students """
        thread = Thread(title="Temp title", author=self.student.user, recipient=user.user)
        thread.save()

        thread.skills = Skill.objects.filter(pk__in=self.skill.all())
        thread.save()

        self.thread = thread
        self.save()

    def close_request(self, comment=None, close_category=None):
        self.change_state(HelpRequest.CLOSED)
        """ If a comment is present """
        if comment is not None:
            self.comment = comment
        else:
            self.comment = HelpRequest.DEFAULT_COMMENT
        """ If another category is provided than the ones by default """
        if close_category is not None:
            self.closedReason = close_category
        else:
            self.closedReason = HelpRequest.CLOSED_BY_SYSTEM
        self.save()

    def change_settings(self, new_settings):
        self.settings = new_settings
        self.save()

    def change_state(self, new_state):
        self.state = new_state
        self.timestamp = datetime.now()
        self.save()

    """ Signal : When a skill is mastered, all the open help requests are automatically closed """

    @receiver(post_save, sender=SkillHistory)
    def check_status(sender, instance, **kwargs):
        if instance.value == 'acquired':
            """ Filter all the help requests to get the ones who need to be closed """
            helprequest_to_be_closed = HelpRequest.objects.filter(
                student=instance.student,
                skill=instance.skill,
            ).exclude(
                state=HelpRequest.CLOSED
            )
            """ Si trouvé, on les ferme """
            if not helprequest_to_be_closed:
                for closed in helprequest_to_be_closed.all():
                    closed.close_request()
