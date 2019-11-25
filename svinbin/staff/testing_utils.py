# -*- coding: utf-8 -*-
from mixer.backend.django import mixer

from django.contrib.auth.models import User

from staff.models import WorkShopEmployee
from locations.models import WorkShop


def create_employee(farm_name=''):
    user = mixer.blend('auth.user')
    WorkShopEmployee.objects.create(user=user, is_seminator=True, farm_name=farm_name)
    return user


def create_test_users():
    try:
        user = User.objects.create_user('test_seminator', 't@t.ru', 'svinbin123')
        WorkShopEmployee.objects.create(user=user, is_seminator=True, is_officer=True)
        return user
    except:
        pass

def create_user(username, farm_name):
    user = User.objects.create_user(username, 't@t.ru', 'svinbin123')
    WorkShopEmployee.objects.create(user=user, is_seminator=True, is_officer=False, farm_name=farm_name)
    return user


def create_workshop_user(username, password, ws_number, is_seminator=False, is_officer=False):
    workshop = WorkShop.objects.filter(number=ws_number).first()
    user = User.objects.create_user(username, 't@t.ru', password)
    WorkShopEmployee.objects.create(user=user, workshop=workshop, \
        is_seminator=is_seminator, is_officer=is_officer)
    return user


def create_svinbin_users():
    User.objects.create_superuser(username='kaizerj',email='kzrster@gmail.com', password='svinbin123')
    create_user('shmigina', 'ШМЫГИ')
    create_user('borisov', 'БОРИС')
    create_user('semenova', 'СЕМЕН')
    create_user('gary', 'ГАРИ')
    create_user('ivanov', 'ИВАНО')