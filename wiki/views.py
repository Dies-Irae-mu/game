from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView
from .models import WikiPage, FeaturedImage
from django.db.models import Q, F
from django.db.models.functions import Length
from django.core.paginator import Paginator
import logging
from evennia.objects.models import ObjectDB
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
import markdown2

logger = logging.getLogger(__name__)

# Create your views here.

def page_list(request):
    """Show index page if one exists, otherwise show list of pages."""
    try:
        index_page = WikiPage.objects.get(is_index=True)
        return page_detail(request, index_page.slug)
    except WikiPage.DoesNotExist:
        pages = WikiPage.objects.all().order_by('title')
        return render(request, 'wiki/page_list.html', {'pages': pages})


def page_detail(request, slug):
    """Display a single wiki page."""
    page = get_object_or_404(WikiPage, slug=slug)
    
    # Check if the user has access to this page based on lock settings
    if page.lock_settings and not request.user.is_staff:
        has_access = False
        
        # Skip lock check for the creator
        if request.user.is_authenticated and page.creator and page.creator == request.user:
            has_access = True
        else:
            # Check lock settings against user's character
            has_access = check_character_access(request.user, page.lock_settings)
        
        if not has_access:
            raise Http404("Page not found")
    
    # Get featured articles - order by featured_order instead of title
    featured_articles = WikiPage.objects.filter(
        is_featured=True,
        published=True
    ).order_by('featured_order')[:10]  # Changed from order_by('title')
    
    # Get related articles
    related_articles = page.related_to.all().order_by('title')
    
    # Check if the current user can edit this page
    # Staff can always edit any page
    can_edit = False
    if request.user.is_authenticated:
        if request.user.is_staff:
            can_edit = True
        elif page.creator and page.creator == request.user:
            can_edit = True
        else:
            can_edit = page.can_edit(request.user)
    
    if page.content:
        page.processed_content = ''
    
    context = {
        'page': page,
        'featured_articles': featured_articles,
        'related_articles': related_articles,
        'can_edit': can_edit
    }
    
    return render(request, 'wiki/base_wiki.html', context)


def page_history(request, slug):
    """View revision history of a wiki page."""
    page = get_object_or_404(WikiPage, slug=slug)
    revisions = page.revisions.all()
    context = {'page': page, 'revisions': revisions}
    return render(request, 'wiki/page_history.html', context)


class WikiPageDetailView(DetailView):
    model = WikiPage
    template_name = 'wiki/page_detail.html'
    context_object_name = 'page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get featured articles, ordered by featured_order (including current page)
        context['featured_articles'] = WikiPage.objects.filter(
            is_featured=True,
            published=True
        ).order_by('featured_order')[:10]
        
        if self.object:
            context['related_articles'] = self.object.related_to.filter(
                published=True
            )
            
            # Check if the current user can edit this page
            context['can_edit'] = self.object.can_edit(self.request.user) if self.request.user.is_authenticated else False
        
        return context


