from django.urls import path
from . import views

urlpatterns = [
   path("report_27_28", views.report2728),
   path("report_29_30", views.report2930),
   path("report_33_35", views.report3335),
   path("report_37_39", views.report3739),
   path("report_1_4", views.report1_4),
   path("report_2_5", views.report2_5),
   path("report_14", views.report_14),
   path("report_25", views.report_25),
   path("report_8_10", views.report8_10),
   path("report_7_9", views.report7_9),
   path("report_isp_420", views.report_isp_420),
   path("report_isp_219", views.report_isp_219),
   path("report_diff_pay_obl", views.report_diff_pay_obl),
   path("report_diff_god_sum", views.report_diff_god_sum),
]
