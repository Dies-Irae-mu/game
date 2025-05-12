"""
Views for the NPC Manager app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from evennia.utils.search import search_object

@staff_member_required
def index(request):
    """
    Main index page for NPC Manager.
    """
    # Import here to avoid circular imports
    from .models import NPC, NPCGroup
    from .utils import sync_all_npcs, sync_all_groups
    
    # Get counts
    npc_count = NPC.objects.count()
    group_count = NPCGroup.objects.count()
    
    # Get recent NPCs and groups
    recent_npcs = NPC.objects.all().order_by('-db_date_created')[:5]
    recent_groups = NPCGroup.objects.all().order_by('-db_date_created')[:5]
    
    # Check if there are in-game NPCs that aren't in the database
    in_game_npcs = search_object(None, typeclass="typeclasses.npcs.NPC")
    in_game_npc_count = len(in_game_npcs)
    
    # Check if there are in-game NPC Groups that aren't in the database
    in_game_groups = search_object(None, typeclass="typeclasses.npc_groups.NPCGroup")
    in_game_group_count = len(in_game_groups)
    
    context = {
        'npc_count': npc_count,
        'group_count': group_count,
        'recent_npcs': recent_npcs,
        'recent_groups': recent_groups,
        'in_game_npc_count': in_game_npc_count,
        'in_game_group_count': in_game_group_count,
        'sync_needed': (in_game_npc_count > npc_count or in_game_group_count > group_count),
    }
    
    return render(request, 'npc_manager/index.html', context)

@staff_member_required
def npc_list(request):
    """
    List all NPCs.
    """
    # Import here to avoid circular imports
    from .models import NPC
    
    # Get filter parameters
    splat = request.GET.get('splat')
    temporary = request.GET.get('temporary')
    group = request.GET.get('group')
    query = request.GET.get('q')
    
    # Start with all NPCs
    npcs = NPC.objects.all()
    
    # Apply filters
    if splat:
        npcs = npcs.filter(db_splat=splat)
    if temporary:
        is_temp = temporary.lower() == 'true'
        npcs = npcs.filter(db_is_temporary=is_temp)
    if group:
        npcs = npcs.filter(db_group__db_key__icontains=group)
    if query:
        npcs = npcs.filter(db_key__icontains=query)
    
    # Sort by key
    npcs = npcs.order_by('db_key')
    
    # Paginate
    paginator = Paginator(npcs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique splat types and groups for filter dropdowns
    splat_types = NPC.objects.values_list('db_splat', flat=True).distinct()
    
    context = {
        'npcs': page_obj,
        'splat_types': splat_types,
        'query': query,
        'splat': splat,
        'temporary': temporary,
        'group': group,
    }
    
    return render(request, 'npc_manager/npc_list.html', context)

@staff_member_required
def npc_detail(request, npc_id):
    """
    Show details for a specific NPC.
    """
    # Import here to avoid circular imports
    from .models import NPC
    
    npc = get_object_or_404(NPC, id=npc_id)
    
    context = {
        'npc': npc,
    }
    
    return render(request, 'npc_manager/npc_detail.html', context)

@staff_member_required
def group_list(request):
    """
    List all NPC Groups.
    """
    # Import here to avoid circular imports
    from .models import NPCGroup
    
    # Get filter parameters
    group_type = request.GET.get('type')
    splat = request.GET.get('splat')
    query = request.GET.get('q')
    
    # Start with all groups
    groups = NPCGroup.objects.all()
    
    # Apply filters
    if group_type:
        groups = groups.filter(db_group_type__icontains=group_type)
    if splat:
        groups = groups.filter(db_splat=splat)
    if query:
        groups = groups.filter(db_key__icontains=query)
    
    # Sort by key
    groups = groups.order_by('db_key')
    
    # Paginate
    paginator = Paginator(groups, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique group types and splat types for filter dropdowns
    group_types = NPCGroup.objects.values_list('db_group_type', flat=True).distinct()
    splat_types = NPCGroup.objects.values_list('db_splat', flat=True).distinct()
    
    context = {
        'groups': page_obj,
        'group_types': group_types,
        'splat_types': splat_types,
        'query': query,
        'type': group_type,
        'splat': splat,
    }
    
    return render(request, 'npc_manager/group_list.html', context)

@staff_member_required
def group_detail(request, group_id):
    """
    Show details for a specific NPC Group.
    """
    # Import here to avoid circular imports
    from .models import NPCGroup
    
    group = get_object_or_404(NPCGroup, id=group_id)
    
    context = {
        'group': group,
        'npcs': group.npcs.all().order_by('db_key'),
        'goals': group.goals.all().order_by('db_order'),
    }
    
    return render(request, 'npc_manager/group_detail.html', context)

@staff_member_required
def sync_npcs(request):
    """
    Synchronize NPCs and NPC Groups between the database and game objects.
    """
    # Import here to avoid circular imports
    from .utils import sync_all_npcs, sync_all_groups
    
    if request.method == 'POST':
        # Run the sync
        npcs_created, npcs_updated = sync_all_npcs()
        groups_created, groups_updated = sync_all_groups()
        
        # Add message
        messages.success(
            request, 
            f"Sync complete: {npcs_created} NPCs created, {npcs_updated} NPCs updated, "
            f"{groups_created} groups created, {groups_updated} groups updated."
        )
        
        # Redirect to index
        return redirect('npc_manager:index')
    
    return render(request, 'npc_manager/sync.html') 