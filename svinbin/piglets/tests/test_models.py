# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase

import sows.models as sows_models
import piglets.models as piglets_models
import piglets_events.models as piglets_events_models

import locations.testing_utils as locations_testing
import sows.testing_utils as sows_testing
import piglets.testing_utils as piglets_testing


class NewBornModelManagerTest(TestCase):
    def setUp(self):
        locations_testing.create_workshops_sections_and_cells()
        sows_testing.create_statuses()

    def test_groups_with_gilts(self):
        new_born_group1 = piglets_testing.create_new_born_group(cell_number=5)
        sow1 = new_born_group1.farrows.first().sow
        gilt1 = sows_models.Gilt.objects.create_gilt(1, new_born_group1)
        new_born_group1.refresh_from_db()
        
        new_born_group2 = piglets_testing.create_new_born_group(cell_number=6)
        sow2 = new_born_group2.farrows.first().sow
        gilt2 = sows_models.Gilt.objects.create_gilt(2, new_born_group2)

        new_born_group3 = piglets_testing.create_new_born_group(cell_number=4)

        self.assertEqual(piglets_models.NewBornPigletsGroup.objects.groups_with_gilts().count(), 2)
        self.assertEqual(piglets_models.NewBornPigletsGroup.objects.all().count(), 3)


class NomadPigletsModelManagerTest(TransactionTestCase):
    def setUp(self):
        locations_testing.create_workshops_sections_and_cells()
        piglets_testing.create_piglets_statuses()
        sows_testing.create_statuses()

        self.piglets_group1 = piglets_testing.create_new_born_group(1, 1, 1, 10)
        self.piglets_group2 = piglets_testing.create_new_born_group(1, 2, 1, 12)
        self.piglets_group3 = piglets_testing.create_new_born_group(1, 3, 2, 15)

        self.piglets_group4 = piglets_testing.create_new_born_group(
            section_number=1,
            cell_number=4,
            week=1,
            quantity=10)
        self.piglets_group5 = piglets_testing.create_new_born_group(1, 5, 1, 12)
        
        piglets_groups_same_tour = piglets_models.NewBornPigletsGroup.objects.filter(pk__in=
            [self.piglets_group4.pk, self.piglets_group5.pk])
        piglets_groups_two_tours = piglets_models.NewBornPigletsGroup.objects.filter(pk__in=
            [self.piglets_group1.pk, self.piglets_group2.pk, self.piglets_group3.pk])

        self.new_born_merger_same_tour = piglets_events_models.NewBornPigletsMerger.objects \
            .create_merger_and_return_nomad_piglets_group(piglets_groups_same_tour, 
                part_number=1)[0]
        self.new_born_merger_two_tours = piglets_events_models.NewBornPigletsMerger.objects \
            .create_merger_and_return_nomad_piglets_group(piglets_groups_two_tours, 
                part_number=2)[0]

    def test_merger_part_number(self):
        nomad_group1 = self.new_born_merger_same_tour.nomad_group
        nomad_group2 = self.new_born_merger_two_tours.nomad_group
        self.assertEqual(nomad_group1.merger_part_number, 1)
        self.assertEqual(nomad_group2.merger_part_number, 2)

    def test_cells_numbers_from_merger(self):
        nomad_group1 = self.new_born_merger_same_tour.nomad_group
        nomad_group2 = self.new_born_merger_two_tours.nomad_group
        self.assertEqual(list(nomad_group1.cells_numbers_from_merger), 
            list(self.new_born_merger_same_tour.cells))
        self.assertEqual(list(nomad_group2.cells_numbers_from_merger), 
            list(self.new_born_merger_two_tours.cells))

    def test_queryset_piglets_with_weighing_record(self):
        pass