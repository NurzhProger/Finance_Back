from django.urls import path
from . import views

urlpatterns = [
    path('userlist', views.userlist, name='index'),
    path('useritem/<int:id>', views.useritem, name='index'),
    path('usersave', views.usersave, name='index'),
    path('changepass', views.changepass, name='index'),
    path('userdel/<int:id>', views.userdel, name='index'),
    path('logineduser', views.logineduser, name='index'),
    path('getinfo', views.getinfo, name='index'),
    path('cleartoken', views.cleartoken, name='index'),

    path('organizationlist', views.organizationlist, name='index'),
    path('organizationitem/<int:id>', views.organizationitem, name='index'),
    path('organizationsave', views.organizationsave, name='index'),
    path('organizationdelete/<int:id>', views.organizationdelete, name='index'),
    path('parent_organization_add', views.parent_organization_add, name='index'),
    path('parent_organization_del/<int:id>', views.parent_organization_del, name='index'),

    path('budjetlist', views.budjetlist, name='index'),

    path('typeincdoclist', views.typeincdoclist, name='index'),
    path('regionlist', views.regionlist, name='index'),

    path('categorylist', views.categorylist, name='index'),
    path('categoryadd', views.categoryadd, name='index'),
    path('categoryedit', views.categoryedit, name='index'),
    path('categorydelete/<int:id>', views.categorydelete, name='index'),

    path('classlist', views.classlist, name='index'),
    path('classadd', views.classadd, name='index'),
    path('classedit', views.classedit, name='index'),
    path('classdelete/<int:id>', views.classdelete, name='index'),

    path('podclasslist', views.podclasslist, name='index'),
    path('podclassadd', views.podclassadd, name='index'),
    path('podclassedit', views.podclassedit, name='index'),
    path('podclassdelete/<int:id>', views.podclassdelete, name='index'),

    path('specinclist', views.specinclist, name='index'),
    path('specincadd', views.specincadd, name='index'),
    path('specincedit', views.specincedit, name='index'),
    path('specincdelete/<int:id>', views.specincdelete, name='index'),

    path('classificationinclist', views.classificationinclist, name='index'),
    path('classificationincitem/<int:id>', views.classificationincitem, name='index'),
    path('classificationincadd', views.classificationincadd, name='index'),
    path('classificationincedit', views.classificationincedit, name='index'),
    path('classificationincdelete/<int:id>', views.classificationincdelete, name='index'),

    path('funcgrouplist', views.funcgrouplist, name='index'),
    path('funcpodgrouplist', views.funcpodgrouplist, name='index'),
    path('abplist', views.abplist, name='index'),
    path('programlist', views.programlist, name='index'),
    path('podprogramlist', views.podprogramlist, name='index'),
    path('fkrlist', views.fkrlist, name='index'),
    path('specexplist', views.specexplist, name='index'),


    path('fkrupdate', views.fkrupdate, name='index'),
    path('ekrupdate', views.ekrupdate, name='index'),
    path('inc_dir_import', views.inc_dir_import, name='index'),


    path('repayexplist', views.repayexplist, name='index'),
    path('repayinclist', views.repayinclist, name='index'),
    path('repayexportqazna', views.repayexportqazna, name='index'),
]
