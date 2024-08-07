# Generated by Django 5.0.6 on 2024-05-26 20:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('User', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=10)),
                ('source', models.CharField(choices=[('IND', 'India'), ('PAK', 'Pakistan'), ('USA', 'United States'), ('GER', 'Germany'), ('FRA', 'France')], max_length=10)),
                ('destination', models.CharField(choices=[('IND', 'India'), ('PAK', 'Pakistan'), ('USA', 'United States'), ('GER', 'Germany'), ('FRA', 'France')], max_length=10)),
                ('capacity', models.PositiveIntegerField()),
                ('vacancy', models.PositiveIntegerField(blank=True, default=None)),
                ('departure', models.DateTimeField()),
                ('reach', models.DateTimeField()),
                ('price_per_head', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n_passenger', models.PositiveIntegerField()),
                ('number', models.CharField(max_length=10)),
                ('booked_at', models.DateTimeField(auto_now=True)),
                ('totalPrice', models.PositiveIntegerField(default=0)),
                ('flight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='AirApp.flight')),
                ('passenger', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='User.passenger')),
            ],
        ),
    ]
