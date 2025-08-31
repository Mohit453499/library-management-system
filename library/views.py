from django.shortcuts import redirect, render, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import date

from .models import *
from .forms import IssueBookForm
from . import forms, models

# ------------------------------
# INDEX / HOME PAGE
# ------------------------------
def index(request):
    return render(request, "index.html")


# ------------------------------
# ADD BOOK (Admin Only)
# ------------------------------
@login_required(login_url='/admin_login')
def add_book(request):
    if request.method == "POST":
        name = request.POST['name']
        author = request.POST['author']
        isbn = request.POST['isbn']
        category = request.POST['category']

        books = Book.objects.create(name=name, author=author, isbn=isbn, category=category)
        books.save()
        alert = True
        return render(request, "add_book.html", {'alert': alert})
    return render(request, "add_book.html")
@login_required(login_url='/admin_login')
def view_books(request):
    books = Book.objects.all().order_by('id')  # fetch all books
    return render(request, "view_books.html", {'books': books})

# ------------------------------
# VIEW ALL BOOKS (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def view_books(request):
    books = Book.objects.all()
    return render(request, "view_books.html", {'books': books})


# ------------------------------
# VIEW ALL STUDENTS (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def view_students(request):
    students = Student.objects.all()
    return render(request, "view_students.html", {'students': students})


# ------------------------------
# ISSUE BOOK (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def issue_book(request):
    form = forms.IssueBookForm()
    if request.method == "POST":
        form = forms.IssueBookForm(request.POST)
        if form.is_valid():
            obj = models.IssuedBook()
            obj.student_id = request.POST['name2']
            obj.isbn = request.POST['isbn2']
            obj.save()
            alert = True
            return render(request, "issue_book.html", {'obj': obj, 'alert': alert})
    return render(request, "issue_book.html", {'form': form})


# ------------------------------
# VIEW ISSUED BOOKS (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def view_issued_book(request):
    issuedBooks = IssuedBook.objects.all()
    details = []

    for i in issuedBooks:
        days = (date.today() - i.issued_date)
        d = days.days
        fine = 0
        if d > 14:
            day = d - 14
            fine = day * 5

        books = list(models.Book.objects.filter(isbn=i.isbn))
        students = list(models.Student.objects.filter(user=i.student_id))
        idx = 0
        for l in books:
            t = (
                students[idx].user,
                students[idx].user_id,
                books[idx].name,
                books[idx].isbn,
                issuedBooks[0].issued_date,
                issuedBooks[0].expiry_date,
                fine
            )
            idx += 1
            details.append(t)

    return render(request, "view_issued_book.html", {'issuedBooks': issuedBooks, 'details': details})


# ------------------------------
# STUDENT ISSUED BOOKS (Student)
# ------------------------------
@login_required(login_url='/student_login')
def student_issued_books(request):
    student = Student.objects.filter(user_id=request.user.id)
    issuedBooks = IssuedBook.objects.filter(student_id=student[0].user_id)
    li1 = []
    li2 = []

    for i in issuedBooks:
        books = Book.objects.filter(isbn=i.isbn)
        for book in books:
            t = (request.user.id, request.user.get_full_name, book.name, book.author)
            li1.append(t)

        days = (date.today() - i.issued_date)
        d = days.days
        fine = 0
        if d > 14:
            day = d - 14
            fine = day * 5
        t = (issuedBooks[0].issued_date, issuedBooks[0].expiry_date, fine)
        li2.append(t)

    return render(request, 'student_issued_books.html', {'li1': li1, 'li2': li2})


# ------------------------------
# STUDENT PROFILE
# ------------------------------
@login_required(login_url='/student_login')
def profile(request):
    return render(request, "profile.html")


# ------------------------------
# EDIT PROFILE (Student)
# ------------------------------
@login_required(login_url='/student_login')
def edit_profile(request):
    student = Student.objects.get(user=request.user)
    if request.method == "POST":
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']

        student.user.email = email
        student.phone = phone
        student.branch = branch
        student.classroom = classroom
        student.roll_no = roll_no
        student.user.save()
        student.save()
        alert = True
        return render(request, "edit_profile.html", {'alert': alert})
    return render(request, "edit_profile.html")


