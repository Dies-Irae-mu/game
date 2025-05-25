from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Group
from django.utils.text import slugify
from evennia.utils import logger
# We'll add signal handlers here if needed in the future

@receiver(post_save, sender=Group)
def create_wiki_page_for_group(sender, instance, created, **kwargs):
    """
    Signal handler to create a wiki page for a newly created group.
    """
    if created:
        try:
            # Import here to avoid circular imports
            from wiki.models import WikiPage
            
            # Create a slug from the group name
            slug = slugify(instance.name)
            
            # Check if a wiki page with this slug already exists
            if not WikiPage.objects.filter(slug=slug).exists():
                # Create the wiki page
                wiki_page = WikiPage.objects.create(
                    title=instance.name,
                    slug=slug,
                    content=instance.description or f"Wiki page for {instance.name}",
                    page_type=WikiPage.GROUP,
                    mush_group=instance,
                    published=True
                )
                logger.log_info(f"Created wiki page for group {instance.name}")
            else:
                # If a page with this slug exists, try to find an unused slug
                new_slug = f"{slug}-{instance.group_id}"
                if not WikiPage.objects.filter(slug=new_slug).exists():
                    wiki_page = WikiPage.objects.create(
                        title=instance.name,
                        slug=new_slug,
                        content=instance.description or f"Wiki page for {instance.name}",
                        page_type=WikiPage.GROUP,
                        mush_group=instance,
                        published=True
                    )
                    logger.log_info(f"Created wiki page for group {instance.name} with slug {new_slug}")
                else:
                    logger.log_err(f"Could not create wiki page for group {instance.name} - slug conflict")
        except Exception as e:
            logger.log_err(f"Error creating wiki page for group {instance.name}: {e}")
