from rest_framework import generics
from rest_framework import permissions

from .models import Test, JmeterRawLogsFile
from .serializers import TestSerializer, JmeterRawLogsFileSerializer


class TestList(generics.ListCreateAPIView):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [permissions.DjangoModelPermissions]


class JmeterLogsFileList(generics.ListCreateAPIView):
    queryset = JmeterRawLogsFile.objects.all()
    serializer_class = JmeterRawLogsFileSerializer
    permission_classes = [permissions.DjangoModelPermissions]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