def search_wiki(request):
    """Search wiki pages and characters by title/name and content."""
    query = request.GET.get('q', '').strip()
    wiki_results = []
    character_results = []
    
    logger.debug(f"Starting search with query: '{query}'")
    logger.debug(f"Request GET params: {dict(request.GET)}")
    
    try:
        if query:
            # Split query into words for better matching
            query_words = query.split()
            logger.debug(f"Query words: {query_words}")
            
            # Search Wiki Pages
            try:
                base_wiki_qs = WikiPage.objects.filter(published=True)
                title_q = Q()
                content_q = Q()
                for word in query_words:
                    title_q |= Q(title__icontains=word)
                    content_q |= Q(content__icontains=word)
                
                wiki_results = base_wiki_qs.filter(title_q | content_q).distinct()
                logger.debug(f"Wiki search SQL: {wiki_results.query}")
                logger.debug(f"Found {wiki_results.count()} wiki results")
            except Exception as e:
                logger.error(f"Error searching wiki pages: {str(e)}", exc_info=True)
                wiki_results = []
            
            # Search Characters - More carefully now
            try:
                # First get all character objects
                base_char_qs = ObjectDB.objects.filter(
                    db_typeclass_path__icontains='characters'
                ).exclude(
                    db_typeclass_path__icontains='npc'
                )
                logger.debug(f"Base character query found {base_char_qs.count()} characters")
                logger.debug(f"Character typeclass paths: {list(base_char_qs.values_list('db_typeclass_path', flat=True))}")
                
                # Build character search query more carefully
                char_results = []
                for character in base_char_qs:
                    score = 0
                    matches = False
                    
                    # Check character key (name)
                    char_name = character.key.lower()
                    for word in query_words:
                        word = word.lower()
                        if word in char_name:
                            matches = True
                            score += 50 if word == char_name else 10
                    
                    # Check attributes one by one
                    attr_fields = {
                        'biography': character.db.biography or "",
                        'rp_hooks': character.db.rp_hooks or "",
                        'full_name': character.db.full_name or "",
                        'appears_as': character.db.appears_as or "",
                        'occupation': character.db.occupation or "",
                        'affiliation': character.db.affiliation or ""
                    }
                    
                    for field_name, field_value in attr_fields.items():
                        if not isinstance(field_value, str):
                            logger.warning(f"Non-string value for {field_name} on character {character.key}: {type(field_value)}")
                            continue
                            
                        field_value = field_value.lower()
                        for word in query_words:
                            word = word.lower()
                            if word in field_value:
                                matches = True
                                score += 2
                    
                    if matches:
                        character.search_rank = score
                        character.result_type = 'character'
                        char_results.append(character)
                
                logger.debug(f"Found {len(char_results)} matching characters")
                character_results = char_results
                
            except Exception as e:
                logger.error(f"Error searching characters: {str(e)}", exc_info=True)
                character_results = []
            
            # Combine and sort all results
            all_results = []
            
            # Add wiki results
            for result in wiki_results:
                score = 0
                if result.title.lower() == query.lower():
                    score += 100
                elif query.lower() in result.title.lower():
                    score += 50
                title_word_matches = sum(1 for word in query_words if word.lower() in result.title.lower())
                score += title_word_matches * 10
                content_word_matches = sum(1 for word in query_words if word.lower() in result.content.lower())
                score += content_word_matches * 2
                result.search_rank = score
                result.result_type = 'wiki'
                all_results.append(result)
            
            # Add character results
            all_results.extend(character_results)
            
            # Sort results
            all_results.sort(key=lambda x: (-x.search_rank, x.key.lower() if hasattr(x, 'key') else x.title.lower()))
            
            logger.debug(f"Combined results before pagination: {len(all_results)} total")
            if all_results:
                logger.debug(f"First few results: {[r.key if hasattr(r, 'key') else r.title for r in all_results[:5]]}")
            
            # Pagination
            paginator = Paginator(all_results, 10)
            page = request.GET.get('page')
            results = paginator.get_page(page)
            
            logger.debug(f"Page number requested: {page}")
            logger.debug(f"Number of pages: {paginator.num_pages}")
            logger.debug(f"Results on current page: {len(results)}")
        else:
            results = []
            logger.debug("No query provided")
        
        # Get featured articles for navigation
        featured_articles = WikiPage.objects.filter(
            is_featured=True,
            published=True
        ).order_by('featured_order')
        
        context = {
            'query': query,
            'results': results,
            'featured_articles': featured_articles,
            'search_performed': bool(query)
        }
        
        return render(request, 'wiki/search_results.html', context)
        
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        context = {
            'query': query,
            'results': [],
            'featured_articles': WikiPage.objects.filter(is_featured=True, published=True).order_by('featured_order'),
            'search_performed': bool(query),
            'error': "An error occurred while performing the search."
        }
        return render(request, 'wiki/search_results.html', context)


def groups_index(request):
    """Display list of all group pages."""
    # Filter out locked group pages that the user can't access
    all_groups = WikiPage.get_groups().order_by('title')
    accessible_groups = []
    
    for group in all_groups:
        # Skip locked pages if user can't access them
        if group.lock_settings:
            if request.user.is_staff or (group.creator and group.creator == request.user):
                accessible_groups.append(group)
            elif request.user.is_authenticated and check_character_access(request.user, group.lock_settings):
                accessible_groups.append(group)
        else:
            accessible_groups.append(group)
    
    context = {
        'groups': accessible_groups,
        'featured_articles': WikiPage.objects.filter(
            is_featured=True,
            published=True
        ).order_by('featured_order')[:10],
        'can_create': request.user.is_authenticated,
    }
    
    return render(request, 'wiki/groups_index.html', context)


