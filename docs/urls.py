from django.urls import path
from . import views

urlpatterns = [
    # Доходы утв документы
    path('utvinclist', views.utvinclist, name='index'),
    path('utvincitem/<int:id>', views.utvincitem, name='index'),
    path('utvincsave', views.utvincsave, name='index'),
    path('utvincdelete/<int:id>', views.utvincdelete, name='index'),

    # Доходы изм документы
    path('izminclist', views.izminclist, name='index'),
    path('izmincitem/<int:id>', views.izmincitem, name='index'),
    path('izmincsave', views.izmincsave, name='index'),
    path('izmincdelete/<int:id>', views.izmincdelete, name='index'),
    path('incgetplanbyclassif', views.incgetplanbyclassif, name='index'), 


    # Расходы утв документы
    path('utvexplist', views.utvexplist, name='index'),
    path('utvexpitem/<int:id>', views.utvexpitem, name='index'),
    path('utvexpsave', views.utvexpsave, name='index'),
    path('utvexpdelete/<int:id>', views.utvexpdelete, name='index'),


    path('izmexplist', views.izmexplist, name='index'),
    path('izmexpitem/<int:id_doc>', views.izmexpitem, name='index'),
    path('izmexpsave', views.izmexpsave, name='index'),
    path('izmexpdelete/<int:id>', views.izmexpdelete, name='index'),
    path('expgetplanbyclassif', views.expgetplanbyclassif, name='index'),

    path('import219', views.import219, name='index'), 
]