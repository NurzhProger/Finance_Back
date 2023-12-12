from django.urls import path
from . import views

urlpatterns = [
    # Доходы утв документы
    path('utvinclist', views.utvinclist, name='index'),
    path('utvincitem/<int:id>', views.utvincitem, name='index'),
    path('utvincsave', views.utvincsave, name='index'),
    path('utvincdelete', views.utvincdelete, name='index'),

    # Доходы изм документы
    path('izminclist', views.izminclist, name='index'),
    path('izmincitem/<int:id>', views.izmincitem, name='index'),
    path('izmincsave', views.izmincsave, name='index'),
    path('izmincdelete', views.izmincdelete, name='index'),
    path('incgetplanbyclassif', views.incgetplanbyclassif, name='index'),


    # Расходы утв документы
    path('utvexplist', views.utvexplist, name='index'),
    path('utvexpitem/<int:id>', views.utvexpitem, name='index'),
    path('utvexpsave', views.utvexpsave, name='index'),
    path('utvexpdelete/<int:id>', views.utvexpdelete, name='index'),


    path('izmexplist', views.izmexplist, name='index'),
    path('izmexpselect', views.izmexpselect, name='index'),
    path('izmexpitem/<int:id_doc>', views.izmexpitem, name='index'),
    path('izmexpsave', views.izmexpsave, name='index'),
    path('izmexpchangestatus', views.izmexpchangestatus, name='index'),
    path('izmexpdelete', views.izmexpdelete, name='index'),
    path('expgetplanbyclassif', views.expgetplanbyclassif, name='index'),


    path('svodexplist', views.svodexplist, name='index'),
    path('svodexpadd', views.svodexpadd, name='index'),
    path('svodexpitem/<int:id_doc>', views.svodexpitem, name='index'),
    path('svodexpitem/<int:id_doc>/add', views.svodexp_add_doc, name='index'),
    path('svodexpdelete', views.svodexpdelete, name='index'),
    path('svodexpitem/<int:id_doc>/delete', views.svodexp_del_doc, name='index'),
    path('svodexpchangestatus', views.svodexpchangestatus, name='index'),


    path('import219', views.import_219, name='index'), 
    path('import219list', views.import219list, name='index'), 
    path('import219item/<int:id_doc>', views.import219item, name='index'),  
    path('import219delete', views.import219delete, name='index'),


    path('import420', views.import_420, name='index'), 
    path('import420list', views.import420list, name='index'), 
    path('import420item/<int:id_doc>', views.import420item, name='index'),
    path('import420delete', views.import420delete, name='index'), 
]
