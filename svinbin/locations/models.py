# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models, connection
from django.db.models import Sum, OuterRef, Subquery, Q, Count, Value

from core.models import CoreModel, CoreModelManager
import piglets as piglets_app


class WorkShop(CoreModel):
    number = models.IntegerField()
    title = models.CharField(max_length=128)

    def __str__(self):
        return self.title


class Section(CoreModel):
    workshop = models.ForeignKey(WorkShop, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    def __str__(self):
        return 'Секция {} {}'.format(self.number, self.workshop)

    def sows_count_by_tour(self):
        # only work for ws3
        if self.workshop.number != 3:
            return None

        return self.location.sows_count_by_tour

    def count_piglets(self):
        if self.workshop.number == 3:
            return None

        return self.location.count_piglets


class Cell(CoreModel):
    workshop = models.ForeignKey(WorkShop, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    number = models.CharField(max_length=4)
    
    class Meta:
        abstract = True


class SowSingleCell(Cell):
    pass
    

class SowGroupCell(Cell):
    sows = models.ManyToManyField('sows.Sow', related_name='sows_in_cell')
    sows_quantity = models.IntegerField(default=0)

    
class PigletsGroupCell(Cell):
    def __str__(self):
        return 'Групповая клетка № {}, {}'.format(self.number, str(self.section))


class SowAndPigletsCell(Cell):
    def __str__(self):
        return 'секция {}, клетка {}'.format(str(self.section.number), self.number)
    

class LocationQuerySet(models.QuerySet):
    def get_workshop_location(self, workshop):
        return Location.objects.all().filter(
            Q(
                Q(workshop=workshop) |
                Q(pigletsGroupCell__workshop=workshop) | 
                Q(section__workshop=workshop) |
                Q(sowAndPigletsCell__workshop=workshop)
                )
            )

    def get_with_count_piglets_in_section(self):
        ''' 
            aggregate in field count_piglets sum of all piglets in piglets section(exclude ws3 sections)

            thanks to 
            https://stackoverflow.com/questions/55925437/django-subquery-with-aggregate
            https://medium.com/@hansonkd/the-dramatic-benefits-of-django-subqueries-and-annotations-4195e0dafb16
        '''
        
        subquery = Location.objects.all().filter(pigletsGroupCell__section=OuterRef('section')) \
                            .values('section') \
                            .annotate(all=Sum('piglets__quantity'))\
                            .values('all')

        return self.annotate(pigs_count=models.Subquery(subquery, output_field=models.IntegerField()))

    def add_pigs_count_by_sections(self):        
        locations_subquery = models.Subquery(Location.objects.all().filter(
                Q(Q(pigletsGroupCell__section=OuterRef(OuterRef('section'))) | 
                  Q(section=OuterRef(OuterRef('section'))) |
                  Q(sowAndPigletsCell__section=OuterRef(OuterRef('section')))
                  )).values('pk'))

        piglets = piglets_app.models.Piglets.objects.filter(
            location__in=locations_subquery, active=True) \
            .values('active') \
            .annotate(qnty=Sum('quantity')) \
            .values('qnty')

        return self.annotate(
            pigs_count=models.Subquery(piglets, output_field=models.IntegerField()),
            )

    def add_sows_count_by_sections(self):        
        subquery = Location.objects.all().filter(
            Q(Q(section=OuterRef('section')) |
              Q(sowAndPigletsCell__section=OuterRef('section')))) \
                        .values('workshop') \
                        .annotate(all=Count('sow'))\
                        .values('all')

        return self.annotate(sows_count=models.Subquery(subquery, output_field=models.IntegerField()))

    def add_pigs_count_by_workshop(self):        
        locations_subquery = models.Subquery(Location.objects.all().filter(
                Q(Q(pigletsGroupCell__workshop=OuterRef(OuterRef('workshop'))) | 
                  Q(workshop=OuterRef(OuterRef('workshop'))) |
                  Q(section__workshop=OuterRef(OuterRef('workshop'))) |
                  Q(sowAndPigletsCell__workshop=OuterRef(OuterRef('workshop')))
                  )).values('pk'))

        piglets = piglets_app.models.Piglets.objects.filter(
            location__in=locations_subquery, active=True) \
            .values('active') \
            .annotate(qnty=Sum('quantity')) \
            .values('qnty')

        return self.annotate(pigs_count=models.Subquery(piglets, output_field=models.IntegerField()))

    def add_sows_count_by_workshop(self):        
        subquery = self.get_workshop_location(OuterRef('workshop')) \
                        .annotate(flag=Value(0)) \
                        .values('flag') \
                        .annotate(all=Count('sow'))\
                        .values('all')

        return self.annotate(sows_count=models.Subquery(subquery, output_field=models.IntegerField()))

    def gen_sections_pigs_count_dict(self):
        secs = Location.objects.all().filter(section__isnull=False) \
            .select_related('section__workshop') \
            .add_pigs_count_by_sections() \
            .add_sows_count_by_sections()
        data = {'sections': {}, 'workshops': {}}

        for sec_number in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            data['sections'][f'sec_{sec_number}'] = {}
            for ws_number in [1, 2, 3, 4, 5, 6, 7, 8, 11]:
                data['sections'][f'sec_{sec_number}'][f'ws{ws_number}_pigs_count'] = None
                data['sections'][f'sec_{sec_number}'][f'ws{ws_number}_sows_count'] = None

        for sec in secs:
            if hasattr(sec, 'pigs_count'):
                data['sections'][f'sec_{sec.section.number}'][f'ws{sec.section.workshop.number}_pigs_count'] = sec.pigs_count

            if hasattr(sec, 'sows_count'):
                data['sections'][f'sec_{sec.section.number}'][f'ws{sec.section.workshop.number}_sows_count'] = sec.sows_count

        workshops = Location.objects.all().filter(workshop__isnull=False) \
            .select_related('workshop') \
            .add_pigs_count_by_workshop() \
            .add_sows_count_by_workshop()

        for ws in workshops:
            data['workshops'][f'ws{ws.workshop.number}'] = {}
            data['workshops'][f'ws{ws.workshop.number}']['pigs_count'] = ws.pigs_count
            data['workshops'][f'ws{ws.workshop.number}']['sows_count'] = ws.sows_count              

        return data


class LocationManager(CoreModelManager):
    def get_queryset(self):
        return LocationQuerySet(self.model, using=self._db)

    def create_location(self, pre_location):
        if isinstance(pre_location, WorkShop):
            location = self.create(workshop=pre_location)
        elif isinstance(pre_location, Section):
            location = self.create(section=pre_location)
        elif isinstance(pre_location, SowSingleCell):
            location = self.create(sowSingleCell=pre_location)
        elif isinstance(pre_location, SowGroupCell):
            location = self.create(sowGroupCell=pre_location)
        elif isinstance(pre_location, PigletsGroupCell):
            location = self.create(pigletsGroupCell=pre_location)
        elif isinstance(pre_location, SowAndPigletsCell):
            location = self.create(sowAndPigletsCell=pre_location)
        return location

    def get_sowandpiglets_cells_by_section(self, section):
            return self.get_queryset().filter(sowAndPigletsCell__section=section)

    def get_sowandpiglets_cells_by_workshop(self, workshop):
            return self.get_queryset().filter(sowAndPigletsCell__workshop=workshop)


class Location(CoreModel):
    workshop = models.OneToOneField(WorkShop, null=True, on_delete=models.SET_NULL,
     related_name='location')
    section = models.OneToOneField(Section, null=True, on_delete=models.SET_NULL,
     related_name='location')
    sowSingleCell = models.OneToOneField(SowSingleCell, null=True, on_delete=models.SET_NULL,
     related_name='location')
    pigletsGroupCell = models.OneToOneField(PigletsGroupCell, null=True, on_delete=models.SET_NULL,
     related_name='location')
    sowAndPigletsCell = models.OneToOneField(SowAndPigletsCell, null=True, on_delete=models.SET_NULL,
     related_name='location')
    sowGroupCell = models.OneToOneField(SowGroupCell, null=True, on_delete=models.SET_NULL,
     related_name='location')

    objects = LocationManager()

    @property
    def get_location(self):
        if self.workshop:
            return self.workshop

        if self.section:
            return self.section

        # if self.sowSingleCell:
        #     return self.sowSingleCell

        if self.pigletsGroupCell:
            return self.pigletsGroupCell

        if self.sowAndPigletsCell:
            return self.sowAndPigletsCell

        # if self.sowGroupCell:
        #     return self.sowGroupCell

    @property
    def get_sow_location(self):
        if self.workshop:
            return self.workshop

        if self.section:
            return self.section

        # if self.sowSingleCell:
        #     return self.sowSingleCell

        if self.sowAndPigletsCell:
            return self.sowAndPigletsCell

        # if self.sowGroupCell:
        #     return self.sowGroupCell

    @property
    def get_workshop(self):
        if self.workshop:
            return self.workshop

        if self.section:
            return self.section.workshop

        if self.sowSingleCell:
            return self.sowSingleCell.section.workshop

        if self.pigletsGroupCell:
            return self.pigletsGroupCell.section.workshop

        if self.sowAndPigletsCell:
            return self.sowAndPigletsCell.section.workshop

        if self.sowGroupCell:
            return self.sowGroupCell.section.workshop

    def __str__(self):
        return str(self.pk)

    @property
    def is_empty(self):
        if not self.get_located_active_piglets() and \
            not self.sow_set.all() and \
            not self.gilt_set.all():
                return True
        return False

    @property
    def is_sow_empty(self):
        if not self.sow_set.all():
            return True
        return False

    @property
    def is_piglets_empty(self):
        if not self.piglets.all():
            return True
        return False

    @property
    def get_cell_number(self):
        if self.sowSingleCell:
            return f'{self.sowSingleCell.section.number}/{self.sowSingleCell.number}'

        if self.pigletsGroupCell:
            return f'{self.pigletsGroupCell.section.number}/{self.pigletsGroupCell.number}'

        if self.sowAndPigletsCell:
            return f'{self.sowAndPigletsCell.section.number}/{self.sowAndPigletsCell.number}'

        if self.sowGroupCell:
            return f'{self.sowGroupCell.section.number}/{self.sowGroupCell.number}'

        return None

    @property
    def sows_count_by_tour(self):
        return self.sow_set.get_tours_with_count_sows_by_location(self)
