from django.db import models

class Roles(models.Model):
    roles = models.CharField(unique=True, max_length=100)
    status = models.CharField(max_length=200)

    def __str__(self):
        return "%s" % (self.roles)


class Admin(models.Model):
    email = models.CharField(max_length=200)
    password = models.CharField(max_length=230)
    status = models.CharField(max_length=230)
    def __str__(self):
        return "%s" % (self.email)


class Registration(models.Model):
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    gstn = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    pincode = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    end_date = models.DateTimeField()
    no_of_license = models.IntegerField()
    contact_person = models.CharField(max_length=200)
    username = models.CharField(max_length=100, default='', null=True)
    password = models.CharField(max_length=100, default='', null=True)

    def __str__(self):
        return "%s" % (self.company_name)




class Licenses(models.Model):
    client = models.ForeignKey('Registration', models.DO_NOTHING, blank=True, null=True)
    user_name = models.CharField(max_length=200)
    start_date = models.DateField()
    user_phone = models.CharField(max_length=200)
    user_email = models.CharField(max_length=200)
    status = models.CharField(max_length=200)  # Field name made lowercase.
    device_id = models.CharField(max_length=200)
    device_name = models.CharField(max_length=200)
    users_designation = models.CharField(max_length=200)

    def __str__(self):
        return "%s" % (self.client.company_name)


class Material(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    uom = models.CharField(max_length=200)
    status = models.CharField(max_length=200)

    def __str__(self):
        return "%s" % (self.name)


class Checklist(models.Model):
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200)

    def __str__(self):
        return "%s" % (self.name)


class Questions(models.Model):
    checklist = models.ForeignKey('Checklist', models.DO_NOTHING, blank=True, null=True)
    text = models.TextField()
    status = models.CharField(max_length=120)

    def __str__(self):
        return "%s" % (self.checklist.name)


class Queries(models.Model):
    email = models.CharField(max_length=100)
    client = models.ForeignKey('Registration', models.DO_NOTHING, blank=True, null=True)
    device_id = models.CharField(max_length=200)
    query = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    date = models.DateTimeField()

    def __str__(self):
        return "%s" % (self.client.email)


class FAQs(models.Model):
    questions = models.TextField()
    status = models.CharField(max_length=200)

    def __str__(self):
        return "%s" % (self.questions)


class siteInstruction(models.Model):
    category = models.TextField()
    security_level = models.TextField()

    def __str__(self):
        return "%s" % (self.category)
