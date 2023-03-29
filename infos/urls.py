from django.urls import path, re_path
from . import views
from . import special_views

app_name = "infos"
urlpatterns = [
    path(r"project-team/", special_views.TeamView.as_view(), name="project-team"),
    path(
        r"about-the-project/",
        special_views.SpecialAboutView.as_view(),
        name="about-the-project",
    ),
    path(r"about/", views.AboutTheProjectListView.as_view(), name="about_browse"),
    re_path(
        r"^about/detail/(?P<pk>[0-9]+)$",
        views.AboutTheProjectDetailView.as_view(),
        name="about_detail",
    ),
    path(r"about/create/", views.AboutTheProjectCreate.as_view(), name="about_create"),
    re_path(
        r"^about/edit/(?P<pk>[0-9]+)$",
        views.AboutTheProjectUpdate.as_view(),
        name="about_edit",
    ),
    re_path(
        r"^about/delete/(?P<pk>[0-9]+)$",
        views.AboutTheProjectDelete.as_view(),
        name="about_delete",
    ),
    path(r"teammember/", views.TeamMemberListView.as_view(), name="teammember_browse"),
    re_path(
        r"^teammember/detail/(?P<pk>[0-9]+)$",
        views.TeamMemberDetailView.as_view(),
        name="teammember_detail",
    ),
    path(
        r"teammember/create/",
        views.TeamMemberCreate.as_view(),
        name="teammember_create",
    ),
    re_path(
        r"^teammember/edit/(?P<pk>[0-9]+)$",
        views.TeamMemberUpdate.as_view(),
        name="teammember_edit",
    ),
    re_path(
        r"^teammember/delete/(?P<pk>[0-9]+)$",
        views.TeamMemberDelete.as_view(),
        name="teammember_delete",
    ),
    path(
        r"projectinst/", views.ProjectInstListView.as_view(), name="projectinst_browse"
    ),
    re_path(
        r"^projectinst/detail/(?P<pk>[0-9]+)$",
        views.ProjectInstDetailView.as_view(),
        name="projectinst_detail",
    ),
    path(
        r"projectinst/create/",
        views.ProjectInstCreate.as_view(),
        name="projectinst_create",
    ),
    re_path(
        r"^projectinst/edit/(?P<pk>[0-9]+)$",
        views.ProjectInstUpdate.as_view(),
        name="projectinst_edit",
    ),
    re_path(
        r"^projectinst/delete/(?P<pk>[0-9]+)$",
        views.ProjectInstDelete.as_view(),
        name="projectinst_delete",
    ),
]


