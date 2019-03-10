from django.db import models
from django.core.validators import MinValueValidator
from enum import Enum

# Create your models here.
class CuentaEmpresa(models.Model):
    saldo = models.DecimalField(null=False, validators=[MinValueValidator(0)], max_digits=10, decimal_places=2)   


class CuentaPagar(models.Model):
    ORDER_STATUS = (
        ('1', 'Cancelled'),
        ('2', 'Paid'),
        ('3', 'Pending'),
        ('4', 'Overdue'),
    )
    
    total = models.DecimalField(null=False, validators=[MinValueValidator(0)], max_digits=10, decimal_places=2)
    invoice = models.CharField(max_length=255, null=False)
    invoice_date = models.DateField(null=False)
    term_date = models.DateField(null=False)
    # status = models.BooleanField(null=False)
    status = models.CharField(max_length=1, choices=ORDER_STATUS)
    order_id = models.IntegerField(null=False, validators=[MinValueValidator(1)])
    supplier_id = models.IntegerField(null=False, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order_id

    def to_dict_json(self):
        return {
            'pk':self.pk,
            'invoice_date':self.invoice_date,
            'term_date':self.term_date,
            'status':self.status,
            'order_id':self.order_id,
            'supplier_id':self.supplier_id,
            'total':self.total
        }

class Item(models.Model):
    name = models.CharField(max_length=254, null=False)
    value = models.DecimalField(null=False, validators=[MinValueValidator(0)], max_digits=10, decimal_places=2)
    account = models.ForeignKey(CuentaPagar, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def uncommad(self):
        return str(self.value).replace(',', '.')

    class Meta:
        ordering = ('pk',)

class Payment(models.Model):
    account = models.ForeignKey(CuentaPagar, on_delete=models.CASCADE)
    bank = models.ForeignKey(CuentaEmpresa, on_delete=models.CASCADE)
    total = models.DecimalField(null=False, validators=[MinValueValidator(0)], max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CuentaCobrar(models.Model):
    tarifa = models.IntegerField()
    costo_total = models.IntegerField()
    Fecha_vencimiento = models.DateTimeField()
    estado = models.BooleanField()
    servicio = models.CharField(max_length=50)
    cuenta_empresa = models.ForeignKey(CuentaEmpresa, on_delete=models.CASCADE)