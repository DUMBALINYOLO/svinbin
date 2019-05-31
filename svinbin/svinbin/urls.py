# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.conf.urls import url, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from rest_framework import routers

from transactions import views as transaction_views
from workshops.views import CreateWorkshopsView

router = routers.DefaultRouter()
router.register(r'sowtransactions/workshops', transaction_views.WorkShopOneTwoSowTransactionViewSet,
    basename='workshop-sowtransactions')
router.register(r'sowtransactions/transactions', transaction_views.SowTransactions,
    basename='sowtransactions')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(router.urls)),
    url(r'^api/create_workshops/', CreateWorkshopsView.as_view()),

    ]
