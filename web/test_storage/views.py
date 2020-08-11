import logging

from rest_framework import generics
from rest_framework import permissions

from .models import Test, JmeterRawLogsFile
from .serializers import TestSerializer, JmeterRawLogsFileSerializer

logger = logging.getLogger(__name__)


class TestList(generics.ListCreateAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class JmeterLogsFileList(generics.ListCreateAPIView):
    queryset = JmeterRawLogsFile.objects.all()
    serializer_class = JmeterRawLogsFileSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def perform_create(self, serializer):
        logger.debug('JmeterLogsFileList going to save', self)
        serializer.save(user=self.request.user)
        logger.info('JmeterLogsFileList saved', self)