# ------------------------------
# DELETE BOOK (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def delete_book(request, myid):
    books = Book.objects.filter(id=myid)
    books.delete()
    return redirect("/view_books")


# ------------------------------
# DELETE STUDENT (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def delete_student(request, myid):
    students = Student.objects.filter(id=myid)
    students.delete()
    return redirect("/view_students")


# ------------------------------
# CHANGE PASSWORD (Student)
# ------------------------------
@login_required(login_url='/student_login')
def change_password(request):
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(current_password):
                u.set_password(new_password)
                u.save()
                alert = True
                return render(request, "change_password.html", {'alert': alert})
            else:
                currpasswrong = True
                return render(request, "change_password.html", {'currpasswrong': currpasswrong})
        except:
            pass
    return render(request, "change_password.html")


# ------------------------------
# STUDENT REGISTRATION
# ------------------------------
def student_registration(request):
    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        phone = request.POST['phone']
        branch = request.POST['branch']
        classroom = request.POST['classroom']
        roll_no = request.POST['roll_no']
        image = request.FILES['image']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            passnotmatch = True
            return render(request, "student_registration.html", {'passnotmatch': passnotmatch})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        student = Student.objects.create(
            user=user,
            phone=phone,
            branch=branch,
            classroom=classroom,
            roll_no=roll_no,
            image=image
        )
        user.save()
        student.save()
        alert = True
        return render(request, "student_registration.html", {'alert': alert})
    return render(request, "student_registration.html")


# ------------------------------
# STUDENT LOGIN
# ------------------------------
def student_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return HttpResponse("You are not a student!")
            else:
                return redirect("student_dashboard")
        else:
            alert = True
            return render(request, "student_login.html", {'alert': alert})
    return render(request, "student_login.html")


# ------------------------------
# ADMIN LOGIN
# ------------------------------
def admin_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if request.user.is_superuser:
                return redirect("admin_dashboard")
            else:
                return HttpResponse("You are not an admin.")
        else:
            alert = True
            return render(request, "admin_login.html", {'alert': alert})
    return render(request, "admin_login.html")


# ------------------------------
# LOGOUT (Admin & Student)
# ------------------------------
def Logout(request):
    logout(request)
    return redirect("/")
    

# ------------------------------
# ADMIN DASHBOARD
# ------------------------------
@login_required(login_url='/admin_login')
def admin_dashboard(request):
    total_books = Book.objects.count()
    total_students = Student.objects.count()
    issued_books = IssuedBook.objects.count()
    overdue_books = IssuedBook.objects.filter(expiry_date__lt=timezone.now()).count()
    available_books = total_books - issued_books

    return render(request, 'admin_dashboard.html', {
        'total_books': total_books,
        'total_students': total_students,
        'issued_books': issued_books,
        'overdue_books': overdue_books,
        'available_books': available_books,
    })


# ------------------------------
# STUDENT DASHBOARD
# ------------------------------
@login_required(login_url='/student_login')
def student_dashboard(request):
    student = Student.objects.get(user=request.user)
    
    # Filter using the correct field name
    issued_books = IssuedBook.objects.filter(student_id=student.user.id)
    
    overdue_books = issued_books.filter(expiry_date__lt=timezone.now()).count()
    available_books = Book.objects.exclude(isbn__in=issued_books.values_list('isbn', flat=True)).count()

    return render(request, 'student_dashboard.html', {
        'available_books': available_books,
        'issued_books': issued_books.count(),
        'overdue_books': overdue_books,
    })
@login_required(login_url='/student_login')
def profile(request):
    try:
        student = Student.objects.get(user=request.user)  # Fetch student data
    except Student.DoesNotExist:
        student = None  # Handle case where student record doesn't exist

    return render(request, "profile.html", {'student': student})