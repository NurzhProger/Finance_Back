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


    path('izmexppaymlist', views.izmexppaymlist, name='index'),
    path('izmexppaymitem/<int:id>', views.izmexppaymitem, name='index'),
    path('izmexppaymsave', views.izmexppaymsave, name='index'),
    path('izmexppaymdelete/<int:id>', views.izmexppaymdelete, name='index'),

    path('import219', views.import219, name='index'), 
]