def plots_index(request):
    """Display list of all plot pages."""
    # Filter out locked plot pages that the user can't access
    all_plots = WikiPage.get_plots().order_by('title')
    accessible_plots = []
    
    for plot in all_plots:
        # Skip locked pages if user can't access them
        if plot.lock_settings:
            if request.user.is_staff or (plot.creator and plot.creator == request.user):
                accessible_plots.append(plot)
            elif request.user.is_authenticated and check_character_access(request.user, plot.lock_settings):
                accessible_plots.append(plot)
        else:
            accessible_plots.append(plot)
    
    context = {
        'plots': accessible_plots,
        'featured_articles': WikiPage.objects.filter(
            is_featured=True,
            published=True
        ).order_by('featured_order')[:10],
        'can_create': request.user.is_authenticated,
    }
    
    return render(request, 'wiki/plots_index.html', context)


@login_required
def create_page(request, page_type=WikiPage.REGULAR):
    """Create a new wiki page with the specified page type."""
    # Check permissions - only staff can create regular pages
    if page_type == WikiPage.REGULAR and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to create this type of page.")
    
    # Import lock data for dropdowns
    from world.wod20th.utils.stat_mappings import (
        CLAN, GAROU_TRIBE, VALID_SPLATS
    )
    from world.wod20th.locks import LOCK_FUNCS
    
    # Define available lock options
    available_locks = {
        'has_splat': VALID_SPLATS,
        'has_type': [], # Will be populated based on splat selection
        'has_clan': list(CLAN),
        'has_tribe': list(GAROU_TRIBE),
        'has_auspice': ['Ragabash', 'Galliard', 'Theurge', 'Ahroun', 'Philodox'],
        'has_tradition': ['Cultists of Ecstasy', 'Euthanatos', 'Celestial Chorus', 'Akashic Brotherhood',
                          'Dreamspeakers', 'Virtual Adepts', 'Order of Hermes', 'Verbena', 'Sons of Ether'],
        'has_affiliation': ['Traditions', 'Technocracy', 'Nephandi'],
        'has_convention': ['Iteration X', 'New World Order', 'Progenitor', 'Syndicate', 'Void Engineer'],
        'has_nephandi_faction': ['Herald of the Basilisk', 'Obliviate', 'Malfean', 'Baphie', 
                                  'Infernalist', 'Ironhand', 'Mammonite', "K'llashaa"],
        'has_court': ['Seelie', 'Unseelie'],
        'has_kith': ['Boggan', 'Clurichaun', 'Eshu', 'Nocker', 'Piskie', 'Pooka', 'Redcap', 'Satyr', 
                     'Selkie', 'Sidhe', 'Sluagh', 'Troll', 'Nunnehi', 'Inanimae'],
    }
    
    # Format lock names for display
    formatted_lock_names = {
        lock_type: lock_type.replace('_', ' ').replace('has ', 'Has ').title()
        for lock_type in available_locks.keys()
    }
    
    if request.method == 'POST':
        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        brief_description = request.POST.get('brief_description', '')
        banner_image = request.FILES.get('banner_image', None)
        featured_image = request.FILES.get('featured_image', None)
        show_texture = request.POST.get('show_texture', 'on') == 'on'
        
        # Process lock settings
        lock_settings = {}
        for lock_type in LOCK_FUNCS.keys():
            if request.POST.get(f'lock_{lock_type}', '') == 'on':
                lock_value = request.POST.get(f'lock_value_{lock_type}', '')
                if lock_value:
                    lock_settings[lock_type] = lock_value
        
        if not title:
            messages.error(request, "Title is required")
            return render(request, 'wiki/create_page.html', {
                'page_type': page_type,
                'available_locks': available_locks,
                'formatted_lock_names': formatted_lock_names
            })
        
        # Create the page
        page = WikiPage(
            title=title,
            content=content,
            brief_description=brief_description,
            page_type=page_type,
            lock_settings=lock_settings,
        )
        
        # Save with the current user
        page.save(current_user=request.user)
        
        # Handle images if provided
        if banner_image or featured_image:
            featured_img_obj = FeaturedImage(page=page, show_texture=show_texture)
            if banner_image:
                featured_img_obj.banner = banner_image
            if featured_image:
                featured_img_obj.image = featured_image
            featured_img_obj.save()
        
        messages.success(request, f"'{title}' has been created successfully!")
        return redirect(page.get_absolute_url())
    
    # Determine page type name for template context
    page_type_name = dict(WikiPage.PAGE_TYPE_CHOICES).get(page_type, 'Regular')
    
    return render(request, 'wiki/create_page.html', {
        'page_type': page_type,
        'page_type_name': page_type_name,
        'allow_html': True,  # Allow HTML in content
        'available_locks': available_locks,
        'formatted_lock_names': formatted_lock_names
    })


