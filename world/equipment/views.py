from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Equipment
from .forms import EquipmentForm

@login_required
def equipment_list(request):
    """List all equipment items."""
    equipment = Equipment.objects.all().order_by('sequential_id')
    return render(request, 'equipment_list.html', {'equipment': equipment})

@login_required
def add_equipment(request):
    """Add a new equipment item."""
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            # The sequential_id will be automatically assigned by the Equipment model's save() method
            # The category-specific details will be handled by the form's save method
            equipment = form.save()
            messages.success(request, f'Equipment {equipment.name} (ID #{equipment.sequential_id}) added successfully with specific {equipment.category} properties.')
            return redirect('equipment_list')
        else:
            # Check for category-specific field errors
            category = request.POST.get('category')
            if category:
                messages.error(request, f'Please fill in all required fields for the {category} category.')
    else:
        form = EquipmentForm()
    
    return render(request, 'equipment_form.html', {'form': form})

@login_required
def edit_equipment(request, pk):
    """Edit an existing equipment item."""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            # Save the form but don't modify the sequential_id which is read-only
            # The category-specific details will be updated by the form's save method
            updated_equipment = form.save()
            messages.success(request, f'Equipment {updated_equipment.name} (ID #{updated_equipment.sequential_id}) updated successfully.')
            return redirect('equipment_list')
        else:
            # Check for category-specific field errors
            category = request.POST.get('category')
            if category:
                messages.error(request, f'Please fill in all required fields for the {category} category.')
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'equipment_form.html', {'form': form, 'category': equipment.category})

@login_required
def delete_equipment(request, pk):
    """Delete an equipment item."""
    equipment = get_object_or_404(Equipment, pk=pk)
    if request.method == 'POST':
        # Note: related category-specific details will be deleted automatically due to on_delete=CASCADE
        equipment.delete()
        messages.success(request, 'Equipment deleted successfully.')
    return redirect('equipment_list') 