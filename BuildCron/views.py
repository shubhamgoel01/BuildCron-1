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

#mongodb://ec2-54-169-244-23.ap-southeast-1.compute.amazonaws.com:27017/?readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false
client = MongoClient('ec2-54-169-244-23.ap-southeast-1.compute.amazonaws.com', 27017)

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
        finding_exising_user = Registration.objects.filter(Q(phone__exact=data.get('mobile')))

        if finding_exising_user.exists():
            if Registration.objects.filter(Q(password__iexact=data.get('password'))):
                dbs = client.list_database_names()
                if data.get('mobile') in dbs:
                    return Response({"message": "Successfully Logged In User"},
                                    status=status.HTTP_200_OK)
                else:
                    checkist_data = Checklist.objects.all()
                    question_data = Questions.objects.all()
                    db = client[data.get('mobile')]
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
                            'status':data.status,
                            'note':""
                        })

                    return Response({"message": "Successfully Logged In"},
                                    status=status.HTTP_200_OK)
            return Response({"message": "Wrong Password"},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'No Such email exists'}, status=status.HTTP_400_BAD_REQUEST)

class QuestionPostView(APIView):
    permission_classes = (permissions.AllowAny,)

    def getChecklistData(self, db, sub_type):
        if sub_type == "Quality":
            checklist_data = list(db.checklist.find({'type':sub_type}))
            if checklist_data:
                stringify_object_id(checklist_data)
                return checklist_data
            else:
                return None
        else:
            checklist_data = list(db.checklist.find({'type': sub_type}))
            if checklist_data:
                stringify_object_id(checklist_data)
                return checklist_data
            else:
                return None

    def getQuestionData(self, db):
        question_data = list(db.questions.find({}))
        if question_data:
            stringify_object_id(question_data)
            return question_data
        else:
            return None

    def get(self, request):
        data = request.data
        if (request.GET.get('type') == "checklist"):
            db_name = request.GET.get('mobile')
            sub_type = request.GET.get('sub_type')
            db = client[db_name]
            retrieve = self.getChecklistData(db,sub_type)
            return Response({'status':True, 'Message':retrieve}, status=status.HTTP_200_OK)
        else:
            db_name = request.GET.get('mobile')
            db = client[db_name]
            retrieve = self.getQuestionData(db)
            return Response({'status': True, 'Message': retrieve}, status=status.HTTP_200_OK)

    def post(self, request):
        user_name = request.GET.get('mobile')
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
                            "status": data.get('status'),
                            "note": data.get('note') if data.get('status') == "2" else ""
                        }
                }
            )
            return Response({'Status': True, 'Message': 'Successfully Updated Question'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

class PostImagesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def getChecklistImagesData(self, db):
        checklist_data = list(db.Checklist_Images.find({}))
        if checklist_data:
            stringify_object_id(checklist_data)
            return checklist_data
        else:
            return None

    def get(self, request):
        user = request.GET.get('mobile')
        db = client[user]
        retrieve = self.getChecklistImagesData(db)
        return Response({'status':True, 'Message':retrieve}, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        try:
            db = client[data.get('mobile')]
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
                        text=row[0],
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


# ---------------------------------  7 aug -----------

class siteInstructionView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        userId = request.GET.get('id')
        reg_id = request.GET.get('siteInstruction_id')
        if userId:
            return Response(siteInstructionSerializer(get_object_or_404(siteInstruction, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                siteInstructionSerializer(get_object_or_404(siteInstruction, Q(siteInstruction__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = siteInstructionSerializer(siteInstruction.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            pass
            #Do the bulk upload here
        try:
            serializer = siteInstructionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added siteInstruction"},
                                status=status.HTTP_201_CREATED)
            serializer.save()
            return Response({"Status": True,
                             "Message": "Successfully Added siteInstruction"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = siteInstruction.objects.get(id=userId)
        except siteInstruction.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = siteInstructionSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successfull'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(siteInstruction, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(siteInstruction, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class FAQsView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        userId = request.GET.get('id')
        reg_id = request.GET.get('FAQs_id')
        if userId:
            return Response(FAQsSerializer(get_object_or_404(FAQs, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
                FAQsSerializer(get_object_or_404(FAQs, Q(FAQs__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = FAQsSerializer(FAQs.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            pass
            #Do the bulk upload here
        try:
            serializer = FAQsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added FAQs"},
                                status=status.HTTP_201_CREATED)
            serializer.save()
            return Response({"Status": True,
                             "Message": "Successfully Added FAQs"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = FAQs.objects.get(id=userId)
        except FAQs.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = FAQsSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successfull'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(FAQs, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(FAQs, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class RolesView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        userId = request.GET.get('id')
        reg_id = request.GET.get('Roles_id')
        if userId:
            return Response(RolesSerializer(get_object_or_404(Roles, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
               RolesSerializer(get_object_or_404(Roles, Q(Roles__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = RolesSerializer(Roles.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            pass
            #Do the bulk upload here
        try:
            serializer = FAQsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added Roles"},
                                status=status.HTTP_201_CREATED)
            serializer.save()
            return Response({"Status": True,
                             "Message": "Successfully Added Roles"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = Roles.objects.get(id=userId)
        except Roles.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RolesSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successfull'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Roles, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Roles, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class AdminView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        userId = request.GET.get('id')
        reg_id = request.GET.get('Admin_id')
        if userId:
            return Response(AdminSerializer(get_object_or_404(Admin, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
               AdminSerializer(get_object_or_404(Admin, Q(Admin__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = AdminSerializer(Admin.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            pass
            #Do the bulk upload here
        try:
            serializer = FAQsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully Added Admin"},
                                status=status.HTTP_201_CREATED)
            serializer.save()
            return Response({"Status": True,
                             "Message": "Successfully Added Admin"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = Admin.objects.get(id=userId)
        except Admin.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AdminSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successfull'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(Admin, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(Admin, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        
class NCView(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        userId = request.GET.get('id')
        reg_id = request.GET.get('NC_id')
        if userId:
            return Response(NCSerializer(get_object_or_404(NC, id=userId), many=False).data,
                            status=status.HTTP_200_OK)
        elif reg_id:
            return Response(
               NCSerializer(get_object_or_404(NC, Q(NC__id=reg_id)),
                                    many=False).data, status=status.HTTP_200_OK)

        serializer = NCSerializer(NC.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if (data.get('Action') == "Bulk"):
            pass
            #Do the bulk upload here
        try:
            serializer = FAQsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True,
                                 "Message": "Successfully AddedNC"},
                                status=status.HTTP_201_CREATED)
            serializer.save()
            return Response({"Status": True,
                             "Message": "Successfully Added NC"},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"Errors": "Some field miss check and enter", "exception": str(e), "status": False},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = request.data
        userId = request.GET.get('id')
        try:
            user = NC.objects.get(id=userId)
        except NC.DoesNotExist:
            return Response({"error": "User ID not found", "status": False}, status=status.HTTP_400_BAD_REQUEST)
        serializer = NCSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_206_PARTIAL_CONTENT)
        return Response({'Status': False, 'Message': 'Not Successfull'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.GET.get('id'):
            get_object_or_404(NC, id=request.GET.get('id')).delete()
        else:
            get_object_or_404(NC, id=request.data.get('id')).delete()
        return Response({"success": "Id related data deleted successfully"}, status=status.HTTP_204_NO_CONTENT)