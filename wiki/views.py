from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView
from .models import WikiPage
from django.db.models import Q, F
from django.db.models.functions import Length
from django.core.paginator import Paginator
import logging
from evennia.objects.models import ObjectDB

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
    
    # Get featured articles - order by featured_order instead of title
    featured_articles = WikiPage.objects.filter(
        is_featured=True,
        published=True
    ).order_by('featured_order')[:10]  # Changed from order_by('title')
    
    # Get related articles
    related_articles = page.related_to.all().order_by('title')
    
    context = {
        'page': page,
        'featured_articles': featured_articles,
        'related_articles': related_articles
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
