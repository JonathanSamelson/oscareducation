# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.core.checks import messages
from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.db.models import Q
from django.urls import reverse

from student_collaboration.models import StudentCollaborator, CollaborativeSettings, HelpRequest
from users.models import Student
from skills.models import Skill
from .forms import StudentCollaboratorForm, CollaborativeSettingsForm, UnmasteredSkillsForm, HelpRequestForm, SkillsForm
from math import sin, cos, sqrt, atan2, radians
from decorators import user_has_collaborative_tool_active
from notifications.signals import notify

# Create your views here.
@login_required
def update_settings(request):
    notify.send(sender=request.user, recipient=request.user, verb='Ceci est un test de notifications')
    # POST request; we perform an update
    true_student = get_object_or_404(Student, user=request.user.pk)
    student = get_object_or_404(StudentCollaborator, pk=true_student.studentcollaborator.pk)

    if request.method == 'POST':
        settings = get_object_or_404(CollaborativeSettings, pk=true_student.studentcollaborator.settings.pk)
        settings_form = CollaborativeSettingsForm(request.POST, instance=settings)
        student_form = StudentCollaboratorForm(request.POST, instance=student)

        if student_form.is_valid() and settings_form.is_valid():
            settings = settings_form.save(commit=False)
            student = student_form.save(commit=False)
            student_form.settings = settings
            settings.save()
            student.save()
            return HttpResponseRedirect('/student_collaboration/settings/')
    else:
        # The user has or doesn't have settings
        settings_pk = None
        if true_student.studentcollaborator.settings:
            settings_pk = true_student.studentcollaborator.settings.pk
        settings, is_created = CollaborativeSettings.objects.get_or_create(
            pk=settings_pk
        )
        # settings just created ; add them to user
        if is_created:
            student.settings = settings
            student.save()

        settings_form = CollaborativeSettingsForm(instance=settings)
        student_form = StudentCollaboratorForm(instance=student)
    return render(request, 'student_collaboration/student_settings.haml', {
        'student_form': student_form,
        'settings_form': settings_form
    })


@login_required
# @user_has_collaborative_tool_active
def submit_help_request(request):
    student_collab = get_object_or_404(StudentCollaborator, pk=request.user.student.studentcollaborator.pk)
    list_skills_id = student_collab.get_skills('not acquired')
    has_a_skill = True
    if list_skills_id:
        list_skill_unmastered = Skill.objects.filter(id__in=list_skills_id)
    else:
        list_skill_unmastered = list_skills_id  # student had no skill, no need to filter => empty query set
        has_a_skill = False

    if request.method == 'POST':
        skill_form = UnmasteredSkillsForm(request.POST, skills=list_skill_unmastered, current_user=request.user.student.pk)
        if skill_form.is_valid():  # All validation rules pass
            settings = get_object_or_404(CollaborativeSettings, pk=request.user.student.studentcollaborator.settings.pk)
            created_hr = student_collab.launch_help_request(settings)
            for skill in skill_form.cleaned_data.get("list"):
                created_hr.skill.add(skill)
	    
            return HttpResponseRedirect("/student_collaboration/help_request_history/")
    else:
        skill_form = UnmasteredSkillsForm(skills=list_skill_unmastered, current_user=request.user.student.pk)

    return render(request, "student_collaboration/request_help.haml", {
        'skill_form': skill_form,
        'has_a_skill': has_a_skill
    })


@login_required
@user_has_collaborative_tool_active
def open_help_request(request, id=None):
    if id:
        hp = HelpRequest.objects.filter(id=id).first()
        hp.reply_to_unanswered_help_request(request.user.student)

    """ We redirect to the list view """
    return redirect('provide_help')


@login_required
def collaborative_home(request):
    return render(request, 'student_collaboration/student_collaboration_home.haml')


@login_required
@user_has_collaborative_tool_active
def help_request_hist(request):
    if request.GET.get('id',None):
        hp = HelpRequest.objects.filter(id=request.GET.get('id',None)).first()
        if hp:
            if hp.student == request.user.student or hp.tutor == request.user.student:
                hp.close_request(None, None)
    return HelpRequestHistory.as_view()(request)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_has_collaborative_tool_active, name='dispatch')
