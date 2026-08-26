from django.shortcuts import redirect, render, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date

from .models import Book, Student, IssuedBook
from .forms import IssueBookForm


# =========================================================
# HOME / INDEX
# =========================================================

def index(request):
    total_books = Book.objects.count()
    total_students = Student.objects.count()
    issued_books = IssuedBook.objects.count()

    # Count unique books currently issued
    issued_isbns = set(
        IssuedBook.objects.values_list('isbn', flat=True)
    )

    available_books = total_books - len(issued_isbns)

    categories = (
        Book.objects
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    recent_books = Book.objects.all().order_by('-id')[:6]

    return render(request, "index.html", {
        'total_books': total_books,
        'total_students': total_students,
        'issued_books': issued_books,
        'available_books': max(available_books, 0),
        'categories': categories,
        'recent_books': recent_books,
    })


# =========================================================
# BROWSE BOOKS
# =========================================================

def browse_books(request):

    books = Book.objects.all().order_by('-id')

    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()

    if search:

        books = books.filter(
            Q(name__icontains=search) |
            Q(author__icontains=search)
        )

        # Search by ISBN if numeric
        if search.isdigit():
            books = (
                books |
                Book.objects.filter(isbn=int(search))
            )

    if category:
        books = books.filter(category=category)

    categories = (
        Book.objects
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    # Currently issued ISBNs
    issued_isbns = set(
        str(isbn)
        for isbn in IssuedBook.objects.values_list('isbn', flat=True)
    )

    return render(request, 'browse_books.html', {
        'books': books.distinct(),
        'categories': categories,
        'search': search,
        'selected_category': category,
        'issued_isbns': issued_isbns,
    })


# =========================================================
# ADD BOOK
# =========================================================

@login_required(login_url='/admin_login')
def add_book(request):

    if request.method == "POST":

        name = request.POST.get('name')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        category = request.POST.get('category')

        try:

            Book.objects.create(
                name=name,
                author=author,
                isbn=isbn,
                category=category
            )

            return render(request, "add_book.html", {
                'success': True
            })

        except Exception as e:

            return render(request, "add_book.html", {
                'error': str(e)
            })

    return render(request, "add_book.html")


# =========================================================
# VIEW BOOKS
# =========================================================

@login_required(login_url='/admin_login')
def view_books(request):

    books = Book.objects.all().order_by('id')

    return render(
        request,
        "view_books.html",
        {
            'books': books
        }
    )


# =========================================================
# VIEW STUDENTS
# =========================================================

@login_required(login_url='/admin_login')
def view_students(request):

    students = Student.objects.all().order_by('id')

    return render(
        request,
        "view_students.html",
        {
            'students': students
        }
    )


# =========================================================
# ISSUE BOOK
# =========================================================

# ------------------------------
# ISSUE BOOK (Admin)
# ------------------------------
@login_required(login_url='/admin_login')
def issue_book(request):

    students = Student.objects.select_related('user').all().order_by(
        'user__first_name',
        'user__last_name'
    )

    books = Book.objects.all().order_by('name')

    if request.method == "POST":

        student_id = request.POST.get('student_id')
        isbn = request.POST.get('isbn')
        issue_date = request.POST.get('issue_date')
        expiry_date = request.POST.get('expiry_date')

        # Check all fields
        if not student_id or not isbn or not issue_date or not expiry_date:
            return render(request, "issue_book.html", {
                'students': students,
                'books': books,
                'error': 'Please fill in all fields.'
            })

        # Check student exists
        student = Student.objects.filter(user_id=student_id).first()

        if not student:
            return render(request, "issue_book.html", {
                'students': students,
                'books': books,
                'error': 'Selected student does not exist.'
            })

        # Check book exists
        book = Book.objects.filter(isbn=isbn).first()

        if not book:
            return render(request, "issue_book.html", {
                'students': students,
                'books': books,
                'error': 'Selected book does not exist.'
            })

        # Check whether this book is already issued
        already_issued = IssuedBook.objects.filter(
            isbn=str(book.isbn)
        ).exists()

        if already_issued:
            return render(request, "issue_book.html", {
                'students': students,
                'books': books,
                'error': f'"{book.name}" is already issued.'
            })

        # Create issued book
        IssuedBook.objects.create(
            student_id=str(student.user.id),
            isbn=str(book.isbn),
            issued_date=issue_date,
            expiry_date=expiry_date
        )

        return render(request, "issue_book.html", {
            'students': students,
            'books': books,
            'success': True
        })

    return render(request, "issue_book.html", {
        'students': students,
        'books': books
    })


# =========================================================
# VIEW ISSUED BOOKS
# =========================================================

@login_required(login_url='/admin_login')
def view_issued_book(request):

    issued_books = IssuedBook.objects.all().order_by('-issued_date')

    details = []

    for issued in issued_books:

        # Find book
        book = Book.objects.filter(
            isbn=issued.isbn
        ).first()

        # Find student
        student = Student.objects.filter(
            user_id=issued.student_id
        ).first()

        if not book or not student:
            continue

        # Calculate overdue days
        days = (
            date.today() - issued.issued_date
        ).days

        fine = 0

        if days > 14:
            fine = (days - 14) * 5

        details.append({
            'student': student.user,
            'student_id': student.user.id,
            'book': book.name,
            'author': book.author,
            'isbn': book.isbn,
            'issued_date': issued.issued_date,
            'expiry_date': issued.expiry_date,
            'fine': fine,
            'issued_id': issued.id,
        })

    return render(
        request,
        "view_issued_book.html",
        {
            'issuedBooks': issued_books,
            'details': details
        }
    )


# =========================================================
# RETURN BOOK
# =========================================================

@login_required(login_url='/admin_login')
def return_book(request, myid):

    issued_book = IssuedBook.objects.filter(
        id=myid
    ).first()

    if issued_book:
        issued_book.delete()

    return redirect("view_issued_book")


# =========================================================
# STUDENT ISSUED BOOKS
# =========================================================
# ------------------------------
# STUDENT ISSUED BOOKS
# ------------------------------
@login_required(login_url='/student_login')
def student_issued_books(request):

    student = Student.objects.get(user=request.user)

    issued_books = IssuedBook.objects.filter(
        student_id=str(student.user.id)
    ).order_by('-issued_date')

    details = []

    for issued in issued_books:

        book = Book.objects.filter(
            isbn=int(issued.isbn)
        ).first()

        days = (date.today() - issued.issued_date).days

        fine = 0

        if days > 14:
            fine = (days - 14) * 5

        if book:
            details.append({
                'book': book,
                'issued_date': issued.issued_date,
                'expiry_date': issued.expiry_date,
                'fine': fine,
            })

    return render(
        request,
        'student_issued_books.html',
        {
            'details': details
        }
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

@login_required(login_url='/student_login')
def profile(request):

    try:
        student = Student.objects.get(
            user=request.user
        )
    except Student.DoesNotExist:
        student = None

    return render(
        request,
        "profile.html",
        {
            'student': student
        }
    )


# =========================================================
# EDIT PROFILE
# =========================================================

@login_required(login_url='/student_login')
def edit_profile(request):

    student = Student.objects.get(
        user=request.user
    )

    if request.method == "POST":

        email = request.POST.get('email')
        phone = request.POST.get('phone')
        branch = request.POST.get('branch')
        classroom = request.POST.get('classroom')
        roll_no = request.POST.get('roll_no')

        student.user.email = email
        student.phone = phone
        student.branch = branch
        student.classroom = classroom
        student.roll_no = roll_no

        student.user.save()
        student.save()

        return render(
            request,
            "edit_profile.html",
            {
                'alert': True
            }
        )

    return render(
        request,
        "edit_profile.html"
    )


# =========================================================
# DELETE BOOK
# =========================================================

@login_required(login_url='/admin_login')
def delete_book(request, myid):

    book = Book.objects.filter(
        id=myid
    ).first()

    if book:
        book.delete()

    return redirect("/view_books")


# =========================================================
# DELETE STUDENT
# =========================================================

@login_required(login_url='/admin_login')
def delete_student(request, myid):

    student = Student.objects.filter(
        id=myid
    ).first()

    if student:
        student.delete()

    return redirect("/view_students")


# =========================================================
# CHANGE PASSWORD
# =========================================================

@login_required(login_url='/student_login')
def change_password(request):

    if request.method == "POST":

        current_password = request.POST.get(
            'current_password'
        )

        new_password = request.POST.get(
            'new_password'
        )

        user = User.objects.get(
            id=request.user.id
        )

        if user.check_password(current_password):

            user.set_password(new_password)
            user.save()

            return render(
                request,
                "change_password.html",
                {
                    'alert': True
                }
            )

        return render(
            request,
            "change_password.html",
            {
                'currpasswrong': True
            }
        )

    return render(
        request,
        "change_password.html"
    )


# =========================================================
# STUDENT REGISTRATION
# =========================================================

def student_registration(request):

    if request.method == "POST":

        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        branch = request.POST.get('branch')
        classroom = request.POST.get('classroom')
        roll_no = request.POST.get('roll_no')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        image = request.FILES.get('image')

        if password != confirm_password:

            return render(
                request,
                "student_registration.html",
                {
                    'passnotmatch': True
                }
            )

        # Prevent duplicate username
        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "student_registration.html",
                {
                    'error': 'Username already exists.'
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        Student.objects.create(
            user=user,
            phone=phone,
            branch=branch,
            classroom=classroom,
            roll_no=roll_no,
            image=image
        )

        return render(
            request,
            "student_registration.html",
            {
                'alert': True
            }
        )

    return render(
        request,
        "student_registration.html"
    )


# =========================================================
# STUDENT LOGIN
# =========================================================

def student_login(request):

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:

            if user.is_superuser:
                return HttpResponse(
                    "You are not a student!"
                )

            login(request, user)

            return redirect(
                "student_dashboard"
            )

        return render(
            request,
            "student_login.html",
            {
                'alert': True
            }
        )

    return render(
        request,
        "student_login.html"
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

def admin_login(request):

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:

            if not user.is_superuser:
                return HttpResponse(
                    "You are not an admin."
                )

            login(request, user)

            return redirect(
                "admin_dashboard"
            )

        return render(
            request,
            "admin_login.html",
            {
                'alert': True
            }
        )

    return render(
        request,
        "admin_login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

def Logout(request):

    logout(request)

    return redirect("/")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@login_required(login_url='/admin_login')
def admin_dashboard(request):

    total_books = Book.objects.count()

    total_students = Student.objects.count()

    issued_books = IssuedBook.objects.count()

    overdue_books = IssuedBook.objects.filter(
        expiry_date__lt=date.today()
    ).count()

    issued_isbns = set(
        IssuedBook.objects.values_list(
            'isbn',
            flat=True
        )
    )

    available_books = (
        total_books -
        len(issued_isbns)
    )

    return render(
        request,
        'admin_dashboard.html',
        {
            'total_books': total_books,
            'total_students': total_students,
            'issued_books': issued_books,
            'overdue_books': overdue_books,
            'available_books': max(
                available_books,
                0
            ),
        }
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@login_required(login_url='/student_login')
def student_dashboard(request):

    student = Student.objects.get(
        user=request.user
    )

    issued_books = IssuedBook.objects.filter(
        student_id=str(student.user.id)
    )

    overdue_books = issued_books.filter(
        expiry_date__lt=date.today()
    ).count()

    issued_isbns = issued_books.values_list(
        'isbn',
        flat=True
    )

    available_books = Book.objects.exclude(
        isbn__in=issued_isbns
    ).count()

    return render(
        request,
        'student_dashboard.html',
        {
            'available_books': available_books,
            'issued_books': issued_books.count(),
            'overdue_books': overdue_books,
        }
    )