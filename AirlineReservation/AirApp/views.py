from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect,get_object_or_404
from . import forms
from . import models
from User.models import Passenger,User
from AirApp.models import Ticket
import time,razorpay
from razorpay import client
from django.core.mail import send_mail


def landing(request):
    if request.method=='POST':
        filterform = forms.FlightFilterForm(request.POST)
        if filterform.is_valid():
            source = filterform.cleaned_data['source']
            destination = filterform.cleaned_data['destination']
            errors = []
            if(source==destination):
                errors.append("Source and destination are the same.")
            if errors==[]:
                context={ "flight_list": models.Flight.objects.all().filter(source=source).filter(destination=destination) }
                return render(request, 'FlightList.html', context)
            else :
                return render(request, 'FormPage.html', {"title":"Welcome!", "form":forms.FlightFilterForm, "error":True, "error_msg":errors, "formName":"HomePage"})
        else:
            return render(request, 'FormPage.html', {"title":"Welcome!", "form":forms.FlightFilterForm, "error":True, "error_msg":["Corrupted Form"], "formName":"HomePage"})
    context= {"title":"Welcome!", "form":forms.FlightFilterForm, "error":False, "error_msg":[], "formName":"HomePage"}
    return render(request, 'FormPage.html',context)


def flight_full_list(request):
    return render(request, "FlightList.html", { "flight_list": models.Flight.objects.all() })


@login_required
def addFlight(request):
    if request.user.is_superuser :
        if request.method=='POST':
            flight = forms.FlightAddForm(data = request.POST)
            errors = []
            if flight.is_valid():
                if flight.cleaned_data['source']==flight.cleaned_data['destination'] :
                    errors.append("Source and destination are the same.")
                if flight.cleaned_data['capacity']==0:
                    errors.append("Capacity of flight is 0.")
                if flight.cleaned_data['vacancy']>flight.cleaned_data['capacity']:
                    errors.append("Vacancy of flight is more than capacity.")
                if flight.cleaned_data['vacancy']==0:
                    errors.append("Flight capacity is 0.")
                if flight.cleaned_data['departure']>=flight.cleaned_data['reach']:
                    errors.append("Depature earlier than reahing time.")
            else:
                return render(request, "FormPage.html", {"title":"Add Flight!", "form":forms.FlightAddForm, "error":True, "error_msg":["Corrupted form"], "formName":"AddFlight"})
            if len(errors)>0:
                return render(request, "FormPage.html", {"title":"Add Flight!", "form":forms.FlightAddForm, "error":True, "error_msg":errors, "formName":"AddFlight"})
            flight.save().save()
            return redirect("/flights/")
        return render(request, "FormPage.html", {"title":"Add Flight!", "form":forms.FlightAddForm, "error":False, "error_msg":[], "formName":"AddFlight"})
    else:
        return render(request, "MessagePage.html", {"title":"Unauthorised!", "message":"You are not authorised to view this page!"}) 


@login_required
def bookticket(request, flight_id):
    # Prevent superuser from booking tickets
    if request.user.is_superuser:
        return render(request, "MessagePage.html", {"title": "Not allowed", "message": "Superuser is not allowed to book tickets :("})
    
    # Handle POST request for ticket booking
    if request.method == 'POST':
        flight = get_object_or_404(models.Flight, pk=flight_id)  # Use get_object_or_404 to handle missing flight
        ticket_form = forms.TicketForm(request.POST)
        
        if ticket_form.is_valid():
            
            n_booking = ticket_form.cleaned_data['n_passenger']
            
            if n_booking > flight.vacancy:
                return render(request, "MessagePage.html", {"title": "Error", "message": "Number of bookings exceeds vacancy!"})
            
            passenger = get_object_or_404(models.Passenger, user=request.user)  # Use get_object_or_404 for passenger
            
            ticket = models.Ticket()
            ticket.passenger = passenger
            ticket.n_passenger = n_booking
            ticket.flight = flight
            ticket.number = str(time.time()).replace('.', '')[-12:]
            ticket.save()
            
            # Update the flight vacancy
            flight.vacancy -= n_booking
            flight.save()
            client = razorpay.Client(auth=("rzp_test_CbepQPSX6Lp3CN", "dk1YgCyVZRSVoUT1OGNgjWC0"))
            t=Ticket.objects.all()
            #print(t)

            for i in t:
                s=i.totalPrice
            data = { "amount": s*100
                    , "currency": "INR", "receipt": "order_rcptid_11" }
            payment = client.order.create(data=data)
            #print(payment)
            context={}
            context['payment']=payment
            return render(request,'pay.html',context)
            
            #return render(request, "MessagePage.html", {"title": "Booked", "message": "Your ticket has been successfully booked!"})
        else:
            return render(request, "MessagePage.html", {"title": "Error!", "message": "Form Corrupted."})
    
    # Handle GET request to show the booking form
    return render(request, "FormPage.html", {"title": "Booking", "form": forms.TicketForm(), "error": False, "error_msg": [], "formName": "ticket"})