@login_required
def edit_page(request, slug, return_to=None):
    """Edit an existing wiki page."""
    page = get_object_or_404(WikiPage, slug=slug)
    
    # Import lock data for dropdowns
    from world.wod20th.utils.stat_mappings import (
        CLAN, GAROU_TRIBE, VALID_SPLATS
    )
    from world.wod20th.locks import LOCK_FUNCS
    
    # Define available lock options
    available_locks = {
        'has_splat': VALID_SPLATS,
        'has_type': [], # Will be populated based on splat selection
        'has_clan': list(CLAN),
        'has_tribe': list(GAROU_TRIBE),
        'has_auspice': ['Ragabash', 'Galliard', 'Theurge', 'Ahroun', 'Philodox'],
        'has_tradition': ['Cultists of Ecstasy', 'Euthanatos', 'Celestial Chorus', 'Akashic Brotherhood',
                          'Dreamspeakers', 'Virtual Adepts', 'Order of Hermes', 'Verbena', 'Sons of Ether'],
        'has_affiliation': ['Traditions', 'Technocracy', 'Nephandi'],
        'has_convention': ['Iteration X', 'New World Order', 'Progenitor', 'Syndicate', 'Void Engineer'],
        'has_nephandi_faction': ['Herald of the Basilisk', 'Obliviate', 'Malfean', 'Baphie', 
                                  'Infernalist', 'Ironhand', 'Mammonite', "K'llashaa"],
        'has_court': ['Seelie', 'Unseelie'],
        'has_kith': ['Boggan', 'Clurichaun', 'Eshu', 'Nocker', 'Piskie', 'Pooka', 'Redcap', 'Satyr', 
                     'Selkie', 'Sidhe', 'Sluagh', 'Troll', 'Nunnehi', 'Inanimae'],
    }
    
    # Format lock names for display
    formatted_lock_names = {
        lock_type: lock_type.replace('_', ' ').replace('has ', 'Has ').title()
        for lock_type in available_locks.keys()
    }
    
    # Check if user has permission to edit this page
    # Staff can always edit, otherwise check page permissions
    if request.user.is_staff:
        can_edit = True
    else:
        can_edit = page.can_edit(request.user)
    
    if not can_edit:
        return HttpResponseForbidden("You don't have permission to edit this page.")
    
    # Get or create featured image
    try:
        featured_image = page.featured_image
    except:
        featured_image = None
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        comment = request.POST.get('comment', '')
        brief_description = request.POST.get('brief_description', '') if page.page_type != WikiPage.REGULAR else ''
        
        # Process lock settings for all users who can edit the page
        if page.page_type in [WikiPage.GROUP, WikiPage.PLOT]:
            lock_settings = {}
            for lock_type in LOCK_FUNCS.keys():
                if request.POST.get(f'lock_{lock_type}', '') == 'on':
                    lock_value = request.POST.get(f'lock_value_{lock_type}', '')
                    if lock_value:
                        lock_settings[lock_type] = lock_value
            
            page.lock_settings = lock_settings
        
        # Update the page
        page.content = content
        
        # Update brief_description if this is a group or plot page
        if page.page_type in [WikiPage.GROUP, WikiPage.PLOT]:
            page.brief_description = brief_description
            
        # Handle the images for all users, not just staff
        banner_image = request.FILES.get('banner_image', None)
        featured_image_file = request.FILES.get('featured_image', None)
        show_texture = request.POST.get('show_texture', 'on') == 'on'
        
        if banner_image or featured_image_file or show_texture is not None:
            if not featured_image:
                featured_image = FeaturedImage(page=page)
            
            if banner_image:
                featured_image.banner = banner_image
            
            if featured_image_file:
                featured_image.image = featured_image_file
            
            featured_image.show_texture = show_texture
            featured_image.save()
        
        # Save the page with the current user
        page.save(current_user=request.user)
        
        # Create a revision
        page.revisions.create(
            content=content,
            editor=request.user,
            comment=comment
        )
        
        messages.success(request, f"'{page.title}' has been updated successfully!")
        
        # Determine where to redirect based on page type or return_to parameter
        if return_to == 'group' or page.page_type == WikiPage.GROUP:
            return redirect('wiki:group_detail', slug=page.slug)
        elif return_to == 'plot' or page.page_type == WikiPage.PLOT:
            return redirect('wiki:plot_detail', slug=page.slug)
        else:
            return redirect(page.get_absolute_url())
    
    # Always allow image uploads for users who can edit the page
    can_upload_images = True
    
    context = {
        'page': page,
        'featured_image': featured_image,
        'allow_html': True,  # Allow HTML in content
        'can_upload_images': can_upload_images,
        'available_locks': available_locks,
        'formatted_lock_names': formatted_lock_names
    }
    
    # Add return_to to context if provided
    if return_to:
        context['return_to'] = return_to
    
    # Use edit_page.html template for all users who can edit the page
    return render(request, 'wiki/edit_page.html', context)


