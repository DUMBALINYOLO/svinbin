# -*- coding: utf-8 -*-
from django.db import models

# from django_bulk_update.helper import bulk_update

from transactions.models import Location, SowTransaction, GiltTransaction
from workshops.models import Section, SowGroupCell, WorkShop
# import events.models as event_models


class SowStatus(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class GiltStatus(models.Model):
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Pig(models.Model):
    birth_id = models.CharField(max_length=10, unique=True, null=True)
    location = models.OneToOneField("transactions.Location", on_delete=models.SET_NULL, null=True)

    class Meta:
        abstract = True

    # def move_to_workshop(self, location, initiator):
    #     pass


class SowManager(models.Manager):
    def create_new_from_gilt_and_put_in_workshop_one(self, farm_id):
        # DECREASE GILT QUANTITY!!!
        
        return self.create(farm_id=farm_id,
            location=Location.objects.create_location(pre_location=WorkShop.objects.get(number=1)))

    def get_or_create_by_farm_id(self, farm_id):
        sow = Sow.objects.filter(farm_id=farm_id).first()
        if not sow:
            return self.create_new_from_gilt_and_put_in_workshop_one(farm_id)
        return sow

    def get_by_farm_id(self, farm_id):
        sow = Sow.objects.filter(farm_id=farm_id).first()
        # if not sow:
        #     raise error
        return sow

    def move_to(self, sow, pre_location, initiator=None):
        location = Location.objects.create_location(pre_location)
        transaction = SowTransaction.objects.create_transaction(                
                initiator=initiator,
                to_location=location,
                sow=sow
                )
        return transaction

    def create_and_move_to_by_farm_id(self, farm_id, pre_location, initiator=None):
        sow = self.get_or_create_by_farm_id(farm_id)
        transaction = self.move_to(sow, pre_location, initiator)
        return sow, transaction

    def move_to_by_farm_id(self, farm_id, pre_location, initiator=None):
        sow = self.get_by_farm_id(farm_id)
        transaction = self.move_to(sow, pre_location, initiator)
        return sow, transaction

    def move_many(self, sows, pre_location, initiator=None):
        for sow in sows.all():
            self.move_to(sow, pre_location, initiator)


class Sow(Pig):
    farm_id = models.IntegerField(null=True, unique=True)
    status = models.ForeignKey(SowStatus, on_delete=models.SET_NULL, null=True)
    tour = models.ForeignKey('tours.Tour', on_delete=models.SET_NULL, null=True)
    alive = models.BooleanField(default=True)

    objects = SowManager()

    def __str__(self):
        return 'Sow #%s' % self.farm_id

    def change_status_to(self, status_title, alive=True):
        self.status = SowStatus.objects.get(title=status_title)
        self.alive = alive
        self.save()


class Gilt(Pig):
    status = models.ForeignKey(SowStatus, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return 'Gilt #%s' % self.birth_id


class PigletsGroupManager(models.Manager):
    def reset_quantity_and_deactivate(self):
        self.update(quantity=0, active=False)


class PigletsGroup(models.Model):
    location = models.ForeignKey('transactions.Location', on_delete=models.SET_NULL, null=True)
    start_quantity = models.IntegerField()
    quantity = models.IntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class NewBornPigletsGroupManager(PigletsGroupManager):
    pass


class NewBornPigletsGroup(PigletsGroup):
    merger = models.ForeignKey('events.NewBornPigletsMerger', on_delete=models.SET_NULL, null=True,
        related_name='piglets_groups')
    tour = models.ForeignKey('tours.Tour', on_delete=models.SET_NULL, null=True,
     related_name="new_born_piglets")

    objects = NewBornPigletsGroupManager()

    def add_piglets(self, quantity):
        self.quantity = self.quantity + quantity
        self.save()

    def __str__(self):
        return 'NewBornPiglets group #%s' % self.pk


class NomadPigletsGroupManager(PigletsGroupManager):
    pass
    # def create_two_from_split(self, split_event):
    #     # self.create
    #     pass


class NomadPigletsGroup(PigletsGroup):
    split_record = models.ForeignKey('events.SplitNomadPigletsGroup', on_delete=models.SET_NULL, null=True)
    groups_merger = models.ForeignKey('events.NomadPigletsGroupMerger', on_delete=models.SET_NULL, null=True,
        related_name="groups_merger")

    objects = NomadPigletsGroupManager()

    def __str__(self):
        return 'NomadPiglets group #%s' % self.pk

    def reset_quantity_and_deactivate(self):
        self.quantity = 0
        self.active = False
        self.save()