@login_required
def flush_data(request):
    if request.user.is_superuser:
        models.Flight.objects.all().delete()
        models.Ticket.objects.all().delete()
        return redirect("/flights/")
    else:
        return render(request, "MessagePage.html", {"title":"Unauthorised!", "message":"You are not authorised to view this page!"}) 


@login_required
def profile_page(request):
    if request.user.is_superuser:
        return redirect('admin/')
    else:
        passenger = Passenger.objects.all().filter(user=request.user)[0]
        if passenger:
            return render(request, "ProfilePage.html", {"title":"Your Profile", "passenger" : passenger})
        else:
            return render(request, "MessagePage.html", {"title":"Not found", "message":"User not found!"})


@login_required
def cancelTicket(request, pk):
    ticket = models.Ticket.objects.all().filter(pk = pk)[0]
    if ticket.passenger.user != request.user:
        return render(request, "MessagePage.html", {"title":"Unauthorised!", "message":"Ticket does not belong to your account!"})
    if request.method=="POST":
        ticket.delete()
        return redirect('/profile')
    return render(request, "ConfirmationDelete.html", { "message":"Are you sure you want to delete this ticket? ", "cancelLink":"/profile"})


@login_required
def deleteFlight(request, pk):
    if request.user.is_superuser:
        flight = models.Flight.objects.all().filter(pk = pk)[0]
        if request.method=="POST":
            flight.delete()
            return redirect('/flights')
        return render(request, "ConfirmationDelete.html", { "message":"Are you sure you want to delete the flight : "+str(flight.number), "cancelLink":"/flights"})
    else:
        return render(request, "MessagePage.html", {"title":"Unauthorised!", "message":"You are not authorised to do perform this action!"})


@login_required
def editFlight(request, pk):
    if request.user.is_superuser :
        flight_instance = models.Flight.objects.all().filter(pk = pk)[0]
        if request.method=='POST':
            flight = forms.FlightAddForm(data = request.POST, instance = flight_instance)
            errors = []
            if flight.is_valid():
                if flight.cleaned_data['source']==flight.cleaned_data['destination'] :
                    errors.append("Source and destination are the same")
                if flight.cleaned_data['capacity']==0:
                    errors.append("Capacity of flight is 0")
                if flight.cleaned_data['vacancy']>flight.cleaned_data['capacity']:
                    errors.append("Vacancy in flight is more than capacity")
                if flight.cleaned_data['vacancy']==0:
                    errors.append("Flight capacity is 0")
                if flight.cleaned_data['departure']>=flight.cleaned_data['reach']:
                    errors.append("Depature earlier than reahing time")
            else:
                return render(request, "FormPage.html", {"title":"Add Flight!", "form":forms.FlightAddForm(instance = flight_instance), "error":True, "error_msg":["Corrupted form"], "formName":"AddFlight"})

            if len(errors)>0:
                return render(request, "FormPage.html", {"title":"Add Flight!", "form":forms.FlightAddForm(instance = flight_instance), "error":True, "error_msg":errors, "formName":"AddFlight"})

            flight.save().save()
            return redirect("/flights/")

        return render(request, "FormPage.html", {"title":"Add Flight!", "form":forms.FlightAddForm(instance = flight_instance) , "error":False, "error_msg":[], "formName":"AddFlight"})
    else:
        return render(request, "MessagePage.html", {"title":"Unauthorised!", "message":"You are not authorised to view this page!"}) 



def makepayment(request):
    client = razorpay.Client(auth=("rzp_test_CbepQPSX6Lp3CN", "dk1YgCyVZRSVoUT1OGNgjWC0"))
    o=Ticket.objects.all()
    for i in o:
        s=i.totalPrice
        s=int(s)
    print(s)
    
    data = { "amount": s*100, "currency": "INR", "receipt": "order_rcptid_11" }
    payment = client.order.create(data=data)
    #print(payment)
    context={}
    context['payment']=payment
    return render(request,'pay.html',context)


def paymentsuccess(request):
    u=User.objects.filter(id=request.user.id)
    to=u[0].email
    sub='Flight Booking  Status'
    msg='Thanks For Booking'
    frm ='aishwaryasonkule@gmail.com'
    send_mail(
        sub, 
        msg, 
        frm, 
        [to], 
        fail_silently=False
    )
     
    return render(request,"MessagePage.html", {"title": "Booked", "message": "Your ticket has been successfully booked!"})