@login_required
@require_POST
def preview_markdown(request):
    """Preview markdown content."""
    content = request.POST.get('content', '')
    
    # Use markdown2 (or any other markdown library you prefer)
    markdowner = markdown2.Markdown(extras=[
        'fenced-code-blocks',
        'tables',
        'break-on-newline',
        'header-ids',
        'strike',
        'footnotes'
    ])
    
    # Convert markdown to HTML
    html = markdowner.convert(content)

    return JsonResponse({
        'success': True,
        'html': html
    })


def create_group(request):
    """Create a new group page."""
    return create_page(request, page_type=WikiPage.GROUP)


def create_plot(request):
    """Create a new plot page."""
    return create_page(request, page_type=WikiPage.PLOT)


def group_detail(request, slug):
    """Display a group wiki page."""
    page = get_object_or_404(WikiPage, slug=slug, page_type=WikiPage.GROUP)
    
    # Check if the user has access to this page based on lock settings
    if page.lock_settings and not request.user.is_staff:
        has_access = False
        
        # Skip lock check for the creator
        if request.user.is_authenticated and page.creator and page.creator == request.user:
            has_access = True
        else:
            # Check lock settings against user's character
            has_access = check_character_access(request.user, page.lock_settings)
        
        if not has_access:
            raise Http404("Page not found")
    
    # Get featured articles
    featured_articles = WikiPage.objects.filter(
        is_featured=True,
        published=True
    ).order_by('featured_order')[:10]
    
    # Get related articles
    related_articles = page.related_to.all().order_by('title')
    
    # Check if the current user can edit this page
    can_edit = False
    if request.user.is_authenticated:
        if request.user.is_staff:
            can_edit = True
        elif page.creator and page.creator == request.user:
            can_edit = True
        else:
            can_edit = page.can_edit(request.user)
    
    # Process mermaid diagrams in content
    if page.content:
        page.processed_content = ''
    
    context = {
        'page': page,
        'featured_articles': featured_articles,
        'related_articles': related_articles,
        'can_edit': can_edit,
        'is_group_page': True
    }
    
    return render(request, 'wiki/base_wiki.html', context)


def plot_detail(request, slug):
    """Display a plot wiki page."""
    page = get_object_or_404(WikiPage, slug=slug, page_type=WikiPage.PLOT)
    
    # Check if the user has access to this page based on lock settings
    if page.lock_settings and not request.user.is_staff:
        has_access = False
        
        # Skip lock check for the creator
        if request.user.is_authenticated and page.creator and page.creator == request.user:
            has_access = True
        else:
            # Check lock settings against user's character
            has_access = check_character_access(request.user, page.lock_settings)
        
        if not has_access:
            raise Http404("Page not found")
    
    # Get featured articles
    featured_articles = WikiPage.objects.filter(
        is_featured=True,
        published=True
    ).order_by('featured_order')[:10]
    
    # Get related articles
    related_articles = page.related_to.all().order_by('title')
    
    # Check if the current user can edit this page
    can_edit = False
    if request.user.is_authenticated:
        if request.user.is_staff:
            can_edit = True
        elif page.creator and page.creator == request.user:
            can_edit = True
        else:
            can_edit = page.can_edit(request.user)
    
    # Process mermaid diagrams in content
    if page.content:
        page.processed_content = ''
    
    context = {
        'page': page,
        'featured_articles': featured_articles,
        'related_articles': related_articles,
        'can_edit': can_edit,
        'is_plot_page': True
    }
    
    return render(request, 'wiki/base_wiki.html', context)


@login_required
def edit_group(request, slug):
    """Edit a group wiki page."""
    # Get the group page
    page = get_object_or_404(WikiPage, slug=slug, page_type=WikiPage.GROUP)
    
    # Redirect to the standard edit page view with a return_to parameter
    return edit_page(request, slug, return_to='group')