class HelpRequestHistory(ListView):
    model = HelpRequest
    template_name = "student_collaboration/help_request_history.haml"
    context_object_name = "open_help_requests"

    def dispatch(self, *args, **kwargs):
        return super(HelpRequestHistory, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HelpRequestHistory, self).get_context_data(**kwargs)
        context['currentStatus'] = self.request.GET.get('requests', None)
        context['showClosed'] = self.request.GET.get('showClosed', 0)
        context['sort'] = self.request.GET.get('sort', 'timestamp')
        context['requestType'] = self.request.GET.get('requestType', 'all')
        context['filteredSkill'] = self.request.GET.get('filteredSkill', 'all')
        skill_list_id = self.request.user.student.studentcollaborator.get_skills()
        skill_list = Skill.objects.filter(id__in=skill_list_id)
        context['skills'] = skill_list
        # context['skills'] = SkillsForm(skills=skill_list, current_user=self.request.user.student.pk)
        return context

    def get_queryset(self):
        """We recover help request from User"""
        order = self.request.GET.get('sort', 'timestamp')
        if self.request.GET.get('requestType', None) == "provided":
            open_help_requests = HelpRequest.objects.filter(tutor=self.request.user.student).order_by('-'+order)
        elif self.request.GET.get('requestType', None) == "requested":
            open_help_requests = HelpRequest.objects.filter(student=self.request.user.student).order_by('-'+order)
        else:
            open_help_requests = HelpRequest.objects.filter(
                Q(tutor=self.request.user.student) | Q(student=self.request.user.student)).order_by('-'+order)
        if self.request.GET.get('showClosed', "0") == "0":
            not_closed_help_requests = []
            for help_request in open_help_requests:
                if help_request.state != "Closed":
                    not_closed_help_requests.append(help_request)
            open_help_requests = not_closed_help_requests
        if self.request.GET.get('filteredSkill', "all") != "all":
            filter_help_request = []
            for help_request in open_help_requests:
                for skill in help_request.skill.all():
                    id_wanted = self.request.GET.get('filteredSkill', None)
                    id_found = skill.id
                    if str(id_found) == str(id_wanted):
                        filter_help_request.append(help_request)
            open_help_requests = filter_help_request
        return open_help_requests


@method_decorator(login_required, name='dispatch')
@method_decorator(user_has_collaborative_tool_active, name='dispatch')
class OpenHelpRequestsListView(ListView):
    model = HelpRequest
    paginate_by = 10
    template_name = "student_collaboration/open_help_requests_list.haml"
    context_object_name = "open_help_requests"

    def dispatch(self, *args, **kwargs):
        return super(OpenHelpRequestsListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OpenHelpRequestsListView, self).get_context_data(**kwargs)
        context['currentUserPk'] = self.request.user.student.studentcollaborator.pk
        return context

    def get_queryset(self):
        """ We fetch the skills mastered by the helper """
        mastered_skill_list = self.request.user.student.studentcollaborator.get_skills('acquired')
        open_help_requests = HelpRequest.objects.filter(
            state=HelpRequest.OPEN,
            skill__in=mastered_skill_list
        ).distinct()
        filtered_help_requests = []
        # We only take the requests in the user's area
        for help_request in open_help_requests:
            """ Haversine's formula to compute the distance between two geographical points """
            earth_radius = 6373.0

            lat1 = radians(help_request.student.studentcollaborator.postal_code.latitude)
            lon1 = radians(help_request.student.studentcollaborator.postal_code.longitude)
            lat2 = radians(self.request.user.student.studentcollaborator.postal_code.latitude)
            lon2 = radians(self.request.user.student.studentcollaborator.postal_code.longitude)

            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = earth_radius * c
            if distance <= help_request.settings.distance:
                filtered_help_requests.append(help_request)

        """ We could still filter """
        """ https://stackoverflow.com/a/33350839/6149867 """

        return filtered_help_requests


@login_required
def collaborative_notifications(request):
    return render(request, 'student_collaboration/notifications.haml')

@login_required
class NotificationViewList(ListView):
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(NotificationViewList, self).dispatch(
            request, *args, **kwargs)
