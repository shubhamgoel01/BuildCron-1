import csv
import os

from bson import ObjectId
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from pymongo import MongoClient
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from BuildCron.serializers import *
from django.db.models import Q
from BuildCron.config import stringify_object_id

client = MongoClient('localhost', 27017)

class CustomUserCreate(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format='json'):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegistrationView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        userId = request.GET.get('id')
        reg_id = request.GET.get('client_id')
        if userId:
            return Response(RegistrationSerializer(get_object_or_404(Registration, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                RegistrationSerializer(get_object_or_404(Registration, Q(client__id=reg_id)),
                                       many=False).data, status=status.HTTP_200_OK)

        serializer = RegistrationSerializer(Registration.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        finding_exising_user = Registration.objects.filter(Q(client_id__iexact=data.get('client_id')))

        if finding_exising_user.exists():
            return Response({"message": "Client Already Registered"},
                            status=status.HTTP_200_OK)

        if data.get('gstn'):
            finding_exising_user_detail = Registration.objects.filter(gstn__iexact=data.get('gstn'))

            if finding_exising_user_detail.exists():
                return Response({"message": "GST Already Exists"},
                                status=status.HTTP_200_OK)
        if data.get('email'):
            finding_exising_user_detail = Registration.objects.filter(email__iexact=data.get('email'))
            if finding_exising_user_detail.exists():
                return Response({"message": "Email Already Exists"},
                                status=status.HTTP_200_OK)

        try:
            serializer = RegistrationSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            return Response({"Status": True,
                             "Message": "Successfully Registered User"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        userId = request.GET.get('id')
        clientId = request.GET.get('client_id')
        user = ""
        if userId:
            try:
                user = Registration.objects.get(id=userId)
            except Registration.DoesNotExist:
                return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        elif clientId:
            try:
                user = Registration.objects.get(client_id=userId)
            except Registration.DoesNotExist:
                return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if (request.data.get("status") == "Active"):
                data = {"username": request.data.get('username'), "password": request.data.get('password')}
                serializer = RegistrationSerializer(user, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                serializer_user = CustomUserSerializer(data=request.data)
                if serializer_user.is_valid():
                    serializer_user.save()
                return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
            else:
                return Response({"error": "user not approved yet", "status": False}, status=status.HTTP_400_BAD_REQUEST)

        except:
            return Response({"error": "Something went wrong", "status": False}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        if request.GET.get('id'):
            get_object_or_404(Registration, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Registration, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



class Login(APIView):

    permission_classes = (permissions.AllowAny,)



    def post(self, request):
        data = request.data
        finding_exising_user = Registration.objects.filter(Q(email__iexact=data.get('email')))

        if finding_exising_user.exists():
            if Registration.objects.filter(Q(password__iexact=data.get('password'))):
                dbs = client.list_database_names()
                if data.get('user') in dbs:
                    return Response({"message": "Successfully Logged In User"},
                                    status=status.HTTP_200_OK)
                else:
                    checkist_data = Checklist.objects.all()
                    question_data = Questions.objects.all()
                    db = client[data.get('user')]
                    checklist = db['checklist']
                    questions = db['questions']
                    for data in checkist_data:
                        checklist.insert_one({
                            'checklist_id':data.id,
                            'name':data.name,
                            'type':data.type
                        })
                    for data in question_data:
                        questions.insert_one({
                            'checklist_id':data.checklist.id,
                            'text':data.text,
                            'status':data.status
                        })

                    return Response({"message": "Successfully Logged In"},
                                    status=status.HTTP_200_OK)
            return Response({"message": "Wrong Password"},
                            status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No Such email exists'}, status=status.HTTP_200_OK)

class QuestionPostView(APIView):
    permission_classes = (permissions.AllowAny,)

    def getChecklistData(self, db):
        checklist_data = db.checklist.find({})
        if checklist_data:
            checklist_data = stringify_object_id(checklist_data)
            return checklist_data
        else:
            return None

    def getQuestionData(self, db):
        question_data = db.questions.find({})
        if question_data:
            checklist_data = stringify_object_id(question_data)
            return checklist_data
        else:
            return None

    def get(self, request):
        data = request.data
        user = request.GET.get('user')
        if (data.get('type') == "checklist"):
            db = client[user]
            retrieve = self.getChecklistData(db)
            return Response({'status':True, 'Message':retrieve}, status=status.HTTP_200_OK)
        else:
            db = client[user]
            retrieve = self.getQuestionData(db)
            return Response({'status': True, 'Message': retrieve}, status=status.HTTP_200_OK)

    def post(self, request):
        user_name = request.GET.get('user')
        data = request.data
        try:
            db = client[user_name]
            questions = db['questions']
            questions.update_one(
                {
                    '_id': ObjectId(data.get('id'))
                },
                {
                    "$set":
                        {
                            "status": data.get('status')
                        }
                }
            )
            return Response({'Status': True, 'Message': 'Successfully Updated Question'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

class PostImagesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def getChecklistData(self, db):
        checklist_data = db.checklist.find({})
        if checklist_data:
            checklist_data = stringify_object_id(checklist_data)
            return checklist_data
        else:
            return None

    def get(self, request):
        user = request.GET.get('user')
        db = client[user]
        retrieve = self.getChecklistData(db)
        return Response({'status':True, 'Message':retrieve}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        try:
            db = client[data.get('user')]
            checklist_images = db['Checklist_Images']
            checklist_images.insert_one({
                'checklist_id':data.get('checklist_id'),
                'images': data.get('images')
            })
            return Response({'Status': True, 'Message': 'Successfully Added Images'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

class LicensesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        userId = request.GET.get('id')
        reg_id = request.GET.get('license_id')
        if userId:
            return Response(LicensesSerializer(get_object_or_404(Licenses, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                LicensesSerializer(get_object_or_404(Licenses, Q(license__id=reg_id)),
                                   many=False).data, status=status.HTTP_200_OK)

        serializer = LicensesSerializer(Licenses.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        try:
            serializer = LicensesSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added License"},
                                status=status.HTTP_201_CREATED)

            return Response({"Status": True,
                             "Message": "Successfully Added License"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        userId = request.GET.get('id')
        client_id = request.GET.get('client_id')
        try:
            user = Licenses.objects.get(id=userId)
        except Licenses.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        data = {'status': 'Approved'}
        serializer = LicensesApprovedSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': ''})

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Licenses, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Licenses, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class ChecklistView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        userId = request.GET.get('id')
        reg_id = request.GET.get('checklist_id')
        if userId:
            return Response(ChecklistSerializer(get_object_or_404(Checklist, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                ChecklistSerializer(get_object_or_404(Checklist, Q(checklist__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = ChecklistSerializer(Checklist.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            with open(os.path.join(settings.BASE_DIR, 'media/Checklist.csv')) as csv_file:
                data = csv.reader(csv_file)
                for row in data:
                    print(row)
                    checklist = Checklist.objects.get_or_create(
                        name=row[0],
                        type=row[1],
                    )
            try:
                serializer = ChecklistSerializer(data=checklist)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"Status": True,
                                     "Message": "Successfully Added Checklist"},
                                    status=status.HTTP_201_CREATED)
                return Response({"Status": True,
                                 "Message": "Successfully Added Checklist"},
                                status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = ChecklistSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added Checklist"},
                                status=status.HTTP_201_CREATED)

            return Response({"Status": True,
                             "Message": "Successfully Added Checklist"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = Checklist.objects.get(id=userId)
        except Checklist.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ChecklistSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successfull'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Checklist, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Checklist, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class QuestionsView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        userId = request.GET.get('id')
        reg_id = request.GET.get('question_id')
        if userId:
            return Response(QuestionsSerializer(get_object_or_404(Questions, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                QuestionsSerializer(get_object_or_404(Questions, Q(question__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = QuestionsSerializer(Questions.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        data = request.data
        if (data.get('Action') == "Bulk"):
            with open(os.path.join(settings.BASE_DIR, 'media/Question.csv')) as csv_file:
                data = csv.reader(csv_file)
                for row in data:
                    question = Questions.objects.get_or_create(
                        name=row[0],
                        status=row[1],
                        checklist_id=row[2]
                    )
            try:
                serializer = QuestionsSerializer(data=question)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"Status": True,
                                     "Message": "Successfully Added Question"},
                                    status=status.HTTP_201_CREATED)
                return Response({"Status": False,
                                 "Message": "Failed To Add Question"},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = QuestionsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added Question"},
                                status=status.HTTP_201_CREATED)
            return Response({"Status": False,
                             "Message": "Failed To Add Question"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        client_id = request.GET.get('checklist_id')
        try:
            user = Questions.objects.get(id=userId)
        except Questions.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = QuestionsSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successful'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Questions, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Questions, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class MaterialsView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        userId = request.GET.get('id')
        reg_id = request.GET.get('material_id')
        if userId:
            return Response(MaterialSerializer(get_object_or_404(Material, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                MaterialSerializer(get_object_or_404(Material, Q(material__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = MaterialSerializer(Material.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            with open(os.path.join(settings.BASE_DIR, 'media/Material.csv')) as csv_file:
                data = csv.reader(csv_file)

                for row in data:
                    material = Material.objects.get_or_create(
                        name=row[0],
                        description=row[1],
                        uom=row[2],
                        status=row[3],
                    )
            try:
                serializer = MaterialSerializer(data=material)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"Status": True,
                                     "Message": "Successfully Added Material"},
                                    status=status.HTTP_201_CREATED)
                return Response({"Status": False,
                                 "Message": "Failed To Add Material"},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer = MaterialSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added Material"},
                                status=status.HTTP_201_CREATED)
            return Response({"Status": False,
                             "Message": "Failed To Add Material"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = Material.objects.get(id=userId)
        except Material.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = MaterialSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successful'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Material, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Material, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class QueriesView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        userId = request.GET.get('id')
        reg_id = request.GET.get('query_id')
        if userId:
            return Response(QuerySerializer(get_object_or_404(Queries, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                QuerySerializer(get_object_or_404(Queries, Q(query__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = QuerySerializer(Queries.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        try:
            serializer = QuerySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added Query"},
                                status=status.HTTP_201_CREATED)

            return Response({"Status": False,
                             "Message": "Failed To Add Query"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = Queries.objects.get(id=userId)
        except Queries.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = QuerySerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successful'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Queries, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Queries, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