@login_required
def edit_plot(request, slug):
    """Edit a plot wiki page."""
    # Get the plot page
    page = get_object_or_404(WikiPage, slug=slug, page_type=WikiPage.PLOT)
    
    # Redirect to the standard edit page view with a return_to parameter
    return edit_page(request, slug, return_to='plot')


def check_character_access(user, lock_settings):
    """
    Check if user's character meets the lock requirements
    
    Args:
        user: User object
        lock_settings: Dictionary of lock settings
        
    Returns:
        bool: True if user's character has access, False otherwise
    """
    # If no locks or user is staff, always grant access
    if not lock_settings or user.is_staff:
        return True
        
    # If user is not authenticated, deny access
    if not user.is_authenticated:
        return False
    
    # Get user's characters
    if not hasattr(user, 'characters') or not user.characters:
        return False
    
    # Check each character for any that satisfy the lock conditions
    for character_ref in user.characters:
        character = character_ref
        
        # Skip if character is not approved
        if hasattr(character, 'db') and not character.db.approved:
            continue
        
        # Group locks by related categories
        splat_check = None
        type_check = None
        
        # First check basic splat access
        if 'has_splat' in lock_settings:
            splat_check = check_lock_condition(character, 'has_splat', lock_settings['has_splat'])
            if not splat_check:
                continue  # If character doesn't meet the splat requirement, skip to next character
        
        # Check type if splat passed and type lock exists
        if splat_check and 'has_type' in lock_settings:
            type_check = check_lock_condition(character, 'has_type', lock_settings['has_type'])
            if not type_check:
                continue  # If character doesn't meet the type requirement, skip to next character
        
        # Check other locks based on character type
        # For Shifters
        if (splat_check and lock_settings.get('has_splat') == 'Shifter'):
            # If there's a tribe lock, check it
            if 'has_tribe' in lock_settings and not check_lock_condition(character, 'has_tribe', lock_settings['has_tribe']):
                continue
                
            # If there's an auspice lock, check it (primarily for Garou)
            if type_check and lock_settings.get('has_type') == 'Garou' and 'has_auspice' in lock_settings:
                if not check_lock_condition(character, 'has_auspice', lock_settings['has_auspice']):
                    continue
        
        # For Vampires
        elif (splat_check and lock_settings.get('has_splat') == 'Vampire'):
            # If there's a clan lock, check it
            if 'has_clan' in lock_settings and not check_lock_condition(character, 'has_clan', lock_settings['has_clan']):
                continue
        
        # For Mages
        elif (splat_check and lock_settings.get('has_splat') == 'Mage'):
            # Check relevant mage locks
            if 'has_tradition' in lock_settings and not check_lock_condition(character, 'has_tradition', lock_settings['has_tradition']):
                continue
            if 'has_affiliation' in lock_settings and not check_lock_condition(character, 'has_affiliation', lock_settings['has_affiliation']):
                continue
            if 'has_convention' in lock_settings and not check_lock_condition(character, 'has_convention', lock_settings['has_convention']):
                continue
            if 'has_nephandi_faction' in lock_settings and not check_lock_condition(character, 'has_nephandi_faction', lock_settings['has_nephandi_faction']):
                continue
        
        # For Changelings
        elif (splat_check and lock_settings.get('has_splat') == 'Changeling'):
            # Check changeling-specific locks
            if 'has_court' in lock_settings and not check_lock_condition(character, 'has_court', lock_settings['has_court']):
                continue
            if 'has_kith' in lock_settings and not check_lock_condition(character, 'has_kith', lock_settings['has_kith']):
                continue
        
        # If we made it this far, the character has passed all relevant checks
        return True
    
    # No character passed all checks
    return False


def check_lock_condition(character, lock_type, lock_value):
    """
    Check if character meets a specific lock condition
    
    Args:
        character: Character object
        lock_type: Type of lock (e.g., 'has_splat', 'has_clan')
        lock_value: Value to check against (e.g., 'Vampire', 'Brujah')
        
    Returns:
        bool: True if character meets the condition, False otherwise
    """
    from world.wod20th.locks import LOCK_FUNCS
    
    # Get the lock function
    lock_func = LOCK_FUNCS.get(lock_type)
    if not lock_func:
        return False
    
    # Call the lock function with character and lock value
    return lock_func(character, None, lock_value)
