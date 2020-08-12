from django.test import TestCase
from ..models import Project
from ..models import Customer


class CustomerTest(TestCase):
    """
    Test module for Customer model
    """

    def setUp(self):
        Customer.objects.create(
            name='test-key',
            description='Test description',
        )

    def test_customer_description(self):
        test_key_customer = Customer.objects.get(name='test-key')
        self.assertEqual(
            test_key_customer.description, "Test description")


class ProjectTest(TestCase):
    """
    Test module for Project model
    """

    def setUp(self):
        customer = Customer.objects.create(
            name='test-customer',
            description='Test customer description',
        )
        Project.objects.create(
            key='test-project',
            name='Test name project',
            customer=customer,
        )

    def test_project_description(self):
        project = Project.objects.get(key='test-project')
        self.assertEqual(
            project.name, "Test name project")
        self.assertEqual(
            project.customer.description, "Test customer description")
